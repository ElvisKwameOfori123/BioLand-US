"""Repository-relative path management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import load_config, repository_root


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    raw: Path
    restricted: Path
    interim: Path
    frozen: Path
    results: Path
    figures: Path
    logs: Path
    manifests: Path

    @classmethod
    def from_config(cls) -> "ProjectPaths":
        root = repository_root()
        cfg = load_config()["paths"]

        return cls(
            root=root,
            raw=root / cfg["raw"],
            restricted=root / cfg["restricted"],
            interim=root / cfg["interim"],
            frozen=root / cfg["frozen"],
            results=root / cfg["results"],
            figures=root / cfg["figures"],
            logs=root / cfg["logs"],
            manifests=root / cfg["manifests"],
        )

    def create_output_directories(self) -> None:
        """Create non-source output directories used by the pipeline."""
        for path in (
            self.interim,
            self.frozen,
            self.results,
            self.figures,
            self.logs,
            self.manifests,
        ):
            path.mkdir(parents=True, exist_ok=True)
