from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_GIST = Path("public/data/gist-plants.v1.json")
DEFAULT_MEASURE = Path(
    "tmp/source-packages/eu-steel-measure/derived/eu-steel-measure-2026-1457.v1.json"
)
DEFAULT_BILATERAL = Path(
    "tmp/source-packages/eu-steel-measure/derived/eu-steel-bilateral-2026-1930.v1.json"
)
DEFAULT_MAPPING = Path("config/eu-steel-measure-product-map.v1.json")
DEFAULT_OUTPUT = Path(
    "tmp/source-packages/eu-steel-measure/review/gist-eu-steel-measure-profile.v1.json"
)
SCHEMA = "steel-exposure-atlas/gist-eu-steel-measure-profile-v1.1"

EU_COUNTRIES = {
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Czechia",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Ireland",
    "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands", "Poland",
    "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden",
}
EEA_EXEMPT_NON_EU = {"Iceland", "Liechtenstein", "Norway"}
COUNTRY_ALIASES = {
    "Turkey": "Türkiye",
    "Türkiye": "Türkiye",
    "South Korea": "Korea",
    "Republic of Korea": "Korea",
    "Korea, Republic of": "Korea",
    "Vietnam": "Viet Nam",
    "Viet Nam": "Viet Nam",
    "United States of America": "United States",
    "UAE": "United Arab Emirates",
}


def _clean(value: object) -> str:
    return " ".join(str(value or "").split())


def _product_values(plant: dict[str, object]) -> list[str]:
    value = plant.get("steel_products")
    if isinstance(value, dict):
        values = value.get("values")
        if isinstance(values, list):
            return [_clean(item) for item in values if _clean(item)]
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)]
    raise ValueError(f"Plant {_clean(plant.get('plant_id'))!r} has invalid steel_products.")


def _country_for_measure(country: str) -> str:
    return COUNTRY_ALIASES.get(country, country)


def _bilateral_country_set(bilateral: dict[str, object] | None) -> set[str]:
    if bilateral is None:
        return set()
    countries = bilateral.get("countries")
    if not isinstance(countries, list):
        raise ValueError("EU bilateral safeguard payload has no countries list.")
    return {_clean(country) for country in countries if _clean(country)}


def build_profile(
    gist: dict[str, object],
    measure: dict[str, object],
    mapping: dict[str, object],
    bilateral: dict[str, object] | None = None,
) -> dict[str, object]:
    plants = gist.get("plants")
    products = measure.get("products")
    allocations = measure.get("allocations")
    mappings = mapping.get("mappings")
    if not isinstance(plants, list):
        raise ValueError("GIST payload has no plants list.")
    if not isinstance(products, list) or not isinstance(allocations, list):
        raise ValueError("EU steel-measure payload is missing products or allocations.")
    if not isinstance(mappings, dict):
        raise ValueError("EU steel product mapping has no mappings object.")

    bilateral_countries = _bilateral_country_set(bilateral)
    product_meta = {
        _clean(item.get("product_number")): item
        for item in products
        if isinstance(item, dict) and _clean(item.get("product_number"))
    }
    named_allocations: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    generic_allocations = {"FTA Quota – CSQ", "Other countries", "FTA Quota – Other countries"}
    for item in allocations:
        if not isinstance(item, dict):
            continue
        number = _clean(item.get("product_number"))
        allocation = _clean(item.get("allocation"))
        if number and allocation and allocation not in generic_allocations:
            named_allocations[(number, allocation)].append(item)

    rows: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    mapped_label_counts: Counter[str] = Counter()
    named_origin_candidate_plants: set[str] = set()
    residual_review_candidate_plants: set[str] = set()
    bilateral_origin_plants: set[str] = set()
    bilateral_candidate_plants: set[str] = set()

    for raw_plant in plants:
        if not isinstance(raw_plant, dict):
            continue
        plant_id = _clean(raw_plant.get("plant_id"))
        plant_name = _clean(raw_plant.get("plant_name"))
        country = _clean(raw_plant.get("country_area"))
        if not plant_id or not country:
            raise ValueError("GIST plant is missing plant_id or country_area.")

        labels = _product_values(raw_plant)
        mapped_products: list[dict[str, object]] = []
        for label in labels:
            rule = mappings.get(label.casefold())
            if not isinstance(rule, dict):
                mapped_products.append(
                    {
                        "gist_product": label,
                        "state": "no_mapping_rule",
                        "product_numbers": [],
                    }
                )
                continue
            state = _clean(rule.get("state"))
            numbers = rule.get("product_numbers")
            if not isinstance(numbers, list):
                raise ValueError(f"Mapping for {label!r} has no product_numbers list.")
            clean_numbers = [_clean(value) for value in numbers if _clean(value)]
            unknown = [value for value in clean_numbers if value not in product_meta]
            if unknown:
                raise ValueError(f"Mapping for {label!r} references unknown product numbers: {unknown}")
            mapped_products.append(
                {
                    "gist_product": label,
                    "state": state,
                    "family": _clean(rule.get("family")),
                    "product_numbers": clean_numbers,
                    "note": _clean(rule.get("note")),
                }
            )
            if state in {"family_candidate", "ambiguous_family_candidate"}:
                mapped_label_counts[label.casefold()] += 1

        measure_country = _country_for_measure(country)
        if country in EU_COUNTRIES:
            scenario_state = "not_applicable_intra_eu_origin"
            legal_route = "intra_eu_origin"
            candidate_details: list[dict[str, object]] = []
        elif country in EEA_EXEMPT_NON_EU:
            scenario_state = "quota_duty_exempt_eea_origin"
            legal_route = "eea_exempt_origin"
            candidate_details = []
        else:
            legal_route = (
                "bilateral_safeguard_2026_1930"
                if measure_country in bilateral_countries
                else "steel_regulation_2026_1384"
            )
            if legal_route == "bilateral_safeguard_2026_1930":
                bilateral_origin_plants.add(plant_id)

            candidate_details = []
            for mapped in mapped_products:
                if mapped["state"] not in {"family_candidate", "ambiguous_family_candidate"}:
                    continue
                for number in mapped["product_numbers"]:  # type: ignore[union-attr]
                    meta = product_meta[number]
                    origin_rows = named_allocations.get((number, measure_country), [])
                    candidate_details.append(
                        {
                            "gist_product": mapped["gist_product"],
                            "mapping_state": mapped["state"],
                            "product_number": number,
                            "product_category": meta.get("product_category"),
                            "cn_codes": meta.get("cn_codes", []),
                            "taric_codes": meta.get("taric_codes", []),
                            "legal_route": legal_route,
                            "named_origin_quota_rows": [
                                {
                                    "allocation": item.get("allocation"),
                                    "total_yearly_volume_tonnes": item.get("total_yearly_volume_tonnes"),
                                    "quarterly_volume_tonnes": item.get("quarterly_volume_tonnes"),
                                    "additional_duty_rate_pct": item.get("additional_duty_rate_pct"),
                                    "order_number": item.get("order_number"),
                                }
                                for item in origin_rows
                            ],
                        }
                    )
            if candidate_details:
                if legal_route == "bilateral_safeguard_2026_1930":
                    bilateral_candidate_plants.add(plant_id)
                if any(item["named_origin_quota_rows"] for item in candidate_details):
                    scenario_state = "candidate_with_named_origin_quota_row"
                    named_origin_candidate_plants.add(plant_id)
                else:
                    scenario_state = "candidate_requires_residual_quota_review"
                    residual_review_candidate_plants.add(plant_id)
            else:
                scenario_state = "no_supported_product_family_candidate"

        counts[scenario_state] += 1
        rows.append(
            {
                "plant_id": plant_id,
                "plant_name": plant_name,
                "country_area": country,
                "measure_country": measure_country,
                "legal_route": legal_route,
                "scenario_state": scenario_state,
                "gist_products": labels,
                "product_mapping": mapped_products,
                "measure_candidates": candidate_details,
            }
        )

    rows.sort(key=lambda item: str(item["plant_id"]))
    measure_meta = measure.get("meta") if isinstance(measure.get("meta"), dict) else {}
    bilateral_meta = bilateral.get("meta") if isinstance(bilateral, dict) and isinstance(bilateral.get("meta"), dict) else {}
    return {
        "meta": {
            "schema": SCHEMA,
            "gist_schema": (gist.get("meta") or {}).get("schema")
            if isinstance(gist.get("meta"), dict)
            else None,
            "measure_schema": measure_meta.get("schema"),
            "measure_snapshot_sha256": measure_meta.get("raw_sha256"),
            "bilateral_schema": bilateral_meta.get("schema"),
            "bilateral_snapshot_sha256": bilateral_meta.get("raw_sha256"),
            "mapping_schema": mapping.get("schema"),
            "scenario": "hypothetical import of plant-listed steel products into the EU",
            "interpretation": (
                "Profile only. GIST product-family mapping is review evidence for an EU-import scenario. "
                "Current legal route is retained separately for the Steel Regulation and bilateral safeguards."
            ),
        },
        "counts": {
            "gist_plants": len(rows),
            "not_applicable_intra_eu_origin": counts["not_applicable_intra_eu_origin"],
            "quota_duty_exempt_eea_origin": counts["quota_duty_exempt_eea_origin"],
            "candidate_with_named_origin_quota_row": counts["candidate_with_named_origin_quota_row"],
            "candidate_requires_residual_quota_review": counts[
                "candidate_requires_residual_quota_review"
            ],
            "no_supported_product_family_candidate": counts[
                "no_supported_product_family_candidate"
            ],
            "plants_with_any_trade_measure_candidate": (
                len(named_origin_candidate_plants | residual_review_candidate_plants)
            ),
            "plants_with_named_origin_quota_candidate": len(named_origin_candidate_plants),
            "plants_requiring_residual_quota_review": len(residual_review_candidate_plants),
            "plants_from_bilateral_safeguard_origins": len(bilateral_origin_plants),
            "candidate_plants_from_bilateral_safeguard_origins": len(bilateral_candidate_plants),
            "mapped_product_label_occurrences": dict(sorted(mapped_label_counts.items())),
        },
        "plants": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Profile GIST plant product/origin context against the pinned EU 2026 steel import measure. "
            "This is a scenario profile for procurement follow-up."
        )
    )
    parser.add_argument("--gist", type=Path, default=DEFAULT_GIST)
    parser.add_argument("--measure", type=Path, default=DEFAULT_MEASURE)
    parser.add_argument("--bilateral", type=Path, default=DEFAULT_BILATERAL)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    gist = json.loads(args.gist.read_text(encoding="utf-8"))
    measure = json.loads(args.measure.read_text(encoding="utf-8"))
    bilateral = json.loads(args.bilateral.read_text(encoding="utf-8"))
    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    payload = build_profile(gist, measure, mapping, bilateral)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = payload["counts"]
    print(f"GIST plants: {counts['gist_plants']}")
    print(f"EU-origin plants: {counts['not_applicable_intra_eu_origin']}")
    print(f"EEA exempt non-EU origins: {counts['quota_duty_exempt_eea_origin']}")
    print(f"plants with any product-family candidate: {counts['plants_with_any_trade_measure_candidate']}")
    print(f"  with named origin quota row: {counts['plants_with_named_origin_quota_candidate']}")
    print(f"  residual quota review needed: {counts['plants_requiring_residual_quota_review']}")
    print(f"plants from bilateral safeguard origins: {counts['plants_from_bilateral_safeguard_origins']}")
    print(
        "  with product-family candidate: "
        f"{counts['candidate_plants_from_bilateral_safeguard_origins']}"
    )
    print(f"no supported product-family candidate: {counts['no_supported_product_family_candidate']}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
