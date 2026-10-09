# INTERFACE-CHECK —— 参考件拼合 · 接口检查 · 自研边界

> 日期：2026-10-09 ｜ 状态：全部接口已实测（除 M1 级 crowd-kit 为签名级核对）
> 上游：`ARCHITECTURE.md` v0.1 ｜ 下游：M0 骨架（可直接按 §5 清单开工）

---

## 0. 一页结论

1. **已下载 5 件**（14 MB），全部落在 `reference/`（gitignore，不进运行时、不进发布）。
2. **数值件对拍 6/6 全绿**：手写 Forman 与 GraphRicciCurvature 两图 154 边**精确零差**；手写 matvec ≡ scipy 拉普拉斯**零差**；λ₂ 两路一致到 **1e-15**。零依赖手写件的数值正确性有了外部锚。
3. **锚点件已转换**：bandit 黑名单 → `anchors-bandit.json`（**33 tag** = 12 内置语义全覆盖 + 31 新增），regex 实测 3/3 命中。
4. **自研边界敲定**（§5）：7 个模块必须自写（无现成件），4 个位置用外部件（已验接口），1 个待裁决（semgrep-rules，LGPL）。
5. **1 件失败**：code-maat（镜像全挂）；churn 对拍降级由自家 E-T3 实测兜底。

## 1. 获取台账

| 件 | 路径 | 许可 | 体积 | 获取方式 | 状态 |
|---|---|---|---|---|---|
| bandit | `reference/bandit` | Apache-2.0 | 5.3M | tarball（gh-proxy） | ✅ |
| GraphRicciCurvature | `reference/GraphRicciCurvature` | MIT | 4.4M | 浅克隆 | ✅ |
| crowd-kit | `reference/crowd-kit` | Apache-2.0 | 1.6M | 浅克隆 | ✅ |
| binGroup2 | `reference/binGroup2` | GPL-3 | 2.4M | 浅克隆（cran 镜像） | ✅ |
| scipy / networkx / pandas / attrs | venv 已有 | BSD/MIT | — | 无需下载 | ✅ |
| code-maat | — | Apache-2.0 | — | tarball×3 镜像 + ls-remote 全挂 | ❌ 失败 |
| semgrep-rules | — | **LGPL** | — | **故意未下** | ⏸ 待裁决 |

坑实录：bandit 默认分支是 `main`（tarball 目录 `bandit-main`，不是 clone 猜的 `master`——master/main/develop 三连 404 后 tarball 一次成功）；binGroup2 用 cran GitHub 镜像。

## 2. 逐件接口检查

### 2.1 bandit（锚点规则源）——已拼合 ✅

- **接口**：`bandit.blacklists.calls.gen_blacklist()["Call"]` → 20 条调用黑名单；`imports.gen_blacklist()["Import"]` → 13 条导入黑名单。每条 `{name, qualnames[], level, message}`。
- **加载策略**：pip 源不可用（`from versions: none`，openpyxl 同款症状）→ **sys.path + 包壳 shim**（伪造 `bandit`/`bandit.core`/`bandit.blacklists` 三个模块壳，单文件加载 constants→utils→issue→blacklists.utils→calls/imports），绕开会拉 stevedore 的 `__init__.py`。依赖链全 stdlib，实测可跑。
- **拼合产物**：`reference/anchors-bandit.json`（`_make_anchors_bandit.py` 生成），格式 = `[[tag, regex], ...]`，与 `coord_mini._load_patterns` 的外置清单格式**逐字对齐**（已核对源码 134-142 行）。
- **转换规则**：calls → `sink:<name>`，qualname → `\b<escaped>\s*\(`；imports → `import:<name>`，→ `\b<escaped>\b`。
- **实测**：`sink:eval`/`sink:pickle`/`import:import_pycrypto` 三条 regex 对样例源码 3/3 命中。
- **语义覆盖**：内置 12 类（sink:eval/exec/os-system/subprocess/pickle、sql:raw、io:*、secret、entry:*）中 sink 系全部被覆盖；**新增 31 tag**：md5、ciphers、cipher_modes、mktemp_q、urllib_urlopen、random、telnet、XML 全家桶（6 个）、ftplib、unverified_context、mark_safe、marshal + import 系 13 个。
- **Gap（如实）**：bandit 按 AST qualified-name 匹配，我们按源码文本近似——`from x import eval as e` 这类别名场景文本正则会漏。这与 E 路调研的"regex 轴天然下限"一致，不改设计，靠后验层兜。

### 2.2 GraphRicciCurvature（Forman 对拍校验器）——已实测 ✅

- **接口**：`FormanRicci(G: nx.Graph, weight, method, verbose)` + `compute_ricci_curvature()` → 边属性 `formanCurvature`（**注意：属性名无下划线**；且 `from GraphRicciCurvature import FormanRicci` 拿到的是子模块不是类，必须 `from GraphRicciCurvature.FormanRicci import FormanRicci`）。
- **口径核对（源码级）**：`method="1d"` 分支排除对端邻居后 `F = 1+1−(du−1)−(dv−1) = 4−du−dv` ——与手写 `coord_mini.forman_curvature` **逐字同口径**。
- **对拍结果**（`_crosscheck.py`，Karate N=34/E=78 + mini-lab 调用图 N=65/E=76）：
  - Karate **78/78 边 max|Δ|=0.00e+00**
  - mini-lab **76/76 边 max|Δ|=0.00e+00**
- **踩过的坑（进了对拍脚本注释）**：karate_club_graph 自带 `weight` 边属性，GC 自动走加权路径 → 必须先去权（第一轮 max|Δ|=11.5 就是它，不是实现错）。
- **加载策略**：shim 假 `community.community_louvain` 模块（python-louvain pip 装不上，FormanRicci 只用 util 的 logger/set_verbose，louvain 是死依赖）。
- **角色**：**离线校验器**（CI 里抽图对拍），不进运行时——维持零依赖红线。

### 2.3 scipy（λ₂ 真值锚）——已实测 ✅

- **接口**：`eigsh(L, k=2, which="SA")`；`csgraph.laplacian(A)` 当参考 L；`LinearOperator(matvec=…)` 可直接包住手写 `_matvec_L`。
- **实测**：dense L 与 LinearOperator 两路 λ₂：Karate 0.468525 / mini-lab 0.000000（调用图多分量，λ₂=0 合理），Δ ≤ 3.8e-15。
- **手写侧验证**：`_matvec_L` 逐列 vs scipy 拉普拉斯，两图 **max|Δ|=0**。
- **坑**：shift-invert（`sigma=0`）对奇异 L 内部 gmres 不收敛 → 用 `which="SA"`。
- **对 mini-lab 的含义**：E1 的 Lanczos(m=80) λ₂ 残差 1e-7 之外，现在**连 L 矩阵本身**也被外部锚定——谱链路（图→L→λ）全程可校验。

### 2.4 crowd-kit（M1 标定用）——签名级核对，M1 接线

- **接口**：`DawidSkene(n_iter=..., tol=...)` + `fit(data: pd.DataFrame)` / `fit_predict()` / `labels_` / `probas_`；同族还有 `OneCoinDawidSkene`（**两群体 Se/Sp 场景更贴**）、`GoldMajorityVote`（有金标种子时）。
- **输入契约**：DataFrame 三列 `task / worker / label`（众包命名）。映射到我们：task=单元 id，worker=信号源（正则批/LLM 批/测试批），label=该源的判定。
- **依赖面（已核源码）**：`attr + numpy + pandas + sklearn`（base 的 BaseEstimator）——venv **全部已有**。
- **加载策略**：**单模块 shim**（`crowdkit/__init__` 干净，但 `aggregation/__init__` 会拉 embeddings/texts/image_segmentation 旁支）——伪造 `crowdkit.aggregation` 包壳只加载 base + classification。
- **Gap**：输入必须是 pandas DataFrame（我们内部是 dict）→ 一层适配（几行）；`DawidSkene` 输出标签后验，**不含标注者混淆矩阵的置信区间** → Hui–Walter 的区间估计要自补（M1 的真实工作量）。
- **裁决点**：M1 时若 shim 加载成功则直接用；失败则按其源码自写精简 D-S（EM 核心 ~100 行）。

### 2.5 binGroup2（组验算法参考）——读源参考，不接线

- R 包，`R/` 目录即算法手册：`DorfmanFunctions.R`（二阶段 Dorfman）、`Inf.Array/Inf.D3/Inf.D4/Inf.D5`（信息矩阵最优设计）、`NI.A2M/NI.Array`（非信息设计）、`MultiplexHierarchicalFunctions.R`（分层法）。
- **用途**：DD/SCOMP 的标准实现对照 + **池设计的优化目标函数参考**（`Inf.*` 系列就是在算"什么样的设计矩阵信息量最大"——直接对应 §4.5 的 D-最优准入）。
- **不接线理由**：GPL-3 传染 + R 运行时不存在；当**纸面规范**用。

### 2.6 code-maat（churn 对拍）——❌ 失败，降级

master/main/develop 三个分支 tarball 在 gh-proxy/ghproxy.net 均 404，`ls-remote` 挂死（仓库疑似改名/转移）。**影响评估：零**——churn 轴的正确性已有 E-T3 实测兜底（8/1 commits 精确恢复），code-maat 本来就只是锦上添花的第二锚。churn 对拍需求改判：**用 git log 直接重放两种解析器互证**（自家 30 行 vs `git shortlog` 聚合，零外部依赖）。

## 3. 对拍回执汇总

| 对拍 | 图 | 结果 |
|---|---|---|
| A Forman 边曲率（手写 vs GC 1d） | Karate | 78/78，max\|Δ\|=0 |
| A Forman 边曲率 | mini-lab 调用图 | 76/76，max\|Δ\|=0 |
| B matvec ≡ scipy L | 两图 | max\|Δ\|=0 |
| C λ₂（dense vs LinearOperator） | Karate | 0.468525，Δ=3.2e-15 |
| C λ₂ | mini-lab | 0.000000，Δ=9.2e-16 |
| 锚点 regex 实测 | 3 样例 | 3/3 命中 |

原始回执：`reference/crosscheck-result.json`（由 `_crosscheck.py` 落盘）。

## 4. 拼合落位（哪些清单改了）

| 位置 | 动作 | 状态 |
|---|---|---|
| `topos-audit/.gitignore` | 新建：ignore `reference/`（保留 INTERFACE-CHECK.md 与 anchors-bandit.json 两个例外） | ✅ |
| `reference/anchors-bandit.json` | bandit 33 tag 锚点清单（清单 v3 的 `fields[]` 直接引用） | ✅ |
| `reference/_make_anchors_bandit.py` | 一次性转换工具（bandit→清单） | ✅ |
| `reference/_crosscheck.py` | 三组对拍脚本（Forman/matvec/λ₂） | ✅ |
| mini-lab `axes.json` | **未动**——迁移到清单 v3 是 M0 的事，遵守"mini-lab 冻结" | — |

## 5. 自研边界（界定"我们需要写的部分"）

### 5.1 必须自写（无现成件可拿，全部有预注册判据）

| # | 模块 | 为什么买不到 | 预注册判据 |
|---|---|---|---|
| W1 | **四层解耦引擎**（fields/slicers/pools/design + 清单 v3 加载校验） | 项目本体，`axes[]→三段拆分`是本设计书核心修正 | 仅改清单新增 2 场+1 组合池，零代码改动；契约自检 ≥12 项 |
| W2 | **五类耦合边抽取器**（call/data/control/return/vardep） | 没有任何现成库在函数级抽这五类（Joern 的 CPG 是另一形态，仅离线校验） | 合成仓逐层断言（space_mini 已 10/10，正式版继承） |
| W3 | **sheaf 层**（stalk/限制映射/Laplacian/H⁰ 亏空/残差） | 只有学术原型（Hansen & Gebhart），无生产级库 | X5 三判据（frustrated→ker=0；残差定位；TV 分离） |
| W4 | **Weitzman 最优停止**（σ 树+冷启动闭式+Snell 包络） | 最优停止无通用开源实现 | 模拟仓预算-召回曲线优于固定下钻基线 |
| W5 | **解码器**（COMP/DD/SCOMP/NB/图先验宽度自适应） | Python 侧无组验库（binGroup2 是 R 且 GPL） | 真仓三解码器对照读数；硬排除 8.8× 复现 |
| W6 | **观测与诊断**（带噪 OR、c_min/zero_cover/宽度、设计矩阵三诊断） | 微小但无现成——是条款的载体 | E-X1 条款数字在工具内可复算 |
| W7 | **报告层**（MD/JSON 输出、schema 版本化） | 胶水，无买点 | 产物带 schema 号；缺必填诊断字段即 bug |

### 5.2 用外部件（只写胶水，不写本体）

| # | 位置 | 件 | 胶水量 | 状态 |
|---|---|---|---|---|
| E1 | 锚点轴规则源 | bandit 黑名单 | 转换脚本 60 行（**已写完已实测**） | ✅ |
| E2 | Forman 校验器 | GraphRicciCurvature | adj→nx.Graph 适配 + community shim ≈20 行（已写） | ✅ |
| E3 | 谱校验锚 | scipy eigsh | LinearOperator 包装 3 行（已写） | ✅ |
| E4 | M1 标定 | crowd-kit DawidSkene/OneCoinDawidSkene | dict→DataFrame 适配 + 包壳 shim（M1 写） | ⏳ M1 |

### 5.3 待裁决

| # | 事项 | 建议默认 |
|---|---|---|
| P1 | **semgrep-rules 要不要下**：LGPL 许可（规则文本传染风险）+ 多语言大仓 + bandit 已覆盖 Python sink 语义；收益主要在非 sink 类规则（secrets、crypto 误用） | **不下**；若要，先只转 Apache 兼容的规则语义并做来源登记 |
| P2 | code-maat 替代：churn 双解析器互证（git shortlog vs 自家解析） | 采纳，M0 顺手做 |
| P3 | Joern（M5 离线校验器）：GB 级 JVM 发行包，C 盘紧张 | **M5 时再下**，下前给你体积预算 |
| P4 | crowd-kit 装法：pip 装不上已成事实 → vendor 单模块 shim vs 自写精简 D-S | M1 先试 shim，不行自写 |

## 6. 红线核对（本批动作是否违规）

- 零依赖红线：**未破**——bandit/GC/crowd-kit 全部只当参考件/离线校验器，venv 里装的只有本就存在的 scipy/networkx/pandas，运行时（topos 包）仍 stdlib-only。
- mini-lab 冻结：**未动一行**。
- 沙箱纪律：所有下载与脚本全在 `topos-audit/reference/`。
