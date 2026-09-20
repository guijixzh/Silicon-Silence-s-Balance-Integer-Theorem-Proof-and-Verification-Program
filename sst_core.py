#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SS 定理核心库 / Core library for the SS Theorem.

硅基-沉默整数平衡化定理 (Silicium-Silence's Balance Integer Theorem)
-------------------------------------------------------------------
本模块实现数字串的插符值集计算与可归零 / 可平衡化判定，是全部脚本的公共核心。
This module implements value-set computation for digit strings together with the
zeroability / balanceability tests shared by all scripts.

术语 / Terminology
------------------
插符 (symbol insertion)
    在数字串中插入 +,-,*,/ 与括号的操作（"_" 表示不插符，即拼接）。
    Inserting +,-,*,/ and parentheses into a digit string ("_" = concatenation).
插符值集 Val(w) (value set)
    数字串 w 经插符可得到的所有精确值（Fraction 有理数）。
    All exact values obtainable from w (Fraction rationals).
可归零 (zeroable)
    存在一种切分与插符，使 w 的插符值为 0。
    w is zeroable if some cut of w can evaluate to 0.
平衡化 (balancing)
    把 w 切成若干段，使各段插符值集的交集非空（各段可插符为同一值）。
    Cutting w into segments whose value sets share a common value.
强平衡化 (strong balancing)
    只用两段（恰好一个等号）即可平衡化。
    Two segments (exactly one '=') suffice.
弱平衡化 (weak balancing)
    需要三段及以上（多个等号）才能平衡化。
    Three or more segments (multiple '=') are required.

规则模式 / Rule modes
---------------------
strict 模式
    仅允许二元运算 +,-,*,/ 与括号；单个数词前不允许前导负号。
    Only the binary operations +,-,*,/ and parentheses; no leading unary minus.
segment 模式（默认，与已发布数据一致 / default, matches published data）
    允许每个分割段的首个数词带前导负号（例如 1433 -> (-1)+4=3=3）。
    A leading unary minus is allowed on the first number token of every segment
    (e.g. 1433 -> (-1)+4=3=3).

数值等价说明 / Value equivalence note
-------------------------------------
实测并可在 tests/test_core.py 中复核：对全部长度 <= 4 的数字串，
"段首负号"值集恰为严格值集的 ± 闭包；对 2 分割平衡判定而言，
两种模式给出相同的可平衡性；但多分割（弱平衡）分类会受规则影响：
已发布的 1317 个弱串中有 412 个依赖前导负号。
Empirically (checked in tests/test_core.py): for all digit strings of length <= 4,
the segment-mode value set equals the sign closure of the strict value set.
Both modes agree on 2-segment balanceability, while the weak/strong split does
depend on the rule: 412 of the published 1317 weak strings need the leading minus.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

__all__ = [
    "DIGITS_NONZERO",
    "DIGITS_ALL",
    "DEFAULT_MAX_SEGMENT_LENGTH",
    "DATA_DIR",
    "Witness",
    "values",
    "segment_values",
    "abs_values",
    "expr_map",
    "can_zero",
    "split_points_center_out",
    "find_balance",
    "eval_fraction",
    "check_equation",
    "eval_equation",
    "verify_equation",
    "clear_caches",
    "sort_numbers",
    "load_numbers",
    "save_numbers",
    "load_classification",
    "save_classification",
    "path_in_data_dir",
]

# ---------------------------------------------------------------------------
# 常量 / Constants
# ---------------------------------------------------------------------------

DIGITS_NONZERO = "123456789"          # 不含 0 的数字表 / digits without 0
DIGITS_ALL = "0123456789"             # 全部数字 / all digits
DEFAULT_MAX_SEGMENT_LENGTH = 8        # 单个分割段的最大长度 / max chars per segment
DATA_DIR = Path(__file__).resolve().parent / "data"  # 默认数据目录 / default data dir

_PRIORITY = {"+": 1, "-": 1, "*": 2, "/": 2}
_NEG_LEAF = "-"  # 前导负号标记 / leading minus marker


def path_in_data_dir(name: str, data_dir: Optional[Path] = None) -> Path:
    """返回 data 目录下的路径 / Return a path inside the data directory."""
    base = Path(data_dir) if data_dir is not None else DATA_DIR
    return base / name


# ---------------------------------------------------------------------------
# 插符值集 / Value sets
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def values(s: str) -> frozenset:
    """严格插符值集 Val(w)，不含前导负号。
    Strict value set Val(w): binary +,-,*,/ and parentheses only.

    参数 / Args:
        s: 数字串 / digit string.
    返回 / Returns:
        全部可得到的有理数（精确值）/ all obtainable rationals (exact).
    """
    out = {Fraction(s)}
    for i in range(1, len(s)):
        for a in values(s[:i]):
            for b in values(s[i:]):
                out.add(a + b)
                out.add(a - b)
                out.add(a * b)
                if b:
                    out.add(a / b)
    return frozenset(out)


@lru_cache(maxsize=None)
def segment_values(s: str) -> frozenset:
    """默认规则（段首负号）下的插符值集。
    Value set under the default rule (leading minus on the first number token).

    递归定义 / Recursion: 根切分 w = L R 时，首数词必在 L 中，
    故左部可为段首负号值集，右部只能为严格值集。
    For a root split w = L R the first token lies in L, so L may carry the
    leading minus while R must be strict.
    """
    out = {Fraction(s), -Fraction(s)}
    for i in range(1, len(s)):
        for a in segment_values(s[:i]):
            for b in values(s[i:]):
                out.add(a + b)
                out.add(a - b)
                out.add(a * b)
                if b:
                    out.add(a / b)
    return frozenset(out)


@lru_cache(maxsize=None)
def abs_values(s: str) -> frozenset:
    """严格值集的绝对值集合（用于可归零判定）/ absolute values of the strict set."""
    return frozenset(abs(v) for v in values(s))


def _apply(op: str, a: Fraction, b: Fraction) -> Fraction:
    """应用二元运算 / Apply one binary operator."""
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a / b


def _wrap(child_expr: str, child_op: Optional[str], parent_op: Optional[str],
          is_right: bool, child_negative_leaf: bool) -> str:
    """按运算优先级与结合性决定是否加括号。
    Decide whether parentheses are needed for a child expression."""

    def wrap(text: str) -> str:
        return f"({text})"

    if parent_op is None:
        return child_expr
    if child_op is None:
        # 单个（可能为负的）数词 / a possibly negative number token
        return wrap(child_expr) if child_negative_leaf else child_expr
    child_prio, parent_prio = _PRIORITY[child_op], _PRIORITY[parent_op]
    if child_prio < parent_prio:
        return wrap(child_expr)
    if child_prio == parent_prio and is_right:
        # 右操作数同优先级、父运算为 - 或 / 时需要括号
        # same precedence on the right of '-' or '/' needs parentheses
        if (parent_op, child_op) in {("-", "+"), ("-", "-"), ("/", "*"), ("/", "/")}:
            return wrap(child_expr)
    return child_expr


def _token_allowed(token: str) -> bool:
    """禁止带前导零的多位数词（值集不变，仅影响写法美观）。
    Disallow multi-digit tokens with leading zeros (value sets are unchanged:
    "0...0d" can always be rewritten as "0+0+...+d")."""
    return len(token) == 1 or token[0] != "0"


@lru_cache(maxsize=None)
def _strict_expr_map(s: str) -> Dict[Fraction, Tuple[str, Optional[str]]]:
    """严格模式：值 -> (表达式, 根运算符) 的首次出现记录。
    Strict mode: first-found map value -> (expression, root operator)."""
    records: Dict[Fraction, Tuple[str, Optional[str]]] = {}
    if _token_allowed(s):
        records[Fraction(s)] = (s, None)
    for i in range(1, len(s)):
        for a_val, (a_expr, a_op) in _strict_expr_map(s[:i]).items():
            for b_val, (b_expr, b_op) in _strict_expr_map(s[i:]).items():
                for op in "+-*/":
                    if op == "/" and b_val == 0:
                        continue
                    val = _apply(op, a_val, b_val)
                    if val in records:
                        continue
                    left = _wrap(a_expr, a_op, op, False, a_expr.startswith(_NEG_LEAF))
                    right = _wrap(b_expr, b_op, op, True, b_expr.startswith(_NEG_LEAF))
                    records[val] = (f"{left} {op} {right}", op)
    return records


@lru_cache(maxsize=None)
def expr_map(s: str) -> Dict[Fraction, Tuple[str, Optional[str]]]:
    """默认规则：值 -> (表达式, 根运算符) 的首次出现记录。
    Default rule: first-found map value -> (expression, root operator)."""
    records: Dict[Fraction, Tuple[str, Optional[str]]] = {}
    if _token_allowed(s):
        records[Fraction(s)] = (s, None)
        records.setdefault(-Fraction(s), (f"{_NEG_LEAF}{s}", None))
    for i in range(1, len(s)):
        for a_val, (a_expr, a_op) in expr_map(s[:i]).items():
            for b_val, (b_expr, b_op) in _strict_expr_map(s[i:]).items():
                for op in "+-*/":
                    if op == "/" and b_val == 0:
                        continue
                    val = _apply(op, a_val, b_val)
                    if val in records:
                        continue
                    left = _wrap(a_expr, a_op, op, False, a_expr.startswith(_NEG_LEAF))
                    right = _wrap(b_expr, b_op, op, True, b_expr.startswith(_NEG_LEAF))
                    records[val] = (f"{left} {op} {right}", op)
    return records


def clear_caches() -> None:
    """清空全部值集缓存（长任务可周期性调用以控制内存）。
    Clear all value/expression caches (call periodically in long runs)."""
    values.cache_clear()
    segment_values.cache_clear()
    abs_values.cache_clear()
    _strict_expr_map.cache_clear()
    expr_map.cache_clear()


# ---------------------------------------------------------------------------
# 可归零判定 / Zeroability
# ---------------------------------------------------------------------------

def can_zero(s: str) -> bool:
    """判断数字串是否可归零 / Test whether the digit string is zeroable.

    对切分 w = L R，若满足下列任一条件即可归零：
    For a cut w = L R, w is zeroable if either condition holds:
    1. L 与 R 的绝对值集合相交（由 a-b=0 或 a+b=0 归零）；
       the absolute value sets of L and R intersect (a - b = 0 or a + b = 0);
    2. L 或 R 自身可得到 0（由 a*0=0 或 0/b=0 归零）。
       L or R itself can evaluate to 0 (a * 0 = 0 or 0 / b = 0).
    """
    for i in range(1, len(s)):
        left, right = abs_values(s[:i]), abs_values(s[i:])
        if left & right:
            return True
        if 0 in left or 0 in right:
            return True
    return False


# ---------------------------------------------------------------------------
# 平衡化搜索 / Balancing search
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Witness:
    """平衡化见证 / A balancing witness."""

    number: str                       # 原始数字串 / original digit string
    segments: Tuple[str, ...]         # 分割段 / segments
    expression: str                   # 含等号的等式 / the equation text
    common_value: Fraction            # 各段公共值 / common value of all segments
    mode: str = "segment"             # 规则模式 / rule mode: "segment" or "strict"

    @property
    def equals_count(self) -> int:
        """等号个数 / number of equals signs."""
        return len(self.segments) - 1

    def as_record(self) -> Dict[str, object]:
        """转为可序列化记录 / Convert to a JSON-serializable record."""
        return {
            "number": self.number,
            "expression": self.expression,
            "segments": list(self.segments),
            "equals_count": self.equals_count,
            "common_value": f"{self.common_value.numerator}/{self.common_value.denominator}",
            "mode": self.mode,
        }


def split_points_center_out(n: int) -> Iterator[int]:
    """按由中间向两侧的顺序枚举 2 分割点 / 2-cut split points, center out."""
    mid = n // 2
    yield mid
    for offset in range(1, n):
        if mid - offset >= 1:
            yield mid - offset
        if mid + offset <= n - 1:
            yield mid + offset


def _iter_cuts_exact(s: str, k: int, max_segment_length: int,
                     value_fn) -> Iterator[Tuple[Tuple[str, ...], set]]:
    """枚举恰好 k 段的有效切分，并在过程中剪枝。
    Enumerate cuts with exactly k segments, pruning by value intersection.

    剪枝规则 / Pruning rules:
    1. 长度为 1 的段必须同数字（否则其值集 ±d 必不相交）。
       Single-char segments must share the same digit (their ±d sets never meet).
    2. 当前各段值集交集为空则不再向下搜索。
       Stop as soon as the running intersection becomes empty.
    生成 (segments, common_values)；common_values 为各段值集交集。
    Yields (segments, common_values) where common_values is the intersection.
    """
    n = len(s)
    parts: List[str] = []
    first_single: List[Optional[str]] = [None]

    def dfs(start: int, common: Optional[set]) -> Iterator[Tuple[Tuple[str, ...], set]]:
        if len(parts) == k:
            if start == n and common:
                yield tuple(parts), common
            return
        remaining_parts = k - len(parts)
        max_end = min(n - (remaining_parts - 1), start + max_segment_length)
        for end in range(start + 1, max_end + 1):
            part = s[start:end]
            if len(part) == 1 and first_single[0] is not None and part != first_single[0]:
                continue
            part_values = set(value_fn(part))
            new_common = part_values if common is None else (common & part_values)
            if not new_common:
                continue
            prev_single = first_single[0]
            if len(part) == 1 and prev_single is None:
                first_single[0] = part
            parts.append(part)
            yield from dfs(end, new_common)
            parts.pop()
            first_single[0] = prev_single

    yield from dfs(0, None)


_LEADING_ZERO_RE = re.compile(r"(?<!\d)0\d")
_NEG_LEAF_RE = re.compile(r"\(-")


def _score_expression(expression: str) -> int:
    """表达式美观度打分（越小越好）：长度、先导零数词、括号负数惩罚。
    Aesthetics score (smaller is better): length, leading-zero tokens and
    parenthesized negative leaves are penalized."""
    score = len(expression)
    score += 10 * len(_LEADING_ZERO_RE.findall(expression))
    score += 2 * len(_NEG_LEAF_RE.findall(expression))
    return score


def find_balance(number: str,
                 max_segments: Optional[int] = None,
                 max_segment_length: int = DEFAULT_MAX_SEGMENT_LENGTH,
                 strict: bool = False,
                 verify: bool = True) -> Optional[Witness]:
    """搜索平衡化方案，优先二分割（一个等号），再依次增加段数。
    Search for a balancing witness: two segments (one '=') first, then more.

    参数 / Args:
        number: 数字串（不含先导零）/ digit string without leading zero.
        max_segments: 最大段数，None 表示不限（至多 len(number) 段）。
            max number of segments; None = unlimited (up to len(number)).
        max_segment_length: 单段最大字符数 / max characters per segment.
        strict: True 使用严格规则（禁止前导负号）。
            True selects the strict rule (no leading unary minus).
        verify: 是否用独立解析器复核等式 / verify the equation independently.
    返回 / Returns:
        Witness 或 None（在限制内找不到）/ Witness or None if not found.
    """
    if len(number) < 2:
        return None
    mode = "strict" if strict else "segment"
    value_fn = values if strict else segment_values
    upper = max_segments if max_segments is not None else len(number)

    # 二分割优先，且由中间向两侧 / 2-segment cuts first, center out
    if upper >= 2:
        for i in split_points_center_out(len(number)):
            common = set(value_fn(number[:i])) & set(value_fn(number[i:]))
            if common:
                return _build_witness(number, (number[:i], number[i:]),
                                      common, mode, verify)

    for k in range(3, upper + 1):
        for parts, common in _iter_cuts_exact(number, k, max_segment_length, value_fn):
            return _build_witness(number, parts, common, mode, verify)
    return None


def _build_witness(number: str, parts: Tuple[str, ...], common: Iterable[Fraction],
                   mode: str, verify: bool) -> Witness:
    """根据切分与公共值构造并（可选）验证见证 / Build and optionally verify a witness.

    在多个公共值中挑选表达式最简洁（见 _score_expression）的方案。
    Among the common values, pick the one giving the most readable expressions.
    """
    mapper = _strict_expr_map if mode == "strict" else expr_map
    candidates = sorted(common, key=lambda v: (v < 0, v.denominator, v.numerator))
    if len(candidates) > 512:
        candidates = candidates[:512]
    best_exprs: Optional[List[str]] = None
    best_value: Optional[Fraction] = None
    best_score = None
    for value in candidates:
        exprs = []
        for part in parts:
            record = mapper(part).get(value)
            if record is None:
                exprs = []
                break
            exprs.append(record[0])
        if not exprs:
            continue
        score = sum(_score_expression(item) for item in exprs)
        if best_score is None or score < best_score:
            best_score, best_exprs, best_value = score, exprs, value
    if best_exprs is None or best_value is None:
        raise AssertionError(f"internal error: no expression witness for {number!r}")
    expression = "=".join(best_exprs)
    witness = Witness(number=number, segments=tuple(parts), expression=expression,
                      common_value=best_value, mode=mode)
    if verify:
        part_values = eval_equation(expression)
        if any(item != best_value for item in part_values):
            raise AssertionError(f"invalid witness: {expression} ({part_values} vs {best_value})")
        if "".join(parts) != number:
            raise AssertionError(f"segments do not rebuild the number: {parts}")
    return witness


# ---------------------------------------------------------------------------
# 表达式求值 / Expression evaluation
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\d+|[()+\-*/]")


def eval_fraction(expression: str) -> Fraction:
    """用递归下降解析器精确求插符表达式的值（支持一元负号与括号）。
    Evaluate an insertion expression exactly with a recursive-descent parser
    (supports unary minus and parentheses)."""
    tokens = _TOKEN_RE.findall(expression)
    pos = 0

    def parse_expression() -> Fraction:
        nonlocal pos
        value = parse_term()
        while pos < len(tokens) and tokens[pos] in "+-":
            op = tokens[pos]
            pos += 1
            rhs = parse_term()
            value = value + rhs if op == "+" else value - rhs
        return value

    def parse_term() -> Fraction:
        nonlocal pos
        value = parse_factor()
        while pos < len(tokens) and tokens[pos] in "*/":
            op = tokens[pos]
            pos += 1
            rhs = parse_factor()
            value = value * rhs if op == "*" else value / rhs
        return value

    def parse_factor() -> Fraction:
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError(f"unexpected end of expression: {expression!r}")
        token = tokens[pos]
        if token == "(":
            pos += 1
            value = parse_expression()
            if pos >= len(tokens) or tokens[pos] != ")":
                raise ValueError(f"missing ')': {expression!r}")
            pos += 1
            return value
        if token == "-":
            pos += 1
            return -parse_factor()
        if token == "+":
            pos += 1
            return parse_factor()
        pos += 1
        return Fraction(int(token))

    result = parse_expression()
    if pos != len(tokens):
        raise ValueError(f"trailing tokens: {expression!r}")
    return result


def check_equation(equation: str) -> Tuple[Fraction, Fraction]:
    """求单等号等式两边的值 / Evaluate both sides of a single-'=' equation."""
    if equation.count("=") != 1:
        raise ValueError(f"expected exactly one '=': {equation!r}")
    left, right = equation.split("=")
    return eval_fraction(left), eval_fraction(right)


def eval_equation(equation: str) -> List[Fraction]:
    """求等式（可含多个等号）各段的值 / Evaluate every part of an equation chain."""
    parts = equation.split("=")
    if len(parts) < 2:
        raise ValueError(f"expected at least one '=': {equation!r}")
    return [eval_fraction(part) for part in parts]


def verify_equation(equation: str, number: Optional[str] = None) -> bool:
    """校验等式：数字重建（可选）且各段求值相等。
    Validate an equation: digits rebuild (optional) and all parts are equal."""
    digits = "".join(ch for ch in equation if ch.isdigit())
    if number is not None and digits != number:
        return False
    try:
        parts = eval_equation(equation)
    except (ValueError, ZeroDivisionError):
        return False
    return all(value == parts[0] for value in parts)


# ---------------------------------------------------------------------------
# 数据读写 / Data I/O
# ---------------------------------------------------------------------------

def sort_numbers(numbers: Iterable[str]) -> List[str]:
    """统一排序：先按长度，再按字典序 / canonical order: (length, lexicographic)."""
    return sorted(numbers, key=lambda s: (len(s), s))


def load_numbers(path) -> List[str]:
    """读取数字串列表 JSON / Load a JSON list of digit strings."""
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"expected a JSON list in {path}")
    return [str(item) for item in data]


def save_numbers(path, numbers: Iterable[str]) -> None:
    """保存数字串列表 JSON（统一排序、UTF-8、缩进 2）。
    Save a JSON list of digit strings (canonical order, UTF-8, indent=2)."""
    payload = sort_numbers(numbers)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_classification(path) -> Dict[str, Optional[str]]:
    """读取分类表 JSON：{数字串: 等式或 null} / Load {number: equation or null}."""
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return {str(key): (None if value is None else str(value)) for key, value in data.items()}


def save_classification(path, mapping: Dict[str, Optional[str]]) -> None:
    """保存分类表 JSON（键统一排序）/ Save the classification map (sorted keys)."""
    ordered = {key: mapping[key] for key in sort_numbers(mapping.keys())}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(ordered, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
