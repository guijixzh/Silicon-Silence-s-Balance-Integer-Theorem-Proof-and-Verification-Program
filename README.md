# SS 定理 / The SS Theorem

**硅基-沉默整数平衡化定理 / Silicium-Silence's Balance Integer Theorem**

> **主定理 / Main theorem**
>
> 在十进制下，对于 8 位及以上位数的任意整数，我们总能在其中插入加减乘除、
> 小括号与一个等号，使之成为正确的等式。
>
> Every decimal integer with 8 or more digits can be turned into a true
> equation by inserting `+ - * /`, parentheses and one `=` into its digit
> string.

例如 / for example:

| 数字串 / digits | 等式 / equation |
| --- | --- |
| `1234` | `12=3 * 4` |
| `1919810` | `19 - 1=9 + 8 + 1 + 0` |
| `222` | `2=2=2`（弱平衡，两个等号 / weak, two `=`） |
| `113` | 不存在 / none（不可平衡 / non-balanceable） |

本仓库包含定理结论、全部筛选数据与可复现的验证代码。
This repository ships the theorem statement, the full screening data and
reproducible verification code.

---

## 目录 / Contents

1. [问题与定义 / Problem and definitions](#1-问题与定义--problem-and-definitions)
2. [主要结论与数据 / Results and data](#2-主要结论与数据--results-and-data)
3. [规则说明 / Rule modes](#3-规则说明--rule-modes)
4. [快速开始 / Quick start](#4-快速开始--quick-start)
5. [脚本说明 / Scripts](#5-脚本说明--scripts)
6. [数据文件 / Data files](#6-数据文件--data-files)
7. [验证与复现 / Verification and reproduction](#7-验证与复现--verification-and-reproduction)
8. [目录结构 / Layout](#8-目录结构--layout)
9. [已知限制 / Known limitations](#9-已知限制--known-limitations)
10. [引用与许可 / Citation and license](#10-引用与许可--citation-and-license)

---

## 1. 问题与定义 / Problem and definitions

**中文**

给定一个不含先导零的十进制数字串 `w`，可以向其中插入 `+`、`-`、`*`、`/`、
小括号与等号（连接符 `_` 表示两数字不插符、直接拼接）：

- **插符**：在数字串中插入运算符的操作；得到的表达式之值称为**插符值**，
  所有可得到的插符值构成**插符值集** `Val(w)`（本仓库用精确有理数计算）。
- **可归零**：存在一种切分 `w = L R` 与插符，使 `w` 的插符值为 `0`
  （等价于两侧存在公共值，或其中一侧可得到 `0` 再乘到整体上）。
- **平衡化**：把 `w` 切成若干段，使各段插符值集的交集非空，即插入等号后
  成为正确等式。
  - **强平衡化**：只需两段（恰好一个等号）。
  - **弱平衡化**：需要三段及以上（多个等号）。
- **不可归零数 / 不可平衡数 / 强、弱不可平衡数**：上述性质不成立的反例。

问题：是否存在位数下界 `N`，使任何 `n >= N` 位的数字串总可平衡化？

**English**

Given a decimal digit string `w` without leading zeros, one may insert `+`,
`-`, `*`, `/`, parentheses and `=` signs (juxtaposition, written `_`, means no
operator is inserted):

- **Insertion**: the operation of inserting operators; the resulting expression
  values form the **value set** `Val(w)` (computed here with exact rationals).
- **Zeroable**: some cut `w = L R` and insertion yields value `0`.
- **Balancing**: cutting `w` into segments whose value sets share a common
  value, so the inserted `=` signs form true equations.
  - **Strong**: two segments (exactly one `=`) suffice.
  - **Weak**: three or more segments (multiple `=`) are needed.
- **Non-zeroable / non-balanceable / strongly or weakly non-balanceable**:
  the corresponding counterexamples.

Question: is there a length bound `N` such that every string with `n >= N`
digits is balanceable?

---

## 2. 主要结论与数据 / Results and data

**中文**

- 不可归零串共 **2873** 个，最长 7 位，最大为 `8985898`，且它是唯一的 7 位
  不可归零串；因此 **N' = 8**：任何 8 位及以上的数字串都可归零。
- 素可归零串（本身可归零、真子串均不可归零）共 **6534** 个（含平凡串 `0`），
  最大为 `9896989`。
- 无单等号解的串共 **19515** 个（2–7 位；8–15 位候选全部可解），最大为
  `9989858`。
- 其中 **18198** 个即使允许任意多个等号也无法平衡（强不可平衡），最大仍为
  `9989858`；**1317** 个可通过多个等号平衡（弱不可平衡）。
- 结合 `N' = 8` 与 `0=0` 构造可得 `N <= 16`，而候选集穷举把结论收紧为
  **N = 8**：即主定理。

**English**

- There are **2873** non-zeroable strings, all at most 7 digits; the largest is
  `8985898`, the unique 7-digit one. Hence **N' = 8**: every 8+ digit string is
  zeroable.
- There are **6534** prime zeroable strings (zeroable while all proper
  substrings are not; including the trivial string `0`), the largest being
  `9896989`.
- Exactly **19515** strings (2–7 digits) admit no single-`=` balancing
  (all 8–15 digit candidates do admit one); the largest is `9989858`.
- **18198** of them remain non-balanceable even with arbitrarily many `=`
  signs (strongly non-balanceable, largest `9989858`), while **1317** become
  balanceable with multiple `=` signs (weakly non-balanceable).
- Combining `N' = 8` with the `0=0` construction gives `N <= 16`; the
  candidate sweep tightens it to **N = 8**, i.e. the main theorem.

| 数据 / data | 数量 / count | 最大元素 / maximum |
| --- | ---: | --- |
| 素可归零串 / prime zeroable | 6534 | `9896989` |
| 不可归零串 / non-zeroable | 2873 | `8985898` |
| 无单等号解 / no single-`=` solution | 19515 | `9989858` |
| 强不可平衡 / strongly non-balanceable | 18198 | `9989858` |
| 弱不可平衡 / weakly non-balanceable | 1317 | `999894` |

---

## 3. 规则说明 / Rule modes

**中文**

- **默认模式 `segment`（与已发布数据一致）**：每个分割段的首个数词允许带
  前导负号，例如 `1433 -> (-1)+4=3=3`。这对应在段首数字前插入 `-`。
- **严格模式 `strict`（脚本加 `--strict`）**：只允许二元运算与括号，不允许前导
  负号。可以证明（并在单元测试中复核）：对长度 ≤ 4 的全部数字串，
  段首负号值集恰为严格值集的 ± 闭包；对二分割平衡判定两种模式等价，
  但**弱/强分类依赖规则**：1317 个弱串中有 412 个需要前导负号。

**English**

- **Default `segment` mode (matches the published data)**: the first number
  token of every segment may carry a leading minus, e.g. `1433 -> (-1)+4=3=3`.
- **Strict `--strict` mode**: only binary operators and parentheses; no leading
  minus. One can show (and the unit tests re-check) that for all strings of
  length ≤ 4 the segment value set equals the sign closure of the strict one;
  the two modes agree on 2-segment balanceability, but the **weak/strong split
  depends on the rule**: 412 of the 1317 weak strings need the leading minus.

---

## 4. 快速开始 / Quick start

环境 / Requirements: **Python >= 3.10**，仅标准库 / standard library only.

```bash
# 平衡化一个数字（默认现场搜索，优先二分割）/ balance a number (search first, 2 segments preferred)
python 04_balance_number.py 1919810

# 查表快速判定 / fast table lookup
python 04_balance_number.py 222 --table
python 04_balance_number.py 9989858 --table

# 重新筛选不可归零数（7 位，分钟级）/ re-run the zeroability sieve (7 digits, minutes)
python 01_sieve_zeroable.py -n 7

# 验证全部发布数据（约 30 秒）/ verify all shipped data (~30 s)
python verify_results.py

# 单元测试 / unit tests
python -m unittest discover -s tests -v
```

输出示例 / sample output:

```text
$ python 04_balance_number.py 1919810
数字 / number : 1919810
模式 / mode : segment (允许段首负号 / segment-leading minus)
结果 / result : 19 - 1=9 + 8 + 1 + 0
分割 / segments : 191 | 9810
段数 / segment count : 2, 等号 / equals : 1
公共值 / common value : 18
验证 / verification : 通过 / valid
```

```text
$ python 04_balance_number.py 9989858 --table
数字 / number : 9989858
表中判定 / table result : 强不可平衡 / strongly non-balanceable
说明 / note : 无论插入多少等号都无法构成等式 / no number of '=' can form an equation
```

```text
$ python verify_results.py
A. 数据一致性检查 / data consistency
B. 小规模全量复算（长度 <= 5，分类 <= 4）/ small-scale exhaustive recomputation
  复算条目 / recomputed: 可归零 66429, 二分割 99990, 分类 9990; 用时 / 23.8s

验证通过 / verification PASSED （共 41 项检查 / checks）
```

---

## 5. 脚本说明 / Scripts

| 脚本 / script | 作用 / purpose | 输入 / input | 输出 / output |
| --- | --- | --- | --- |
| `sst_core.py` | 核心库：值集、可归零、平衡化搜索、表达式求值 / core library | — | — |
| `01_sieve_zeroable.py` | 不可归零数筛选 / zeroability sieve | 无 / none | `prime_zeroable.json`, `non_zeroable.json` |
| `02_sieve_nonbalanceable.py` | 不可平衡数筛选 / single-`=` sieve | `non_zeroable.json` | `non_balanceable.json` |
| `03_classify_nonbalanceable.py` | 强/弱不可平衡分类 / strong-weak classification | `non_balanceable.json` | `classification.json`, `strong_*.json`, `weak_*.json` |
| `04_balance_number.py` | 手动输入平衡化 / interactive balancing | 命令行/REPL / CLI or REPL | 屏幕输出 / stdout |
| `verify_results.py` | 数据一致性 + 全量/小规模复算 / verification | `data/` | 报告 / report |

常用参数 / common options:

```bash
# 01：位数上限 / max length
python 01_sieve_zeroable.py -n 7

# 02：仅检验不超过 15 位的候选，带断点续跑 / up to 15 digits with checkpoint
python 02_sieve_nonbalanceable.py --max-length 15 \
    --checkpoint checkpoint_sieve.json --resume

# 03：严格规则分类 / classify under the strict rule
python 03_classify_nonbalanceable.py --strict

# 04：限制段数、严格规则、JSON 输出 / segment limit, strict rule, JSON output
python 04_balance_number.py 1433 --max-segments 3
python 04_balance_number.py 1234 --json
```

`04_balance_number.py` 默认不查表、现场搜索（优先二分割，再依次增加段数），
加 `--table` 则先查 `data/classification.json`：强不可平衡串直接判定，
弱不可平衡串直接给出已收录的见证等式。
Without `--table`, `04_balance_number.py` searches from scratch (two segments
first, then more). With `--table` it consults `data/classification.json`
first: strongly non-balanceable strings are reported directly and weak ones
print their recorded witnesses.

---

## 6. 数据文件 / Data files

全部位于 `data/`，均为 UTF-8 JSON。

| 文件 / file | 内容 / content | 条数 / count |
| --- | --- | ---: |
| `prime_zeroable.json` | 素可归零串列表（含 `0`）/ list, includes `0` | 6534 |
| `non_zeroable.json` | 不可归零串列表 / list | 2873 |
| `non_balanceable.json` | 无单等号解的串列表 / list | 19515 |
| `strong_non_balanceable.json` | 强不可平衡串列表 / list | 18198 |
| `weak_non_balanceable.json` | 弱不可平衡串列表 / list | 1317 |
| `classification.json` | `{数字串: 见证等式或 null}` / `{number: witness or null}` | 19515 |
| `manifest.json` | 计数、最大值、规则、SHA-256 校验和 / metadata and hashes | — |

列表文件均按 `(长度, 字典序)` 排序且无重复；`classification.json` 中
`null` 表示强不可平衡，字符串值为形如 `2=2=2` 的见证等式（由程序独立求值
验证 / validated by an independent evaluator）。
List files are sorted by `(length, lexicographic)` and unique; `null` in the
classification marks strongly non-balanceable strings.

---

## 7. 验证与复现 / Verification and reproduction

**中文**

`verify_results.py` 提供三级验证：

1. **数据一致性**（默认）：计数、最大值、排序、集合关系、1317 条见证等式求值。
2. **小规模全量复算**（默认，长度 ≤ 5，分类 ≤ 4）：对全部数字串从零复算
   可归零性与二分割/多分割可平衡性，与发布数据逐条比对。
3. **全量复核**（`--deep`）：对 2873 不可归零串、19515 无单等号解串、
   18198 强不可平衡串逐条重算。

本仓库的复现记录 / reproduction record:

- `01_sieve_zeroable.py -n 7` 重新生成的 6534/2873 条数据与原始发布数据完全一致；
- `02_sieve_nonbalanceable.py --max-length 5` 检验 185377 个候选，得到 16248 个
  结果，恰好等于发布数据中长度 ≤ 5 的子集；
- `03_classify_nonbalanceable.py` 一次运行（32 核 8.2 秒）得到的强/弱集合与
  原始数据完全一致，1317 条见证等式全部通过独立求值验证；
  原始数据中有 88 条见证等式存在格式化错误（求值不成立），本仓库已全部修正；
- `verify_results.py --deep` 通过（约 51 秒）。

完整重跑 `02` 需要检验约 8200 万个候选（2–15 位），建议使用
`--checkpoint`/`--resume` 与多核；本仓库数据已按上述方式迁移并复核。
A full `02` sweep tests about 82 million candidates (2–15 digits); use
`--checkpoint`/`--resume` and multiple cores.

**English**

`verify_results.py` performs three levels of verification:

1. **Data consistency** (default): counts, maxima, ordering, set relations and
   evaluation of all 1317 witness equations.
2. **Small-scale exhaustive recomputation** (default, length ≤ 5,
   classification ≤ 4): recomputes zeroability and balanceability from scratch
   for every digit string and compares with the shipped data.
3. **Full re-check** (`--deep`): rechecks every shipped entry (2873 / 19515 /
   18198).

Reproduction record: `01 -n 7` reproduces the published 6534/2873 sets exactly;
`02 --max-length 5` yields exactly the length-≤5 subset (16248 entries);
`03` reproduces the identical strong/weak sets and all 1317 witnesses validate
(88 malformed legacy witness texts were fixed); `verify_results.py --deep`
passes in about 51 seconds.

---

## 8. 目录结构 / Layout

```text
SS-Theorem/
├─ README.md                       # 本文档（中英双语）/ this file (bilingual)
├─ LICENSE                         # MIT
├─ requirements.txt                # 仅标准库 / standard library only
├─ sst_core.py                     # 核心库 / core library
├─ 01_sieve_zeroable.py            # 不可归零数筛选 / zeroability sieve
├─ 02_sieve_nonbalanceable.py      # 不可平衡数筛选 / single-'=' sieve
├─ 03_classify_nonbalanceable.py   # 强/弱分类 / strong-weak classification
├─ 04_balance_number.py            # 手动平衡化 / interactive balancing
├─ verify_results.py               # 验证 / verification
├─ data/                           # 全部发布数据 / shipped data
└─ tests/                          # 单元测试 / unit tests
```

---

## 9. 已知限制 / Known limitations

**中文**

- `04_balance_number.py` 对很长的数字串（如 20 位以上）可能搜索较慢；可先用
  `--table` 或限制 `--max-segments`。8 位及以上一定存在解，但本工具不保证
  在限定时间内找到。
- 默认规则与严格规则的强/弱分类不同（见第 3 节）。
- `02` 的浮点预筛使用相对容差 `1e-12`，所有命中都会用精确有理数复核，
  最终结果精确。
- 数据只涵盖十进制与符号集 `{+, -, *, /, ()}`；任意进制或其它符号集的推广
  属于后续工作。

**English**

- `04_balance_number.py` may be slow for very long strings (20+ digits); use
  `--table` or a `--max-segments` limit. A solution always exists for 8+
  digits but is not guaranteed to be found within a time budget.
- The weak/strong split differs between the default and strict rules (section 3).
- The float prefilter in `02` uses relative tolerance `1e-12`; every hit is
  confirmed with exact rationals, so final results are exact.
- Data cover base 10 and the symbol set `{+, -, *, /, ()}` only; other bases or
  symbol sets are future work.

---

## 10. 引用与许可 / Citation and license

**中文**

- 定理与原始数据的提出与证明：硅基飙尘葆光，
  《为何所有 8 位及以上的数都可以变为等式？——硅基-沉默整数平衡化定理及其证明
  简明介绍》，2025-11-30（原始文档与证明未包含在本仓库中）。
- 本仓库代码与数据以 MIT 许可发布，见 `LICENSE`。

**English**

- Theorem and original data: "硅基飙尘葆光", 2025-11-30 (the original manuscript
  and proof are not included in this repository).
- Code and data are released under the MIT license, see `LICENSE`.
