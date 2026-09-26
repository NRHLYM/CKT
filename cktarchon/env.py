from __future__ import annotations

from pathlib import Path as _CktPath
import os as _ckt_os
CKT_WORK = _CktPath(_ckt_os.environ.get('CKT_WORK', str(_CktPath.home() / 'ckt_work')))
import os
import shutil
from pathlib import Path


def load_env_file(path: Path) -> dict[str, str]:
    """Load KEY=VALUE lines into ``os.environ`` without printing secrets."""
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded
    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        os.environ.setdefault(key, value)
        loaded[key] = value
    return loaded


def model_alias(name: str) -> str:
    """Normalize user-facing model aliases used in NL2Chip scripts."""
    aliases = {
        "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
        "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",
        "sonnet-4.5": "claude-sonnet-4-5-20250929",
        "sonnet": "claude-sonnet-4-5-20250929",
        "opus-4-7": "claude-opus-4-7",
    }
    return aliases.get(name, name)


def ensure_runtime_env() -> None:
    """Expose the local Lean/Lake runtime without assuming the the eval host home path."""
    project_root = Path(__file__).resolve().parents[1]
    prefixes = [
        str(project_root / ".venv" / "bin"),
        str(Path.home() / ".elan" / "bin"),
        str(Path.home() / ".local" / "bin"),
        str(Path.home() / "toolcache" / "iverilog_deb" / "extract" / "usr" / "bin"),
        str(_CktPath.home() / ".elan/bin"),
        str(_CktPath.home() / ".elan/toolchains/leanprover--lean4---v4.28.0-rc1/bin"),
        str(_CktPath.home() / ".local/bin"),
        str(_CktPath.home() / ".local/share/mamba/bin"),
    ]
    current = os.environ.get("PATH", "")
    parts = current.split(os.pathsep) if current else []
    for prefix in reversed(prefixes):
        if Path(prefix).exists() and prefix not in parts:
            parts.insert(0, prefix)
    os.environ["PATH"] = os.pathsep.join(parts)

    configured = os.environ.get("LAKE_PATH", "").strip()
    configured_path = Path(configured).expanduser() if configured else None
    if configured_path is not None and configured_path.is_file():
        return

    discovered = shutil.which("lake", path=os.environ["PATH"])
    if discovered:
        os.environ["LAKE_PATH"] = discovered
    else:
        # Do not preserve a stale host-specific path. LeanREPL will report its
        # normal local fallback if Lake truly is unavailable on this host.
        os.environ.pop("LAKE_PATH", None)
