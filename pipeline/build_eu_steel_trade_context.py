from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_PROFILE = Path(
    "tmp/source-packages/eu-steel-measure/review/gist-eu-steel-measure-profile.v1.json"
)
DEFAULT_OUTPUT = Path("public/data/eu-steel-trade-context.v1.json")
SCHEMA = "steel-exposure-atlas/eu-steel-trade-context-v1.1"
EXPECTED_MEASURE_SHA256 = "B869A4BB8C4E4F7AE320B4CE4A117A33B05CADEEDF1C9DF106845EBCA9D9B21B"
EXPECTED_BILATERAL_SHA256 = "5F0214CD0FC9FC85A114B9EC485E2D6887F3F2137BD177EE357CC00FE2BB32BE"
CANDIDATE_STATES = {
    "candidate_with_named_origin_quota_row",
    "candidate_requires_residual_quota_review",
}


def _clean(value: object) -> str:
    return " ".join(str(value or "").split())


def _validate_sources(meta: dict[str, object]) -> None:
    measure = _clean(meta.get("measure_snapshot_sha256")).upper()
    bilateral = _clean(meta.get("bilateral_snapshot_sha256")).upper()
    if measure != EXPECTED_MEASURE_SHA256:
        raise ValueError(
            "EU steel measure snapshot mismatch: "
            f"expected {EXPECTED_MEASURE_SHA256}, got {measure or 'missing'}."
        )
    if bilateral != EXPECTED_BILATERAL_SHA256:
        raise ValueError(
            "EU bilateral safeguard snapshot mismatch: "
            f"expected {EXPECTED_BILATERAL_SHA256}, got {bilateral or 'missing'}."
        )


def build_context(profile: dict[str, object]) -> dict[str, object]:
    plants = profile.get("plants")
    meta = profile.get("meta")
    if not isinstance(plants, list):
        raise ValueError("EU steel-measure profile has no plants list.")
    if not isinstance(meta, dict):
        raise ValueError("EU steel-measure profile has no meta object.")
    _validate_sources(meta)

    context_rows: list[dict[str, object]] = []
    for raw in plants:
        if not isinstance(raw, dict):
            continue
        state = _clean(raw.get("scenario_state"))
        if state not in CANDIDATE_STATES:
            continue

        candidates = raw.get("measure_candidates")
        if not isinstance(candidates, list) or not candidates:
            raise ValueError(f"Candidate plant {_clean(raw.get('plant_id'))!r} has no measure candidates.")

        product_families: list[str] = []
        mapping_states: set[str] = set()
        product_numbers: set[str] = set()
        order_numbers: set[str] = set()
        duty_rates: set[float] = set()

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            family = _clean(candidate.get("product_category"))
            if family and family not in product_families:
                product_families.append(family)
            mapping_state = _clean(candidate.get("mapping_state"))
            if mapping_state:
                mapping_states.add(mapping_state)
            number = _clean(candidate.get("product_number"))
            if number:
                product_numbers.add(number)
            quota_rows = candidate.get("named_origin_quota_rows")
            if isinstance(quota_rows, list):
                for quota in quota_rows:
                    if not isinstance(quota, dict):
                        continue
                    order = _clean(quota.get("order_number"))
                    if order:
                        order_numbers.add(order)
                    rate = quota.get("additional_duty_rate_pct")
                    if isinstance(rate, (int, float)):
                        duty_rates.add(float(rate))

        if not duty_rates:
            duty_rates.add(50.0)
        if duty_rates != {50.0}:
            raise ValueError(
                f"Unexpected duty rates for {_clean(raw.get('plant_id'))}: {sorted(duty_rates)}"
            )

        has_named = state == "candidate_with_named_origin_quota_row"
        mapping_quality = (
            "family_candidate"
            if mapping_states == {"family_candidate"}
            else "family_requires_confirmation"
        )
        context_rows.append(
            {
                "plant_id": _clean(raw.get("plant_id")),
                "plant_name": _clean(raw.get("plant_name")),
                "origin": _clean(raw.get("country_area")),
                "measure_origin": _clean(raw.get("measure_country")),
                "scenario": "if imported into the EU",
                "legal_route": _clean(raw.get("legal_route")),
                "product_family_state": mapping_quality,
                "product_families": product_families,
                "candidate_product_numbers": sorted(product_numbers),
                "quota_route": "origin_specific" if has_named else "pooled_or_residual",
                "customs_order_numbers": sorted(order_numbers),
                "additional_duty_if_quota_exhausted_pct": 50.0,
            }
        )

    context_rows.sort(key=lambda item: str(item["plant_id"]))
    named = sum(1 for row in context_rows if row["quota_route"] == "origin_specific")
    pooled = len(context_rows) - named
    return {
        "meta": {
            "schema": SCHEMA,
            "scenario": "hypothetical import into the EU",
            "profile_schema": meta.get("schema"),
            "sources": {
                "commission_implementing_regulation_2026_1457": {
                    "sha256": EXPECTED_MEASURE_SHA256,
                    "source_url": "https://eur-lex.europa.eu/eli/reg_impl/2026/1457/oj/eng",
                },
                "commission_implementing_regulation_2026_1930": {
                    "sha256": EXPECTED_BILATERAL_SHA256,
                    "source_url": "https://eur-lex.europa.eu/eli/reg_impl/2026/1930/oj/eng",
                },
            },
            "publication_state": "approved minimal derived public context",
            "ui_principle": "evidence -> relationship -> meaning",
            "counts": {
                "plants_with_context": len(context_rows),
                "origin_specific_quota_context": named,
                "pooled_or_residual_quota_context": pooled,
            },
        },
        "plants": context_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the reviewed public EU steel import scenario context from the pinned profile."
    )
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    payload = build_context(profile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = payload["meta"]["counts"]
    print(f"plants with EU import context: {counts['plants_with_context']}")
    print(f"  origin-specific quota context: {counts['origin_specific_quota_context']}")
    print(f"  pooled/residual quota context: {counts['pooled_or_residual_quota_context']}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
