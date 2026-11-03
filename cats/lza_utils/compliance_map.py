# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
# with the License. A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing
# permissions and limitations under the License.

"""LZA compliance mapping for OSCAL standard resolution.

Resolves LZA control IDs (e.g. ``LZA-G-DCP-1``) to framework-specific control
IDs (e.g. NIST ``CM-8``, ``PL-9``) and carries the metadata for each LZA
control, read from the LZA Compliance Workbook shipped at the pack root as
``lza-compliance-workbook-<version>.csv`` (:data:`SHIPPED_WORKBOOK_VERSION`).

The workbook has its own version number, separate from the Universal
Configuration's: the two happen to match at 1.4.0 and are not expected to stay
in step. The ``... v.<x.y.z> Description`` header names the Universal
Configuration release the workbook describes, not the workbook version.

The workbook is a single CSV sheet, one row per LZA control. The leading
columns carry the control's metadata and the remaining columns are frameworks:

* ``LZA Common Control ID``, ``Core Foundations``, ``Capabilities``,
  ``Source Configuration File Reference`` (one file per line),
  ``LZA Universal Configuration v.<x.y.z> Description`` (one sentence),
  ``Security & Compliance Implementation Details`` (the narrative).
* ``Working Notes`` and ``Framework Drafting Column`` are the authors' scratch
  columns and are ignored.
* Every other header is a framework; its cells hold newline-separated framework
  control IDs. The header text is the framework name passed as
  ``LZA_OSCAL_FRAMEWORK`` (optional; unset, results keep their LZA control IDs).

Framework control IDs are normalized to OSCAL tokens as they are read, because
every ID becomes an OSCAL finding ``target-id`` and the CATS OSCAL writer
(aws-cats >= 0.99.4) rejects anything else. A token starts with a letter or
``_`` and contains only letters, digits, ``.``, ``-`` and ``_``. The workbook
spells IDs in several non-token forms, each mapped deterministically:

* NIST-style enhancements ``AC-2 (1)`` -> ``AC-2.1`` (the OSCAL catalog
  convention). Nested references ``164.308(a)(1)`` -> ``164.308.a.1``.
* A comma-separated list of enhancements ``ID.AM-02 (1_O, 2_O)`` (ACN) is one
  ID per enhancement: ``ID.AM-02.1_O``, ``ID.AM-02.2_O``.
* Cells holding several space-separated IDs (``ISM-0041 ISM-1228``,
  ``CC6.1 CC8.1``) are split into one ID each.
* ``:`` and ``&`` become ``-``: ``CID:5820`` (ISM New Zealand) -> ``CID-5820``,
  ``I&S-06`` (CCM) -> ``I-S-06``.
* Digit-leading IDs (``3.1.1``, ``11.1``, ``2-1-T-1-1``) are prefixed with a
  slug of their framework name: ``nist-800-171-rev2-3.1.1``, ``cis-critical-controls-v8-11.1``.
* The placeholders ``No Control Mapping`` and ``N/A`` are dropped.

Case is preserved. An ID that is still not a token after this raises
``ValueError`` when the workbook is loaded, so a workbook edit that breaks
OSCAL output fails the session before any test runs rather than in the report
writer.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path

# The LZA Compliance Workbook edition shipped with the pack. A workbook bump renames the CSV,
# changes this constant, and reviews the pins in lza_utils/tests/workbook_narrative_pins.json.
SHIPPED_WORKBOOK_VERSION = "1.4.0"
DEFAULT_COMPLIANCE_WORKBOOK_PATH = Path(__file__).resolve().parents[1] / f"lza-compliance-workbook-{SHIPPED_WORKBOOK_VERSION}.csv"

LZA_ID_COLUMN = "LZA Common Control ID"
FOUNDATION_COLUMN = "Core Foundations"
CAPABILITY_COLUMN = "Capabilities"
SOURCE_CONFIG_FILES_COLUMN = "Source Configuration File Reference"
NARRATIVE_COLUMN = "Security & Compliance Implementation Details"
# The description header carries the Universal Configuration version it describes.
DESCRIPTION_COLUMN_PATTERN = re.compile(r"^LZA Universal Configuration v\.?\d+\.\d+\.\d+ Description$")
IGNORED_COLUMNS = frozenset({"Working Notes", "Framework Drafting Column"})
_REQUIRED_COLUMNS = (LZA_ID_COLUMN, FOUNDATION_COLUMN, CAPABILITY_COLUMN, SOURCE_CONFIG_FILES_COLUMN, NARRATIVE_COLUMN)

# OSCAL TokenDatatype, as cats.report_writers.oscal_ar enforces it: a letter or
# underscore, then letters, digits, '.', '-', '_'.
_OSCAL_TOKEN = re.compile(r"^[^\W\d][\w.\-]*$")
# A parenthesized suffix such as ' (1)' in 'AC-2 (1)' or '(a)' in '164.308(a)(1)', or the
# bracketed sub-item ITSG-33 (CCCS) writes as 'SC-7a[03][04]'. The optional leading '.'
# absorbs the workbook typo '164.312.(b)' so it lands on the same token as '164.312(b)'.
_PARENTHESIZED = re.compile(r"\s*\.?[(\[]([^()\[\]]+)[)\]]")
# A base ID followed by a comma-separated list of enhancements: 'ID.AM-02 (1_O, 2_O, 3_O)'.
_ENHANCEMENT_LIST = re.compile(r"^(?P<base>\S+)\s*\((?P<items>[^()]*,[^()]*)\)$")
# Anything that is not a letter or digit, for building a framework prefix.
_NON_ALNUM_RUN = re.compile(r"[^a-z0-9]+")
# Workbook placeholders for an LZA control with no equivalent in a framework.
_PLACEHOLDERS = frozenset({"no control mapping", "n/a", "na"})
# Characters the workbook uses inside IDs that OSCAL tokens do not allow, each folded to '-':
# 'CID:5820' (ISM NZ), 'I&S-06' (CCM), '2/5/02' (NCA ECC, written '2-5-2' elsewhere in the column).
_FOLDED_TO_DASH = str.maketrans({":": "-", "&": "-", "/": "-"})


@dataclass(frozen=True)
class ControlMetadata:
    """Metadata for a single LZA control ID.

    ``source_config_files`` lists the LZA configuration files the control is implemented
    in; ``config_description`` is the one-sentence description of what the Universal
    Configuration sets, and ``implementation_narrative`` the longer compliance narrative.
    """

    foundation: str
    capability: str
    source_config_files: tuple[str, ...]
    config_description: str
    implementation_narrative: str


def _framework_prefix(framework: str) -> str:
    """Slug of a framework name used to prefix digit-leading control IDs: 'NIST 800-171 Rev2' -> 'nist-800-171-rev2'."""
    return _NON_ALNUM_RUN.sub("-", framework.lower()).strip("-")


def _normalize_control_id(raw_id: str, framework: str) -> str:
    """Rewrite one workbook control ID as an OSCAL token, or raise ``ValueError`` if that is not possible."""
    control_id = raw_id.translate(_FOLDED_TO_DASH)
    if _OSCAL_TOKEN.match(control_id) is None and control_id[0].isdigit():
        control_id = f"{_framework_prefix(framework)}-{control_id}"
    if _OSCAL_TOKEN.match(control_id) is None:
        raise ValueError(
            f"Control id {raw_id!r} in framework {framework!r} cannot be normalized to an OSCAL token "
            + "(letters, digits, '.', '-', '_', starting with a letter or '_'); fix the workbook cell"
        )
    return control_id


def _expand_enhancement_list(line: str) -> list[str]:
    """'ID.AM-02 (1_O, 2_O)' -> ['ID.AM-02 (1_O)', 'ID.AM-02 (2_O)']; any other line is returned as is."""
    match = _ENHANCEMENT_LIST.match(line)
    if match is None:
        return [line]
    return [f"{match['base']} ({item.strip()})" for item in match["items"].split(",") if item.strip()]


def split_control_ids(cell_value: str | None, framework: str) -> list[str]:
    """Split a mapping cell into normalized OSCAL-token control IDs.

    IDs are newline-separated in the workbook; a few cells also pack several
    IDs on one line separated by spaces, so parenthesized enhancements are
    folded to ``.n`` first and the result is split on any whitespace.
    """
    if not cell_value:
        return []
    control_ids: list[str] = []
    for raw_line in cell_value.replace("\xa0", " ").split("\n"):
        line = raw_line.strip()
        if not line or line.lower() in _PLACEHOLDERS:
            continue
        for expanded in _expand_enhancement_list(line):
            for raw_id in _PARENTHESIZED.sub(r".\1", expanded).split():
                control_ids.append(_normalize_control_id(raw_id, framework))
    return control_ids


def _clean_text(value: str) -> str:
    """Workbook text with non-breaking spaces folded to spaces and surrounding whitespace removed."""
    return value.replace("\xa0", " ").strip()


def _split_lines(value: str) -> tuple[str, ...]:
    """Non-empty, stripped lines of a multi-line cell, in order."""
    return tuple(line for raw in _clean_text(value).split("\n") if (line := raw.strip()))


class ComplianceMap:
    """Resolve LZA control IDs from an LZA Compliance Workbook CSV.

    Construct with :meth:`from_csv`; :func:`default_compliance_map` returns the
    instance backed by the shipped ``lza-compliance-workbook-<version>.csv``.
    """

    def __init__(
        self,
        *,
        frameworks: list[str],
        mappings: dict[str, dict[str, list[str]]],
        controls: list[str],
        metadata: dict[str, ControlMetadata],
    ) -> None:
        self._framework_names = frameworks
        self._mappings = mappings
        self._lza_ids = controls
        self._metadata = metadata

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_csv(cls, path: str | Path) -> ComplianceMap:
        """Load a :class:`ComplianceMap` from a workbook CSV (UTF-8).

        Raises ``ValueError`` when the header lacks a required column, a control
        appears on more than one row, or a control ID cannot be normalized.
        """
        workbook_path = Path(path)
        rows = csv.reader(io.StringIO(workbook_path.read_text(encoding="utf-8"), newline=""))
        header = next(rows, None)
        if header is None:
            raise ValueError(f"{workbook_path} is empty; expected a header row")
        header = [_clean_text(name) for name in header]

        missing = [name for name in _REQUIRED_COLUMNS if name not in header]
        description_columns = [name for name in header if DESCRIPTION_COLUMN_PATTERN.match(name)]
        if missing or len(description_columns) != 1:
            raise ValueError(
                f"{workbook_path} header is missing columns {missing} or has {len(description_columns)} description columns "
                + f"(expected one matching {DESCRIPTION_COLUMN_PATTERN.pattern!r}); header was {header}"
            )
        column_index = {name: index for index, name in enumerate(header)}
        description_column = description_columns[0]
        metadata_columns = {*_REQUIRED_COLUMNS, description_column, *IGNORED_COLUMNS}
        framework_columns = [(index, name) for index, name in enumerate(header) if name and name not in metadata_columns]

        def cell(row: list[str], name: str) -> str:
            index = column_index[name]
            return row[index] if index < len(row) else ""

        frameworks = [name for _, name in framework_columns]
        mappings: dict[str, dict[str, list[str]]] = {name: {} for name in frameworks}
        controls: list[str] = []
        metadata: dict[str, ControlMetadata] = {}
        for row in rows:
            lza_id = _clean_text(cell(row, LZA_ID_COLUMN))
            if not lza_id:
                continue
            if lza_id in metadata:
                raise ValueError(f"{workbook_path} lists {lza_id} more than once; every LZA control is one row")
            controls.append(lza_id)
            metadata[lza_id] = ControlMetadata(
                foundation=_clean_text(cell(row, FOUNDATION_COLUMN)),
                capability=_clean_text(cell(row, CAPABILITY_COLUMN)),
                source_config_files=_split_lines(cell(row, SOURCE_CONFIG_FILES_COLUMN)),
                config_description=_clean_text(cell(row, description_column)),
                implementation_narrative=_clean_text(cell(row, NARRATIVE_COLUMN)),
            )
            for index, framework_name in framework_columns:
                control_ids = split_control_ids(row[index] if index < len(row) else None, framework_name)
                if control_ids:
                    mappings[framework_name][lza_id] = list(dict.fromkeys(control_ids))
        return cls(frameworks=frameworks, mappings=mappings, controls=controls, metadata=metadata)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self, lza_id: str, framework: str) -> list[str]:
        """Return framework control IDs for *lza_id*, or ``[]`` if unknown."""
        framework_map = self._mappings.get(framework)
        if framework_map is None:
            return []
        return list(framework_map.get(lza_id, []))

    def frameworks(self) -> list[str]:
        """Return the ordered list of framework names from the workbook header."""
        return list(self._framework_names)

    def lza_controls(self) -> list[str]:
        """Return all LZA control IDs found in the workbook, in row order."""
        return list(self._lza_ids)

    def metadata(self, lza_id: str) -> ControlMetadata | None:
        """Return metadata for *lza_id*, or ``None``."""
        return self._metadata.get(lza_id)

    def implementation_narrative(self, lza_id: str) -> str | None:
        """Return the implementation narrative for *lza_id*, or ``None``."""
        meta = self._metadata.get(lza_id)
        return meta.implementation_narrative if meta else None

    def all_metadata(self) -> dict[str, ControlMetadata]:
        """Return every control's metadata keyed by LZA ID, in workbook order."""
        return dict(self._metadata)


def default_compliance_map() -> ComplianceMap:
    """Return the :class:`ComplianceMap` backed by the shipped ``lza-compliance-workbook-<version>.csv``."""
    return ComplianceMap.from_csv(DEFAULT_COMPLIANCE_WORKBOOK_PATH)
