from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

try:
    from pipeline.build_reviewed_eu_sanctions_matches import build_reviewed_matches
    from pipeline.profile_gist_eu_sanctions_candidates import build_profile
except ModuleNotFoundError:
    from build_reviewed_eu_sanctions_matches import build_reviewed_matches  # type: ignore[no-redef]
    from profile_gist_eu_sanctions_candidates import build_profile  # type: ignore[no-redef]

DEFAULT_GIST = Path("public/data/gist-plants.v1.json")
DEFAULT_SANCTIONS = Path(
    "tmp/source-packages/eu-sanctions/derived/eu-sanctions-enterprises.v1.json"
)
DEFAULT_REGISTRY = Path("config/reviewed-entity-links.v1.json")
DEFAULT_OUTPUT = Path("public/data/eu-sanctions-owner-status.v1.json")
SCHEMA = "steel-exposure-atlas/eu-sanctions-owner-status-v1.0"


def _clean(value: object) -> str:
    return str(value or "").strip()


def build_status_layer(
    gist: dict[str, object],
    sanctions: dict[str, object],
    registry: dict[str, object],
) -> dict[str, object]:
    """Build the public-safe EU sanctions screening state for usable GIST owner identities.

    The layer publishes categorical evidence states only. It never emits a sanctions
    percentage, probability, risk score or plant-level sanctions finding.
    """
    candidate_profile = build_profile(gist, sanctions)
    reviewed = build_reviewed_matches(gist, sanctions, registry)

    candidate_rows = candidate_profile.get("candidates")
    reviewed_rows = reviewed.get("matches")
    if not isinstance(candidate_rows, list):
        raise ValueError("Candidate profile has no candidates list.")
    if not isinstance(reviewed_rows, list):
        raise ValueError("Reviewed match package has no matches list.")

    reviewed_by_company: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in reviewed_rows:
        if not isinstance(item, dict):
            raise ValueError("Reviewed match entry must be an object.")
        company_id = _clean(item.get("company_id"))
        if not company_id:
            raise ValueError("Reviewed match has no company_id.")
        reviewed_by_company[company_id].append(item)

    statuses: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    candidate_company_ids = {
        _clean(item.get("owner_gem_entity_id"))
        for item in candidate_rows
        if isinstance(item, dict)
    }
    unknown_reviewed = set(reviewed_by_company) - candidate_company_ids
    if unknown_reviewed:
        raise ValueError(
            "Reviewed match references owner outside screened population: "
            + ", ".join(sorted(unknown_reviewed))
        )

    for candidate in candidate_rows:
        if not isinstance(candidate, dict):
            raise ValueError("Candidate row must be an object.")
        company_id = _clean(candidate.get("owner_gem_entity_id"))
        if not company_id:
            raise ValueError("Candidate row has no owner_gem_entity_id.")

        reviewed_matches = reviewed_by_company.get(company_id, [])
        candidate_entity_ids = candidate.get("candidate_eu_entity_ids")
        if not isinstance(candidate_entity_ids, list):
            raise ValueError(f"Candidate row {company_id} has no candidate_eu_entity_ids list.")

        if reviewed_matches:
            state = "direct_list_match"
            status: dict[str, object] = {
                "company_id": company_id,
                "state": state,
                "identity_resolution": "confirmed",
                "reviewed_matches": [
                    {
                        "matched_entity_id": _clean(item.get("matched_entity_id")),
                        "eu_reference": _clean(item.get("eu_reference")),
                        "resolution_id": _clean(item.get("resolution_id")),
                        "reviewed_at": _clean(item.get("reviewed_at")),
                    }
                    for item in reviewed_matches
                ],
            }
        elif candidate_entity_ids:
            state = "review_required"
            status = {
                "company_id": company_id,
                "state": state,
                "identity_resolution": "review_required",
                "candidate_count": len(candidate_entity_ids),
                "candidate_basis": _clean(candidate.get("state")),
            }
        else:
            state = "no_direct_list_match_in_snapshot"
            status = {
                "company_id": company_id,
                "state": state,
                "identity_resolution": "none",
            }

        counts[state] += 1
        statuses.append(status)

    statuses.sort(key=lambda item: str(item["company_id"]))

    sanctions_meta = sanctions.get("meta")
    reviewed_meta = reviewed.get("meta")
    if not isinstance(sanctions_meta, dict) or not isinstance(reviewed_meta, dict):
        raise ValueError("Sanctions inputs are missing metadata.")

    source_hash = _clean(reviewed_meta.get("source_snapshot_sha256"))
    if not source_hash:
        raise ValueError("Reviewed match package has no source snapshot SHA-256.")

    return {
        "meta": {
            "schema": SCHEMA,
            "source": "eu_financial_sanctions",
            "publisher": "European Commission",
            "dataset": "Consolidated Financial Sanctions File 1.1",
            "source_snapshot_sha256": source_hash,
            "source_file_generation_dates": sanctions_meta.get("file_generation_dates", []),
            "screened_owner_identities": len(statuses),
            "counts": {
                "direct_list_match": counts["direct_list_match"],
                "review_required": counts["review_required"],
                "no_direct_list_match_in_snapshot": counts[
                    "no_direct_list_match_in_snapshot"
                ],
            },
            "display_semantics": (
                "Categorical evidence state only. No sanctions percentage, probability, "
                "risk score or red/green verdict is defined by this dataset."
            ),
            "negative_result_boundary": (
                "No direct list match in this snapshot means only that the deterministic "
                "screen found no direct list match for the screened GIST owner identity. "
                "It is not sanctions clearance."
            ),
            "scope": (
                "Company-level GIST owner screening against the pinned EU sanctions "
                "enterprise snapshot. No plant-level sanctions finding is emitted."
            ),
        },
        "statuses": statuses,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build the categorical EU sanctions context layer for screened GIST owner "
            "identities. The default output is the local public-data artifact used by "
            "the relational homepage."
        )
    )
    parser.add_argument("--gist", type=Path, default=DEFAULT_GIST)
    parser.add_argument("--sanctions", type=Path, default=DEFAULT_SANCTIONS)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    gist = json.loads(args.gist.read_text(encoding="utf-8"))
    sanctions = json.loads(args.sanctions.read_text(encoding="utf-8"))
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    payload = build_status_layer(gist, sanctions, registry)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    counts = payload["meta"]["counts"]
    print(f"EU snapshot SHA-256: {payload['meta']['source_snapshot_sha256']}")
    print(f"screened owner identities: {payload['meta']['screened_owner_identities']}")
    print(f"direct list match: {counts['direct_list_match']}")
    print(f"review required: {counts['review_required']}")
    print(
        "no direct list match in snapshot: "
        f"{counts['no_direct_list_match_in_snapshot']}"
    )
    print("sanctions percentages: not defined")
    print("plant-level sanctions findings: not emitted")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
