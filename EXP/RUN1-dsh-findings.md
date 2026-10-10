# RUN1 开池报告 —— p_anchor_breadth（σ=6.11，v1.2 读数）

> σ 停止指路 NEXT → p_anchor_breadth → 本报告 = 开池审查结果。
> 池内 anchor 命中单元 16 个（全部 tag = `import:import_subprocess`），逐个源码级审查。

## 0. 审计结论

**在这 16 个 subprocess 使用点中找到 0 个确认漏洞。** 全部：列表 argv（无 shell=True）、路径来自内部
常量或带守卫的目录扫描。**2 条正面发现**（守卫质量值得表扬），**1 条信任边界注记**。

## 1. 逐单元判定

| # | 单元 | 用法 | 守卫/来源 | 判定 |
|---|---|---|---|---|
| 1 | dsh-accept.py::run_py:22 | `subprocess.run([PYEXE,…,TOOLS/script])` | TOOLS 仓内常量路径 | 良性 |
| 2 | fallback-heal::kill_node:87 | `taskkill /F /PID` | 端口精确判据 + 强刷快照 + **pid_is_node 复核**（注释明言不按镜像名杀，防误杀用户 MCP 工具链）+ PID 复用跳过 | **正面发现** |
| 3 | fallback-heal::heal_profile:118 | cmd.exe /c rmdir + mklink（stdin 批量脚本） | **cmd_arg_safe 元字符闸**（拒绝含 cmd 元字符路径）+ GBK 折叠绕行 + lexists 断链处理 + communicate 超时后 proc.kill()（竞态窗口注释） | **正面发现** |
| 4 | fallback-heal::clean_pnpm_leftovers:226 | cmd.exe /c rmdir 残留目录 | 严格残留正则 `^.+_tmp_\d+_[0-9a-f]+$` + package.json/reparse 双确认 + cmd_arg_safe + 显式 --clean 门 | 良性（守卫到位） |
| 5 | fallback-heal::scan:240 | 同上（扫描递归） | 同上 | 良性 |
| 6 | launcher::kill_leftover:163 | taskkill /F /PID | verified_listening_pids 强刷 + pid_is_node 复核 + 复用跳过 | **正面发现**（同 2） |
| 7 | launcher::run_heal:193 | `[sys.executable, heal]` | heal = TOOLS 常量（dsh-fallback-heal.py） | 良性 |
| 8 | launcher::_spawn_bg_and_wait:467 | **Popen(c["cmdline"] or c["argv"])** | 配置驱动的启动候选执行 | **信任边界注记**（见 §2） |
| 9 | launcher::run_plugins:654 | `[sys.executable, TOOLS/dsh-plugins.py]` | 内部常量 | 良性 |
| 10 | launcher::action_check:746 | `[sys.executable, p, "--check"]` + 600s 超时 | 内部常量 | 良性 |
| 11 | dsh-plugins.py::run_heal:741 | 同 7 | TOOLS 常量 | 良性 |
| 12 | dsh_env.py::_run:66 | 永不抛 subprocess 封装 + PATH 钉扎 + GBK/UTF-8 双解码 | 封装层设计 | 良性（正面） |
| 13 | dsh_env.py::image_names:251 | tasklist 查询 | 参数内部常量 | 良性 |
| 14 | dsh_env.py::pid_alive:288 | tasklist /FI PID | pid 为 int 插值，来自内核枚举 | 良性 |
| 15 | dsh_env.py::port_excluded:862 | netsh 查询 | 参数内部常量 | 良性 |
| 16 | dsh_update.py::run_git:75 | `[git, -C, repo] + args` + CREATE_NO_WINDOW + 永不抛 | args 为内部构造（fetch/status） | 良性 |

## 2. 信任边界注记（唯一非"良性"条目）

`_spawn_bg_and_wait` 执行**配置文件里的 cmdline/argv**——这是启动器的**设计功能**（运行
用户配置的启动候选），不是漏洞。但它是全仓唯一"外部可持久化数据 → 命令执行"的通道：
**配置文件 = 信任边界**。若未来 dsh 配置引入云同步/分享机制，此处升级为必审点。
现状（本地用户目录配置）风险 = 攻击者已有本地 FS 写权限，无增量攻击面。

## 3. 仪器侧回读

- anchor 信号召回的 16 个点**全部值得看一眼**（无一句废话命中），语义判定全部良性——
  说明该仓 subprocess 卫生水平高，仪器召回精度与代码卫生双重达标。
- 审查发现的守卫注释（PID 复用、竞态窗口、GBK 折叠）全是实测踩坑记录——与
  dsh-quick-mutate.py 的变异纪律同源，工程习惯一致。
- σ 下一候选：p_deep_conf（forman:deep，2.74→v1.2 重排后 0.58）——结构异常深点，
  下一开池对象（如继续审计）。
