#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证脚本 / Verification script.

A. 数据一致性 / Data consistency
   - 计数、最大值、排序、去重 / counts, maxima, canonical order, uniqueness
   - 集合关系：分类表键、强/弱名单与不可平衡表一致
     set relations between classification / strong / weak / non-balanceable
   - 弱不可平衡串的见证等式逐条求值验证
     validate every witness equation of the weak non-balanceable strings
B. 小规模全量复算 / Small-scale exhaustive recomputation
   - 对全部长度 <= N（默认 5）的数字串独立复算：
     可归零性、二分割可平衡性、以及（长度 <= 4 时）强/弱分类，
     并与发布数据逐条比对 / recompute zeroability, 2-cut balanceability and
     multi-segment classification from scratch and compare with shipped data
C. --deep 全量复核 / full re-check
   - 对全部 2873 不可归零串复核不可归零、19515 不可平衡串复核无二分割解、
     18198 强不可平衡串复核无多分割解 / re-check every shipped entry

退出码 / Exit code: 0 = 全部通过 / all checks passed, 1 = 存在不一致 / mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sst_core as core  # noqa: E402

EXPECTED_COUNTS = {
    "prime_zeroable": 6534,
    "non_zeroable": 2873,
    "non_balanceable": 19515,
    "strong_non_balanceable": 18198,
    "weak_non_balanceable": 1317,
}
EXPECTED_MAXIMA = {
    "non_zeroable": "8985898",
    "prime_zeroable": "9896989",
    "non_balanceable": "9989858",
    "strong_non_balanceable": "9989858",
}


class Report:
    """简单的双语报告器 / Tiny bilingual reporter."""

    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet
        self.errors: List[str] = []
        self.checks = 0

    def check(self, condition: bool, message: str) -> bool:
        self.checks += 1
        if not condition:
            self.errors.append(message)
            if not self.quiet:
                print(f"  [失败 / FAIL] {message}")
        return condition

    def info(self, message: str) -> None:
        if not self.quiet:
            print(message)


def _sorted_canonical(numbers: Sequence[str]) -> bool:
    return list(numbers) == core.sort_numbers(numbers)


def check_data_consistency(data_dir: Path, report: Report):
    """A. 数据一致性 / data consistency."""
    report.info("A. 数据一致性检查 / data consistency")
    names = ["prime_zeroable", "non_zeroable", "non_balanceable",
             "strong_non_balanceable", "weak_non_balanceable"]
    lists: Dict[str, List[str]] = {}
    for name in names:
        path = data_dir / f"{name}.json"
        if not report.check(path.exists(), f"缺少文件 / missing file: {path}"):
            return None
        lists[name] = core.load_numbers(path)
        values = lists[name]
        report.check(len(values) == len(set(values)),
                     f"{name}: 存在重复 / duplicates found")
        report.check(_sorted_canonical(values),
                     f"{name}: 排序不规范 / not in canonical order")
        report.check(len(values) == EXPECTED_COUNTS[name],
                     f"{name}: 计数 {len(values)} != 期望 / expected {EXPECTED_COUNTS[name]}")
        if values:
            largest = max(values, key=lambda s: (len(s), s))
            expected = EXPECTED_MAXIMA.get(name)
            if expected is not None:
                report.check(largest == expected,
                             f"{name}: 最大值 {largest} != 期望 / expected {expected}")

    classification_path = data_dir / "classification.json"
    if not report.check(classification_path.exists(),
                        f"缺少文件 / missing file: {classification_path}"):
        return None
    classification = core.load_classification(classification_path)
    report.check(len(classification) == len(lists["non_balanceable"]),
                 "classification: 条目数与不可平衡表不符 / size mismatch")
    report.check(set(classification) == set(lists["non_balanceable"]),
                 "classification: 键与不可平衡表不符 / key set mismatch")
    strong = {key for key, value in classification.items() if value is None}
    weak = {key for key, value in classification.items() if value is not None}
    report.check(strong == set(lists["strong_non_balanceable"]),
                 "classification: 强不可平衡集合与 strong 文件不符 / strong mismatch")
    report.check(weak == set(lists["weak_non_balanceable"]),
                 "classification: 弱不可平衡集合与 weak 文件不符 / weak mismatch")

    # 见证等式验证 / validate witness equations
    bad_witness = []
    for number, expression in classification.items():
        if expression is None:
            continue
        if not core.verify_equation(expression, number):
            bad_witness.append((number, expression))
    report.check(not bad_witness,
                 f"存在无效见证等式 / invalid witnesses: {bad_witness[:3]} "
                 f"(共/共 {len(bad_witness)})")

    # 不可归零串不含数字 0 / non-zeroable strings never contain 0
    with_zero = [s for s in lists["non_zeroable"] if "0" in s]
    report.check(not with_zero,
                 f"不可归零串含 0 / non-zeroable with zero: {with_zero[:5]}")

    # 表内键均由数字组成 / keys are digit strings
    bad_keys = [s for s in lists["non_balanceable"] if not s.isdigit()]
    report.check(not bad_keys, f"存在非数字键 / non-digit keys: {bad_keys[:5]}")
    return lists, classification


def check_small_scale(lists: Dict[str, List[str]], max_length: int,
                      classify_max: int, report: Report) -> None:
    """B. 小规模全量复算 / small-scale exhaustive recomputation."""
    report.info(f"B. 小规模全量复算（长度 <= {max_length}，分类 <= {classify_max}）"
                f" / small-scale exhaustive recomputation")
    nz_set = set(lists["non_zeroable"])
    nb_set = set(lists["non_balanceable"])
    strong_set = set(lists["strong_non_balanceable"])
    start = time.time()

    checked = {"zero": 0, "two_cut": 0, "classify": 0}
    zero_errors: List[str] = []
    two_cut_errors: List[str] = []
    classify_errors: List[str] = []

    for length in range(1, max_length + 1):
        tails = [""] if length == 1 else list(_strings_over(core.DIGITS_ALL, length - 1))
        for first in core.DIGITS_NONZERO:
            for tail in tails:
                number = first + tail
                # 可归零 / zeroability（数据只覆盖不含 0 的数字串）
                if "0" not in number:
                    expected_zeroable = number not in nz_set
                    if core.can_zero(number) != expected_zeroable:
                        zero_errors.append(number)
                    checked["zero"] += 1
                # 二分割可平衡性 / 2-cut balanceability
                if length >= 2:
                    expected_nonbal = number in nb_set
                    found = core.find_balance(number, max_segments=2) is not None
                    if found == expected_nonbal:
                        two_cut_errors.append(number)
                    checked["two_cut"] += 1
                # 强/弱分类 / strong-weak classification
                if length >= 2 and length <= classify_max:
                    expected_strong = number in strong_set
                    found = core.find_balance(number) is not None
                    if found == expected_strong:
                        classify_errors.append(number)
                    checked["classify"] += 1

    report.check(not zero_errors,
                 f"可归零复算不一致 / zeroability mismatches: {zero_errors[:5]} "
                 f"(共/共 {len(zero_errors)})")
    report.check(not two_cut_errors,
                 f"二分割复算不一致 / 2-cut mismatches: {two_cut_errors[:5]} "
                 f"(共/共 {len(two_cut_errors)})")
    report.check(not classify_errors,
                 f"强弱分类复算不一致 / classification mismatches: {classify_errors[:5]} "
                 f"(共/共 {len(classify_errors)})")
    report.info(f"  复算条目 / recomputed: 可归零 {checked['zero']}, "
                f"二分割 {checked['two_cut']}, 分类 {checked['classify']}; "
                f"用时 / {time.time() - start:.1f}s")


def _strings_over(alphabet: str, length: int):
    """生成长度为 length 的字母表字符串 / generate strings of given length."""
    if length == 0:
        yield ""
        return
    for prefix in _strings_over(alphabet, length - 1):
        for char in alphabet:
            yield prefix + char


def check_deep(lists: Dict[str, List[str]], report: Report) -> None:
    """C. 全量复核 / full re-check of every shipped entry."""
    report.info("C. 全量复核 / full re-check")
    start = time.time()
    for number in lists["non_zeroable"]:
        if core.can_zero(number):
            report.check(False, f"可归零串被误列入不可归零 / zeroable in non-zeroable: {number}")
    report.info(f"  不可归零串复核完毕 / non-zeroable re-checked ({time.time() - start:.1f}s)")
    start = time.time()
    for number in lists["non_balanceable"]:
        if core.find_balance(number, max_segments=2) is not None:
            report.check(False, f"存在二分割解的串被误列入 / 2-cut solution found: {number}")
    report.info(f"  不可平衡串二分割复核完毕 / 2-cut re-checked ({time.time() - start:.1f}s)")
    start = time.time()
    for number in lists["strong_non_balanceable"]:
        if core.find_balance(number) is not None:
            report.check(False, f"强不可平衡串存在解 / solution found: {number}")
    report.info(f"  强不可平衡串复核完毕 / strong re-checked ({time.time() - start:.1f}s)")


def check_manifest(data_dir: Path, report: Report) -> None:
    """校验 manifest.json 中的哈希 / verify hashes recorded in manifest.json."""
    path = data_dir / "manifest.json"
    if not path.exists():
        report.info("未发现 manifest.json，跳过 / manifest.json not found, skipped")
        return
    with open(path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    for name, expected in manifest.get("sha256", {}).items():
        file_path = data_dir / name
        if not file_path.exists():
            report.check(False, f"manifest: 缺少文件 / missing {name}")
            continue
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        report.check(digest == expected,
                     f"manifest: {name} 哈希不符 / hash mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(description="验证 SS 定理数据与复算 / verify data")
    parser.add_argument("-d", "--data-dir", type=Path, default=core.DATA_DIR,
                        help="数据目录 / data directory")
    parser.add_argument("-n", "--max-length", type=int, default=5,
                        help="小规模复算的最大长度（默认 5）/ max length (default: 5)")
    parser.add_argument("--classify-max-length", type=int, default=4,
                        help="强弱分类复算的最大长度（默认 4）/ classification max length")
    parser.add_argument("--deep", action="store_true",
                        help="对全部发布数据逐条复核 / re-check every shipped entry")
    parser.add_argument("--skip-manifest", action="store_true",
                        help="跳过 manifest 校验 / skip manifest check")
    parser.add_argument("--quiet", action="store_true",
                        help="精简输出 / quiet output")
    args = parser.parse_args()

    report = Report(quiet=args.quiet)
    print("SS 定理验证 / SS Theorem verification")
    print(f"数据目录 / data directory : {args.data_dir}")
    loaded = check_data_consistency(args.data_dir, report)
    if loaded is not None:
        lists, _classification = loaded
        check_small_scale(lists, args.max_length, args.classify_max_length, report)
        if args.deep:
            check_deep(lists, report)
    if not args.skip_manifest:
        check_manifest(args.data_dir, report)

    print()
    if report.errors:
        print(f"验证失败 / verification FAILED: {len(report.errors)} 项不一致 / issues")
        return 1
    print(f"验证通过 / verification PASSED （共 {report.checks} 项检查 / checks）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
