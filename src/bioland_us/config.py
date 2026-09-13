"""Configuration helpers for BioLand-US."""

from __future__ import annotations

from pathlib import Path
import tomllib


def repository_root(start: Path | None = None) -> Path:
    """Return the repository root by locating pyproject.toml."""
    here = (start or Path.cwd()).resolve()

    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate

    raise FileNotFoundError(
        "Could not locate the BioLand-US repository root. "
        "Run from inside the cloned repository."
    )


def load_config(path: Path | None = None) -> dict:
    """Load the public BioLand-US TOML configuration."""
    root = repository_root()
    config_path = path or (root / "config" / "default.toml")

    with config_path.open("rb") as handle:
        return tomllib.load(handle)
