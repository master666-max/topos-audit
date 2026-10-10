# STATE —— 项目全态与实战准备（2026-10-10 俯瞰）

> 上游：ARCHITECTURE.md（设计）/ WORK-ORDERS.md（工单+附录 D 状态注记）/ PREREG/*（判据链）
> 本文件：**证据先行**的全态快照 + 实战运行手册。数字全部可回溯到回执与 selftest。

---

## 0. 一页结论

1. **M0–M5 六个里程碑全部建成**：四层引擎→标定→解码→停止→sheaf 语义→多语言+Joern 校验，
   逐批出口判据留痕（B2 出口豁免按「缺省层如实登记」支线，登记于 WORK-ORDERS 附录 D）。
2. **仪器质量底盘**：selftest **29/29**（c01–c29）；数值对拍 **6/6**（Forman/λ₂ max|Δ|=0）；
   **Joern 金标对拍 v1.3 口径双靶咬合**（py 0.9881 / js 1.0000）；红线（stdlib-only、轴名单源、
   [U] 带证伪判据、既有工程区只读）**全数未破**。
3. **实战可以开打，但精度口径受限**：Se/Sp 未标定（L4 人工仲裁 100 单元欠账），实战读数
   一切精度只许以**「仪器灵敏度」**名义出现——这不是缺陷，是防污染设计。
4. ~~L3 SVEN~~ **已接入**（2026-10-10 晚）：368 对金标种子入库（calib/gold_l3_sven.csv）；五层套件仅剩 L4 人工仲裁欠账。

## 1. 里程碑全景

| 里程碑 | 批 | 出口判据 | 关键读数 | 证据 |
|---|---|---|---|---|
| M0 骨架 | B1 | selftest ≥12 + 解耦验收 + 对拍 6/6 | 四层解耦（仅改清单零代码）| e1b15d4；PREREG/B1.md（追认版） |
| M1 标定 | B2 | E-B2-1..5 | L1 patch 管线 112 样本零人工；L2 变异 26 体 score 0.769；L5 Hui-Walter 6/6 CI 含真值；E-B2-4 一致性 α=0.187→L4-control 作废（prevalence 悖论实证） | B2-E1..E5.md |
| M2 解码 | B3 | 真仓 ≥8× + 双指标 | 硬排除 vs NB **12.4×**；NB AUC 0.888；A8 只出概率（阈值归下游） | B3-E1/E2/E3.md |
| M3 停止 | B4 | 预算-召回 ≥ 基线 | recall_A=0.2419（+8.44pp）；首达 7 池；c₀ 相变 (0.1,0.25) | B4-E1.md |
| M4 盲区 | B5 | X5 三判据真实语义保持 | H⁰ 10/10+10/10；真仓构造性奇环（space→layers 对偶边） | B5-E1/E2.md |
| M5 多语言+校验 | W9 | E-M5-1/2 | JS 全链零退出；Joern 对拍：F1 主链路级 dedent bug 等 5 修复；v1.3 双靶咬合 | M5-E1/E2.md |

## 2. 仪器底盘（质量证据）

| 证据 | 现值 |
|---|---|
| 契约自检 | **29/29**（c01–c29，`python -m topos.selftest`；pytest 入口 `tests/`） |
| 数值对拍 | 6/6（Karate + mini-lab，max\|Δ\|=0，λ₂ Δ≤3.2e-15） |
| 金标对拍（Joern 4.0.652） | py 0.9881 / js **1.0000**（v1.3 口径，FP=0 on js）；金标盲区已分类登记 |
| 红线 | stdlib-only ✓ 轴名单源 ✓ [U]带证伪判据 ✓ 只读边界 ✓ |

## 3. 五层真值套件现状（实战口径的决定因素）

| 层 | 状态 | 产物 |
|---|---|---|
| L1 执行正样本 | ✅ | 112 样本 / 7 项目 / 带上游执行证据（B2-E2） |
| L2 变异注入 | ✅ | 5 算子 26 变异体，score 0.769（B2-E3，召回**下界**） |
| L3 SVEN 锚定集 | **✅ 已接入** | 368 对金标种子（calib/gold_l3_sven.csv，MIT）；EXP/L3-SVEN.md |
| L4 人工仲裁 | ⏳ **欠账** | 100 单元清单已生成（~8h，裁决已有证据而非盲标）；**定标前 Se/Sp 无实测值** |
| L5 Hui-Walter | ✅ | 合成 6/6 CI 含真值；独立性假设成立时可用（B2-E1） |

**推论**：L4 未定标 → 实战报告的一切精度只许以「仪器灵敏度」名义出现（全库已废止
"金标=真值"表述，统一"参照标准"——75b52ec 条款）。

## 4. 实战运行手册（四步 CLI，全链已验证）

```bash
# ① 建空间（py=AST [M]；js=正则级 [U]）
python -m topos space <目标仓> --json out/space.json [--lang js]

# ② 观测：池内锚点命中 → y∈{0,1}（正则批=确定性信号；obs={池名: y}）
#    锚点场已内建（bandit 33 tag 经 expand 自动成片），可按靶自定义 manifest

# ③ 解码（A8：只出概率，不出二值判定）
python -m topos decode out/space.json --obs out/obs.json --decoder nb \
       --adj out/adj.json -o out/belief.json

# ④ 停止决策（Weitzman σ；cost0=0.05）
python -m topos next out/space.json out/belief.json --cost0 0.05

# ⑤ 报告
python -m topos report-md out/space.json --belief out/belief.json -o out/report.md
```

判读三态口径：**咬合 / 不咬合 / 登记盲区**；NEXT→按 σ 序开池，STOP⇔max σ≤0。

## 5. 实战就绪度与首战提案

| 维度 | 就绪度 | 缺口 |
|---|---|---|
| 链路（py/js） | ✅ 双后端全链零退出 | — |
| 锚点 | ✅ 33 tag 内建 | 靶特定信号可加自定义 manifest |
| 精度口径 | ⚠️ 只许"仪器灵敏度" | L4 人工仲裁（~8h 人工） |
| 召回下界 | ✅ L2 变异库 | 扩算子种类=增量 |
| L3 增强 | ✅ 已接入 | SVEN 转换 368 对（EXP/L3-SVEN.md） |
| 校验器 | ✅ Joern 便携环境 | — |

**首战提案（建议顺序）**：① **dsh 仓**（用户主场，bat/cmd 内部机制判读力最强，topos
只读扫描不碰工程区）；② 标准 library 子集（零下载、B3 已有基线）；③ 任意第三方小仓
（express 已跑通，可换靶验证 JS 后端）。**红线**：audit-lab 与既有工程区只读——topos
只做只读扫描，天然兼容。

## 6. 欠账与风险

| # | 项 | 性质 | 影响 |
|---|---|---|---|
| 1 | L4 人工仲裁 100 单元（~8h） | 人工 | 定标前无实测 Se/Sp，精度只报灵敏度 |
| 2 | L3 SVEN 未开工 | 数据 | 金标种子层缺位（L1/L2 已兜底） |
| 3 | py 侧 3 条对拍 FP（from_dict / 嵌套归因 / argparse 撞名） | 可选收敛 | 不影响门（v1.3 py 0.9881） |
| 4 | control/return 层召回欠采 | 已知天花板 | M5 对拍已定量，[M] docstring 声明 |
| 5 | B2 出口豁免（E-B2-4 缺省层） | 已登记 | WORK-ORDERS 附录 D |

---

## 7. 2026-10-10 晚更新（对账铺平批，e751f0e+）

设计书对账（`EXP/DESIGN-RECON.md`）发现的三处差异**全部铺平**：

- **random 对照轴**：已实现未接线 → 接线默认清单（同种子可复现，c33）
- **T 族场 2/5**：补 authors / fix_coupling / stability（git_history 单次全仓 log 解析）→ **T 族 5/5**
- **Fisher 轴准入**：工具化 `topos/axis/admission.py` + CLI `axis-admit`（Δcov / 正相关 ρ / Δlogdet 三读数合看；负 ρ=互补覆盖是组测试的好性质，不算冗余）
- **py 解析器 v0.2 + 图级测试豁免**：点链解析器（F3-py owner 归属、self/别名才解析、不猜）+ manifest 顶层 exclude_tests → **两靶对拍 v1.3 双 1.0000（FP=0）**，py 注册口径 0.9851 咬合；代价 py recall 0.8618→0.6083 如实披露
- selftest 29→**34/34**（c30 owner 归属 / c31 装配级豁免 / c32 T 族 / c33 random / c34 准入）
- RUN1 v1.4 重跑：**10 场全接**，dsh 上 T 族三场 100% 可算（`EXP/run1_dsh/a`）

**剩余欠账（不变）**：L4 人工仲裁 100 单元（~8h 人工）｜ L3 SVEN（对外报数前）｜ forman 豁免已在本批（③方案B）✅
