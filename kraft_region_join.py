#!/usr/bin/env python3
"""Administrative join-key helpers for KRAFT reuse examples."""

from __future__ import annotations

import re
from typing import Hashable

import pandas as pd


_GENERAL_GU_PATTERN = re.compile(r"^(?P<parent>.+?시)\s+(?P<general_gu>[^\s]+구)$")


def normalise_whitespace(value):
    """Trim a location label and collapse repeated whitespace."""
    if pd.isna(value):
        return pd.NA
    return re.sub(r"\s+", " ", str(value).strip())


def education_join_sigungu(value):
    """Return the parent-city key used by the education indicator files.

    Transaction records preserve general-gu labels for cities that contain
    non-autonomous districts, whereas the education indicators are aggregated
    at the parent-city level. Only labels of the form ``<city> <general-gu>``
    are collapsed.

    Examples
    --------
    ``용인시 수지구`` -> ``용인시``
    ``수원시 영통구`` -> ``수원시``
    ``창원시 의창구`` -> ``창원시``
    ``강남구`` -> ``강남구``  (standalone metropolitan district; unchanged)
    ``김해시`` -> ``김해시``  (already at the parent-city level)
    """
    text = normalise_whitespace(value)
    if pd.isna(text):
        return pd.NA

    match = _GENERAL_GU_PATTERN.fullmatch(str(text))
    return match.group("parent") if match else text


def add_education_join_keys(
    frame: pd.DataFrame,
    *,
    sido_column: str = "Sido",
    sigungu_column: str = "Sigungu",
    output_column: str = "Education_Join_Sigungu",
) -> pd.DataFrame:
    """Return a copy with normalised Sido and education Sigungu join keys."""
    missing = [c for c in (sido_column, sigungu_column) if c not in frame.columns]
    if missing:
        raise KeyError(f"Missing required location column(s): {missing}")

    result = frame.copy()
    result[sido_column] = result[sido_column].map(normalise_whitespace)
    result[output_column] = result[sigungu_column].map(education_join_sigungu)
    return result
