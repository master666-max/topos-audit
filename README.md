# ToposAudit

> 在拓扑空间上做统计最优的缺陷检出。
> 把代码映射到多维坐标系（拓扑 / 几何·谱 / 语义 / 时间），坐标系切片组成"池"，
> 用 **组测试（group testing，1943 血统）+ 重叠投票 + 概率算账** 定位缺陷——
> 核心纪律：**可少报，不可误报；一切精度如实冠以"仪器灵敏度"或"实测"名头。**

---

## 状态（2026-10-10）

| 项 | 现值 |
|---|---|
| 里程碑 | **M0–M5 全部建成**（四层引擎 → 标定 → 解码 → 最优停止 → sheaf 语义 → 多语言 + Joern 校验） |
| 契约自检 | **34/34 PASS**（`python -m topos selftest`；pytest 入口 `tests/`） |
| 数值对拍 | 6/6（Forman 曲率 / λ₂ vs GraphRicciCurvature + scipy，max\|Δ\|=0） |
| 金标对拍 | Joern 4.0.652 便携环境；v1.3 口径 **py 1.0000 / js 1.0000 双咬合（FP=0）**，py 注册口径 0.9851 咬合 |
| 坐标系 | **10 场**（拓扑/语义/规模 + 几何·谱 + T 族四场 + random 对照），全部清单单源 |
| 首次实战 | **RUN1 已完成**（dsh-launcher 全仓：全链跑通、σ 数学最优停止、三池全审查、零确认漏洞） |
| 依赖 | 运行时 **stdlib only**；外部件（Joern/scipy 等）只作离线校验器 |

## 它怎么工作

**四族坐标系**叠在同一张函数图上：拓扑族（call 图五类耦合边）、几何·谱族（Forman 曲率 +
扩散嵌入）、语义族（bandit 33 tag 危险 API 锚点）、时间族（git 演化场）。四层引擎把坐标
读数解耦成 **场 → 切片 → 池 → 设计矩阵**；池进组测试观测，NB/DD/SCOMP 解码做概率算账
（图先验让坐标系互相印证），Weitzman σ 停止决定"审到哪算够"，sheaf 接缝专查证词矛盾。

```bash
# ① 建空间（py=AST [M]；js=正则级 [U]）
python -m topos space <目标仓> --json out/space.json [--lang js]
# ② 解码（观测 = {池名: y}，来自锚点批/LLM 批/测试批；A8：只出概率）
python -m topos decode out/space.json --obs out/obs.json --decoder nb --adj out/adj.json -o out/belief.json
# ③ σ 最优停止：NEXT（开哪个池）或 STOP
python -m topos next out/space.json out/belief.json --cost0 0.05
# ④ 报告
python -m topos report-md out/space.json --belief out/belief.json -o out/report.md
# ⑤ 新池准入体检（轴准入三准则 §4.5 的工具化）
python -m topos axis-admit out/space.json --cand-name 新池 --cand 1,2,3 [--belief out/belief.json]
```

## 空间本体论（§3 设计决策）

**底空间 = 函数级单元 + 五类耦合边多层图**——这是"多维拓扑图空间"里唯一的本体。
"多维"指的是**多层**，不是"每个单元是一个 K 维向量"（v0.2 的概念混淆已被 D2 修正废弃）。
**坐标系不拓扑成维度——它们是定义在同一张图上的多个场，经切片后共同生成池空间。**

| 层 | 边类型 | 语义 |
|---|---|---|
| call | 调用 | f 调用 g |
| data | 数据流 | g 的返回值流入 h（含跨函数值穿越） |
| control | 控制依赖 | g 的结果决定 h 是否执行 |
| return | 返回耦合 | 二者向同一调用者返回 |
| vardep | 变量依赖 | 共享模块级可变状态 |

融合图 `w(e) = Σ_t α_t·1[e∈E_t]`。**已知天花板**：data/control/return 为函数对近似
（抽取器天花板已由 Joern 对拍定量，控制/返回层欠采不承诺完备）。

## 坐标系场清单（v0.2，10 场）

| 场 | 层 | method | 语义 |
|---|---|---|---|
| anchor | L | regex | 危险 API 锚点（bandit 33 tag 语义借化；测试豁免 opt-in） |
| loc | L | ast | 函数行数 |
| forman | G | graph | Forman 曲率（图结构异常位置） |
| diffusion | G | graph | 扩散嵌入（**降级为仪表**——E-X1 实测不进控制回路） |
| churn | T | git | 提交次数 |
| age | T | git | 首末提交跨度 |
| authors | T | git | 作者分散度（v0.2 补） |
| fix_coupling | T | git | 缺陷修复耦合（fix commit 触达多文件，v0.2 补） |
| stability | T | git | 演化稳定性 = 1 − 近 90 天提交占比（v0.2 补） |
| random | - | random | 对照轴（同种子可复现；证伪"任何池都有效"） |

**轴准入三准则已工具化**（§4.5）：新池/新轴准入看三读数——**Δcov**（覆盖增量）、
**正相关 ρ**（<0.3 初筛；负 ρ=互补覆盖，是组测试想要的好性质）、**Δlogdet**（Fisher 式
信息增量）。`python -m topos axis-admit …` 三读数合看，不许单读数下结论。

## 五层真值套件（精度口径的决定因素）

| 层 | 状态 | 产物 |
|---|---|---|
| L1 执行正样本 | ✅ | 112 样本 / 7 项目 / 带上游执行证据 |
| L2 变异注入 | ✅ | 5 算子 26 变异体，score 0.769（召回**下界**） |
| L3 SVEN 锚定集 | ❌ 未开工 | 386 Python 漏洞函数（对外报数前开工，0.5–1 天） |
| L4 人工仲裁 | ⏳ 欠账 | 100 单元清单已生成（~8h）；定标前读数以"仪器灵敏度"名义 |
| L5 Hui-Walter | ✅ | 合成 6/6 CI 含真值（需双独立信号源假设） |

## 拼合的开源成果与协议边界

本仪器不是闭门造车——**站在一批开源成果上拼合而成**，但拼合方式经过刻意的协议设计。
台账见 `reference/INTERFACE-CHECK.md`（每件的接口实测、许可、集成方式）：

| 成果 | 许可证 | 拼合角色 | 集成方式 | 传播判定 |
|---|---|---|---|---|
| bandit (PyCQA) | Apache-2.0 | 锚点规则源 | **语义借化**：20 条调用黑名单转成自有清单 `reference/anchors-bandit.json`（33 tag），不拷代码 | 无 |
| GraphRicciCurvature | MIT | Forman 曲率对拍校验器 | 离线跑（不进运行时），数值锚 78+76 边 max\|Δ\|=0 | 无 |
| scipy / networkx / pandas | BSD/MIT | λ₂ 真值锚 / 标定依赖 | venv 内离线对拍；**运行时零 import** | 无 |
| crowd-kit | Apache-2.0 | M1 标定 Dawid-Skene | 包壳 shim 待接（失败则自写精简 EM） | 无 |
| Joern | Apache-2.0 | 离线金标校验器（CPG 对拍） | 便携环境放 `tools/`（gitignore），产物只进回执 | 无 |
| binGroup2 (R) | **GPL-3** | 组检验算法规范（Dorfman/Inf.* 最优设计） | **故意不接线**：只读 R 源码学算法步骤，不抄码不打包 | **防火墙案例** |
| semgrep-rules | **LGPL** | 规则语义参考 | **故意连下载都未做** | **防火墙案例** |
| code-maat | Apache-2.0 | churn 对拍 | 镜像全挂 → 弃；自家 git 重放兜底 | 无 |
| SVEN | 待查 | L3 金标种子层 | 未开工；**开工前先过许可审查** | 待查 |

**协议防火墙的三道边界**（GPL/LGPL 不传播的结构性原因）：

1. **运行时 stdlib-only**——外部件与运行时零链接，无依赖即无传播；
2. **重件不进仓**——`reference/` 克隆件与 `tools/`（Joern 4GB）全部 gitignore，仓库只留
   5 个轻文件（对拍脚本、转换器、结果 json、接口台账、锚点清单）；
3. **借化留痕**——外部成果以「语义转换 / 读数回执 / 纸面规范」三种形态使用，全部在
   INTERFACE-CHECK.md 声明来源与许可证；抄算法步骤不抄码（binGroup2 条款）。

**结论：本仓 MIT 干净成立，发布物零第三方制品。**

## 首战战果（RUN1 · dsh-launcher）

250→169 单元（三轮清单迭代 + 测试豁免）全链跑通；覆盖诊断当场报警默认清单不适配
（96.4% 零覆盖 → 清单迭代修复）；测试豁免（v0.2）把读数从测试脚手架通胀拉回生产风险面；
**σ 停止在数学最优处提前收手**（confirmed=3.54 > 剩余σ=0.58 → STOP，省 2/3 开池成本）；
开池审查 15/15 单元源码级核验——**零确认漏洞，2 条正面发现，1 条信任边界注记**；
v1.3 第三轮（图级豁免 + 点链解析器）后 py/js 对拍 FP=0。全程回执：`EXP/RUN1-dsh*.md`。

## 文档地图

| 文件 | 内容 |
|---|---|
| `ARCHITECTURE.md` | 设计书（架构条款 / ADR / 问答裁决链 / §4 坐标轴系统） |
| `STATE.md` | **项目全态快照 + 实战运行手册**（从这里开始读） |
| `WORK-ORDERS.md` | 自研工单 + 附录 D 逐单状态注记 |
| `PREREG/` | 见数据前注册的判据链（B1–B5、M5 v1.4、RUN1） |
| `EXP/` | 实验回执（B2–B5、M5、RUN1、DESIGN-RECON 对账，全部带 schema 与证据指针） |
| `reference/INTERFACE-CHECK.md` | 参考件接口对拍（外部件全部离线化） |

## 设计纪律（红线）

1. 运行时零第三方依赖；外部件只当离线校验器。
2. 轴名单源：加/减坐标系 = 改 `axes.json`，引擎零代码改动；代码不出现轴名。
3. [U] 部件必须带预注册证伪判据，否则不合入；判据改到第四版停手。
4. 三态口径（咬合 / 不咬合 / 登记盲区）+ 修正案逐版披露。
5. 金标 ≠ 真值：Se/Sp 必须带参照标准标签；精度数字只许以「仪器灵敏度」或
   「实测（含参照标准）」名义出现。

## 路线图（研究主线三段）

1. **① 已建成**（M0–M5）：本 README 描述的全部能力。
2. **② 前沿数学深化**：时间维度序列化（T 族场的时间序列化）、信息论/RAG/向量化坐标、
   最优轴设计（Fisher 准入已工具化，阈值待标定）。
3. **③ 坐标系加减完备性**：模块/文件级拓扑是否入空间、非代码工件、单元粒度扩展——
   走 PREREG 正式议题。

## License

MIT
