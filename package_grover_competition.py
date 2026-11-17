"""Package new Grover records and certify a common complete physical footprint.

Creates only the new archive/manifest entry; never replaces old snapshots.
Raw circuit text is compressed without lossy transformations.
"""
import hashlib
import json
from pathlib import Path
import zipfile

import stim

from public_candidate_pool import canonical
from run_grover_competition import DEFAULT, ARCHIVE, ROOT, check


def main():
    summary = json.loads((DEFAULT / "summary.json").read_text())
    if ARCHIVE.exists():
        raise FileExistsError("Frozen archive already exists")
    rows = json.loads((DEFAULT / "physical_index.json").read_text())
    footprints = {}
    circuits = {}
    for row in rows:
        ideal = stim.Circuit((DEFAULT / "circuits" / (row["ideal_sha256"] + ".stim")).read_text())
        sites = sorted({tuple(p) for p in ideal.get_final_qubit_coordinates().values()})
        if len(sites) != ideal.num_qubits:
            raise AssertionError("Missing/duplicate physical coordinate mapping")
        footprints[row["candidate_id"]] = sites
        circuits[row["candidate_id"]] = ideal
    catalogue = sorted({p for sites in footprints.values() for p in sites})
    catalogue_sha = hashlib.sha256(canonical(catalogue).encode()).hexdigest()
    report = dict(hardware_policy="Common static physical-site catalogue containing every compiled minimum candidate, including H realignment and CX ancillas. No concurrency cap or candidate removal.",
                  physical_site_catalogue=catalogue,
                  physical_site_catalogue_sha256=catalogue_sha,
                  available_physical_sites=len(catalogue),
                  candidate_rows=[dict(candidate_id=r["candidate_id"],
                                       allocated_physical_sites=len(footprints[r["candidate_id"]]),
                                       footprint_sha256=hashlib.sha256(canonical(footprints[r["candidate_id"]]).encode()).hexdigest(),
                                       uses_exact_common_catalogue=footprints[r["candidate_id"]] == catalogue,
                                       stim_ticks=circuits[r["candidate_id"]].num_ticks,
                                       static_hardware_reservation_site_ticks=len(catalogue)*circuits[r["candidate_id"]].num_ticks)
                                  for r in rows],
                  unit_policy="Site*TICK is static hardware reservation, not active-noise exposure, QEC rounds or seconds. Abstract block reservations/protected idle remain separate columns in physical_index.json.",
                  source_builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  new_shots=0)
    (DEFAULT / "resource_certificate.json").write_text(json.dumps(report, indent=2) + "\n")
    files = sorted((DEFAULT / "circuits").iterdir())
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo(str(path.relative_to(ROOT)), date_time=(2026, 11, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    manifest_path = ROOT / "archives/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if ARCHIVE.name in manifest:
        raise ValueError("Archive manifest entry already exists")
    manifest[ARCHIVE.name] = dict(sha256=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
                                 bytes=ARCHIVE.stat().st_size,
                                 result_prefix=str(DEFAULT.relative_to(ROOT)),
                                 description="Complete public Grover candidate and generator ideal/noisy/DEM text; 0 Monte Carlo shots.")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    check()
    print(f"PASS: {len(files)} raw artifacts archived; common hardware has {len(catalogue)} physical sites; {len(rows)} minimum plans")


if __name__ == "__main__":
    main()
