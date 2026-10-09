# WORK-ORDERS —— 自研件编写工单

> **版本**：v1.0 ｜ **日期**：2026-10-09 ｜ **上游**：`ARCHITECTURE.md` v0.1（§9 模块清单、§12 契约自检、§13 路线图）+ `reference/INTERFACE-CHECK.md` §5（自研边界 W1–W8）
> **性质**：执行文档。每单只含四件事——**搬什么、写什么、怎么算完、禁止什么**。不给工期，只给出口判据。
> **批次**：B1（M0 骨架）→ B2（M1 标定）→ B3（M2 解码+真仓）→ B4（M3 停止）→ B5（M4 盲区）。前一批出口判据不满足，下一批不开工。

```mermaid
flowchart LR
    O["工单0 前置<br/>git init + 基线"] --> W1["W1 四层解耦引擎<br/>field/slicer/pool/design"]
    O --> W2["W2 底空间件<br/>units/layers/fuse/embed"]
    W1 --> W6["W6 观测与诊断"]
    W2 --> W6
    W1 --> W7["W7 报告层"]
    W6 --> W8["W8 标定层 ★B2<br/>金标+Hui-Walter+crowd-kit"]
    W2 --> W5["W5 解码器族 ★B3<br/>DD/SCOMP/NB/图先验"]
    W6 --> W5
    W5 --> W4["W4 Weitzman 停止 ★B4"]
    W2 --> W3["W3 sheaf 真实语义 ★B5"]
    W1 -.清单.-> W3
```

---

## 工单 0 · 开工前置（开工当天完成）

| # | 事项 | 完成判据 |
|---|---|---|
| O1 | `topos-audit/` 执行 `git init` + 首次提交（ARCHITECTURE.md / WORK-ORDERS.md / INTERFACE-CHECK.md / .gitignore / reference 两例外文件） | `git log` 有基线提交；`git status` 干净 |
| O2 | 目录骨架落位：`topos/{core,axis,pool,infer,stop,calib,report}` + `PREREG/` + `EXP/` + `tests/` + 默认 `axes.json`（v3 空壳） | 目录树与本工单 §W1 交付物一致 |
| O3 | 推 GitHub（走 `ssh://git@ssh.github.com:443`，建仓 `master666-max/topos-audit`，MIT） | `ls-remote` 回读一致 |

**禁止**：O3 之前不得开始任何 W 编号工单（先有基线，后写代码）。

---

## B1 批 · M0 骨架

### W1 · 四层解耦引擎

| 项 | 内容 |
|---|---|
| **目标** | `axis/`（manifest+registry+methods）+ `pool/`（slicer+pool+design）四层跑通：清单 v3 → 场 → 切片 → 池 → 设计矩阵 |
| **搬**（mini-lab，均已 [M]） | `coord_mini.axis_method` 装饰器 + `AXIS_METHODS` 注册表 → `axis/registry.py`；五个方法学函数改名为 `*_field`（**防遮蔽事故重演**，REPORT §3）；`_load_patterns` → `axis/methods/regex.py`；`git_churn` → `axis/methods/git.py`；`discover_units` → `core/units.py` |
| **新写** | ① manifest v3 加载 + schema 校验（缺字段/未知 method/未知切片引用 → 报错并指名行）；② slicer 算子集 `has / gt / lt / quantile_gt / quantile_le / between_q / notnull / expand`；③ 池布尔组合（嵌套结构，ADR-A10）；④ `constraints` 强制执行（超 max_width/max_pools、低于 min_pool_size 的池**丢弃并告警**） |
| **裁决已定（ADR）** | **A10**：布尔组合用 `{"all":[]}/{"any":[]}/{"not":…}` 嵌套，叶子=切片名，**不做字符串 DSL 解析器**（零解析器、无优先级歧义）；**A11**：`expand` 算子把列表场（如 anchor 的 33 个 tag）自动展开为逐值切片；**A12**：None 是合法场值，切片对 None 单元一律排除，`notnull` 是唯一能捞回它们的算子 |
| **交付物** | `topos/axis/*.py`、`topos/pool/*.py`、默认 `axes.json`（v3：anchor 引用 `reference/anchors-bandit.json` + churn + age + loc + forman + diffusion，含 ≥1 个嵌套组合池）、`PREREG/B1.md` |
| **验收（全过才算完）** | ① `topos selftest` 契约自检 #5/6/7/8/12 全绿（映射见附录 A）；② **解耦验收**：测试脚本只改 `axes.json` 新增 2 场 + 1 组合池 → 引擎零代码改动产出该池（git diff 仅清单文件）；③ 33 个 bandit 锚点经 `expand` 全部成片，无手写声明；④ 对 mini-lab 目录建空间，池数/覆盖诊断与 space_mini v0.1 输出**同量级**（数量不必相等，口径必须可解释） |
| **禁止** | 代码出现任何具体轴名（anchor/churn/…只能出现在清单与测试里）；[U] 部件不带证伪判据合入 |

### W2 · 底空间件

| 项 | 内容 |
|---|---|
| **目标** | `core/`：单元发现 → 五类耦合边 → 融合图 → （仪表）扩散嵌入，一条链可跑 |
| **搬**（均已 [M]） | `space_mini._extract_layers / _walk_calls / _pass_through_data / _resolver` 全家 → `core/layers.py`（selftest 10/10 的合成仓断言一起搬进 `tests/`）；`coord_mini.build_call_graph / forman_curvature / _matvec_L / _jacobi_eig / diffusion_embedding` → `core/`（E1 咬合件，λ₂ 残差 1e-7）；融合图 `w=Σα·A_t` 逻辑 |
| **新写** | ① `Space.build(root, manifest)` 总装入口（替代 space_mini 里轴池焊死的 `_build_axes_and_pools`——**那 60 行整体废弃，由 W1 四层替代**）；② 对拍钩子：`--crosscheck` 开关调 `reference/_crosscheck.py` 同款逻辑（GC Forman + scipy λ₂） |
| **验收** | ① 契约自检 #1/2/3/4 全绿；② 对拍钩子实测：mini-lab 目录 154 边曲率 max\|Δ\|=0、λ₂ Δ<1e-12（沿用今日 6/6 基线）；③ `space.json` 产物含必填三诊断与 schema 版本号 |
| **如实记录** | 抽取器天花板：control=1 / return=2（N=65 样本）——写进模块 docstring，M5 Joern 校验前**不承诺**控制/返回层完备 |
| **禁止** | 为提升 control/return 召回在 B1 加启发式——那是 M5 工单，B1 保持已验证的 10/10 语义不动 |

### W6 · 观测与诊断

| 项 | 内容 |
|---|---|
| **目标** | `infer/observe.py`（带噪 OR）+ `pool/coverage.py`（三诊断）+ 模拟 oracle |
| **搬** | `coord_mini.pool_coverage`（c_min/c_mean/zero_cover）→ `pool/coverage.py`；`decode_mini.run_case` 里的 oracle 采样逻辑（真值集按 Se/Sp 撒噪）→ `infer/observe.py` |
| **新写** | 观测模型显式化：`P(y=1|D) = 1−Sp + (Se+Sp−1)·OR(d_i)`；oracle 接口 `Oracle.observe(pool, truth, se, sp, rng) -> 0/1`（合成 oracle 进 B1，真实信号源适配 B2 起） |
| **验收** | 契约自检 #9；**条款复算**：E-X1 数字在工具内可复现（球池零覆盖 ≈11.5% 量级、随机池 ≈3%，种子固定容差 ±2pp）；观测模型单元测试：Se=1/Sp=1 时退化为干净 OR |
| **禁止** | 把「覆盖率达标」写成硬闸——E-X1 v4 实测覆盖均衡≠检测最优，诊断只告警不拦截 |

### W7 · 报告层（首版）

| 项 | 内容 |
|---|---|
| **目标** | B1 只做 `report/json_out.py`：`space.json` 落盘（schema `topos-space/1`，字段表见 ARCHITECTURE §9.3） |
| **验收** | 产物带 schema 号；`c_min` / `zero_cover_rate` 缺失时抛异常（缺失=bug 不是可选）；MD/HTML 渲染推迟到 B3 |
| **禁止** | B1 阶段做任何美化输出 |

**B1 出口判据**（满足才开 B2）：契约自检 ≥12 项全绿 + 解耦验收通过 + 对拍钩子 6/6 + `topos space <dir> --check` 对 mini-lab 与一个合成仓跑通。

---

## B2 批 · M1 标定

### W8 · 标定层

| 项 | 内容 |
|---|---|
| **目标** | `calib/`：金标管理 + Se/Sp 估计（带 CI）+ crowd-kit 胶水 + 温度缩放 |
| **搬/接** | **E4 crowd-kit**：`DawidSkene` / `OneCoinDawidSkene`（签名已核：`fit(pd.DataFrame task/worker/label)` → `labels_` / `probas_`；依赖 pandas/attrs/sklearn 全在 venv）。加载走**包壳 shim**（INTERFACE-CHECK §2.4），失败则按源码自写精简 EM（~100 行，此为已批准的降级路线） |
| **新写** | ① 金标 CSV 管理器（unit_id, truth, 标注人, 日期；append-only）；② **Hui–Walter 两源两群体估计**（crowd-kit 不给混淆矩阵置信区间——这个 Gap 自补，bootstrap 95% CI）；③ 温度/Platt 缩放（解码分数 → 校准概率）；④ 噪声地板声明：报告模板固定引用 PrimeVul 25%/Devign 24% 口径 |
| **预注册** | `PREREG/B2.md`：金标 300–500 单元的抽样规则（按池分层抽样，保证零覆盖单元入样）；判据 = Se/Sp 的 CI 半宽 < 0.15 视为可标定 |
| **验收** | ① 合成实验：已知 Se/Sp 的两源数据，Hui–Walter 估计落真值 CI 内；② 金标管理器：重复 unit_id 拒绝写入；③ 输出报告含噪声地板声明 |
| **禁止** | 在金标 <100 单元时对外报任何"真实精度"——只许报"仪器灵敏度" |

---

## B3 批 · M2 解码 + 真仓

### W5 · 解码器族

| 项 | 内容 |
|---|---|
| **目标** | `infer/decode.py`：DD / SCOMP / NB 三族 + 图先验宽度自适应 |
| **搬** | `decode_mini` 的 NB + 图先验（真仓 8.8× 实测件）；`power_lam_max` |
| **新写** | DD/SCOMP——**算法规范以 binGroup2 `R/` 源码为纸面基准**（GPL 不抄码，抄算法步骤，自己的实现）；图先验自适应：`α(width)` 随池宽衰减（[M] 条款"救弱不救泛"落地；衰减曲线本身 [U] → **必须预注册证伪判据**：宽池增益应 ≤1pp、窄池应 ≥+5pp，超出即修正） |
| **验收** | ① 真仓（**Python 标准库**，零下载）三解码器对照读数；② 硬排除 vs NB ≥8× 复现（audit-lab 案例口径）；③ 评估强制双指标（AUC+平衡准确率，decode run1 事故条款）；④ MD 报告渲染（W7 解锁美化） |
| **禁止** | 解码层输出二值判定；accuracy 单指标评估 |

---

## B4 批 · M3 停止

### W4 · Weitzman 最优停止

| 项 | 内容 |
|---|---|
| **目标** | `stop/weitzman.py` + `stop/budget.py`：σ 树 + 冷启动闭式 + 预算回路 |
| **新写**（mini-lab 无件，全新） | ① 每候选池 σ 求解（价值分布从当前 belief 导出）；② 冷启动闭式 `σ = w − c/θ`（[T] Weitzman 1979）；③ `topos next` CLI：输出下一个池或 STOP；④ 相关池 4.428-近似声明写进模块 docstring |
| **预注册** | `PREREG/B4.md`：判据 = 合成仓预算-召回曲线**优于固定下钻基线**（不承诺最优，[T] 相关池退化已知） |
| **验收** | 预算 8 池模拟：预算-召回曲线 ≥ 基线（两判据：同预算召回更高，或同召回预算更省） |
| **禁止** | 承诺"最优"；用未经 M1 标定的 Se/Sp 做停止决策 |

---

## B5 批 · M4 盲区

### W3 · sheaf 真实语义

| 项 | 内容 |
|---|---|
| **目标** | `core/sheaf.py`：限制映射从合成 ±1 升级为真实符号语义 |
| **搬** | `sheaf_mini.sheaf_laplacian / residuals / tv_residuals`（X5 三判据 [M] 10/10） |
| **新写** | 真实限制映射规则表：`declassify / endorse / sanitize` 等穿越动作 → ±1/约束（**上游依赖 A 轴工单 E×D×F 接缝判定纪律——该项待你裁决（Q3），裁决前本单不开工**） |
| **验收** | 真实接缝盲区可定位（非合成用例）；X5 三判据在新语义下保持全咬合 |
| **禁止** | 跳过 A 轴工单直接猜符号规则 |

---

## 附录 A · 契约自检 12 项 → 工单映射

| # | 自检项 | 归属 |
|---|---|---|
| 1 | 单元发现正确性 | W2 |
| 2 | 五类边各一例命中 | W2 |
| 3 | 融合图权重 = Σα | W2 |
| 4 | Lanczos λ₂ 残差 < 1e-6 | W2 |
| 5 | **清单解耦验收**（仅改清单加场/切片/组合池） | W1 |
| 6 | 切片算子各 op（含全 None 场边界） | W1 |
| 7 | 布尔嵌套组合 all/any/not | W1 |
| 8 | 空池丢弃 + constraints 执行 | W1 |
| 9 | c_min / zero_cover_rate 计算 | W6 |
| 10 | sheaf frustrated → H⁰=0 | W3（B1 先挂合成版） |
| 11 | 解码输出 ∈ [0,1] 非二值 | W5 |
| 12 | 缺 git → churn/age = None（不填 0） | W1 |

## 附录 B · 全局禁止事项（红线摘录，适用于全部工单）

1. 运行时零第三方依赖（stdlib only）；外部件只存在于 `reference/` 与离线校验。
2. 代码不出现轴名（清单单源）；同一机制禁止平行实现。
3. [U] 部件必须同时落一条预注册证伪判据，否则不合入。
4. 三态口径（咬合/不咬合/登记盲区）+ 修正案逐版披露；判据改到第四版必须停手。
5. `audit-lab` 与既有工程区只读；mini-lab 冻结（只许从它**复制**，不许改它）。
6. 合成仓数字禁止外推；真仓读数用 Python 标准库。

## 附录 C · 本工单新增 ADR

| ADR | 决策 | 理由 |
|---|---|---|
| A10 | 池布尔组合用 JSON 嵌套（`all/any/not`），不用字符串 DSL | 零解析器、无优先级歧义、JSON 原生 |
| A11 | `expand` 算子自动展开列表场 | 33 个 bandit tag 免手写 33 条切片声明 |
| A12 | None 是合法场值；切片一律排除 None，`notnull` 独立捞回 | "如实降级"红线的载体（缺 git 不填 0） |
| A13 | 解码器对照评估强制 AUC + 平衡准确率双指标 | decode run1 accuracy 被 FPR 主导的事故条款 |
