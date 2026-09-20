#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""04 数字平衡化 / Balance a digit string interactively.

手动输入一个数字串，给出平衡化结果（优先二分割，即只插一个等号）。
Balance a digit string entered by hand; two-segment (single '=') solutions are
preferred and multi-segment (multiple '=') solutions are tried next.

默认不查表，直接现场搜索；使用 --table 可快速查阅随仓库发布的反例表：
表中的强不可平衡串直接判定，弱不可平衡串直接输出已有见证等式。
By default no table is consulted; with --table the shipped classification data
is used: strongly non-balanceable strings are reported immediately and weakly
non-balanceable ones print their recorded witness.

用法 / Usage:
    python 04_balance_number.py 1919810
    python 04_balance_number.py --table 8985898
    python 04_balance_number.py --strict 1433
    python 04_balance_number.py                # 交互模式 / REPL
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sst_core as core  # noqa: E402


def parse_number(text: str) -> str:
    """校验并返回数字串 / Validate and return the digit string."""
    number = text.strip().replace(" ", "")
    if not number:
        raise ValueError("输入为空 / empty input")
    if not number.isdigit():
        raise ValueError(f"只能输入数字 / digits only: {text!r}")
    if number[0] == "0":
        raise ValueError("数字串不允许先导零 / leading zero is not allowed")
    if len(number) < 2:
        raise ValueError("至少需要两位数字 / at least two digits are required")
    return number


def balance_one(number: str, args: argparse.Namespace) -> int:
    """处理一个数字串 / Handle one digit string."""
    mode = "strict" if args.strict else "segment"
    table_hit = False

    if args.table:
        table_path = core.path_in_data_dir("classification.json", args.data_dir)
        if table_path.exists():
            table = core.load_classification(table_path)
            if number in table:
                table_hit = True
                expression = table[number]
                if expression is None:
                    print(f"数字 / number : {number}")
                    print("表中判定 / table result : 强不可平衡 / strongly non-balanceable")
                    print("说明 / note : 无论插入多少等号都无法构成等式 / "
                          "no number of '=' can form an equation")
                    return 0
                print(f"数字 / number : {number}")
                print(f"查表结果 / table result : {expression}")
                print(f"验证 / verification : "
                      f"{'通过 / valid' if core.verify_equation(expression, number) else '失败 / invalid'}")
                return 0
        else:
            print(f"警告 / warning : 未找到数据表 {table_path}，转为现场搜索 / "
                  f"table not found, falling back to search")
        if not table_hit:
            print(f"表中无记录 / not in table : {number}")

    if len(number) >= 8:
        print("定理提示 / theorem : 8 位及以上数字串必定可平衡化 / "
              "every 8+ digit string is balanceable")

    witness = core.find_balance(number,
                                max_segments=args.max_segments,
                                max_segment_length=args.max_segment_length,
                                strict=args.strict)
    if witness is None:
        print("在限制内未找到平衡化方案 / no witness found within limits")
        if args.strict:
            print("提示 / hint : 严格规则下可能无解；允许段首负号时可能有解，"
                  "去掉 --strict 再试 / try without --strict")
        elif args.max_segments is None and args.max_segment_length >= len(number):
            print("结论 / conclusion : 默认规则下该数不可平衡化（与反例表一致）"
                  " / not balanceable under the default rule")
        else:
            print("提示 / hint : 可增大 --max-segments 或 --max-segment-length；"
                  "8 位及以上必定存在解 / raise the limits; 8+ digits always have one")
        return 1

    if args.json:
        print(json.dumps(witness.as_record(), ensure_ascii=False))
        return 0

    print(f"数字 / number : {witness.number}")
    print(f"模式 / mode : {mode} "
          f"({'允许段首负号 / segment-leading minus' if mode == 'segment' else '严格 / strict'})")
    print(f"结果 / result : {witness.expression}")
    print(f"分割 / segments : {' | '.join(witness.segments)}")
    print(f"段数 / segment count : {len(witness.segments)}, "
          f"等号 / equals : {witness.equals_count}")
    print(f"公共值 / common value : {witness.common_value}")
    print(f"验证 / verification : "
          f"{'通过 / valid' if core.verify_equation(witness.expression, number) else '失败 / invalid'}")
    return 0


def repl(args: argparse.Namespace) -> int:
    """交互模式 / REPL mode."""
    print("数字平衡化 / Balance a number")
    print("输入数字串后回车；输入 q 退出 / type a digit string, 'q' to quit")
    while True:
        try:
            text = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if text.strip().lower() in {"q", "quit", "exit", "退出"}:
            return 0
        try:
            number = parse_number(text)
        except ValueError as error:
            print(f"无效输入 / invalid input : {error}")
            continue
        balance_one(number, args)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="数字平衡化 / Balance a digit string")
    parser.add_argument("number", nargs="?", default=None,
                        help="待平衡化的数字串（省略则进入交互模式）/ "
                             "digit string (omit for REPL)")
    parser.add_argument("--table", action="store_true",
                        help="先查反例表 / consult the shipped classification table")
    parser.add_argument("--strict", action="store_true",
                        help="严格规则（禁止前导负号）/ strict rule (no leading minus)")
    parser.add_argument("--max-segments", type=int, default=None,
                        help="最大段数，默认不限 / max segments (default: unlimited)")
    parser.add_argument("--max-segment-length", type=int, default=8,
                        help="单段最大字符数（默认 8）/ max chars per segment")
    parser.add_argument("-d", "--data-dir", type=Path, default=core.DATA_DIR,
                        help="数据目录 / data directory")
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 输出 / print JSON output")
    args = parser.parse_args()

    if args.number is None:
        return repl(args)
    try:
        number = parse_number(args.number)
    except ValueError as error:
        parser.error(str(error))
        return 2
    return balance_one(number, args)


if __name__ == "__main__":
    raise SystemExit(main())
