# PREREG RUN1 —— 首战：dsh-launcher 全仓扫描（2026-10-10）

> 性质：**运行预注册**（应用非实验——无设门判据，只有读数口径与诚实条款）。
> 注册先于任何读数。靶仓：`master666-max/dsh-launcher`（沙箱克隆
> `tools/repos/dsh-launcher`，commit 1885de1，topos **只读扫描**，不碰原工程区）。

## 对象与覆盖

- 靶：11 个 .py（7184 行）：dsh_tests 1879 / dsh_env 1356 / dsh-launcher 1061 /
  dsh-plugins 1021 / dsh_update 513 / dsh-selfcheck 462 / dsh-fallback-heal 342 /
  dsh-mutate 274 / dsh-quick-mutate 144 / dsh-accept 94 / dsh-env 38。
- **覆盖边界（先声明）**：2 个 .bat 不在任何后端覆盖内——本读数只对 .py 子空间负责。
- 坐标系：默认 `axes.json`（拓扑 call/data/control/return/vardep + forman + diffusion +
  anchor 33 tag + churn + age + loc；克隆仓有 .git，churn/age 可算）。

## 观测与读数口径

- **观测源**：anchor 33 tag 正则（确定性信号，batch=正则批）；池观测 y = 池内任一单元
  anchor 非空 → 1，否则 0。
- 解码：NB + 图先验（--adj = 融合图边表，prior-steps=4）；Se/Sp 用 CLI 默认
  0.9/0.95——**假设仪器参数，未标定**。
- 读数四件：space 覆盖三诊断 / belief top-N / next 决策（σ）/ report.md。
- **诚实条款**：一切精度只以「仪器灵敏度」名义出现；读出什么登记什么（三态口径），
  不为好看调整清单；.bat 盲区 + 观测源单一（仅正则批）随读数如实登记。
