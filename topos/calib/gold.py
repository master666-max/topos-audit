# -*- coding: utf-8 -*-
"""
topos.calib.gold —— 金标管理器（L4 承载件）。
CSV append-only：unit_id,truth,defect_type,evidence,annotator,date,source_layer
契约：重复 (unit_id) 拒绝写入；truth ∈ {0,1,None}（None=未标注，PU 语义——禁止用 0 冒充"确认干净"）。
"""
import csv
import os

FIELDS = ["unit_id", "truth", "defect_type", "evidence", "annotator", "date", "source_layer"]


class GoldStandard:
    def __init__(self, path):
        self.path = path
        self.rows = []
        self._index = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    self.rows.append(row)
                    self._index[row["unit_id"]] = row

    def add(self, unit_id, truth, defect_type="", evidence="", annotator="",
            date="", source_layer=""):
        if unit_id in self._index:
            raise ValueError("金标拒绝重复 unit_id: %s（append-only）" % unit_id)
        if truth not in ("0", "1", "None", None, 0, 1):
            raise ValueError("truth 必须是 0/1/None（None=未标注），收到: %r" % (truth,))
        row = {"unit_id": unit_id, "truth": str(truth), "defect_type": defect_type,
               "evidence": evidence, "annotator": annotator, "date": date,
               "source_layer": source_layer}
        self.rows.append(row)
        self._index[unit_id] = row
        return row

    def save(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(self.rows)
        return self.path

    def stats(self):
        t1 = sum(1 for r in self.rows if r["truth"] == "1")
        t0 = sum(1 for r in self.rows if r["truth"] == "0")
        tn = sum(1 for r in self.rows if r["truth"] not in ("0", "1"))
        return {"n": len(self.rows), "positive": t1, "negative": t0, "unlabeled": tn}

    def truth_of(self, unit_id):
        row = self._index.get(unit_id)
        return None if row is None else row["truth"]
