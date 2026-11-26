"""Hash-addressed raw-circuit snapshot. Full replay uses the repository checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from run_grover_depth_frontier import ARCHIVE, DEFAULT, ROOT


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pack(result, archive):
    if archive.exists() or (result / 'snapshot_manifest.json').exists():
        raise FileExistsError('Do not overwrite a frozen snapshot')
    summary = json.loads((result / 'summary.json').read_text())
    if summary['new_physical_compilations'] != 260 or not (result / 'analysis.json').exists():
        raise ValueError('Complete analyzed frontier required')
    env = json.loads((result / 'environment.json').read_text())
    assets = {}
    for p in (result / 'circuits').iterdir():
        if p.suffix not in ('.stim', '.dem') or sha(p.read_bytes()) != p.stem:
            raise ValueError('Non hash-addressed circuit artifact')
        assets['circuits/' + p.name] = p
    for p in result.rglob('*.json'):
        if p.name not in ('verification.json', 'snapshot_manifest.json'):
            assets['records/' + p.relative_to(result).as_posix()] = p
    # Include the compiler/adapters/tests, pinned inputs and licenses; old frozen
    # raw archives stay in Git and are referenced by their existing records.
    for p in list(ROOT.glob('*.py')) + list((ROOT / 'tests').rglob('*.py')):
        assets['source/' + p.relative_to(ROOT).as_posix()] = p
    for p in list(ROOT.glob('LICENSE*')) + list(ROOT.glob('NOTICE*')):
        if p.is_file():
            assets['source/' + p.name] = p
    for name, h in env['source_files_sha256'].items():
        p = ROOT / name
        if sha(p.read_bytes()) != h:
            raise ValueError('Frozen source changed: ' + name)
        assets['source/' + name] = p
    for name, h in env['input_files_sha256'].items():
        p = ROOT / name
        if sha(p.read_bytes()) != h:
            raise ValueError('Frozen input changed: ' + name)
        assets['inputs/' + name] = p
    for name in ('environment.json', 'protocol.json', 'snapshot_manifest.json'):
        p = ROOT / 'results/common_physical_pool_2026-11-25' / name
        assets['inputs/' + p.relative_to(ROOT).as_posix()] = p
    p = ROOT / 'results/grover_competition_2026-11-17/resource_certificate.json'
    assets['inputs/' + p.relative_to(ROOT).as_posix()] = p
    manifest = json.loads((ROOT / 'benchmarks/public_2026-11-17/manifest.json').read_text())
    for item in manifest['files']:
        p = ROOT / item['path']
        if sha(p.read_bytes()) != item['sha256']:
            raise ValueError('Original complete source changed')
        assets['inputs/' + item['path']] = p
    hashes = {}
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_LZMA) as z:
        for name, p in sorted(assets.items()):
            raw = p.read_bytes()
            hashes[name] = sha(raw)
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 26, 0, 0, 0))
            info.compress_type = zipfile.ZIP_LZMA
            z.writestr(info, raw)
        z.writestr('sha256.json', json.dumps(hashes, indent=2) + '\n')
    record = dict(archive=str(archive.relative_to(ROOT)) if archive.is_relative_to(ROOT) else str(archive),
                  sha256=sha(archive.read_bytes()), bytes=archive.stat().st_size,
                  assets=len(hashes), files_sha256=hashes,
                  scope='Raw complete circuits/DEMs, core records, source/adapters/tests and pinned inputs. Use the committed repository checkout plus pinned dependencies for replay; not an isolated dependency bundle. Research shots0.')
    (result / 'snapshot_manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: v for k, v in record.items() if k != 'files_sha256'}, indent=2))


def check(result, archive):
    record = json.loads((result / 'snapshot_manifest.json').read_text())
    if sha(archive.read_bytes()) != record['sha256'] or archive.stat().st_size != record['bytes']:
        raise AssertionError('Archive bytes changed')
    with zipfile.ZipFile(archive) as z:
        hashes = json.loads(z.read('sha256.json'))
        if hashes != record['files_sha256'] or set(z.namelist()) != set(hashes) | {'sha256.json'}:
            raise AssertionError('Archive inventory changed')
        for name, h in hashes.items():
            if sha(z.read(name)) != h:
                raise AssertionError('Archive asset changed: ' + name)
    print(f'PASS: archive SHA256 and all{len(hashes)} assets; 0 new shots')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--result', type=Path, default=DEFAULT)
    ap.add_argument('--archive', type=Path, default=ARCHIVE)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    (check if args.check else pack)(args.result, args.archive)
