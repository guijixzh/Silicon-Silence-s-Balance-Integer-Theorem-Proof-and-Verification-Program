#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""01 不可归零数筛选 / Sieve of non-zeroable numbers.

利用可归零集的向上传递性：若数字串 w 可归零，则任何包含 w 的超串也可归零
（在 w 两侧插入乘号即可）。因此按长度递增顺序扫描时，一旦发现可归零串，
即可一次性删除它的全部超串；幸存者即为不可归零串，其中被直接检验出的
可归零串称为"素可归零串"（其所有真子串都不可归零）。
By the upward-closure property of zeroable strings, once a zeroable string w is
found every superstring of w is also zeroable (multiply by the zero it yields).
Scanning in increasing length order, all superstrings can be discarded at once;
the survivors are exactly the non-zeroable strings, and the zeroable strings
that are directly tested are the "prime zeroable" ones.

输出 / Outputs:
    data/prime_zeroable.json   素可归零串（含平凡串 '0'）/ prime zeroable strings
    data/non_zeroable.json     不可归零串 / non-zeroable strings
"""

from __future__ import annotations

import argparse
import sys
import time
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sst_core as core  # noqa: E402


def sieve_zeroable(max_length: int,
                   digits: str = core.DIGITS_NONZERO,
                   progress: bool = True,
                   progress_every: int = 500):
    """执行筛法，返回 (素可归零串, 不可归零串)。
    Run the sieve; return (prime zeroable, non-zeroable) lists."""
    universe = ["".join(items)
                for length in range(1, max_length + 1)
                for items in product(digits, repeat=length)]
    start = time.time()
    prime = []
    index = 0
    while index < len(universe):
        candidate = universe[index]
        if core.can_zero(candidate):
            prime.append(candidate)
            # 删除自身与所有超串 / drop the string itself and all superstrings
            universe = [item for item in universe if candidate not in item]
        else:
            index += 1
        if progress and index and index % progress_every == 0:
            elapsed = time.time() - start
            sys.stdout.write(
                f"\r已检验 / tested {index}, 剩余候选 / remaining {len(universe)}, "
                f"素可归零 / prime {len(prime)}, 用时 / {elapsed:.1f}s")
            sys.stdout.flush()
        if progress and not universe:
            break
    if progress:
        sys.stdout.write("\r" + " " * 78 + "\r")
    return prime, universe


def main() -> int:
    parser = argparse.ArgumentParser(
        description="不可归零数筛选 / Sieve of non-zeroable numbers")
    parser.add_argument("-n", "--max-length", type=int, default=7,
                        help="最大位数（默认 7）/ max length (default: 7)")
    parser.add_argument("-d", "--data-dir", type=Path, default=core.DATA_DIR,
                        help="数据目录 / data directory")
    parser.add_argument("--digits", type=str, default=core.DIGITS_NONZERO,
                        help="数字表（默认不含 0）/ digit alphabet (default: without 0)")
    parser.add_argument("--quiet", action="store_true",
                        help="关闭进度输出 / disable progress output")
    args = parser.parse_args()

    if args.max_length < 1:
        parser.error("最大位数必须 >= 1 / max length must be >= 1")

    prime, non_zeroable = sieve_zeroable(args.max_length, args.digits,
                                         progress=not args.quiet)

    # '0' 自身是平凡的可归零串，按定理口径一并计入素可归零串
    # '0' is trivially zeroable; include it to match the published counts
    prime = ["0"] + prime

    args.data_dir.mkdir(parents=True, exist_ok=True)
    core.save_numbers(args.data_dir / "prime_zeroable.json", prime)
    core.save_numbers(args.data_dir / "non_zeroable.json", non_zeroable)

    print("不可归零数筛选完成 / sieve finished")
    print(f"  素可归零串 / prime zeroable : {len(prime)}  (含 '0' / including '0')")
    print(f"  不可归零串 / non-zeroable : {len(non_zeroable)}")
    if non_zeroable:
        longest = max(non_zeroable, key=lambda s: (len(s), s))
        print(f"  最大不可归零串 / largest : {longest} ({len(longest)} 位/digits)")
    print(f"  输出 / outputs : {args.data_dir / 'prime_zeroable.json'}, "
          f"{args.data_dir / 'non_zeroable.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
