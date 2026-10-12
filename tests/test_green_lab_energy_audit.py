import unittest

from green_lab_energy_audit import estimate_assets


class EstimateAssetsTests(unittest.TestCase):
    def test_formula_and_descending_rank(self):
        rows = [
            {"asset_id": "a", "asset_name": "A", "category": "cold", "rated_kw": "1", "annual_hours": "100", "load_factor": "0.5"},
            {"asset_id": "b", "asset_name": "B", "category": "lab", "rated_kw": "2", "annual_hours": "100", "load_factor": "0.5"},
        ]
        result = estimate_assets(rows, 0.5, 0.4)
        self.assertEqual([item["asset_id"] for item in result], ["b", "a"])
        self.assertEqual(result[0]["estimated_annual_kwh"], 100)
        self.assertEqual(result[0]["estimated_annual_cost_yuan"], 50)
        self.assertEqual(result[0]["estimated_annual_emissions_kgco2e"], 40)

    def test_rejects_impossible_hours_and_duplicate_ids(self):
        base = {"asset_id": "a", "asset_name": "A", "category": "lab", "rated_kw": "1", "annual_hours": "9000", "load_factor": "0.5"}
        with self.assertRaises(ValueError):
            estimate_assets([base], 0.5, 0.4)
        duplicate = dict(base, annual_hours="100")
        with self.assertRaises(ValueError):
            estimate_assets([duplicate, duplicate], 0.5, 0.4)


if __name__ == "__main__":
    unittest.main()
