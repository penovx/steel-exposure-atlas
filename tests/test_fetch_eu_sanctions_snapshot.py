from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from pipeline.fetch_eu_sanctions_snapshot import (
    DATASET,
    LICENCE,
    META_SCHEMA,
    PUBLISHER,
    SOURCE_URL,
    build_metadata,
    profile_csv,
    write_snapshot,
)


CSV = """fileGenerationDate;Entity_LogicalId;Entity_SubjectType_ClassificationCode;Entity_EU_ReferenceNumber;NameAlias_WholeName\n2026-09-15;100;person;EU.100.1;Example Person\n2026-09-15;100;person;EU.100.1;Person Alias\n2026-09-15;200;enterprise;EU.200.1;Example Steel Holdings\n2026-09-15;200;enterprise;EU.200.1;Example Steel Holdings Ltd\n2026-09-15;300;enterprise;EU.300.1;Example Metals Group\n"""


class EuSanctionsSnapshotTests(unittest.TestCase):
    def test_profile_uses_semicolon_csv_and_counts_subject_types(self) -> None:
        raw = CSV.encode("utf-8")
        profile = profile_csv(raw)

        self.assertEqual(profile["row_count"], 5)
        self.assertEqual(profile["unique_entity_logical_ids"], 3)
        self.assertEqual(profile["column_count"], 5)
        self.assertEqual(
            profile["subject_type_row_counts"],
            {"enterprise": 3, "person": 2},
        )
        self.assertEqual(profile["file_generation_dates"], {"2026-09-15": 5})

    def test_metadata_keeps_provenance_and_publication_boundaries(self) -> None:
        raw = CSV.encode("utf-8")
        metadata = build_metadata(
            raw,
            retrieved_at="2026-09-15T21:45:00+00:00",
            transport={"content_type": "text/csv", "final_url": SOURCE_URL},
        )

        self.assertEqual(metadata["schema"], META_SCHEMA)
        self.assertEqual(metadata["publisher"], PUBLISHER)
        self.assertEqual(metadata["dataset"], DATASET)
        self.assertEqual(metadata["source_url"], SOURCE_URL)
        self.assertEqual(metadata["licence"], LICENCE)
        self.assertEqual(
            metadata["raw_sha256"], hashlib.sha256(raw).hexdigest().upper()
        )
        self.assertIn("local-only", metadata["raw_publication_state"])
        self.assertIn("snapshot notice check", metadata["derived_publication_state"])

    def test_write_snapshot_keeps_raw_and_review_metadata_local_paths(self) -> None:
        raw = CSV.encode("utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_path = root / "raw" / "snapshot.csv"
            meta_path = root / "review" / "snapshot.meta.json"

            metadata = write_snapshot(
                raw,
                raw_output=raw_path,
                meta_output=meta_path,
                retrieved_at="2026-09-15T21:45:00+00:00",
            )

            self.assertEqual(raw_path.read_bytes(), raw)
            persisted = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["raw_sha256"], metadata["raw_sha256"])
            self.assertEqual(persisted["profile"]["row_count"], 5)

    def test_missing_required_header_is_rejected(self) -> None:
        malformed = (
            "fileGenerationDate;Entity_LogicalId\n"
            "2026-09-15;100\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(
            ValueError, "Entity_SubjectType_ClassificationCode"
        ):
            profile_csv(malformed)

    def test_empty_csv_is_rejected(self) -> None:
        empty = (
            "fileGenerationDate;Entity_LogicalId;"
            "Entity_SubjectType_ClassificationCode\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "no data rows"):
            profile_csv(empty)


if __name__ == "__main__":
    unittest.main()
