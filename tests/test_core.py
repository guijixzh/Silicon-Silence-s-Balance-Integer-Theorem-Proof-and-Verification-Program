#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核心库单元测试 / Unit tests for sst_core.

运行 / Run:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from fractions import Fraction
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sst_core as core  # noqa: E402


class ValueSetTests(unittest.TestCase):
    """值集计算 / value-set computation."""

    def test_small_values(self):
        self.assertEqual(core.values("1"), frozenset({Fraction(1)}))
        self.assertEqual(core.values("12"),
                         frozenset({Fraction(12), Fraction(3), Fraction(-1),
                                    Fraction(2), Fraction(1, 2)}))

    def test_segment_value_set_includes_leading_minus(self):
        # 1433 -> (-1)+4 = 3 / leading minus is available in segment mode
        self.assertIn(Fraction(3), core.segment_values("14"))
        self.assertNotIn(Fraction(3), core.values("14"))

    def test_expr_maps_match_value_sets(self):
        # 全部长度 <= 3 的数字串 + 长度 4 抽样 / all <= 3 plus length-4 samples
        samples = ["".join(items) for length in (1, 2, 3)
                   for items in product(core.DIGITS_ALL, repeat=length)]
        samples += ["1234", "1433", "1002", "0101", "9999", "5150",
                    "4444", "8985", "1919", "7777"]
        for number in samples:
            with self.subTest(number=number):
                self.assertEqual(frozenset(core.expr_map(number)),
                                 core.segment_values(number))
                self.assertEqual(frozenset(core._strict_expr_map(number)),
                                 core.values(number))

    def test_segment_values_equal_sign_closure(self):
        # 段首负号值集 = 严格值集的 ± 闭包（长度 <= 3 全量抽查）
        # segment value set equals the sign closure of the strict set
        for length in (1, 2, 3):
            for items in product(core.DIGITS_NONZERO, repeat=length):
                number = "".join(items)
                with self.subTest(number=number):
                    closed = set(core.values(number))
                    closed |= {-value for value in core.values(number)}
                    self.assertEqual(set(core.segment_values(number)), closed)

    def test_no_leading_zero_tokens_in_witnesses(self):
        for number in ["1010101", "1204", "1002001", "0150", "9090909"]:
            with self.subTest(number=number):
                for expression, _op in core.expr_map(number).values():
                    for token in expression.replace("(", " ").replace(")", " ") \
                                            .replace("+", " ").replace("-", " ") \
                                            .replace("*", " ").replace("/", " ").split():
                        self.assertFalse(len(token) > 1 and token.startswith("0"),
                                         f"leading-zero token in {expression}")


class ZeroTests(unittest.TestCase):
    """可归零判定 / zeroability."""

    CASES = {"11": True, "12": False, "113": True, "125": False,
             "114": True, "141": False, "1204": True, "8985898": False,
             "9896989": True, "0": False}

    def test_can_zero(self):
        for number, expected in self.CASES.items():
            with self.subTest(number=number):
                self.assertEqual(core.can_zero(number), expected)

    def test_can_zero_equivalent_to_expression_value(self):
        # 可归零 <=> 存在插符表达式取值为 0 / 0 in segment_values for length >= 2
        for number, expected in self.CASES.items():
            if len(number) < 2:
                continue
            with self.subTest(number=number):
                self.assertEqual(expected, Fraction(0) in core.segment_values(number))


class BalanceTests(unittest.TestCase):
    """平衡化搜索 / balancing search."""

    def test_two_segment_examples(self):
        witness = core.find_balance("1234", max_segments=2)
        self.assertIsNotNone(witness)
        self.assertEqual(witness.equals_count, 1)
        self.assertTrue(core.verify_equation(witness.expression, "1234"))

    def test_weak_multi_segment_example(self):
        witness = core.find_balance("222")
        self.assertIsNotNone(witness)
        self.assertEqual(witness.equals_count, 2)
        self.assertTrue(core.verify_equation(witness.expression, "222"))
        self.assertIsNone(core.find_balance("222", max_segments=2))

    def test_known_non_balanceable(self):
        for number in ["113", "125", "8985898", "9989858", "10", "12"]:
            with self.subTest(number=number):
                self.assertIsNone(core.find_balance(number))

    def test_strict_rule_can_differ(self):
        # 1433 只在允许段首负号时可平衡 / weak only with a leading minus
        self.assertIsNotNone(core.find_balance("1433"))
        self.assertIsNone(core.find_balance("1433", strict=True))

    def test_every_witness_reconstructs_and_balances(self):
        for number in ["114514", "1919810", "1234", "222", "1433", "555", "7777"]:
            witness = core.find_balance(number)
            if witness is None:
                continue
            with self.subTest(number=number):
                self.assertEqual("".join(witness.segments), number)
                self.assertTrue(core.verify_equation(witness.expression, number))


class EvaluationTests(unittest.TestCase):
    """表达式求值 / expression evaluation."""

    def test_eval_fraction(self):
        self.assertEqual(core.eval_fraction("1 + 2 * 3"), Fraction(7))
        self.assertEqual(core.eval_fraction("(1 + 2) * 3"), Fraction(9))
        self.assertEqual(core.eval_fraction("-1 + 4"), Fraction(3))
        self.assertEqual(core.eval_fraction("1 - (2 + 3)"), Fraction(-4))
        self.assertEqual(core.eval_fraction("12 / (3 * 4)"), Fraction(1))

    def test_verify_equation(self):
        self.assertTrue(core.verify_equation("12=3 * 4", "1234"))
        self.assertTrue(core.verify_equation("2=2=2", "222"))
        self.assertFalse(core.verify_equation("12=3 * 5", "1235"))
        self.assertFalse(core.verify_equation("12=3 * 4", "1235"))


class IoTests(unittest.TestCase):
    """数据读写 / data I/O."""

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "numbers.json"
            core.save_numbers(path, ["111", "11", "1", "2222"])
            loaded = core.load_numbers(path)
            self.assertEqual(loaded, ["1", "11", "111", "2222"])
            with open(path, "r", encoding="utf-8") as handle:
                self.assertEqual(json.load(handle), loaded)

    def test_classification_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "classification.json"
            mapping = {"222": "2=2=2", "113": None, "12": None}
            core.save_classification(path, mapping)
            loaded = core.load_classification(path)
            self.assertEqual(loaded, {"12": None, "113": None, "222": "2=2=2"})


if __name__ == "__main__":
    unittest.main()
