"""Reconcile recorded full-schedule results and create scientific progress figures.

This audit does not resample. It verifies source requests/certificates, circuit
and DEM hashes, batch counts, intervals, unique-sample accounting and complete
observable rank before reporting any contrasts.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import stim

from memory_calibration_previous import wilson_interval
from route_adapter import canonical_json
from schedule_adapter import certify
from schedule_circuit import _rank
from run_schedule_pilot import PROTOCOL

ROOT = Path(__file__).resolve().parent
LABELS = {"parallel": "Parallel", "serial": "Serial", "serial_reordered": "Serial (reordered)",
          "author_profile": "Author + profile", "one_step": "One-step", "two_step": "Two-step"}


def audit(folder):
    summary = json.loads((folder / "summary.json").read_text())
    if summary["protocol"] != PROTOCOL:
        raise AssertionError("Protocol differs from the reported source")
    samples = {row["sample_id"]: row for row in summary["samples"]}
    if len(samples) != summary["unique_sampled_full_circuits"]:
        raise AssertionError("Duplicate sample IDs")
    if sum(row["shots"] for row in samples.values()) != summary["new_monte_carlo_shots"]:
        raise AssertionError("Unique-shot count differs")
    for sample_id, row in samples.items():
        for field, expected in (("model_id", PROTOCOL["model_id"]), ("decoder_id", PROTOCOL["decoder_id"]),
                                ("distance", 3), ("physical_p", .001),
                                ("shots", PROTOCOL["shots_per_unique_circuit"]), ("batch_size", PROTOCOL["batch_size"])):
            if row[field] != expected:
                raise AssertionError("Sample condition differs: " + field)
        for suffix, field in (("_ideal.stim", "ideal_circuit_sha256"), (".stim", "noisy_circuit_sha256"), (".dem", "dem_sha256")):
            path = folder / "samples" / (sample_id + suffix)
            artifact = stim.DetectorErrorModel.from_file(path) if suffix == ".dem" else stim.Circuit.from_file(path)
            # Experiment IDs hash str(Stim object); to_file adds a final newline.
            # Byte-for-byte file integrity is separately covered by the snapshot.
            if hashlib.sha256(str(artifact).encode()).hexdigest() != row[field]:
                raise AssertionError("Canonical circuit/DEM hash differs")
        if sum(b["shots"] for b in row["batches"]) != row["shots"] or sum(b["failures_any"] for b in row["batches"]) != row["failures_any"]:
            raise AssertionError("Batch count mismatch")
        per = np.array([b["failures_by_observable"] for b in row["batches"]]).sum(axis=0).tolist()
        if per != row["failures_by_observable"] or any(v > row["failures_any"] for v in per):
            raise AssertionError("Per-observable count mismatch")
        if (row["wilson95_low"], row["wilson95_high"]) != wilson_interval(row["failures_any"], row["shots"]):
            raise AssertionError("Confidence interval differs")
        if row["p_fail_any"] != row["failures_any"] / row["shots"]:
            raise AssertionError("Failure probability differs")
        noisy = stim.Circuit.from_file(folder / "samples" / (sample_id + ".stim"))
        for field in ("num_qubits", "num_ticks", "num_observables", "num_detectors"):
            if row[field] != getattr(noisy, field):
                raise AssertionError("Circuit metrics differ")
        if row["shortest_graphlike_error"] != 3:
            raise AssertionError("Distance check did not pass")
    fixture = json.loads((folder / "fixture_selection.json").read_text())
    programs = {row["case_id"]: row for row in [fixture["control"], *fixture["fixtures"].values()]}
    seen = set()
    for row in summary["records"]:
        record_id = row["record_id"]
        if record_id in seen:
            raise AssertionError("Duplicate request record")
        seen.add(record_id)
        request = json.loads((folder / "requests" / (record_id + ".json")).read_text())
        certificate = json.loads((folder / "certificates" / (record_id + ".json")).read_text())
        recomputed = certify(request)
        for key, value in recomputed.items():
            if canonical_json(value) != canonical_json(certificate[key]):
                raise AssertionError("Certificate differs: " + key)
        if request["gates"] != programs[row["case_id"]]["gates"]:
            raise AssertionError("The full predeclared program changed")
        sample = samples[row["sample_id"]]
        if certificate["ideal_circuit_sha256"] != sample["ideal_circuit_sha256"]:
            raise AssertionError("Full-circuit reuse mismatch")
        if row["request_sha256"] != certificate["request_sha256"]:
            raise AssertionError("Request hash mismatch")
        if (sample["basis"], sample["num_observables"], certificate["num_ticks"], certificate["num_qubits"]) != (row["basis"], row["logical_qubits"], sample["num_ticks"], sample["num_qubits"]):
            raise AssertionError("Reference conditions differ")
        n = row["logical_qubits"]
        flows = certificate["backend_meta"]["external_flows"]
        for part in (slice(0, n), slice(n, 2*n)):
            if _rank([[p != "I" for p in f[part]] for f in flows], n) != n:
                raise AssertionError("Observable rank is incomplete")
        validation = certificate["physical_validation"]
        if not validation["all_signed_inputs_passed"] or len(validation["signed_inputs"]) != 2 ** n or len(validation["final_logical_faults"]) != n:
            raise AssertionError("Physical logical-action checks incomplete")
        if not certificate["all_live_memory_verified"] or not certificate["block_footprint_matches_backend"]:
            raise AssertionError("Physical reservation checks incomplete")
    for name, sha in summary["environment"]["source_files_sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != sha:
            raise AssertionError("Experiment source changed: " + name)
    result = {"passed": True, "physical_requests": len(summary["records"]),
              "unique_sampled_full_circuits": len(samples), "new_monte_carlo_shots": summary["new_monte_carlo_shots"],
              "checks": ["source requests and certificates", "complete selected programs", "canonical ideal/noisy/DEM hashes",
                         "basis/distance/noise/decoder/shot/batch conditions",
                         "unique shot accounting", "batch counts and intervals", "complete input/output observable rank",
                         "stored signed-input/fault/distance validation", "stored complete memory and physical footprint", "experiment source hashes"],
              "scope": "Record reconciliation without resampling or rerunning the physical compiler."}
    (folder / "record_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    return summary, samples, result


def contrast(first, second):
    """Second minus first, Newcombe independent-proportions score interval."""
    if first["sample_id"] == second["sample_id"]:
        return {"difference": 0.0, "ci95": [0.0, 0.0], "method": "identical circuit and reused sample: difference identically zero"}
    p1, p2 = first["p_fail_any"], second["p_fail_any"]
    delta = p2 - p1
    low = delta - math.sqrt((p2 - second["wilson95_low"]) ** 2 + (first["wilson95_high"] - p1) ** 2)
    high = delta + math.sqrt((second["wilson95_high"] - p2) ** 2 + (p1 - first["wilson95_low"]) ** 2)
    return {"difference": delta, "ci95": [max(-1., low), min(1., high)],
            "method": "Newcombe hybrid score interval for independent binomial samples; pointwise, exploratory, no familywise adjustment"}


def make_figure(summary, samples):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(3, 2, figsize=(9.5, 8.1))
    cases = [("parallel_control", "Four-qubit structural control"),
             ("two_shorter", "Six-qubit development case: two-step shorter"),
             ("two_longer", "Six-qubit development case: two-step longer")]
    for row_index, (case_id, title) in enumerate(cases):
        for column, basis in enumerate(("x", "z")):
            ax = axes[row_index, column]
            records = [r for r in summary["records"] if r["case_id"] == case_id and r["basis"] == basis]
            data = [samples[r["sample_id"]] for r in records]
            values = np.array([s["p_fail_any"] for s in data]) * 100
            low = values - np.array([s["wilson95_low"] for s in data]) * 100
            high = np.array([s["wilson95_high"] for s in data]) * 100 - values
            ax.bar(range(len(data)), values, color=["#79838c", "#337cad", "#e49743"], width=.6,
                   yerr=np.array([low, high]), capsize=3, error_kw={"elinewidth": 1})
            ax.set_xticks(range(len(data)), [LABELS[r["method"]] + "\n" + str(r["source_steps"]) + " steps" for r in records], fontsize=7)
            ax.set_title(title + ", " + basis.upper() + " basis", fontsize=9)
            ax.set_ylabel("Decoded any-observable failure (%)")
            ax.set_ylim(0, max(values + high) * 1.2)
            ax.grid(axis="y", alpha=.2)
            ax.set_axisbelow(True)
            for x, value in enumerate(values):
                ax.text(x, value + high[x] + max(values) * .025, f"{value:.2f}%", ha="center", fontsize=8)
    fig.suptitle("Complete physical circuits: same logical task and fixed resource profile", fontsize=12, fontweight="bold")
    fig.text(.5, .025, "d=3, p=0.001, pinned TQEC uniform-depolarizing circuit noise, ordinary MWPM.\n100,000 shots per unique circuit; 95% Wilson intervals. Selected development cases, not held-out performance.", ha="center", fontsize=8)
    fig.tight_layout(rect=[0, .07, 1, .96], h_pad=2)
    target = ROOT / "docs/figures/full_schedule_pilot.png"
    fig.savefig(target, dpi=180)
    fig.savefig(target.with_suffix(".pdf"))
    plt.close(fig)


def report(folder):
    summary, samples, checked = audit(folder)
    make_figure(summary, samples)
    contrasts = []
    lookup = {(r["case_id"], r["basis"], r["method"]): r for r in summary["records"]}
    for case_id in ("parallel_control", "two_shorter", "two_longer"):
        pairs = [("parallel", "serial"), ("parallel", "serial_reordered"), ("serial", "serial_reordered")] if case_id == "parallel_control" else [("one_step", "two_step"), ("author_profile", "two_step")]
        for basis in ("x", "z"):
            for first, second in pairs:
                a = lookup[case_id, basis, first]
                b = lookup[case_id, basis, second]
                contrasts.append({"case_id": case_id, "basis": basis, "first": first, "second": second,
                                  **contrast(samples[a["sample_id"]], samples[b["sample_id"]])})
    (folder / "contrasts.json").write_text(json.dumps(contrasts, indent=2) + "\n")
    table = []
    chinese = {"parallel_control": "四位元控制", "two_shorter": "開發：two 較短", "two_longer": "開發：two 較長"}
    for r in summary["records"]:
        s = samples[r["sample_id"]]
        table.append(f"| {chinese[r['case_id']]} | {r['basis'].upper()} | {LABELS[r['method']]} | {r['source_steps']} | {s['num_ticks']} | {s['num_qubits']} | {s['failures_any']}/{s['shots']} | {100*s['p_fail_any']:.3f}% [{100*s['wilson95_low']:.3f}, {100*s['wilson95_high']:.3f}] |")
    delta_table = []
    for c in contrasts:
        lo, hi = c["ci95"]
        delta_table.append(f"| {chinese[c['case_id']]} | {c['basis'].upper()} | {LABELS[c['second']]} − {LABELS[c['first']]} | {100*c['difference']:+.3f} | [{100*lo:+.3f}, {100*hi:+.3f}] |")
    timing = json.loads((folder / "routing_timing.json").read_text())
    timing_table = [f"| {chinese[r['case_id']]} | {LABELS[r['method']]} | {1000*r['median_seconds']:.3f} | 25 |" for r in timing["records"]]
    public = json.loads((ROOT / "results/public_audit_2026-11-02_v2/summary.json").read_text())
    public_table = [f"| {r['name']} | {r['logical_qubits']} | {r['operation_counts'].get('cx',0)} | {len(r['incomparable_cx_pairs'])} | {'是' if r['all_unitaries_clifford'] else '含非 Clifford／動態條件'} |" for r in public["records"]]
    text = f"""# 2026-11-02：不同合法排程接通完整物理電路，保留正反案例

## 新增能力與本次範圍

現在可以把**同一批 CNOT 的不同合法順序／並行排程**，編成含完整等待保護的物理電路，再一起抽樣與解碼。先前兩個相依 CNOT 模板沒有排程選擇；這次擴充為固定 diagonal profile、2–6 個存活邏輯位元、forward CNOT、L 形橋接及並行 layer。以下實驗固定 x spacing=1、d=3、X/Z basis、p=0.001。

本次有 **{summary['source_configurations']} 份來源排程、{summary['physical_requests']} 份物理請求、{summary['unique_sampled_full_circuits']} 個不同的完整電路，共新增 {summary['new_monte_carlo_shots']:,} noisy shots**。完全相同的 ideal/noisy hash 才重用完整電路 counts；不是每份請求都另算 100,000 shots。每個不同電路另做全部 2^n 輸入符號、n 種 final logical fault、輸入／輸出 observable rank 與 graphlike distance=3 檢查。

兩組六位元案例是**開發 fixture**，由固定 seed=204 的搜尋，在第 4 與第 34 個候選找到第一個 two-step 較長／較短的例子；一共檢視 35 個候選，在任何 noisy sampling 前固定。兩個方向都保留。這批驗證閉環與邊界，不能用其勝率宣稱 held-out 演算法表現。公開 benchmark 的完整整合仍保留為必要後續工作。

![完整電路的解碼錯誤率與信賴區間](../figures/full_schedule_pilot.png)

## 完整結果

指標是完整、獨立的 n 個 basis-specific correlation observables 任一解碼錯誤；不是 state/process fidelity。Noise 為固定 TQEC uniform-depolarizing circuit model，decoder 為普通 uncorrelated PyMatching MWPM；不做 postselection。不同任務與不同 basis 的率不直接相減比較。

| 任務 | Basis | 排程 | Steps | TICKs | Qubits | 錯誤／shots | 錯誤率與 95% Wilson CI |
|---|---|---|---:|---:|---:|---:|---|
{chr(10).join(table)}

`Author + profile` 使用固定版本作者的搜尋政策，替換成與我們相同的保守資源保留 primitive；**不是未修改的 DASCOT 原方法**。One-step 與 two-step 皆最多每步 48 個 front evaluations、同 cap=16；小 front 可能先耗盡所有 permutations，預算不一定用滿。實際候選與成本逐步保存在 source_routes。

## 差值與可作出的結論

下表單位為**百分點**，第二種方法減第一種。不同電路採獨立 binomial 樣本的 [Newcombe (1998) score interval](https://pubmed.ncbi.nlm.nih.gov/9595617/)；相同完整電路重用樣本時，差值在這份比較中恆為 0。區間為探索性、逐項 95%，沒有對全部比較作 familywise 校正。

| 任務 | Basis | 比較方向 | 差值（百分點） | 差值 95% CI |
|---|---|---|---:|---|
{chr(10).join(delta_table)}

四位元控制的完整工作是 CNOT(0,1)、CNOT(2,3)、CNOT(1,2)：前兩個可以平行，也可合法換序。它提供排程／等待差異的機制比較，串行版本是顯式控制組，不是宣稱 one-step 只能串行。六位元正反例則直接使用我們的 scheduler 輸出，展示多看一步仍有邊界；作者政策亦可能達到相同排程。單一開發例子的改善不等於普遍優於作者方法。

## 時間、資源與等待

每個 source step 在本 profile 佔 3 個 block-z。TICKs 來自實際 compiler，沒有使用 1 step=1 TICK 的假設。所有資料 patch 從 z=0 同時存在到共同輸出；每一段 temporal pipe 都檢查存在。每個 CNOT 的完整 data/ancilla footprint 在整個 layer 保守保留，不能只看一條細路徑。

同一 case 的 layout、全部 gates、輸入／輸出條件、可用晶片資源與 noise／decoder 固定，允許用不同平行度使用這些資源。`data_reservation_block_z`、ancilla 保留量、逐 qubit active/memory layers、逐 gate 時間與實際 qubits 均保存。等深度且全部狀態同壽命時，總 memory volume 可能相同，不能預設任何等待特徵都能區分風險。

## 搜尋成本

先完成獨立 routing-only 計時，再開始編譯與 Monte Carlo。每項 3 次 warmup、25 次重複；下表為中位數。這是小型受限 profile 的計時，不能當成 Phase 1 較大電路的成本比值；主機可能共享。

| 任務 | 方法 | 中位 routing ms | 重複 |
|---|---|---:|---:|
{chr(10).join(timing_table)}

## 驗證發現：observable 數量正確，rank 仍可能不完整

固定版本的上游 finder 會將互不連通區塊的 correlation generators 作跨區塊組合。對兩個獨立 CNOT，直接取得四個跨區塊乘積時，輸入 rank 可能只有 3；僅檢查「有四個 observables」或每一個單獨 final fault，仍不足以保證完整基底。

本次在 adapter 中逐 connected component 取得 generators，再把聯集交給原 physical compiler；輸入及輸出 rank 都必須等於 n。這不改動上游程式，也不把問題擴大宣稱為所有 TQEC 情況的缺陷。回歸測試涵蓋獨立並行區塊、從未參與 gate 的 spectator、較長的 y arm、共同生命週期，以及不合法順序／重疊 footprint／不支援欄位的拒絕。

## 公開 benchmark 與內容完整性

已保存七份完整 QASMBench 原始碼、license/notice、固定 commit、Git blob SHA 與 SHA-256，並展開自訂 gate、保留量測與 classical dependencies 建立 DAG。下表的可換序配對是 DAG 中互不可達的 CX 對；它不同於某一組 ASAP fronts 裡同時 ready 的 CX 數。

| 公開電路 | 邏輯位元 | CX 數 | 互不可達的 CX 配對 | 靜態 Clifford |
|---|---:|---:|---:|---|
{chr(10).join(public_table)}

優先整合目標為完整 `hs4_n4`：4 CX、20 H、4 X、4 次量測，含可獨立排程的 CX。現有純 CNOT backend 尚未處理其全部單位元閘，因此完整 physical support 為 **0/7**；沒有刪掉 H/X 來製造支援。`error_correctiond3_n5` 亦有被不同 ASAP 時刻掩蓋的合法換序機會，保留為後續候選。

使用者要求「天數壓縮，內容不壓縮」：完整公開 workload、公平比較與計時、trade-off、風險方法的校準／held-out／ablation／文獻比較，以及全部報告材料均繼續推進。這次完成其中的並行／排程閉環與 benchmark DAG 增量，不代表整份 roadmap 已完成。Scheduler **μ 仍為 0**；尚未宣稱 risk-aware 策略改善或方法首創。

## 紀錄與重現

本次 reconciliation 通過：{checked['physical_requests']} 份請求、{checked['unique_sampled_full_circuits']} 個完整電路、circuits/DEMs、batch counts、CI、來源 hash、certificate、observable rank 及唯一 shot 計數。電路 ID 使用 Stim 物件的 canonical 字串 hash；原始檔案的逐 byte hash 另由快照 manifest 保護。這份 audit 不新增抽樣。

```bash
python -m pytest tests -q
python restore_results.py
python report_schedule_pilot.py
python run_public_audit.py --output results_fresh/public_audit
python select_schedule_fixtures.py --output results_fresh/fixtures.json
python run_schedule_pilot.py --output results_fresh/schedule_pilot
```

Runners 拒絕覆寫既有目錄；完整新取樣使用最後一行。公開來源在 `benchmarks/public_2026-11-02/`，選樣規則／35 個試次在 `benchmarks/schedule_pilot_2026-11-02.json`；新資料在 `results/schedule_pilot_2026-11-02/`，完整相容性檢查在 `results/public_audit_2026-11-02_v2/`。快照另保留完整 raw circuits、DEMs 與紀錄；CI 狀態以本次 GitHub Actions 為準。

TQEC 提供原 CNOT 設計、correlation-surface machinery、graph composition 與 physical compiler；Stim/PyMatching 提供抽樣與解碼。新增工作是 L 形空間延伸、完整資源保留 primitive、來源排程與時間合約、component observable 基底處理、驗證、公開來源稽核及完整電路量測。QASMBench 原始電路屬其作者。
"""
    (ROOT / "docs/updates/2026-11-02.md").write_text(text)
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results/schedule_pilot_2026-11-02")
    args = parser.parse_args()
    print(json.dumps(report(args.results)))


if __name__ == "__main__":
    main()
