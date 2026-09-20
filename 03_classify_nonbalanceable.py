#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""03 强不可平衡数筛选 / Classify non-single-'=' strings into strong / weak.

输入 02 得到的"单等号不可平衡"数字串，进一步检验允许任意多个等号（三段及以上
分割）时能否平衡化 / Take the strings that admit no single-'=' balancing (output
of 02) and test whether any multi-segment cut can balance them:

    强不可平衡 (strongly non-balanceable)
        无论插入多少等号都无法平衡化 / no number of '=' can balance the string;
    弱不可平衡 (weakly non-balanceable)
        需要两个及以上等号才能平衡化（附见证等式）/ multiple '=' are needed
        (a witness equation is recorded).

规则 / Rule:
    默认允许各分割段首数词带前导负号（与已发布数据一致）；
    使用 --strict 可切换为严格规则（禁止前导负号）。
    By default a leading unary minus is allowed on the first number token of
    every segment (matches the published data); use --strict to disable it.

输出 / Outputs:
    data/classification.json            {数字串: 见证等式或 null}
    data/strong_non_balanceable.json    强不可平衡串 / strongly non-balanceable
    data/weak_non_balanceable.json      弱不可平衡串 / weakly non-balanceable
"""

from __future__ import annotations

import argparse
import sys
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sst_core as core  # noqa: E402

_CONFIG = {"strict": False, "max_segments": None, "max_segment_length": 8,
           "clear_every": 0}
_COUNTER = {"tasks": 0}


def _worker_init(strict: bool, max_segments: Optional[int],
                 max_segment_length: int, clear_every: int) -> None:
    """初始化工作进程配置 / Initialize worker configuration."""
    _CONFIG.update(strict=strict, max_segments=max_segments,
                   max_segment_length=max_segment_length, clear_every=clear_every)
    _COUNTER["tasks"] = 0


def _check_one(number: str) -> Tuple[str, Optional[str]]:
    """返回 (数字串, 见证等式或 None) / Return (number, witness or None)."""
    witness = core.find_balance(number,
                                max_segments=_CONFIG["max_segments"],
                                max_segment_length=_CONFIG["max_segment_length"],
                                strict=_CONFIG["strict"])
    _COUNTER["tasks"] += 1
    if _CONFIG["clear_every"] and _COUNTER["tasks"] % _CONFIG["clear_every"] == 0:
        core.clear_caches()
    return number, (witness.expression if witness else None)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="强/弱不可平衡数分类 / Strong/weak non-balanceable classification")
    parser.add_argument("--input", type=Path,
                        default=core.DATA_DIR / "non_balanceable.json",
                        help="输入的单等号不可平衡 JSON / input non_balanceable JSON")
    parser.add_argument("-d", "--data-dir", type=Path, default=core.DATA_DIR,
                        help="输出数据目录 / output data directory")
    parser.add_argument("--strict", action="store_true",
                        help="严格规则（禁止前导负号）/ strict rule (no leading minus)")
    parser.add_argument("--max-segments", type=int, default=None,
                        help="最大段数，默认不限 / max segments (default: unlimited)")
    parser.add_argument("--max-segment-length", type=int, default=8,
                        help="单段最大字符数（默认 8）/ max chars per segment")
    parser.add_argument("--limit", type=int, default=None,
                        help="最多检验多少条（冒烟测试）/ max entries (smoke test)")
    parser.add_argument("--workers", type=int, default=0,
                        help="进程数，0 = CPU 核数 / workers, 0 = cpu_count()")
    parser.add_argument("--chunksize", type=int, default=8,
                        help="imap 块大小 / imap chunksize")
    parser.add_argument("--clear-cache-every", type=int, default=0,
                        help="每多少个任务清空一次缓存（0 = 不清）/ cache reset interval")
    parser.add_argument("--quiet", action="store_true",
                        help="关闭进度输出 / disable progress output")
    args = parser.parse_args()

    numbers = core.load_numbers(args.input)
    if args.limit is not None:
        numbers = numbers[:args.limit]
    total = len(numbers)

    workers = args.workers if args.workers > 0 else cpu_count()
    print(f"待分类 / entries to classify: {total}, 进程数 / workers = {workers}, "
          f"规则 / rule = {'strict' if args.strict else 'segment'}")

    classification = {}
    strong: List[str] = []
    weak: List[str] = []
    start = time.time()
    with Pool(processes=workers,
              initializer=_worker_init,
              initargs=(args.strict, args.max_segments,
                        args.max_segment_length, args.clear_cache_every)) as pool:
        for number, expression in pool.imap_unordered(_check_one, numbers,
                                                      chunksize=args.chunksize):
            classification[number] = expression
            if expression is None:
                strong.append(number)
            else:
                weak.append(number)
            done = len(classification)
            if not args.quiet and done % 200 == 0:
                speed = done / max(time.time() - start, 1e-9)
                sys.stdout.write(
                    f"\r进度 / progress {done:,}/{total:,} | 强 / strong "
                    f"{len(strong):,} | 弱 / weak {len(weak):,} | "
                    f"{speed:,.1f} per s")
                sys.stdout.flush()
    if not args.quiet:
        sys.stdout.write("\r" + " " * 78 + "\r")

    args.data_dir.mkdir(parents=True, exist_ok=True)
    core.save_classification(args.data_dir / "classification.json", classification)
    core.save_numbers(args.data_dir / "strong_non_balanceable.json", strong)
    core.save_numbers(args.data_dir / "weak_non_balanceable.json", weak)

    print("强/弱不可平衡分类完成 / classification finished")
    print(f"  强不可平衡 / strongly non-balanceable : {len(strong):,}")
    print(f"  弱不可平衡 / weakly non-balanceable   : {len(weak):,}")
    if strong:
        longest = max(strong, key=lambda s: (len(s), s))
        print(f"  最大强不可平衡串 / largest strong      : {longest} "
              f"({len(longest)} 位/digits)")
    print(f"  用时 / elapsed : {time.time() - start:.1f}s")
    print(f"  输出 / outputs : {args.data_dir / 'classification.json'}, "
          f"{args.data_dir / 'strong_non_balanceable.json'}, "
          f"{args.data_dir / 'weak_non_balanceable.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
