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

"""Tests for the compliance mapping: control-ID normalization, the workbook CSV loader, and the shipped workbook."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import pytest

from lza_utils.compliance_map import (
    CAPABILITY_COLUMN,
    DEFAULT_COMPLIANCE_WORKBOOK_PATH,
    FOUNDATION_COLUMN,
    LZA_ID_COLUMN,
    NARRATIVE_COLUMN,
    SOURCE_CONFIG_FILES_COLUMN,
    ComplianceMap,
    ControlMetadata,
    default_compliance_map,
    split_control_ids,
)

_NARRATIVE_PINS_PATH = Path(__file__).resolve().parent / "workbook_narrative_pins.json"
_DEFAULT_FRAMEWORK = "NIST 800-53 Rev5"
_DESCRIPTION_COLUMN = "LZA Universal Configuration v.1.4.0 Description"
_EXPECTED_SHIPPED_FRAMEWORKS = [
    "NIST 800-53 Rev5",
    "CMMC Level 2",
    "NIST 800-171 Rev2",
    "NIST CSF 2.0",
    "ISO-27001 Annex A (2022)",
    "ISO-27002",
    "HIPAA",
    "SOC2",
    "CIS Critical Controls v8",
    "PCI-DSS v4.0",
    "DoD Control Correlation Identifier (CCI)",
    "NERC-CIP",
    "NATO D-32",
    "C5:2020 (Germany)",
    "ISM Australia",
    "ISM New Zealand",
    "NCA Cloud Cybersecurity Controls (KSA)",
    "NCA Essential Cybersecurity Controls (KSA)",
    "SAMA Cyber Security Framework",
    "CCCS Medium (Canada)",
    "CCCS High (Canada)",
    "ENS - Medium (Spain)",
    "BIO v2 (Netherlands)",
    "ACN - Level 2",
    "CCM (v4.1.0)",
    "CSA Star (CAIQ)",
]
_EXPECTED_SHIPPED_CONTROL_COUNT = 193


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _narrative_pins(cmap: ComplianceMap) -> dict[str, str]:
    """{lza_id: 16-hex digest of (foundation, capability, description)} for every control in the mapping."""
    pins: dict[str, str] = {}
    for lza_id in cmap.lza_controls():
        metadata = cmap.metadata(lza_id)
        assert metadata is not None, f"{lza_id} has no metadata"
        text = f"{metadata.foundation}\n{metadata.capability}\n{metadata.config_description}"
        pins[lza_id] = hashlib.sha256(text.encode()).hexdigest()[:16]
    return pins


_METADATA_HEADER = [LZA_ID_COLUMN, FOUNDATION_COLUMN, CAPABILITY_COLUMN, SOURCE_CONFIG_FILES_COLUMN, _DESCRIPTION_COLUMN, NARRATIVE_COLUMN]
_FRAMEWORK_HEADER = ["NIST 800-53 Rev5", "CMMC Level 2", "HIPAA"]
_DEFAULT_METADATA = ["Governance", "SCPs", "organization-config.yaml", "Config desc", "Impl narrative"]


def _row(lza_id: str, *framework_cells: str, metadata: list[str] | None = None) -> list[str]:
    """One workbook row: *metadata* (defaults) followed by one cell per framework in ``_FRAMEWORK_HEADER``."""
    cells = list(framework_cells) + [""] * (len(_FRAMEWORK_HEADER) - len(framework_cells))
    return [lza_id, *(metadata or _DEFAULT_METADATA), *cells]


def _make_workbook(rows: list[list[str]], tmp_path: Path, header: list[str] | None = None) -> Path:
    """Write a CSV workbook with the standard metadata columns, the test frameworks and *rows*."""
    path = tmp_path / "workbook.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header if header is not None else [*_METADATA_HEADER, *_FRAMEWORK_HEADER])
        writer.writerows(rows)
    return path


# ---------------------------------------------------------------------------
# split_control_ids
# ---------------------------------------------------------------------------

_OSCAL_TOKEN = re.compile(r"^[^\W\d][\w.\-]*$")
_NIST = "NIST 800-53 Rev5"


class TestSplitControlIds:
    def test_none_returns_empty(self) -> None:
        assert split_control_ids(None, _NIST) == []

    def test_empty_string_returns_empty(self) -> None:
        assert split_control_ids("", _NIST) == []

    def test_single_id(self) -> None:
        assert split_control_ids("CM-8", _NIST) == ["CM-8"]

    def test_newline_separated(self) -> None:
        assert split_control_ids("CM-8\nPL-9\nSC-2", _NIST) == ["CM-8", "PL-9", "SC-2"]

    def test_strips_whitespace_and_non_breaking_spaces(self) -> None:
        assert split_control_ids("  CM-8 \n\xa0PL-9\xa0\n", _NIST) == ["CM-8", "PL-9"]

    def test_skips_blank_lines(self) -> None:
        assert split_control_ids("CM-8\n\n\nPL-9", _NIST) == ["CM-8", "PL-9"]

    def test_enhancement_in_parentheses_becomes_dot_suffix(self) -> None:
        assert split_control_ids("AC-2 (1)\nAC-4 (21)\nSA-8(14)", _NIST) == ["AC-2.1", "AC-4.21", "SA-8.14"]

    def test_comma_separated_enhancement_list_expands_to_one_id_each(self) -> None:
        assert split_control_ids("ID.AM-02 (1_O, 2_O, 3_O)\nPR.PT-05 (4_C)", "ACN - Level 2") == [
            "ID.AM-02.1_O",
            "ID.AM-02.2_O",
            "ID.AM-02.3_O",
            "PR.PT-05.4_C",
        ]

    def test_nested_parentheses_become_dot_path(self) -> None:
        assert split_control_ids("164.308(a)(7)(ii)(A)", "HIPAA") == ["hipaa-164.308.a.7.ii.A"]

    def test_stray_dot_before_parenthesis_is_absorbed(self) -> None:
        """The workbook spells '164.312(b)' as '164.312.(b)' in some cells; both must map to one token."""
        assert split_control_ids("164.312.(b)", "HIPAA") == split_control_ids("164.312(b)", "HIPAA")

    def test_space_separated_ids_on_one_line_are_split(self) -> None:
        assert split_control_ids("ISM-0041 ISM-1228 ISM-1616", "ISM Australia") == ["ISM-0041", "ISM-1228", "ISM-1616"]
        assert split_control_ids("CC6.1 CC8.1", "SOC2") == ["CC6.1", "CC8.1"]

    def test_bracketed_sub_items_become_dot_path(self) -> None:
        """ITSG-33 (CCCS) writes sub-items in brackets: 'SC-7a[03][04]'."""
        assert split_control_ids("SC-7a[03][04]", "CCCS Medium (Canada)") == ["SC-7a.03.04"]
        assert split_control_ids("SC-7a[03][04]  \nSC-7(5)", "CCCS High (Canada)") == ["SC-7a.03.04", "SC-7.5"]

    def test_colon_ampersand_and_slash_fold_to_dash(self) -> None:
        assert split_control_ids("CID:5820", "ISM New Zealand") == ["CID-5820"]
        assert split_control_ids("I&S-06", "CCM (v4.1.0)") == ["I-S-06"]
        assert split_control_ids("I&S-06 (1)", "CSA Star (CAIQ)") == ["I-S-06.1"]
        assert split_control_ids("2/5/02", "NCA Essential Cybersecurity Controls (KSA)") == ["nca-essential-cybersecurity-controls-ksa-2-5-02"]

    def test_digit_leading_id_gets_framework_prefix(self) -> None:
        assert split_control_ids("3.1.1", "NIST 800-171 Rev2") == ["nist-800-171-rev2-3.1.1"]
        assert split_control_ids("11.1", "CIS Critical Controls v8") == ["cis-critical-controls-v8-11.1"]
        assert split_control_ids("2-1-T-1-1", "NCA Cloud Cybersecurity Controls (KSA)") == ["nca-cloud-cybersecurity-controls-ksa-2-1-T-1-1"]
        assert split_control_ids("7.2.1", "PCI-DSS v4.0") == ["pci-dss-v4-0-7.2.1"]

    def test_letter_leading_id_is_not_prefixed(self) -> None:
        assert split_control_ids("AC.L2-3.1.1", "CMMC Level 2") == ["AC.L2-3.1.1"]
        assert split_control_ids("org.4\nop.acc.2", "ENS - Medium (Spain)") == ["org.4", "op.acc.2"]

    def test_placeholders_are_dropped(self) -> None:
        assert split_control_ids("No Control Mapping", "CMMC Level 2") == []
        assert split_control_ids("N/A", "PCI-DSS v4.0") == []
        assert split_control_ids("NA", "NERC-CIP") == []
        assert split_control_ids("AC.L2-3.1.1\nNo Control Mapping", "CMMC Level 2") == ["AC.L2-3.1.1"]

    def test_shipped_workbook_resolves_no_placeholder_as_a_control(self) -> None:
        """The workbook spells 'no mapping' three ways; none may reach the OSCAL report as a control ID."""
        parser = ComplianceMap.from_csv(DEFAULT_COMPLIANCE_WORKBOOK_PATH)
        placeholders = {
            (framework, control_id)
            for framework in parser.frameworks()
            for lza_id in parser.lza_controls()
            for control_id in parser.resolve(lza_id, framework)
            if control_id.lower().split("-")[-1] in {"na", "n", "none"} or control_id.lower() in {"na", "n-a", "none"}
        }
        assert placeholders == set()

    def test_unnormalizable_id_raises(self) -> None:
        """Prose in a cell ('SC-7 a(01)(02) and b', as the 1.4.0 workbook first spelled it) is a workbook defect, not two IDs."""
        with pytest.raises(ValueError, match="cannot be normalized to an OSCAL token"):
            split_control_ids("SC-7a(01)(02) & b", "CCCS High (Canada)")

    def test_orphan_enhancement_raises(self) -> None:
        """A line holding only '(3)' (a workbook typo seen in CCCS Medium) must fail, not silently become '.3'."""
        with pytest.raises(ValueError, match="cannot be normalized to an OSCAL token"):
            split_control_ids("AU-3\n (3)", "CCCS Medium (Canada)")


# ---------------------------------------------------------------------------
# ComplianceMap.from_csv — parsing
# ---------------------------------------------------------------------------


class TestFromCsvParsing:
    def test_frameworks_are_every_header_after_the_metadata_columns(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([], tmp_path))
        assert parser.frameworks() == _FRAMEWORK_HEADER

    def test_working_notes_and_drafting_columns_are_not_frameworks(self, tmp_path: Path) -> None:
        header = [*_METADATA_HEADER, "Working Notes", "Framework Drafting Column", *_FRAMEWORK_HEADER]
        row = ["LZA-X-1", *_DEFAULT_METADATA, "a note", "draft", "CM-8", "", ""]
        parser = ComplianceMap.from_csv(_make_workbook([row], tmp_path, header=header))
        assert parser.frameworks() == _FRAMEWORK_HEADER
        assert parser.resolve("LZA-X-1", "NIST 800-53 Rev5") == ["CM-8"]

    def test_lza_controls_in_row_order(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-2", "CM-8"), _row("LZA-X-1", "CM-8")], tmp_path))
        assert parser.lza_controls() == ["LZA-X-2", "LZA-X-1"]

    def test_header_only_has_no_controls(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([], tmp_path))
        assert parser.lza_controls() == []

    def test_skips_rows_with_empty_lza_id(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([_row("", "CM-8")], tmp_path))
        assert parser.lza_controls() == []

    def test_duplicate_lza_id_raises(self, tmp_path: Path) -> None:
        path = _make_workbook([_row("LZA-X-1", "CM-8"), _row("LZA-X-1", "PL-9")], tmp_path)
        with pytest.raises(ValueError, match="lists LZA-X-1 more than once"):
            ComplianceMap.from_csv(path)

    def test_missing_required_column_raises(self, tmp_path: Path) -> None:
        header = [LZA_ID_COLUMN, FOUNDATION_COLUMN, _DESCRIPTION_COLUMN, "NIST 800-53 Rev5"]
        path = _make_workbook([], tmp_path, header=header)
        with pytest.raises(
            ValueError, match=re.escape(f"missing columns ['{CAPABILITY_COLUMN}', '{SOURCE_CONFIG_FILES_COLUMN}', '{NARRATIVE_COLUMN}']")
        ):
            ComplianceMap.from_csv(path)

    def test_missing_description_column_raises(self, tmp_path: Path) -> None:
        header = [*(name for name in _METADATA_HEADER if name != _DESCRIPTION_COLUMN), *_FRAMEWORK_HEADER]
        path = _make_workbook([], tmp_path, header=header)
        with pytest.raises(ValueError, match="has 0 description columns"):
            ComplianceMap.from_csv(path)

    def test_description_column_matches_any_uc_version(self, tmp_path: Path) -> None:
        header = [
            *(name if name != _DESCRIPTION_COLUMN else "LZA Universal Configuration v.2.0.0 Description" for name in _METADATA_HEADER),
            *_FRAMEWORK_HEADER,
        ]
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-1", "CM-8")], tmp_path, header=header))
        assert parser.frameworks() == _FRAMEWORK_HEADER
        meta = parser.metadata("LZA-X-1")
        assert meta is not None
        assert meta.config_description == "Config desc"

    def test_empty_file_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.csv"
        path.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="is empty"):
            ComplianceMap.from_csv(path)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            ComplianceMap.from_csv(tmp_path / "nonexistent.csv")


# ---------------------------------------------------------------------------
# ComplianceMap — resolve
# ---------------------------------------------------------------------------


class TestResolve:
    def test_single_control(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-1", "CM-8")], tmp_path))
        assert parser.resolve("LZA-X-1", "NIST 800-53 Rev5") == ["CM-8"]

    def test_newline_separated_controls(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-1", "CM-8\nPL-9\nSC-2")], tmp_path))
        assert parser.resolve("LZA-X-1", "NIST 800-53 Rev5") == ["CM-8", "PL-9", "SC-2"]

    def test_unknown_lza_id_returns_empty(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-1", "CM-8")], tmp_path))
        assert parser.resolve("LZA-UNKNOWN-99", "NIST 800-53 Rev5") == []

    def test_unknown_framework_returns_empty(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-1", "CM-8")], tmp_path))
        assert parser.resolve("LZA-X-1", "Nonexistent Framework") == []

    def test_multiple_frameworks(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-1", "CM-8", "AC.L2-3.1.1")], tmp_path))
        assert parser.resolve("LZA-X-1", "NIST 800-53 Rev5") == ["CM-8"]
        assert parser.resolve("LZA-X-1", "CMMC Level 2") == ["AC.L2-3.1.1"]

    def test_duplicate_ids_within_a_cell_are_deduplicated_in_order(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-1", "B\nA\nA\nC")], tmp_path))
        assert parser.resolve("LZA-X-1", "NIST 800-53 Rev5") == ["B", "A", "C"]

    def test_empty_cell_returns_empty(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-1", "")], tmp_path))
        assert parser.resolve("LZA-X-1", "NIST 800-53 Rev5") == []


# ---------------------------------------------------------------------------
# ComplianceMap — metadata
# ---------------------------------------------------------------------------


class TestMetadata:
    def test_metadata_parsed(self, tmp_path: Path) -> None:
        metadata = [
            "Governance",
            "Service Control Policies",
            "lza-core-guardrails-1.json\n\nlza-core-guardrails-2.json",
            "Config desc",
            "Impl\xa0narrative ",
        ]
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-1", "CM-8", metadata=metadata)], tmp_path))

        assert parser.metadata("LZA-X-1") == ControlMetadata(
            foundation="Governance",
            capability="Service Control Policies",
            source_config_files=("lza-core-guardrails-1.json", "lza-core-guardrails-2.json"),
            config_description="Config desc",
            implementation_narrative="Impl narrative",
        )

    def test_implementation_narrative_shortcut(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-1", "CM-8")], tmp_path))
        assert parser.implementation_narrative("LZA-X-1") == "Impl narrative"

    def test_unknown_id_returns_none(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([], tmp_path))
        assert parser.metadata("LZA-UNKNOWN") is None
        assert parser.implementation_narrative("LZA-UNKNOWN") is None

    def test_all_metadata_in_row_order(self, tmp_path: Path) -> None:
        parser = ComplianceMap.from_csv(_make_workbook([_row("LZA-X-2", "CM-8"), _row("LZA-X-1", "CM-8")], tmp_path))
        assert list(parser.all_metadata()) == ["LZA-X-2", "LZA-X-1"]


# ---------------------------------------------------------------------------
# Shipped workbook
# ---------------------------------------------------------------------------


class TestShippedWorkbook:
    def test_shipped_workbook_is_utf8_with_unix_newlines(self) -> None:
        raw = DEFAULT_COMPLIANCE_WORKBOOK_PATH.read_bytes()
        raw.decode("utf-8")
        assert b"\r" not in raw

    def test_default_compliance_map_loads_the_shipped_workbook(self) -> None:
        cmap = default_compliance_map()
        assert cmap.frameworks() == _EXPECTED_SHIPPED_FRAMEWORKS
        assert len(cmap.lza_controls()) == _EXPECTED_SHIPPED_CONTROL_COUNT

    def test_shipped_workbook_contract(self) -> None:
        parser = ComplianceMap.from_csv(DEFAULT_COMPLIANCE_WORKBOOK_PATH)

        assert parser.frameworks() == _EXPECTED_SHIPPED_FRAMEWORKS
        assert len(parser.lza_controls()) == _EXPECTED_SHIPPED_CONTROL_COUNT
        assert parser.resolve("LZA-G-RCP-1", "NIST 800-53 Rev5") == ["AC-3", "AC-3.3", "CM-3.1", "CM-3.8", "CM-5", "CM-5.5", "CM-6", "SA-10"]
        assert parser.metadata("LZA-G-RCP-1") is not None

    def test_shipped_workbook_every_framework_maps_at_least_one_control(self) -> None:
        parser = ComplianceMap.from_csv(DEFAULT_COMPLIANCE_WORKBOOK_PATH)
        empty = [framework for framework in parser.frameworks() if not any(parser.resolve(lza_id, framework) for lza_id in parser.lza_controls())]
        assert empty == []

    def test_shipped_workbook_every_control_has_metadata(self) -> None:
        parser = ComplianceMap.from_csv(DEFAULT_COMPLIANCE_WORKBOOK_PATH)
        incomplete = {
            lza_id: meta
            for lza_id in parser.lza_controls()
            if (meta := parser.metadata(lza_id)) is None
            or not (meta.foundation and meta.capability and meta.source_config_files and meta.config_description and meta.implementation_narrative)
        }
        assert incomplete == {}

    def test_shipped_workbook_descriptions_match_pins(self) -> None:
        """Every LZA ID's meaning is pinned; a workbook bump that redefines an ID must fail here.

        Workbook v1.3.0 reassigned LZA-G-SCP-19/27/37 and LZA-SEC-SSM-4/5 to different
        controls without renaming them, and the tests tagged with those IDs silently
        started claiming coverage for controls they did not exercise. The pin file
        holds a digest of (foundation, capability, description) per ID. When this test
        fails, review every test tagged with each changed ID, then regenerate the
        pins with ``_narrative_pins(default_compliance_map())``.
        """
        parser = ComplianceMap.from_csv(DEFAULT_COMPLIANCE_WORKBOOK_PATH)
        expected_pins: dict[str, str] = json.loads(_NARRATIVE_PINS_PATH.read_text())

        actual_pins = _narrative_pins(parser)

        changed = {
            lza_id: (expected_pins.get(lza_id), actual_pins.get(lza_id))
            for lza_id in expected_pins.keys() | actual_pins.keys()
            if expected_pins.get(lza_id) != actual_pins.get(lza_id)
        }
        assert changed == {}, f"Workbook descriptions changed for {sorted(changed)}; review tests tagged with these IDs before updating the pin file"

    def test_pin_moves_only_for_the_redefined_id(self, tmp_path: Path) -> None:
        """The pin isolates a reassigned ID (the v1.3.0 SCP-37 case) from untouched neighbours."""
        # arrange - two workbooks identical except SCP-37's description is redefined
        before_rows = [
            _row("LZA-G-SCP-36", "CM-8", metadata=["Governance", "SCPs", "f.json", "Restricts modification of IAM roles by tag", "n"]),
            _row(
                "LZA-G-SCP-37",
                "CM-8",
                metadata=["Governance", "SCPs", "f.json", "Restricts the modification of IAM Identity Center delegated admin", "n"],
            ),
        ]
        after_rows = [
            before_rows[0],
            _row(
                "LZA-G-SCP-37",
                "CM-8",
                metadata=["Governance", "SCPs", "f.json", "Enables AgentCore KMS encryption enforcement for Memory resources", "n"],
            ),
        ]
        (tmp_path / "before").mkdir()
        (tmp_path / "after").mkdir()
        before = _narrative_pins(ComplianceMap.from_csv(_make_workbook(before_rows, tmp_path / "before")))
        after = _narrative_pins(ComplianceMap.from_csv(_make_workbook(after_rows, tmp_path / "after")))

        # act
        changed = sorted(lza_id for lza_id in before if before[lza_id] != after[lza_id])

        # assert
        assert changed == ["LZA-G-SCP-37"]

    def test_shipped_workbook_resolves_only_oscal_tokens(self) -> None:
        """Every resolved id becomes an OSCAL finding target-id, which aws-cats rejects unless it is a token."""
        parser = ComplianceMap.from_csv(DEFAULT_COMPLIANCE_WORKBOOK_PATH)

        non_tokens = {
            (framework, control_id)
            for framework in parser.frameworks()
            for lza_id in parser.lza_controls()
            for control_id in parser.resolve(lza_id, framework)
            if _OSCAL_TOKEN.match(control_id) is None
        }

        assert non_tokens == set()

    def test_shipped_workbook_nist_enhancements_use_catalog_convention(self) -> None:
        parser = ComplianceMap.from_csv(DEFAULT_COMPLIANCE_WORKBOOK_PATH)

        assert parser.resolve("LZA-G-OM-1", "NIST 800-53 Rev5") == ["AC-2.1", "CM-8", "PL-9", "SA-8.14", "SC-2", "SC-2.1"]

    def test_shipped_workbook_new_framework_spellings(self) -> None:
        """One resolved cell per normalization rule the 1.4.0 workbook introduced."""
        parser = ComplianceMap.from_csv(DEFAULT_COMPLIANCE_WORKBOOK_PATH)

        assert parser.resolve("LZA-G-OM-1", "ISM New Zealand") == ["CID-5820"]
        assert parser.resolve("LZA-G-OM-1", "ACN - Level 2") == [
            "ID.AM-02.1_O",
            "ID.AM-02.2_O",
            "ID.AM-02.3_O",
            "PR.PT-05.1_O",
            "PR.PT-05.2_O",
            "PR.PT-05.3_O",
            "PR.PT-05.4_C",
        ]
        assert parser.resolve("LZA-G-OM-1", "CCM (v4.1.0)") == ["CCC-04", "CCC-06", "IAM-06", "IAM-09", "I-S-06"]
        assert parser.resolve("LZA-G-OM-1", "PCI-DSS v4.0") == [
            "pci-dss-v4-0-7.2.1",
            "pci-dss-v4-0-7.3.1",
            "pci-dss-v4-0-12.5.1",
            "pci-dss-v4-0-12.5.2",
        ]
        assert parser.resolve("LZA-SEC-Config-24", "PCI-DSS v4.0") == []
