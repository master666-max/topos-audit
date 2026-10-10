# DESIGN-RECON —— 设计书对账报告（ARCHITECTURE §1.2/§3/§4 vs 实现现状，2026-10-10）

> 触发：用户问"坐标轴定义核对 + 现在只有函数拓扑到空间吗"。
> 方法：逐条对照 ARCHITECTURE.md D2/D5/D6/§3/§4 原文与代码/清单/回执证据。

---

## 0. 一页结论

1. **坐标轴的核心定义（D2/D5/D6）全部落实且有实战证据**：轴=场不是维度、四层解耦、
   清单单源——B1 解耦验收 + RUN1 三轮清单迭代零代码实测。
2. **"只有函数与函数关系拓扑到空间"= 设计决策，不是欠账**（D2 修正正是废弃
   v0.2"单元=K 维向量"的概念；底空间本体=函数级单元+五类耦合边多层图，§3.1 原文）。
3. **对账差异四处**（复核后修正一处）：random 对照轴**已实现未接线**（此前误报为未实现）；
   T 族场 **2/5**（作者分散度/缺陷修复耦合/演化稳定性三个未做，设计标注 M2 工单）；
   轴准入 Fisher 信息互补**未工具化**（设计标注 M2 落地）；单元粒度=函数/方法**按设计**，
   类/文件/模块级拓扑属第三阶段"坐标系加减完备性"议题。

## 1. 设计定义逐条对照

### 1.1 坐标轴的本体定义（D2 / §4.1）

| 设计原文要点 | 现状 | 证据 |
|---|---|---|
| 轴 = 场 `f: Unit → Value ∪ {None}`，不是维度 | ✅ 全部六个场按此实现 | axis/methods/* 返回 {idx: value\|None} |
| None 合法，禁止填 0（ADR-A12） | ✅ dsh 无 git 会降级；RUN1 实测 churn/age=1.0（有 git） | git_history.py |
| 四层解耦（D5）：场→切片→池→设计矩阵 | ✅ B1 解耦验收 + RUN1 清单三轮迭代零代码 | e1b15d4 |
| 清单单源（D6）：引擎只认 method | ✅ regex/git/ast/graph/random 五注册 | axis/registry.py |
| "维度是临时从场上切出来的" | ✅ slicers quantile/has/expand/between_q/notnull | pool/slicer.py |
| 嵌入降级为仪表（E-X1 不咬合，§3.3 最贵的一条） | ✅ diffusion 不进控制回路 | B1/B3 回执 |

### 1.2 底空间本体（§3.1）——回答"只有函数拓扑到空间吗"

**是，且是设计决策**：§3.1 原文"这是'多维拓扑图空间'里**唯一的本体**。'多维'指的是
**多层**，不是'每个单元是一个 K 维向量'"。单元 = 函数/方法（§1.2，N≈10³–10⁵），
五类耦合边（call/data/control/return/vardep，SCN 血统）构成多层图，融合 w=Σα·A。

| 维度 | 现状 | 边界声明 |
|---|---|---|
| 单元粒度 | 函数/方法（含 Class.method） | 类/文件/模块/包级**未进底空间**——设计内边界；扩展属第三阶段"坐标系加减完备性" |
| 五类边 | call 完整；data/control/return 近似（抽取器天花板 control=1/return=2 已如实登记）；vardep=共享模块级可变状态 | Joern 对拍已定量（M5） |
| 非代码工件 | 配置/文档不入空间 | 非目标（§1.3） |

### 1.3 场清单对照（§4.4 v3 schema vs axes.json）

| 设计场 | 层 | 现状 |
|---|---|---|
| anchor | L | ✅（33 tag，bandit 语义借化；v0.2 测试豁免 opt-in） |
| churn / age | T | ✅（E-T3 咬合件 8/1 commits） |
| loc | L | ✅（ast metrics） |
| forman / diffusion | G | ✅（forman 进控制回路；diffusion 降级仪表） |
| **random** | - | ✅ 已实现（random_fields.py，同种子可复现）——**默认 axes.json 未接线**（对账原报"未实现"修正为"未接线"） |
| authors（作者分散度） | T | ❌ 本批补 |
| fix_coupling（缺陷修复耦合） | T | ❌ 本批补 |
| stability（演化稳定性） | T | ❌ 本批补 |
| Fisher 轴准入 | - | ❌ 设计"可算化（M2 落地）"——本批补（topos/axis/admission.py） |

### 1.4 轴准入三准则（§4.5）

| 准则 | 设计 | 现状 |
|---|---|---|
| 信息互补 | 新轴 Fisher 行列式增量达阈值；\|ρ\|<0.3 只是初筛 | ❌→✅ 本批工具化（axis/admission.py） |
| 结构正交 | 信号来自不同工件类型（语法/配置/协作/历史） | 人工判据——本批进 admission 输出提示 |
| 尺度分层 | L/G/T；每加一个 L 轴必问 T 轴 | 人工判据——T 族补齐后达成 L2:G2:T4 配比 |

## 2. 铺平动作（本批 §3）

| # | 动作 | 落点 |
|---|---|---|
| 1 | random 场接线默认清单 | axes.json fields |
| 2 | T 族三场：authors / fix_coupling / stability | git_history.py（全仓单次 log 解析） |
| 3 | Fisher 轴准入工具 Δdet(FIM) | axis/admission.py + CLI axis-admit |
| 4 | selftest c32/c33/c34 | 31→34 |
| 5 | RUN1 v1.4 重跑（新 T 场实证） | EXP/run1_dsh/a |
