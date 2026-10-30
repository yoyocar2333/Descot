"""Load pinned wisq modules without importing its unrelated synthesis frontend."""
from pathlib import Path
import importlib
import subprocess
import sys
import types

COMMIT = "97c12a5e22cf16e37288c60a0a5735c58c6fe8ca"


def load_core(repo):
    repo = Path(repo).resolve()
    actual = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if actual != COMMIT:
        raise ValueError(f"Expected {COMMIT}, got {actual}")
    name = "wisq_pinned_core"
    if name not in sys.modules:
        package = types.ModuleType(name)
        package.__path__ = [str(repo / "src/wisq")]
        sys.modules[name] = package
    elif Path(sys.modules[name].__path__[0]) != repo / "src/wisq":
        raise ValueError("A different wisq checkout is already loaded")
    return {key: importlib.import_module(f"{name}.{key}")
            for key in ["architecture", "sarouting", "phased_graph", "dascot"]}
