from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

try:
    from pipeline.build_reviewed_ofac_sanctions_matches import build_reviewed_matches
    from pipeline.profile_gist_ofac_candidates import build_profile
except ModuleNotFoundError:
    from build_reviewed_ofac_sanctions_matches import build_reviewed_matches  # type: ignore[no-redef]
    from profile_gist_ofac_candidates import build_profile  # type: ignore[no-redef]

DEFAULT_GIST = Path("public/data/gist-plants.v1.json")
DEFAULT_SANCTIONS = Path("tmp/source-packages/ofac/derived/ofac-sanctions-entities.v1.json")
DEFAULT_REGISTRY = Path("config/reviewed-entity-links.v1.json")
DEFAULT_DESIGNATIONS = Path("config/ofac-designation-context.v1.json")
DEFAULT_OUTPUT = Path("public/data/ofac-sanctions-owner-status.v1.json")
SCHEMA = "steel-exposure-atlas/ofac-sanctions-owner-status-v1.0"
DESIGNATION_SCHEMA = "steel-exposure-atlas/ofac-designation-context-v1.0"


def _clean(value: object) -> str:
    return str(value or "").strip()


def _designation_map(payload: dict[str, object] | None) -> dict[str, dict[str, str]]:
    if payload is None:
        return {}
    if payload.get("schema") != DESIGNATION_SCHEMA:
        raise ValueError("Unexpected OFAC designation-context schema.")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("OFAC designation context has no records list.")

    result: dict[str, dict[str, str]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("OFAC designation-context record must be an object.")
        entity_id = _clean(record.get("entity_id"))
        if not entity_id:
            raise ValueError("OFAC designation-context record has no entity_id.")
        if entity_id in result:
            raise ValueError(f"Duplicate OFAC designation context for {entity_id}.")
        listed_since = _clean(record.get("listed_since"))
        source_url = _clean(record.get("source_url"))
        if not listed_since or not source_url.startswith("https://ofac.treasury.gov/"):
            raise ValueError(f"OFAC designation context for {entity_id} is incomplete.")
        result[entity_id] = {
            "listed_since": listed_since,
            "designation_action": _clean(record.get("designation_action")),
            "designation_summary": _clean(record.get("designation_summary")),
            "designation_source_url": source_url,
        }
    return result


def build_status_layer(
    gist: dict[str, object],
    sanctions: dict[str, object],
    registry: dict[str, object],
    designation_context: dict[str, object] | None = None,
) -> dict[str, object]:
    candidate_profile = build_profile(gist, sanctions)
    reviewed = build_reviewed_matches(gist, sanctions, registry)
    designation_by_entity = _designation_map(designation_context)

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

    candidate_company_ids = {
        _clean(item.get("owner_gem_entity_id"))
        for item in candidate_rows
        if isinstance(item, dict)
    }
    unknown_reviewed = set(reviewed_by_company) - candidate_company_ids
    if unknown_reviewed:
        raise ValueError(
            "Reviewed OFAC match references owner outside screened population: "
            + ", ".join(sorted(unknown_reviewed))
        )

    statuses: list[dict[str, object]] = []
    counts: Counter[str] = Counter()

    for candidate in candidate_rows:
        if not isinstance(candidate, dict):
            raise ValueError("Candidate row must be an object.")
        company_id = _clean(candidate.get("owner_gem_entity_id"))
        if not company_id:
            raise ValueError("Candidate row has no owner_gem_entity_id.")

        candidate_entity_ids = candidate.get("candidate_ofac_entity_ids")
        if not isinstance(candidate_entity_ids, list):
            raise ValueError(f"Candidate row {company_id} has no candidate_ofac_entity_ids list.")

        reviewed_matches = reviewed_by_company.get(company_id, [])
        if reviewed_matches:
            state = "direct_list_match"
            public_matches: list[dict[str, object]] = []
            for item in reviewed_matches:
                entity_id = _clean(item.get("matched_entity_id"))
                source_list = _clean(item.get("source_list"))
                match: dict[str, object] = {
                    "matched_entity_id": entity_id,
                    "source_list": source_list,
                    "ofac_uid": _clean(item.get("ofac_uid")),
                    "programmes": item.get("programmes", []),
                    "resolution_id": _clean(item.get("resolution_id")),
                    "reviewed_at": _clean(item.get("reviewed_at")),
                }
                designation = designation_by_entity.get(entity_id)
                if designation:
                    match.update(designation)
                elif designation_context is not None and source_list == "SDN":
                    raise ValueError(
                        f"Reviewed SDN match {entity_id} has no designation context."
                    )
                public_matches.append(match)

            status = {
                "company_id": company_id,
                "state": state,
                "identity_resolution": "confirmed",
                "reviewed_matches": public_matches,
            }
        elif candidate_entity_ids:
            state = "review_required"
            status = {
                "company_id": company_id,
                "state": state,
                "identity_resolution": "review_required",
                "candidate_count": len(candidate_entity_ids),
                "candidate_basis": _clean(candidate.get("state")),
                "candidate_source_lists": candidate.get("candidate_source_lists", []),
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
        raise ValueError("OFAC sanctions inputs are missing metadata.")

    snapshots = reviewed_meta.get("source_snapshot_sha256")
    if not isinstance(snapshots, dict):
        raise ValueError("Reviewed OFAC match package has no source snapshot hashes.")

    files = sanctions_meta.get("files")
    if not isinstance(files, dict):
        raise ValueError("OFAC sanctions subset has no files metadata.")

    def publish_date(key: str) -> str:
        item = files.get(key)
        return _clean(item.get("publish_date")) if isinstance(item, dict) else ""

    return {
        "meta": {
            "schema": SCHEMA,
            "source": "ofac",
            "publisher": "U.S. Department of the Treasury, Office of Foreign Assets Control",
            "datasets": [
                "Specially Designated Nationals and Blocked Persons List",
                "Consolidated Non-SDN Sanctions List",
            ],
            "source_snapshot_sha256": snapshots,
            "source_publish_dates": {
                "SDN": publish_date("sdn"),
                "Consolidated Non-SDN": publish_date("consolidated_non_sdn"),
            },
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
                "screen found no direct OFAC list match for the screened GIST owner identity. "
                "It is not sanctions clearance and does not address ownership/control effects."
            ),
            "scope": (
                "Company-level GIST owner screening against pinned OFAC SDN and Consolidated "
                "Non-SDN Entity snapshots. No separate plant-level sanctions finding is emitted."
            ),
        },
        "statuses": statuses,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build the categorical OFAC sanctions context layer for screened GIST owner identities."
        )
    )
    parser.add_argument("--gist", type=Path, default=DEFAULT_GIST)
    parser.add_argument("--sanctions", type=Path, default=DEFAULT_SANCTIONS)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--designations", type=Path, default=DEFAULT_DESIGNATIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    gist = json.loads(args.gist.read_text(encoding="utf-8"))
    sanctions = json.loads(args.sanctions.read_text(encoding="utf-8"))
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    designations = json.loads(args.designations.read_text(encoding="utf-8"))
    payload = build_status_layer(gist, sanctions, registry, designations)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    counts = payload["meta"]["counts"]
    print(f"OFAC snapshot SHA-256: {payload['meta']['source_snapshot_sha256']}")
    print(f"screened owner identities: {payload['meta']['screened_owner_identities']}")
    print(f"direct list match: {counts['direct_list_match']}")
    print(f"review required: {counts['review_required']}")
    print(
        "no direct list match in snapshot: "
        f"{counts['no_direct_list_match_in_snapshot']}"
    )
    print("designation dates: attached to reviewed SDN matches")
    print("sanctions percentages: not defined")
    print("plant-level sanctions findings: not emitted")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
