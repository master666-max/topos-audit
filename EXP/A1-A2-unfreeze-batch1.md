# A1/A2 解冻第一批回执（2026-10-11）

> **触发**：用户裁定「取消冻结，又不是什么生产环境，全面开工」→ `PREREG/UNFREEZE.md`
> **范围**：A1（α 接线）+ A2（多层进场层）+ B-1（顺手修的既有 bug）
> **selftest**：**34 → 37/37 PASS**（新增 c38/c39/c40）

---

## 1. A1 · α 从死旋钮变活旋钮（修既有 bug，非加场）

**根因**：`fuse()` 早已算出 `w(e)=Σα`（`topos/core/fuse.py:14-19`），但旧 `to_adj()` 只 `for (u,v) in fused_edges` 取**键**，权重从不读。
**修法**：`to_adj(fused, min_weight=None)` 按权重阈值取边。`min_weight=None`（缺省）⇒ 与旧行为**逐字相同**，默认不破基线。

**为什么不改成"带权 Forman"**：带权 Forman-Ricci 的正确形式需引文献推导，本项目**不自造公式硬编码**。
按权重阈值取边是"加权图 → 无权图"的标准做法，且 α 语义直接可达（α_t=0 ⇒ 该层整层消失）。
带权 Forman 登记为 **[U] 待办**（`DECISIONS-PENDING.md` / DEFERRED-REGISTRY 岗位三延伸）。

### 实测（`EXP/_a1_a2_evidence.py`，dsh 169 单元）

| α 配置 | 解冻前 边数 / 曲率和 | 解冻后 min_weight=2.0 边数 / 曲率和 |
|---|---|---|
| 全 1.0 | 445 / −2310 | **203 / −783** |
| 全 0.0 | 445 / −2310 | **0 / 0** |
| call=1 其余=100 | 445 / −2310 | **345 / −1628** |

> 解冻前三档**逐字相同**（死旋钮实锤，与 `EXP/_b6_s1_alpha_inert.py` 一致）；
> 解冻后三档**全部不同** ⇒ **α 已活**。`min_weight=None` 时仍为 445 / −2310 ⇒ 基线未破。

---

## 2. A2 · 多层进场层（岗位三解冻后的第一刀）

新增 `topos/axis/methods/layer_fields.py`，注册方法 `"layer"`，`formula`：`deg:<层名>` / `span` / `gap`。
`Space` 的 `ctx` 新增 `"layers"` —— 此前 `self.layers` **只有 `summary()` 的一个标量读它，零个场读它**。

| 场 | 定义 | 用途 |
|---|---|---|
| `layer_span` | 该单元参与了几类层（0–5） | 跨层角色宽度 |
| `layer_gap` | `(deg_data + deg_vardep) − deg_call` | **正 gap = call 层是叶子、data/vardep 层是枢纽** ⇒ 跨层失配的可观测形态 |

### 实测分布（dsh 169 单元）

```
layer_span: {0:14, 1:16, 2:60, 3:48, 4:27, 5:4}
layer_gap : =0:36  <0:71  >0:62   （最大 5 个值: 11, 11, 10, 10, 10）
```

**62 个单元（36.7%）gap > 0** —— 它们在 call 图上几乎是叶子，却通过共享状态与一堆单元耦合。
这正是 clone 型缺陷（复制粘贴体互不调用）唯一可能在图上显形的地方。

### 准入硬门（R6：ρ ≥ 0.3 不许准入）

| 候选池 | Δcov | max ρ（对 forman_deep） | Δlogdet | 判定 |
|---|---|---|---|---|
| `layer_span_hi` | 0.473 | **+0.297** | 6.941 | ⚠️ **擦线通过** |
| `layer_gap_hi` | 0.509 | +0.243 | 6.991 | ✅ 通过 |

⚠️ **必须披露的两点**：
1. `layer_span` 的 ρ=0.297 距硬门 0.3 只差 **0.003**，属于擦线，不是安全通过；换靶可能就翻。
2. 按 DEFERRED-REGISTRY §3 第 2 条，**分层场与 `forman` 同源于图 ⇒ 结构正交不通过**。
   单看 ρ 不够，**必须与 git 族（非图工件类型）组组合池再评**，否则就是 R6 假共识。
   ⇒ 这两场当前**只登记、不单独当轴用**，待组合池读数。

---

## 3. B-1 · 顺手修的既有 bug：扫子目录时 T 族三场全灭

**现象**（本次扫 `topos/` 时发现）：`authors` / `fix_coupling` / `stability` 的 nonnull = **0.000**。
**根因**：`git -C <子目录> log --name-only` 打印的是**仓库根相对**路径（`topos/cli.py`），
而单元 `file` 是**扫描根相对**路径（`cli.py`）⇒ `touched` 恒为空。
注意 `churn`/`age` 不受影响（它们走 `git log --follow -- <rel>`，用的是扫描根相对路径）。
**修法**：`_git_prefix()` 取 `git rev-parse --show-prefix`，从 commit 文件路径剥掉该前缀。

| 场 | 修复前 nonnull | 修复后 nonnull |
|---|---|---|
| authors | 0.000 | **0.991** |
| fix_coupling | 0.000 | **0.991** |
| stability | 0.000 | **0.991** |

> 这条也意味着：**历史上任何"扫子目录"的读数，T 族三场都是死的**。
> 扫仓库根的读数（如 RUN1 的 dsh 全仓扫描）不受影响。

---

## 4. 变更清单

| 文件 | 改动 |
|---|---|
| `topos/core/layers.py` | `to_adj(fused, min_weight=None)`（A1） |
| `topos/space.py` | 读 `manifest["fuse"]["min_weight"]`；`ctx` 增 `"layers"`（A1/A2） |
| `topos/axis/methods/layer_fields.py` | **新增**（A2，`layer` 方法：deg/span/gap） |
| `topos/axis/__init__.py` | 注册 layer_fields |
| `topos/axis/methods/git_history.py` | `_git_prefix` + 路径归一化（B-1） |
| `topos/selftest.py` | +c38 / +c39 / +c40 ⇒ **37/37** |
| `axes.json` | +`layer_span` +`layer_gap`；+`"fuse": {"min_weight": null}`（默认不动） |
| `PREREG/UNFREEZE.md` | **新增**：裁定记录 + T-B6-b..f 不变 |
| `PREREG/B6.md` | v1.0 → **v1.1**（T-B6-a 取消横幅） |
| `PREREG/DEFERRED-REGISTRY.md` | 解冻横幅 + 4 处订正（0.969→0.9764 / E-X1 二分 / 号位锚定 / 行号） |
| `PREREG/B6-DEFERRED-*.md`、`B7-DEFERRED-*.md` | 落库（原在 `D:/tmp/ta-read`） |
| `EXP/_a1_a2_evidence.py` | 本批证据脚本 |
