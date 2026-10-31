"""Restore frozen result snapshots, preserving existing different files."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parent

def main():
    archive=ROOT/'archives/phase1_snapshot.zip'
    metadata=json.loads((ROOT/'archives/manifest.json').read_text())['phase1_snapshot.zip']
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==metadata['sha256'], 'Archive hash mismatch'
    restored=unchanged=0
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read('dascot_phase1/ARTIFACT_MANIFEST.json'))
        for entry in manifest['files']:
            rel=Path(entry['path'])
            if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe archive path')
            if rel.parts[0]!='results':continue
            data=z.read('dascot_phase1/'+rel.as_posix())
            assert hashlib.sha256(data).hexdigest()==entry['sha256'], 'Archived file hash mismatch'
            path=ROOT/rel
            if path.exists():
                if path.read_bytes()!=data:raise FileExistsError(f'Existing file differs; preserved: {rel}')
                unchanged+=1
            else:
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);restored+=1
    chain=ROOT/'archives/composition_2026-10-30.zip'
    info=json.loads((ROOT/'archives/manifest.json').read_text())[chain.name]
    assert hashlib.sha256(chain.read_bytes()).hexdigest()==info['sha256'], 'Composition archive hash mismatch'
    with zipfile.ZipFile(chain) as z:
        for name in z.namelist():
            rel=Path(name)
            if rel.is_absolute() or '..' in rel.parts or rel.parts[:2]!=('results','composition'):
                raise ValueError('Unsafe composition archive path')
            data=z.read(name);path=ROOT/rel
            if path.exists():
                if path.read_bytes()!=data:raise FileExistsError(f'Existing file differs; preserved: {rel}')
                unchanged+=1
            else:
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);restored+=1
    metadata=json.loads((ROOT/'archives/manifest.json').read_text())
    extra=[(name,info) for name,info in metadata.items()
           if name not in ['phase1_snapshot.zip','composition_2026-10-30.zip']]
    for archive_name,info in extra:
        if Path(archive_name).name!=archive_name:raise ValueError('Unsafe archive name')
        prefix=Path(info['result_prefix'])
        if prefix.is_absolute() or '..' in prefix.parts or prefix.parts[0]!='results':
            raise ValueError('Unsafe result prefix')
        archive=ROOT/'archives'/archive_name
        assert hashlib.sha256(archive.read_bytes()).hexdigest()==info['sha256'], 'Archive hash mismatch'
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                rel=Path(name)
                if rel.is_absolute() or '..' in rel.parts or rel.parts[:len(prefix.parts)]!=prefix.parts:
                    raise ValueError('Unsafe result path')
                data=z.read(name);path=ROOT/rel
                if path.exists():
                    if path.read_bytes()!=data:raise FileExistsError(f'Existing file differs; preserved: {rel}')
                    unchanged+=1
                else:
                    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);restored+=1
    print(json.dumps({'restored':restored,'unchanged':unchanged,'archives_verified':2+len(extra)}))

if __name__=='__main__':main()
