"""Create a separate Python3.12 overlay; never modify the research base lock."""
import argparse
import importlib.metadata as md
from pathlib import Path
import subprocess
import sys
import sysconfig

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--env", type=Path, required=True)
    a = p.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise ValueError("Run with the locked base Python3.12")
    for line in (ROOT / "requirements-lock.txt").read_text().splitlines():
        if "==" in line:
            name, version = line.split("==")
            if md.version(name) != version:
                raise ValueError(f"Base pin differs: {name}")
    if a.env.exists():
        raise FileExistsError("Fresh environment required")
    subprocess.run([sys.executable, "-m", "venv", str(a.env)], check=True)
    python = a.env / "bin/python"
    purelib = subprocess.check_output([str(python), "-c", "import sysconfig;print(sysconfig.get_paths()['purelib'])"], text=True).strip()
    (Path(purelib) / "descot_frozen_base.pth").write_text(str(Path(sysconfig.get_paths()["purelib"]).resolve()) + "\n")
    subprocess.run([str(python), "-m", "pip", "install", "--no-deps", "--require-hashes",
                    "-r", str(ROOT / "requirements-circls-extra-2026-11-21.txt")], check=True)
    subprocess.run([str(python), "-m", "pip", "check"], check=True)
    print(python)


if __name__ == "__main__":
    main()
