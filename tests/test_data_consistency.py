#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布数据一致性测试 / Consistency tests for the shipped data.

运行 / Run:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sst_core as core  # noqa: E402
import verify_results  # noqa: E402


class DataConsistencyTests(unittest.TestCase):
    """数据文件自洽性 / shipped-data self-consistency."""

    @classmethod
    def setUpClass(cls):
        cls.report = verify_results.Report(quiet=True)
        cls.loaded = verify_results.check_data_consistency(core.DATA_DIR, cls.report)

    def test_data_files_are_consistent(self):
        self.assertIsNotNone(self.loaded, "data files missing / 数据文件缺失")
        self.assertEqual(self.report.errors, [])

    def test_small_scale_recomputation(self):
        lists, _classification = self.loaded
        report = verify_results.Report(quiet=True)
        verify_results.check_small_scale(lists, max_length=3,
                                         classify_max=3, report=report)
        self.assertEqual(report.errors, [])

    def test_known_extremes(self):
        lists, classification = self.loaded
        self.assertIn("9989858", lists["strong_non_balanceable"])
        self.assertIn("8985898", lists["non_zeroable"])
        self.assertIn("9896989", lists["prime_zeroable"])
        self.assertIn("222", lists["weak_non_balanceable"])
        self.assertEqual(classification["222"], "2=2=2")


if __name__ == "__main__":
    unittest.main()
