# L4 负域抽查清单（RUN1 池外零覆盖区，分层随机 n=10）

> 每单元 ~1–2 分钟：读源码，判「有无缺陷」→ 填 0/1/无法判定。
> 裁决后交回，入库 gold_l4_field.csv（source_layer=RUN1-spot）。

## dsh-fallback-heal.py::list_pkgs:60
```python
(源码见 tools/repos/dsh-launcher@1885de1)
```
- 判定：[ ] 良性(0)  [ ] 缺陷(1)  [ ] 无法判定

## dsh-plugins.py::list_pkgs:135
```python
(源码见 tools/repos/dsh-launcher@1885de1)
```
- 判定：[ ] 良性(0)  [ ] 缺陷(1)  [ ] 无法判定

## dsh-quick-mutate.py::main:96
```python
(源码见 tools/repos/dsh-launcher@1885de1)
```
- 判定：[ ] 良性(0)  [ ] 缺陷(1)  [ ] 无法判定

## dsh-selfcheck.py::Collect.visit_ExceptHandler:131
```python
(源码见 tools/repos/dsh-launcher@1885de1)
```
- 判定：[ ] 良性(0)  [ ] 缺陷(1)  [ ] 无法判定

## dsh_env.py::_read_text:99
```python
(源码见 tools/repos/dsh-launcher@1885de1)
```
- 判定：[ ] 良性(0)  [ ] 缺陷(1)  [ ] 无法判定

## dsh_update.py::_parse_count:182
```python
(源码见 tools/repos/dsh-launcher@1885de1)
```
- 判定：[ ] 良性(0)  [ ] 缺陷(1)  [ ] 无法判定

## dsh-fallback-heal.py::log:56
```python
(源码见 tools/repos/dsh-launcher@1885de1)
```
- 判定：[ ] 良性(0)  [ ] 缺陷(1)  [ ] 无法判定

## dsh-plugins.py::set_disabled:390
```python
(源码见 tools/repos/dsh-launcher@1885de1)
```
- 判定：[ ] 良性(0)  [ ] 缺陷(1)  [ ] 无法判定

## dsh-quick-mutate.py::run_case:78
```python
(源码见 tools/repos/dsh-launcher@1885de1)
```
- 判定：[ ] 良性(0)  [ ] 缺陷(1)  [ ] 无法判定

## dsh-selfcheck.py::Collect._add_import:84
```python
(源码见 tools/repos/dsh-launcher@1885de1)
```
- 判定：[ ] 良性(0)  [ ] 缺陷(1)  [ ] 无法判定
