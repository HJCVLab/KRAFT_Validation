#!/usr/bin/env python3
"""Utilities for reading a KRAFT release from a ZIP file or extracted directory.

The public ZIP may contain either files directly at its root::

    Data/...
    README.md

or a single top-level release directory::

    KRAFT_v1.0/Data/...
    KRAFT_v1.0/README.md

This module exposes both layouts through the same logical paths, e.g.
``Data/Macroeconomic/CPI.csv``.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable
import zipfile

import pandas as pd


def _normalise_logical_path(path: str | Path) -> str:
    """Return a clean forward-slash relative path."""
    text = str(path).replace("\\", "/").strip()
    while text.startswith("./"):
        text = text[2:]
    return text.lstrip("/").rstrip("/")


class KraftPackage:
    """Read logical files from a KRAFT ZIP package or extracted directory."""

    def __init__(self, source: str | Path):
        self.source = Path(source).expanduser().resolve()
        if not self.source.exists():
            raise FileNotFoundError(f"Input package does not exist: {self.source}")

        self._zip: zipfile.ZipFile | None = None
        self.root: Path | None = None
        self._logical_to_actual: dict[str, str] = {}

        if self.source.is_file() and self.source.suffix.lower() == ".zip":
            self._init_zip()
        elif self.source.is_dir():
            self._init_directory()
        else:
            raise ValueError(
                "Input must be a .zip file or an extracted KRAFT directory: "
                f"{self.source}"
            )

    def _init_zip(self) -> None:
        self._zip = zipfile.ZipFile(self.source)
        file_names = [
            _normalise_logical_path(info.filename)
            for info in self._zip.infolist()
            if not info.is_dir()
        ]

        # Detect the path prefix immediately preceding Data/. The most common
        # prefix is used so unrelated archive metadata does not affect routing.
        prefixes: list[str] = []
        for name in file_names:
            marker = "Data/"
            idx = name.find(marker)
            if idx >= 0:
                prefixes.append(name[:idx])

        if not prefixes:
            raise FileNotFoundError(
                "Could not locate a Data/ directory inside the ZIP package."
            )

        prefix = Counter(prefixes).most_common(1)[0][0]
        for actual in file_names:
            if actual.startswith(prefix):
                logical = _normalise_logical_path(actual[len(prefix):])
                if logical:
                    self._logical_to_actual[logical] = actual

        if not any(p.startswith("Data/") for p in self._logical_to_actual):
            raise FileNotFoundError(
                "The detected ZIP root does not contain logical Data/ files."
            )

    def _init_directory(self) -> None:
        # Accept either the release root itself or a parent directory containing
        # one extracted release folder such as KRAFT_v1.0/.
        if (self.source / "Data").is_dir():
            root = self.source
        else:
            candidates = sorted(
                {
                    p.parent
                    for p in self.source.rglob("Data")
                    if p.is_dir() and (p / "Transactions").exists()
                },
                key=lambda p: (len(p.relative_to(self.source).parts), str(p)),
            )
            if not candidates:
                raise FileNotFoundError(
                    f"Could not locate an extracted KRAFT Data/ directory under {self.source}"
                )
            root = candidates[0]

        self.root = root
        for path in root.rglob("*"):
            if path.is_file():
                logical = path.relative_to(root).as_posix()
                self._logical_to_actual[logical] = str(path)

    def __enter__(self) -> "KraftPackage":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._zip is not None:
            self._zip.close()
            self._zip = None

    @property
    def logical_files(self) -> list[str]:
        return sorted(self._logical_to_actual)

    def exists(self, logical_path: str | Path) -> bool:
        return _normalise_logical_path(logical_path) in self._logical_to_actual

    def list_files(
        self,
        prefix: str | Path = "",
        suffix: str | None = None,
    ) -> list[str]:
        logical_prefix = _normalise_logical_path(prefix)
        if logical_prefix:
            logical_prefix += "/"
        files = [
            path
            for path in self.logical_files
            if path.startswith(logical_prefix)
            and (suffix is None or path.endswith(suffix))
        ]
        return files

    def open_binary(self, logical_path: str | Path) -> BinaryIO:
        logical = _normalise_logical_path(logical_path)
        if logical not in self._logical_to_actual:
            available_hint = ", ".join(self.logical_files[:8])
            raise FileNotFoundError(
                f"Logical file not found in KRAFT package: {logical}. "
                f"First available files: {available_hint}"
            )

        actual = self._logical_to_actual[logical]
        if self._zip is not None:
            return self._zip.open(actual, "r")
        return open(actual, "rb")

    def read_csv(self, logical_path: str | Path, **kwargs) -> pd.DataFrame:
        with self.open_binary(logical_path) as stream:
            return pd.read_csv(stream, **kwargs)

    def read_csv_header(self, logical_path: str | Path) -> list[str]:
        return self.read_csv(logical_path, nrows=0).columns.tolist()

    def describe(self) -> str:
        if self._zip is not None:
            return f"ZIP package: {self.source}"
        return f"Extracted directory: {self.root}"
