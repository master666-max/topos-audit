# RUN1 —— 首战回执：dsh-launcher 全仓扫描（2026-10-10）

> 预注册：`PREREG/RUN1-dsh.md`（读数前落定口径）｜ 靶沙箱：`tools/repos/dsh-launcher`
> （克隆 commit 1885de1，**topos 只读扫描**，原工程区零接触）｜ 运行辅助：`EXP/_run1_dsh.py`

## 0. 一页结论

1. **全链首跑成功**：250 单元 → 4 池 → NB 解码（图先验）→ σ 停止 → report.md，四步 CLI 零人工干预。
2. **默认清单在 250 单元靶上不适配**：`max_width_pct=0.03` 限死宽度，零覆盖 **96.4%**——覆盖
   三诊断当场报警（仪器按设计工作）。按工作流调清单重跑（清单单源，零代码），两版读数全留痕。
3. **top 读数源码级核验为真**，但语义集中在**测试脚手架**（dsh_tests.py 的 subprocess mock）——
   单正则信号源无生产/测试甄别，正是 seam 规则表 v0.2 已登记的「测试豁免缺失」条目。
4. 一切精度以「仪器灵敏度」名义出现（PREREG 诚实条款）。

## 1. 覆盖边界（先声明）

11 个 .py（7184 行）全覆盖；**2 个 .bat 不在任何后端覆盖内**——本读数只对 .py 子空间负责。

## 2. RUN1 v1（默认清单）——诊断读数

| 项 | 读数 |
|---|---|
| 空间 | 250 单元 ｜ 融合边 762 ｜ 13.1s |
| 场非空率 | anchor 0.084 ｜ churn/age **1.0**（克隆仓有 git）｜ forman 0.948 ｜ diffusion 1.0 |
| 覆盖 | n_pools=2 ｜ c_mean=0.04 ｜ **zero_cover=96.4%** |
| 设计告警 | p_anchor_breadth(21) 与 p_hot(81) 超 max_width=7 丢弃；p_stale_big(1) < min_pool_size 丢弃 |

**判定：默认清单不适配小靶**（其为 1.3 万单元标定量级调参）→ 触发工作流内置步骤：调清单重跑。

## 3. RUN1 v1.1（靶定制清单）——正式读数

清单：约束放宽 `max_width_pct 0.03→0.3`（250 单元靶配 75），池加 2 个组合
（p_semantic_hot = anchor∩churn:top，p_stale_hot = age:old∩churn:top）。

| 项 | 读数 |
|---|---|
| 池 | 4 存活：p_anchor_breadth / p_semantic_hot / p_deep_conf / p_big1（p_hot(81) 仍超宽丢弃、p_stale_hot 空池丢弃——如实） |
| 覆盖 | c_mean 0.04→**0.14** ｜ zero_cover 96.4%→**88.4%** |
| 观测 | **3 阳 1 阴**（p_big1=0，其余=1；anchor 命中 27 单元·次） |
| 解码（NB+图先验） | belief min=0.0151 / med=0.0429 / **max=0.9310** |
| σ 停止（cost0=0.05） | **NEXT → p_anchor_breadth（σ=10.8522）**，次序 p_semantic_hot 4.83 → p_deep_conf 2.74 → p_big1 0.35 |

**belief top-6**：`_Boom.run` 0.931 ｜ `t_kill_guard` 0.868 ｜ `_git_cmd` 0.737 ｜
`t_run_heal` 0.720 ｜ `_probe_tools` 0.683（前五全部 dsh_tests.py）｜ `dsh-accept.py::run_py` 0.399

## 4. 源码级核验（top-3 逐行验）

| 单元 | 实测命中 | 判读 |
|---|---|---|
| `_Boom.run:905` | L906-912 `subprocess.TimeoutExpired` mock、`L.subprocess = _Boom` | **信号真**；语义 = 测试替身（故意超时的 kill-guard 测试） |
| `t_kill_guard:890` | 同上（span 覆盖该测试体） | 同上 |
| `_git_cmd:1467` | L1470-1471 `subprocess.run([g, "-C", repo], capture_output=True, CREATE_NO_WINDOW)` | **信号真**；语义 = git 辅助（正规用法） |

**判读**：仪器报出的命中全部源码可指认（precision 语义达标）；但 top 读数集中在测试代码
——正则单信号源不区分生产/测试。**这正是 B5 已登记的 seam 规则表 v0.2「测试豁免缺失」
条目**——首战实战直接验证了该改进项的优先级。

## 5. 诚实条款与欠账

- 观测源单一（仅正则批）；Se/Sp=0.9/0.95 为**假设参数**——一切精度以「仪器灵敏度」名义。
- .bat×2 覆盖盲区；零覆盖仍 88.4%（池宽度与组合策略是 v0.2 迭代空间）。
- σ 停止的 cost0=0.05 沿用 B4 v1.4 实测默认，未按靶校准。

## 6. 战果与下一步

- **战果**：仪器首次在自家真实仓上全链跑通；覆盖诊断与源码核验均按设计工作；实测暴露的
  改进项（测试豁免、池宽自适应、多信号源）全部落在已登记的 v0.2 清单内。
- **下一步候选**：① v0.2 测试豁免 + 池宽自适应 → 重跑 RUN1 读数对照；② 接 LLM 批作第二
  信号源（B2 E4 既有管线）；③ L4 人工仲裁定标后重读。

## 7. RUN1 v1.2 addendum——测试豁免落地（v0.2 修复①，2026-10-10 同日）

**改动**：`axis/methods/regex.py` anchor 场新增 opt-in 参数 `exclude_tests: true`（token 化
测试识别：路径段 test(s)/spec(s)、conftest.py、文件名 token 含 test/tests——`dsh_tests.py`
命中、`latest.py` 不误伤）。**默认关闭，selftest 29/29 不受扰**；dsh 定制清单开启。
（池宽自适应**不做自动放宽**——W6 禁止条款「诊断只告警不拦截」，调清单走工作流人工步骤。）

### v1.1 vs v1.2 对照（同靶同清单仅差测试豁免）

| 项 | v1.1 | v1.2（测试豁免） |
|---|---|---|
| anchor 非空率 | 0.084 | 0.064（测试命中豁免） |
| 存活池 | 4（3 阳 1 阴） | 3（**1 阳 2 阴**；p_semantic_hot 变空池如实丢弃、p_deep_conf 阳→阴——原阳性就是测试单元） |
| belief max | 0.9310（`_Boom.run`，测试替身） | **0.3945**（`dsh-accept.py::run_py`） |
| top-12 构成 | 前五全 dsh_tests.py | **零测试文件**：dsh-accept / dsh-fallback-heal ×4 / dsh_env ×4 / dsh-launcher ×2 / dsh-plugins |
| σ 停止 | NEXT → p_anchor_breadth（10.85） | NEXT → p_anchor_breadth（6.11） |
| zero_cover | 88.4% | 90.4%（anchor 池收窄，如实） |

**榜首源码核验**：`dsh-accept.py::run_py` L24 `subprocess.run([PYEXE, "-X", "utf8",
str(TOOLS / script)], …)`——生产代码真实 subprocess 直连 ✓。

**判读**：测试豁免把读数从「测试脚手架通胀」拉回「生产危险 API 面」——top-12 全部是
进程管理/环境治理函数（kill_node、pid_alive、port_excluded、run_plugins、action_check），
这正是 dsh-launcher 作为启动器的真实风险面。v0.2 修复①实战闭环完成。

## 8. RUN1 v1.3 addendum——解析器 v0.2 + 装配级测试豁免（同日第三轮）

改动：layers.py 点链解析器（F3-py owner 归属 + self/import 别名才解析 + bare Name import
绑定精确解析）+ space.py 装配级 exclude_tests（图级豁免，测试单元及边最上游滤除）。
selftest c30/c31 → **31/31**。PREREG/M5 v1.4 登记。

| 项 | v1.1 | v1.2 | **v1.3（本轮）** |
|---|---|---|---|
| 单元 | 250 | 250 | **169**（装配级豁免） |
| 融合边 | 762 | 762 | 445 |
| 零覆盖 | 96.4% | 90.4% | **69.2%** |
| belief max | 0.9310（测试替身） | 0.3945 | **0.9724（run_heal——编排执行面）** |
| top-12 构成 | 测试通胀 | 生产面 | **dsh-launcher 编排执行面全占**（图先验扩散到危险操作调用方） |
| σ NEXT | anchor（10.85） | anchor（6.11） | **p_hot（24.67，池宽修复后最大池回归）** |

**判读**：测试豁免从「anchor 场读数豁免」升级为「图级豁免」后，几何/谱族读数同步对齐
生产面；图先验把信念扩散到危险操作的**调用方**（run_heal/run_plugins/_spawn_bg_and_wait
——恰是 §2 信任边界注记点），读数语义与架构认知一致。py 对拍 v1.3 = 1.0000（FP=0）、
js = 1.0000（FP=0）；**代价如实登记：py recall 0.8618→0.6083**（非别名链头不再猜）。
