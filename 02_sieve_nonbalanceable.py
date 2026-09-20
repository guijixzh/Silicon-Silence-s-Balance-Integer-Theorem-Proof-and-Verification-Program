#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""02 不可平衡数筛选 / Sieve of numbers without a single-'=' balancing.

输入 01 得到的所有不可归零串，构造候选集 / Build candidates from non-zeroable
strings (output of 01):

    s1 + c + s2,   s1 + c,   c + s2
    （s1、s2 为不可归零串，c 为 0-9 的某个数字 / c is a single digit）

定理保证：任何无法用一个等号平衡化的数字串都形如上述候选之一，因此只需检验
这一远小于全体数字串的集合。对每个候选依次尝试所有二分切割（由中间向两侧），
若某个切割两侧的插符值集有公共值（a = b 或 a = -b），则该数可平衡化。
The theorem guarantees every string without a one-'=' balancing has the form
above. For each candidate we try all 2-cut splits (center outward); if both
sides share a value (a = b or a = -b), the string is balanceable.

输出 / Output:
    data/non_balanceable.json   单等号不可平衡的数字串 / strings without one-'=' balancing
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sst_core as core  # noqa: E402

# 浮点预筛容差（相对容差，仅用于加速，最终以精确有理数复核）
# float prefilter tolerance (relative; only a speed-up, exact rationals decide)
_REL_TOL = 1e-12
_ABS_TOL = 1e-15

_FLOAT_CACHE: dict = {}


def _float_values(s: str) -> frozenset:
    """浮点值集（带缓存）/ float value set (cached)."""
    cached = _FLOAT_CACHE.get(s)
    if cached is not None:
        return cached
    out = {float(s)}
    for i in range(1, len(s)):
        for a in _float_values(s[:i]):
            for b in _float_values(s[i:]):
                out.add(a + b)
                out.add(a - b)
                out.add(a * b)
                if abs(b) > _ABS_TOL:
                    out.add(a / b)
    frozen = frozenset(out)
    _FLOAT_CACHE[s] = frozen
    return frozen


def _has_common_float(left: str, right: str) -> bool:
    """排序 + 双指针的浮点公共值检测（容差比较）。
    Two-pointer common-value test on sorted float magnitudes (tolerant)."""
    a = sorted(abs(v) for v in _float_values(left))
    b = sorted(abs(v) for v in _float_values(right))
    i = j = 0
    while i < len(a) and j < len(b):
        x, y = a[i], b[j]
        if math.isclose(x, y, rel_tol=_REL_TOL, abs_tol=_ABS_TOL):
            return True
        if x < y:
            i += 1
        else:
            j += 1
    return False


def is_two_cut_balanceable(number: str) -> bool:
    """是否存在二分切割使两侧有公共插符值（一个等号即可平衡化）。
    Whether some 2-cut split admits a common value (a single '=')."""
    for i in core.split_points_center_out(len(number)):
        left, right = number[:i], number[i:]
        if _has_common_float(left, right):
            # 浮点预筛命中后用精确有理数复核 / exact rational confirmation
            if core.abs_values(left) & core.abs_values(right):
                return True
    return False


def iter_candidates(non_zeroable: List[str],
                    max_length: Optional[int] = None) -> Iterator[str]:
    """生成全部候选数字串 / Generate all candidate digit strings."""
    digits_all = core.DIGITS_ALL
    digits_nonzero = core.DIGITS_NONZERO
    if max_length is None:
        max_length = 10 ** 9
    for s1 in non_zeroable:
        for s2 in non_zeroable:
            if len(s1) + 1 + len(s2) > max_length:
                continue
            for digit in digits_all:
                yield s1 + digit + s2
    for s1 in non_zeroable:
        if len(s1) + 1 > max_length:
            continue
        for digit in digits_all:
            yield s1 + digit
    for s2 in non_zeroable:
        if len(s2) + 1 > max_length:
            continue
        for digit in digits_nonzero:
            yield digit + s2


def _check_one(number: str) -> Optional[str]:
    """工作进程入口：返回不可平衡数或 None / worker entry point."""
    return None if is_two_cut_balanceable(number) else number


def load_checkpoint(path: Path) -> Tuple[int, Set[str]]:
    """读取断点 / Load a checkpoint file."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as handle:
            state = json.load(handle)
        return int(state.get("processed", 0)), set(state.get("results", []))
    return 0, set()


def save_checkpoint(path: Path, processed: int, results: Iterable[str]) -> None:
    """写入断点 / Write a checkpoint file."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"processed": processed, "results": sorted(results)},
                  handle, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="不可平衡数筛选 / Sieve of numbers without one-'=' balancing")
    parser.add_argument("--non-zeroable", type=Path,
                        default=core.DATA_DIR / "non_zeroable.json",
                        help="输入的不可归零串 JSON / input non-zeroable JSON")
    parser.add_argument("--output", type=Path,
                        default=core.DATA_DIR / "non_balanceable.json",
                        help="输出 JSON / output JSON")
    parser.add_argument("--max-length", type=int, default=None,
                        help="仅检验不超过该位数的候选 / candidate length limit")
    parser.add_argument("--limit", type=int, default=None,
                        help="最多检验多少候选（冒烟测试）/ max candidates (smoke test)")
    parser.add_argument("--workers", type=int, default=0,
                        help="进程数，0 = CPU 核数 / workers, 0 = cpu_count()")
    parser.add_argument("--chunksize", type=int, default=20000,
                        help="imap 块大小 / imap chunksize")
    parser.add_argument("--tasks-per-child", type=int, default=20000,
                        help="每个工作进程回收前的任务数 / tasks per worker process")
    parser.add_argument("--checkpoint", type=Path, default=None,
                        help="断点文件 / checkpoint file")
    parser.add_argument("--checkpoint-every", type=int, default=200000,
                        help="每处理多少候选写一次断点 / checkpoint interval")
    parser.add_argument("--resume", action="store_true",
                        help="从断点继续 / resume from checkpoint")
    parser.add_argument("--quiet", action="store_true",
                        help="关闭进度输出 / disable progress output")
    args = parser.parse_args()

    non_zeroable = core.load_numbers(args.non_zeroable)
    candidates = iter_candidates(non_zeroable, args.max_length)
    if args.limit is not None:
        candidates = (candidate for index, candidate in enumerate(candidates)
                      if index < args.limit)

    processed = 0
    failures: Set[str] = set()
    if args.resume and args.checkpoint is not None:
        processed, failures = load_checkpoint(args.checkpoint)
        print(f"断点续跑 / resuming: 已处理 {processed}, 已发现 {len(failures)}")

    workers = args.workers if args.workers > 0 else cpu_count()
    start = time.time()
    print(f"候选生成完毕 / candidates ready, 进程数 / workers = {workers}")

    with Pool(processes=workers, maxtasksperchild=args.tasks_per_child) as pool:
        for result in pool.imap_unordered(_check_one, candidates,
                                          chunksize=args.chunksize):
            processed += 1
            if result is not None:
                failures.add(result)
            if not args.quiet and processed % 20000 == 0:
                speed = processed / max(time.time() - start, 1e-9)
                sys.stdout.write(
                    f"\r已检验 / tested {processed:,} | 不可平衡 / failures "
                    f"{len(failures):,} | 速度 / {speed:,.0f} per s")
                sys.stdout.flush()
            if args.checkpoint is not None and processed % args.checkpoint_every == 0:
                save_checkpoint(args.checkpoint, processed, failures)
    if not args.quiet:
        sys.stdout.write("\r" + " " * 70 + "\r")

    if args.checkpoint is not None:
        save_checkpoint(args.checkpoint, processed, failures)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    core.save_numbers(args.output, failures)

    print("不可平衡数筛选完成 / sieve finished")
    print(f"  检验候选 / candidates tested : {processed:,}")
    print(f"  不可平衡数 / failures        : {len(failures):,}")
    if failures:
        longest = max(failures, key=lambda s: (len(s), s))
        print(f"  最大不可平衡串 / largest     : {longest} ({len(longest)} 位/digits)")
    print(f"  输出 / output : {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
