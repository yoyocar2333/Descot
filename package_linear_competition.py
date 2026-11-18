"""Freeze the new linear-family raw circuits and common hardware footprint."""
import hashlib
import json
from pathlib import Path
import zipfile

import stim

from public_candidate_pool import canonical
from run_linear_competition import ROOT, DEFAULT, ARCHIVE, check


def main():
    if ARCHIVE.exists():
        raise FileExistsError("Frozen archive already exists")
    rows = json.loads((DEFAULT / "physical_index.json").read_text())
    sites = {}
    ticks = {}
    for row in rows:
        ideal = stim.Circuit((DEFAULT / "circuits" / (row["ideal_sha256"] + ".stim")).read_text())
        coords = sorted({tuple(p) for p in ideal.get_final_qubit_coordinates().values()})
        if len(coords) != ideal.num_qubits:
            raise AssertionError("Missing or duplicate physical coordinates")
        sites[row["candidate_id"]] = coords
        ticks[row["candidate_id"]] = ideal.num_ticks
    catalogue = sorted({p for coords in sites.values() for p in coords})
    report = dict(hardware_policy="Common complete static physical-site catalogue, including all data/CX ancillas; no concurrency cap or candidate exclusion",
                  physical_site_catalogue=catalogue,
                  available_physical_sites=len(catalogue),
                  physical_site_catalogue_sha256=hashlib.sha256(canonical(catalogue).encode()).hexdigest(),
                  candidate_rows=[dict(candidate_id=r["candidate_id"], allocated_physical_sites=len(sites[r["candidate_id"]]),
                                       footprint_sha256=hashlib.sha256(canonical(sites[r["candidate_id"]]).encode()).hexdigest(),
                                       uses_exact_common_catalogue=sites[r["candidate_id"]] == catalogue,
                                       stim_ticks=ticks[r["candidate_id"]],
                                       static_hardware_reservation_site_ticks=len(catalogue)*ticks[r["candidate_id"]]) for r in rows],
                  unit_policy="Static site*TICK reservation is not active-noise exposure or QEC rounds; abstract block-z waits are separate",
                  builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), new_shots=0)
    (DEFAULT / "resource_certificate.json").write_text(json.dumps(report, indent=2) + "\n")
    files = sorted((DEFAULT / "circuits").iterdir())
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            info = zipfile.ZipInfo(str(p.relative_to(ROOT)), date_time=(2026, 11, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    path = ROOT / "archives/manifest.json"
    manifest = json.loads(path.read_text())
    if ARCHIVE.name in manifest:
        raise ValueError("Existing archive entry must not change")
    manifest[ARCHIVE.name] = dict(sha256=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
                                 bytes=ARCHIVE.stat().st_size,
                                 result_prefix=str(DEFAULT.relative_to(ROOT)),
                                 description="Full public Qiskit X/CX generated benchmark, all minimum candidates and generator ideal/noisy/DEM artifacts; zero shots")
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    check()
    print(f"PASS: {len(files)} raw artifacts; common physical sites={len(catalogue)}; {len(rows)} full minimum plans")


if __name__ == "__main__":
    main()
