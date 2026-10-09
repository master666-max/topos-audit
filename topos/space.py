# -*- coding: utf-8 -*-
"""
topos.space —— 总装：目录 + 清单 v3 → 三层空间（底空间/场/池-设计矩阵）。
替代 mini-lab/space_mini 的 Space（其 _build_axes_and_pools 轴池焊死段整体废弃，
由 axis 四层 field→slicer→pool→design 替代——W1 核心修正）。
"""
import os
import time

from topos.core import units as units_mod
from topos.core.layers import _extract_layers, LAYER_TYPES, to_adj
from topos.core.fuse import fuse
from topos.core.embed import forman_curvature, diffusion_embedding
from topos.axis.registry import FIELD_METHODS
from topos.axis.registry import is_missing
from topos.axis.manifest import load_manifest
from topos.pool.pool import eval_pools
from topos.pool.design import build_design, coverage


class Space:
    """一次建空间的完整快照。契约：units 编号在本次空间内稳定。"""

    def __init__(self, root, manifest_path=None):
        t0 = time.time()
        self.root = os.path.abspath(root)
        if manifest_path is None:
            manifest_path = os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "axes.json")
        self.manifest_path = os.path.abspath(manifest_path)
        self.manifest = load_manifest(self.manifest_path)
        manifest_dir = os.path.dirname(self.manifest_path)

        # ① 底空间
        self.units = units_mod.discover_units(self.root)
        self.n = len(self.units)
        self.layers = _extract_layers(self.root, self.units)
        self.alpha = self.manifest.get("layers", {})
        self.fused = fuse(self.layers, self.alpha)
        self.adj = to_adj(self.fused)

        # ② 图上懒构建（forman + diffusion 共享一次谱分解）
        self._graph_cache = {}
        self.embed_dims = 0
        self.lam_residual = None

        # ③ 场（引擎只认 method，不认场名）
        self.fields = {}
        ctx = {"root": self.root, "manifest_dir": manifest_dir,
               "graph": self._graph_builder}
        for spec in self.manifest.get("fields", []):
            fn = FIELD_METHODS[spec["method"]]
            self.fields[spec["name"]] = fn(self.units, spec.get("params", {}), ctx)

        # ④ 切片 → 池 → 设计矩阵（含 constraints）
        pool_pairs, self.slices = eval_pools(
            self.manifest.get("pools", []),
            self.manifest.get("slicers", []),
            self.fields, self.n)
        self.rows, self.design_warnings = build_design(
            pool_pairs, self.n, self.manifest.get("constraints"))
        self.coverage = coverage(self.rows, self.n)
        self.elapsed = round(time.time() - t0, 2)

    # -- 图上量懒构建（forman 与 diffusion 一次算完） --
    def _graph_builder(self):
        if "g" not in self._graph_cache:
            curv, _ec = forman_curvature(self.adj, self.n)
            coords, k_used, lam1 = diffusion_embedding(self.adj, self.n, k=3)
            self.embed_dims, self.lam_residual = k_used, lam1
            self._graph_cache["g"] = {"adj": self.adj, "curv": curv,
                                      "coords": coords, "k_used": k_used,
                                      "lam_residual": lam1}
        return self._graph_cache["g"]

    # -- 诊断 --
    def fields_nonnull(self):
        from topos.axis.registry import is_missing as _miss
        return {name: round(sum(1 for v in f.values() if not _miss(v))
                            / max(self.n, 1), 3)
                for name, f in self.fields.items()}

    def summary(self):
        layer_counts = {t: len(self.layers.get(t, ())) for t in LAYER_TYPES}
        call_set = self.layers.get("call", set())
        outside = sum(1 for e in self.fused if e not in call_set)
        g = self._graph_cache.get("g", {})
        return {
            "n_units": self.n,
            "layer_edges": layer_counts,
            "fused_edges": len(self.fused),
            "edges_outside_call": outside,
            "embed_dims": g.get("k_used", self.embed_dims),
            "lam_residual": g.get("lam_residual", self.lam_residual),
            "coverage": self.coverage,
            "fields_nonnull": self.fields_nonnull(),
            "design_warnings": self.design_warnings,
            "elapsed_s": self.elapsed,
        }

    def pool_overview(self):
        return [{"name": nm, "width": len(m)} for nm, m in self.rows]
