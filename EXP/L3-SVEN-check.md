# L3-SVEN-check —— L3 种子对仪器的第三方对照报告（2026-10-10）

> 触发：用户令"用 L3 种子对 RUN1 的 dsh 读数做第三方对照"。
> **对照形式澄清**：SVEN 与 dsh-launcher 零代码重叠——dsh 读数本身无法用 SVEN 直接核对。
> 可行的落地 = **把 L3 当已知真值靶（368 对漏洞/修复函数），实测产生 RUN1 读数的同一套
> 仪器链路在已知真值上的判别力**。这是 RUN1 结论的第三方检验。
> 脚本：`EXP/_l3_check.py` ｜ 数据：`EXP/l3_sven/`（PREREG/L3.md 口径）

---

## 0. 一页结论（诚实、且疼）

1. **anchor 正则信号源在 SVEN 已知漏洞域的配对判别力 = 零正向，且统计显著地反向**：
   368 对（漏洞版 vs 修复版）中 win **0** / tie 360 / **loss 8**（符号检验 p=0.0078，
   反向显著）。Phase 2 全链（738 单元端到端解码）同向：win 0 / tie 359 / loss 9。
2. **反向机制已实锤**：8 个 loss 全部 cwe-078（命令注入），模式一致——**漏洞版没有
   subprocess，修复版反而 `import subprocess`**（backintime / mobly / isort /
   rust-build / titania-os 五个真实项目）。机制 = 命令注入的标准修复方式就是
   "弃 shell 拼接、改 subprocess 列表参数"——bandit 的 `import_subprocess` tag 在
   **加固后的代码上亮灯**。API 使用 ≠ 漏洞，regex 原理性测不出方向。
3. **对项目主张的影响**：RUN1 从未声称"anchor 命中=漏洞"（注意力分配器 + 人工审查
   定位），该用法不受影响；但**任何"用正则信号直接判漏洞"的外推被本对照击杀**。
   L4 人工仲裁的必要性从"流程欠账"升级为**"有对照实验支撑的硬前提"**；多信号源
   （LLM 批）从"条件触发"获得第一条实测证据（单信号在 SVEN 域判别力为零）。
4. **这恰好是 L3 存在的意义**：没有 L3，这个反向现象不可知。金标种子的价值第一次
   兑现——它证明了我们不知道自己不知道什么。

## 1. Phase 1 信号层配对判别（368 对，直接正则）

| 读数 | 值 |
|---|---|
| 配对数 | 368（漏洞版 func_src_before vs 修复版 func_src_after） |
| win（vul 命中 > fix） | **0** |
| tie | 360 |
| loss（fix 命中 > vul） | **8**（全部 cwe-078） |
| 符号检验 | p = 0.0078（反向显著） |

**per-CWE**：cwe-022 33 对全 tie；cwe-078 90 tie + 8 loss；cwe-079 37 全 tie；
cwe-089 200 全 tie。SQL 注入（089）的拼接模式（format/f-string）在修复版里通常只是
换成参数化查询——**两次都不命中"import"类 tag**，信号对 SQL 注入域近乎全盲（360 tie）。

## 2. loss 对深挖（8 对，机制 100% 一致）

| 项目 | 文件 | vul tags | fix tags |
|---|---|---|---|
| backintime | qt4/plugins/notifyplugin.py | [] | [import_subprocess] |
| titania-os | vuedj/configtitania/views.py | [] | [import_subprocess] |
| rust-build ×3 | repack_rust.py | [] | [import_subprocess] |
| isort ×2 | test_isort.py | [] | [import_subprocess] |
| mobly | adb.py | [] | [import_subprocess] |

修复方式 = 引入 `subprocess` 列表参数调用替代 shell 拼接（加固），bandit tag 反向亮灯。

## 3. Phase 2 全链端到端（sven_space 738 单元）

- 空间：每函数一文件（dedent 后写入——F1 同病第三处，写入时修复）；738 单元
  （736 记录 + 2 个 dedent 后暴露的多函数文件）。
- 观测：正池（34 个 anchor 命中单元）y=1 ｜ 负池（704 个无命中）y=0。
- 解码（NB+图先验，Se/Sp=0.9/0.95 假设参数）：belief ∈ [0.0044, 0.4286]——
  0.4286 = 正池后验的理论值（se·π/(se·π+(1−sp)(1−π))，π=0.04）✓ 解码数学自洽。
- 配对 belief：win 0 / tie 359 / loss 9 —— 与 Phase 1 同向。

## 4. 三读数合看的结论

| 命题 | 判定 |
|---|---|
| "anchor 信号在 SVEN 域可作漏洞检测器" | **证伪**（win=0，反向显著） |
| "RUN1 的注意力分配用法" | **不受影响**（从未声称命中=漏洞；且 dsh 域的命中已人工复核为良性/守卫） |
| "单信号源可定标" | **证伪** → L4 必要性实测坐实 |
| "多信号源条件触发" | **获得第一条实测证据**（但仍等 L4 后再议——顺序纪律不变） |
| 仪器新改进条目 | +1：**加固识别**——regex 无法区分"危险使用"与"加固使用"，此为 LLM 批/执行证据批的结构性论据（登记 v0.2+） |

## 5. 诚实条款

- 本对照只测 **anchor 正则信号源**；几何/时间族在 SVEN 域不可用（无项目上下文/git）。
- Se/Sp 为假设参数；SVEN 标注 94% 精度（~6% 噪声）；Python 子集 4 CWE。
- 738 vs 736：dedent 后 2 个文件暴露多函数结构（如实）。
- Phase 2 的 obs 由信号自身生成（正池=命中的单元）——本对照测的是**信号判别力**，
  不是解码器增益；解码数学自洽（max belief = 理论后验）。
