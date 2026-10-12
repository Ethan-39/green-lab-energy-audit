"""Estimate and rank fictional laboratory asset energy, cost, and carbon."""

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
INVENTORY_PATH = DATA_DIR / "assets.csv"
DEFAULT_PRICE_YUAN_PER_KWH = 0.72
DEFAULT_EMISSION_FACTOR_KG_PER_KWH = 0.536


def write_example(path=INVENTORY_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"asset_id": "LAB-01", "asset_name": "示例超低温冰箱", "category": "冷藏", "rated_kw": "0.72", "annual_hours": "6800", "load_factor": "0.55"},
        {"asset_id": "LAB-02", "asset_name": "示例通风柜", "category": "通风", "rated_kw": "0.45", "annual_hours": "4200", "load_factor": "0.70"},
        {"asset_id": "LAB-03", "asset_name": "示例培养箱", "category": "培养", "rated_kw": "0.36", "annual_hours": "5200", "load_factor": "0.48"},
        {"asset_id": "LAB-04", "asset_name": "示例离心机", "category": "分析", "rated_kw": "1.10", "annual_hours": "360", "load_factor": "0.35"},
        {"asset_id": "LAB-05", "asset_name": "示例显微镜照明", "category": "分析", "rated_kw": "0.08", "annual_hours": "1800", "load_factor": "0.65"},
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_inventory(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def estimate_assets(rows, price_yuan_per_kwh, emission_factor_kg_per_kwh):
    if price_yuan_per_kwh < 0 or emission_factor_kg_per_kwh < 0:
        raise ValueError("price and emission factor must be non-negative")
    estimates = []
    ids = set()
    for line_number, row in enumerate(rows, start=2):
        asset_id = (row.get("asset_id") or "").strip()
        asset_name = (row.get("asset_name") or "").strip()
        if not asset_id or not asset_name:
            raise ValueError(f"line {line_number}: asset_id and asset_name are required")
        if asset_id in ids:
            raise ValueError(f"line {line_number}: duplicate asset_id {asset_id}")
        ids.add(asset_id)
        try:
            rated_kw = float(row["rated_kw"])
            annual_hours = float(row["annual_hours"])
            load_factor = float(row["load_factor"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"line {line_number}: rated_kw, annual_hours, and load_factor must be numeric") from error
        if rated_kw < 0 or not 0 <= annual_hours <= 8760 or not 0 <= load_factor <= 1:
            raise ValueError(f"line {line_number}: expected rated_kw >= 0, annual_hours in [0, 8760], load_factor in [0, 1]")
        annual_kwh = rated_kw * annual_hours * load_factor
        estimates.append({
            "asset_id": asset_id,
            "asset_name": asset_name,
            "category": (row.get("category") or "").strip(),
            "rated_kw": rated_kw,
            "annual_hours": annual_hours,
            "load_factor": load_factor,
            "estimated_annual_kwh": round(annual_kwh, 2),
            "estimated_annual_cost_yuan": round(annual_kwh * price_yuan_per_kwh, 2),
            "estimated_annual_emissions_kgco2e": round(annual_kwh * emission_factor_kg_per_kwh, 2),
        })
    return sorted(estimates, key=lambda item: item["estimated_annual_kwh"], reverse=True)


def run(inventory_path=INVENTORY_PATH, price=DEFAULT_PRICE_YUAN_PER_KWH,
        emission_factor=DEFAULT_EMISSION_FACTOR_KG_PER_KWH):
    if not inventory_path.exists():
        write_example(inventory_path)
    estimates = estimate_assets(read_inventory(inventory_path), price, emission_factor)
    totals = {
        "estimated_annual_kwh": round(sum(item["estimated_annual_kwh"] for item in estimates), 2),
        "estimated_annual_cost_yuan": round(sum(item["estimated_annual_cost_yuan"] for item in estimates), 2),
        "estimated_annual_emissions_kgco2e": round(sum(item["estimated_annual_emissions_kgco2e"] for item in estimates), 2),
    }
    report = {
        "inventory_file": str(inventory_path.name),
        "assets_ranked_by": "estimated_annual_kwh descending; ranking is for review only",
        "assumptions": {
            "electricity_price_yuan_per_kwh": price,
            "emission_factor_kgco2e_per_kwh": emission_factor,
            "factor_status": "illustrative placeholders; replace with documented local values",
            "formula": "rated_kw * annual_hours * load_factor",
        },
        "asset_count": len(estimates),
        "totals": totals,
        "estimates": estimates,
        "limitations": "Nameplate estimates are not measured consumption or verified emissions.",
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (RESULTS_DIR / "ranked_assets.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(estimates[0]) if estimates else ["asset_id", "asset_name", "category"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(estimates)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    parser.add_argument("--price-yuan-kwh", type=float, default=DEFAULT_PRICE_YUAN_PER_KWH)
    parser.add_argument("--emission-factor-kg-kwh", type=float, default=DEFAULT_EMISSION_FACTOR_KG_PER_KWH)
    args = parser.parse_args()
    run(args.inventory, args.price_yuan_kwh, args.emission_factor_kg_kwh)


if __name__ == "__main__":
    main()
