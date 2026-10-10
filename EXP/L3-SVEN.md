# L3-SVEN —— SVEN 锚定集接入回执（2026-10-10）

> 预注册：`PREREG/L3.md`（转换判据先于转换读数）｜ 数据源：`eth-sri/sven`
> （He & Vechev, CCS'23，arXiv 2302.05319）｜ 转换器：`EXP/_l3_sven.py`
> **许可审查：LICENSE.txt = MIT（SRI Lab, ETH Zurich, 2024）——审查通过**，版权声明
> 已保留于 gold CSV 的 annotator 列与快照。

## 0. 一页结论

1. **L3 从 ❌ → ✅**：gold 种子 **736 行（368 对：368 漏洞版 + 368 修复版）** 入库
   `calib/gold_l3_sven.csv`（首批金标 CSV，source_layer=L3，成对 unit_id @vul/@fix）。
2. **判据 6/6 咬合**（E-L3-3 首跑 208 解析失败 → 诊断为类方法缩进切片（F1 同病）→
   dedent 兜底修复 → 残余 6 条为数据自身语法损坏，如实登记）。
3. **抽样人工核验 5/5** 与 CWE 语义匹配（SQL 注入 4、路径穿越 1）。
4. **诚实差异**：Python 子集实际落 **4 个 CWE**（089×204 / 078×100 / 079×37 / 022×33）——
   设计口径"9 CWE"是全语言口径，Python 子集天然收窄；SVEN 官方 94% 精度 → ~6% 标签
   噪声随数据带入（参照标准标签）。

## 1. 判据逐条

| 判据 | 读数 | 判定 |
|---|---|---|
| E-L3-1 下载完整性 18/18 | 18 文件全非空（train+val，6.2M） | ✅ |
| E-L3-2 Python 子集筛选 | 803 行 → 380 .py（C/C++ 不收，如实） | ✅ |
| E-L3-3 AST 可解析率 | 首跑 208 失败（类方法缩进切片，F1 同病）→ dedent 兜底 → **残余 6**（数据自身语法损坏：invalid syntax / tabs 混用 / py2 风格，样例留档 stats.json） | ✅（残余如实） |
| E-L3-4 成对入库 | 368 对 736 行；**跨 CWE 重复标注 18 对被 gold append-only 拒绝并计数**（保留首标） | ✅ |
| E-L3-5 抽样人工核 5/5 | SQL 注入 4（format/f-string 拼接用户输入，含 `request.args` 直接可达）、路径穿越 1 | ✅ |
| E-L3-6 快照落盘 | `EXP/l3_sven/functions.jsonl`（736 记录：unit_id/truth/cwe/split/file_name/func_name/commit_link/src） | ✅ |

## 2. 入库明细

- **gold**：`calib/gold_l3_sven.csv`——368 positive（漏洞版）+ 368 negative（修复版，
  "补丁即修复"语义同 L1）；duplicate 18 对被拒（append-only 留首标）。
- **分布**：cwe-089=204、cwe-078=100、cwe-079=37、cwe-022=33；split train=336 / val=38。
- **快照**：`EXP/l3_sven/functions.jsonl`（1.2M 级，可直接喂 L 系管线）。

## 3. 对账状态更新

| 项 | 前 | 后 |
|---|---|---|
| 五层套件 | L3 ❌ | **L3 ✅**（L1✅ L2✅ L3✅ L4⏳ L5✅） |
| 设计-实现对账差异（DESIGN-RECON） | 4 处 | random/T 族/Fisher 已铺平；SVEN 本件收官——**对账清零** |

## 4. 欠账与后续

- L4 人工仲裁 100 单元（~8h 人工）——定标后 RUN1 读数可升级为实测精度（SVEN 种子
  可作为仲裁以外的第三方对照）。
- SVEN 的 C/C++ 子集与 6 条语法损坏记录如实不收。
- 修复版 truth=0 依赖「补丁即修复」假设（同 L1 语义），PU 学习口径下如实使用。
