"""
HVAC Energy Optimization - Verification & Simulation Test Suite
Performs audit testing on:
1. SQLite Schema & Persistence
2. Machine Learning Predictive Pipeline
3. Constrained Multi-Objective Optimizer (ASHRAE 55 & 62.1)
4. Telemetry Schema & Payload Validation
5. Energy Savings Calculations
"""

import unittest
import json
from python.config import SQLITE_DB_PATH
from python.database import HVACDatabase
from python.ml_model import HVACEnergyPredictor
from python.optimizer import HVACOptimizer


class TestHVACSimulation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = HVACDatabase()
        cls.predictor = HVACEnergyPredictor()
        cls.optimizer = HVACOptimizer(cls.predictor)

    def test_01_database_persistence(self):
        """Verify telemetry insertion and retrieval from SQLite."""
        telemetry = {
            "device_id": "TEST_AUDIT_NODE_01",
            "temperature": 25.4,
            "humidity": 55.0,
            "occupancy": 1,
            "co2": 650.0,
            "voltage": 230.2,
            "current": 4.90,
            "power": 1080.0,
            "energy_kwh": 2.45,
            "frequency": 50.0,
            "power_factor": 0.94,
            "hvac_state": "ON",
            "active_setpoint": 24.0,
            "active_fan": "MEDIUM"
        }
        row_id = self.db.insert_telemetry(telemetry)
        self.assertGreater(row_id, 0)

        latest = self.db.get_latest_telemetry()
        self.assertIsNotNone(latest)
        self.assertEqual(latest["device_id"], "TEST_AUDIT_NODE_01")
        self.assertAlmostEqual(latest["temperature"], 25.4, places=1)
        self.assertAlmostEqual(latest["power"], 1080.0, places=1)

    def test_02_ml_prediction_pipeline(self):
        """Verify ML model loads and produces thermodynamically consistent predictions."""
        self.assertIsNotNone(self.predictor.model, "ML model file was not loaded into predictor")

        # Test power predictions
        p_base = self.predictor.predict_power(
            indoor_temp=25.0, outdoor_temp=36.0, humidity=55.0,
            occupancy=1, setpoint=21.0, fan_speed="HIGH"
        )
        p_opt = self.predictor.predict_power(
            indoor_temp=25.0, outdoor_temp=36.0, humidity=55.0,
            occupancy=1, setpoint=24.5, fan_speed="MEDIUM"
        )
        p_unocc = self.predictor.predict_power(
            indoor_temp=28.0, outdoor_temp=36.0, humidity=55.0,
            occupancy=0, setpoint=28.0, fan_speed="LOW"
        )

        self.assertGreater(p_base, 0, "Base power must be positive")
        self.assertGreater(p_opt, 0, "Optimized power must be positive")
        self.assertGreater(p_unocc, 0, "Unoccupied power must be positive")

        # Monotonicity: cooling to 21C with HIGH fan draws more power than 24.5C with MEDIUM fan
        self.assertGreater(p_base, p_opt, "Baseline power must exceed optimized power")
        self.assertGreater(p_opt, p_unocc, "Occupied power must exceed unoccupied setback power")

    def test_03_optimizer_occupied_comfort(self):
        """Verify optimizer selects ASHRAE 55 compliant setpoint (23.0C - 25.5C) when occupied."""
        res = self.optimizer.optimize(
            indoor_temp=25.2, outdoor_temp=35.0, humidity=55.0,
            occupancy=1, co2=650.0
        )
        self.assertEqual(res["optimization_mode"], "OCCUPIED_COMFORT")
        self.assertGreaterEqual(res["recommended_setpoint"], 23.0)
        self.assertLessEqual(res["recommended_setpoint"], 25.5)
        self.assertIn(res["recommended_fan_speed"], ["LOW", "MEDIUM", "HIGH"])
        self.assertGreater(res["power_saved_w"], 0)
        self.assertGreater(res["savings_percentage"], 0)

    def test_04_optimizer_unoccupied_setback(self):
        """Verify optimizer triggers ECO_SETBACK (>= 27.0C) when room is unoccupied."""
        res = self.optimizer.optimize(
            indoor_temp=27.0, outdoor_temp=35.0, humidity=55.0,
            occupancy=0, co2=450.0
        )
        self.assertEqual(res["optimization_mode"], "ECO_SETBACK")
        self.assertGreaterEqual(res["recommended_setpoint"], 27.0)
        self.assertIn(res["recommended_fan_speed"], ["LOW", "MEDIUM"])

    def test_05_optimizer_co2_ventilation_override(self):
        """Verify optimizer triggers VENTILATION_PURGE and forces HIGH fan when CO2 >= 1000 ppm."""
        res = self.optimizer.optimize(
            indoor_temp=25.0, outdoor_temp=35.0, humidity=55.0,
            occupancy=1, co2=1250.0
        )
        self.assertEqual(res["optimization_mode"], "VENTILATION_PURGE")
        self.assertEqual(res["recommended_fan_speed"], "HIGH")
        self.assertEqual(res["iaq_status"], "WARNING")
        self.assertIn("Ventilation override", res["justification"])

    def test_06_energy_savings_math(self):
        """Verify mathematical identity: power_saved = baseline - predicted and savings_pct."""
        res = self.optimizer.optimize(
            indoor_temp=25.0, outdoor_temp=35.0, humidity=55.0,
            occupancy=1, co2=650.0
        )
        base = res["baseline_power_w"]
        pred = res["predicted_power_w"]
        saved = res["power_saved_w"]
        pct = res["savings_percentage"]

        expected_saved = max(0.0, base - pred)
        self.assertAlmostEqual(saved, expected_saved, places=1)
        expected_pct = (saved / base) * 100.0 if base > 0 else 0.0
        self.assertAlmostEqual(pct, expected_pct, places=1)

    def test_07_offline_simulation_batch(self):
        """Verify the offline simulation engine executes a batch, logs records to SQLite, and computes summary."""
        from python.simulate_offline import run_offline_simulation
        res = run_offline_simulation(num_samples=4, verbose=False)
        self.assertEqual(res["num_samples"], 4)
        self.assertGreater(res["avg_baseline_power_w"], 0)
        self.assertGreater(res["avg_optimized_power_w"], 0)
        self.assertGreater(res["db_total_optimizations"], 0)


if __name__ == "__main__":
    unittest.main()

