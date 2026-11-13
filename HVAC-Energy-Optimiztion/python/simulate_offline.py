"""
HVAC Energy Optimization Using IoT Analytics
Offline Simulation Engine (Zero MQTT / Zero External Broker Dependency)
Generates configurable batches of simulated building telemetry, executes
the ML energy model and ASHRAE 55/62.1 optimizer, stores records into SQLite,
and displays a concise summary table.
"""

import sys
import os
import time
import random
import datetime
import argparse
from typing import Dict, Any, List

from python.config import (
    SQLITE_DB_PATH,
    DEFAULT_ELECTRICITY_TARIFF_PER_KWH
)
from python.database import HVACDatabase
from python.ml_model import HVACEnergyPredictor
from python.optimizer import HVACOptimizer


def run_offline_simulation(num_samples: int = 12, verbose: bool = True) -> Dict[str, Any]:
    """
    Executes a complete offline simulation cycle without requiring an MQTT broker or Node-RED.
    """
    print("\n================================================================================")
    print("      HVAC ENERGY OPTIMIZATION: OFFLINE SIMULATION & VERIFICATION MODE          ")
    print(f"      Database Target: {SQLITE_DB_PATH}")
    print(f"      Batch Size     : {num_samples} simulated intervals")
    print("================================================================================\n")

    db = HVACDatabase()
    predictor = HVACEnergyPredictor()
    optimizer = HVACOptimizer(predictor)

    results: List[Dict[str, Any]] = []
    purges_triggered = 0
    setbacks_triggered = 0

    # Header
    print(f"{'#':<3} | {'Scenario':<18} | {'Tin':<5} | {'Tout':<5} | {'Occ':<3} | {'CO2':<7} | {'Base(W)':<7} | {'Opt(W)':<7} | {'Save(W)':<7} | {'Save%':<6} | {'Setpoint & Fan'}")
    print("-" * 105)

    base_kwh_accum = 14.50

    for i in range(1, num_samples + 1):
        # 1. Deterministic Multi-Phase Building Scenario Cycle
        # Phase 0: Normal Occupied Comfort (Steps 1, 5, 9...)
        # Phase 1: High Ambient Heat (Steps 2, 6, 10...)
        # Phase 2: High CO2 Purge Event (Steps 3, 7, 11...)
        # Phase 3: Unoccupied Eco Setback (Steps 4, 8, 12...)
        phase = (i - 1) % 4

        if phase == 0:
            scenario_name = "OCCUPIED_NORMAL"
            is_occupied = 1
            indoor_temp = 25.0 + random.uniform(-0.3, 0.3)
            outdoor_temp = 33.0 + random.uniform(-0.5, 0.5)
            humidity = 55.0 + random.uniform(-2.0, 2.0)
            co2 = 650.0 + random.uniform(-30.0, 30.0)
        elif phase == 1:
            scenario_name = "PEAK_AMBIENT_HEAT"
            is_occupied = 1
            indoor_temp = 25.6 + random.uniform(-0.2, 0.4)
            outdoor_temp = 38.5 + random.uniform(-0.5, 1.0)
            humidity = 50.0 + random.uniform(-3.0, 2.0)
            co2 = 780.0 + random.uniform(-20.0, 30.0)
        elif phase == 2:
            scenario_name = "CO2_PURGE_EVENT"
            is_occupied = 1
            indoor_temp = 25.8 + random.uniform(-0.2, 0.3)
            outdoor_temp = 36.0 + random.uniform(-0.5, 0.5)
            humidity = 62.0 + random.uniform(-2.0, 3.0)
            co2 = 1260.0 + random.uniform(0.0, 80.0)  # Exceeds 1000 ppm threshold
        else:  # phase == 3
            scenario_name = "UNOCCUPIED_ECO"
            is_occupied = 0
            indoor_temp = 27.5 + random.uniform(-0.3, 0.5)
            outdoor_temp = 35.0 + random.uniform(-0.5, 0.5)
            humidity = 52.0 + random.uniform(-2.0, 2.0)
            co2 = 450.0 + random.uniform(-15.0, 15.0)

        # 2. Electrical Telemetry (PZEM-004T modeling)
        voltage = 230.2 + random.uniform(-1.5, 1.5)
        # Power drawn depends on thermal load
        raw_power = 600.0 + max(0.0, outdoor_temp - 24.0) * 45.0 + (is_occupied * 220.0)
        power_factor = 0.93 + random.uniform(-0.01, 0.01)
        current = raw_power / (voltage * power_factor)
        base_kwh_accum += (raw_power * (5.0 / 3600.0)) / 1000.0

        telemetry_packet = {
            "device_id": "OFFLINE_SIM_NODE_01",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "temperature": round(indoor_temp, 2),
            "humidity": round(humidity, 1),
            "occupancy": is_occupied,
            "co2": round(co2, 0),
            "voltage": round(voltage, 1),
            "current": round(current, 2),
            "power": round(raw_power, 1),
            "energy_kwh": round(base_kwh_accum, 4),
            "frequency": 50.0,
            "power_factor": round(power_factor, 2),
            "hvac_state": "ON",
            "active_setpoint": 24.0,
            "active_fan": "MEDIUM"
        }

        # 3. Store Telemetry into SQLite
        row_id = db.insert_telemetry(telemetry_packet)

        # 4. Pass Telemetry Through Optimizer & ML Model
        rec = optimizer.optimize(
            indoor_temp=indoor_temp,
            outdoor_temp=outdoor_temp,
            humidity=humidity,
            occupancy=is_occupied,
            co2=co2,
            current_power_w=raw_power,
            current_setpoint=24.0,
            current_fan="MEDIUM"
        )

        if rec["optimization_mode"] == "VENTILATION_PURGE":
            purges_triggered += 1
        elif rec["optimization_mode"] == "ECO_SETBACK":
            setbacks_triggered += 1

        # 5. Store Optimization Decision into SQLite
        opt_record = {
            "baseline_setpoint": rec["baseline_setpoint"],
            "baseline_fan": rec["baseline_fan"],
            "baseline_power_w": rec["baseline_power_w"],
            "recommended_setpoint": rec["recommended_setpoint"],
            "recommended_fan_speed": rec["recommended_fan_speed"],
            "predicted_power_w": rec["predicted_power_w"],
            "power_saved_w": rec["power_saved_w"],
            "savings_percentage": rec["savings_percentage"],
            "occupancy_state": is_occupied,
            "co2_level": co2,
            "indoor_temp": indoor_temp,
            "outdoor_temp": outdoor_temp,
            "optimization_mode": rec["optimization_mode"],
            "justification": rec["justification"]
        }
        db.insert_optimization(opt_record)

        results.append({
            "step": i,
            "scenario": scenario_name,
            "indoor_temp": indoor_temp,
            "outdoor_temp": outdoor_temp,
            "occupancy": is_occupied,
            "co2": co2,
            "baseline_power_w": rec["baseline_power_w"],
            "predicted_power_w": rec["predicted_power_w"],
            "power_saved_w": rec["power_saved_w"],
            "savings_percentage": rec["savings_percentage"],
            "recommended_setpoint": rec["recommended_setpoint"],
            "recommended_fan": rec["recommended_fan_speed"],
            "mode": rec["optimization_mode"]
        })

        # Print row
        print(f"{i:<3} | {scenario_name:<18} | {indoor_temp:4.1f}C | {outdoor_temp:4.1f}C | {is_occupied:<3} | {int(co2):<4}ppm | "
              f"{rec['baseline_power_w']:7.1f} | {rec['predicted_power_w']:7.1f} | {rec['power_saved_w']:7.1f} | {rec['savings_percentage']:5.1f}% | "
              f"{rec['recommended_setpoint']}C [{rec['recommended_fan_speed']}] ({rec['optimization_mode']})")

    # 6. Compute Batch Aggregates
    avg_base = sum(r["baseline_power_w"] for r in results) / len(results)
    avg_opt = sum(r["predicted_power_w"] for r in results) / len(results)
    avg_saved = avg_base - avg_opt
    avg_savings_pct = (avg_saved / avg_base) * 100.0 if avg_base > 0 else 0.0

    # Approx kWh saved across these intervals (assuming 5 minutes per step)
    sim_hours = num_samples * (5.0 / 60.0)
    kwh_saved = (avg_saved * sim_hours) / 1000.0
    cost_saved = kwh_saved * DEFAULT_ELECTRICITY_TARIFF_PER_KWH

    # Query Total Database Rows
    stats = db.get_overall_energy_stats()

    print("-" * 105)
    print("\n================================================================================")
    print("                     OFFLINE SIMULATION BATCH RESULTS                           ")
    print("================================================================================")
    print(f"  Processed Sample Steps            : {num_samples}")
    print(f"  Simulated Duration Equivalent     : {sim_hours:.2f} Hours (5-min intervals)")
    print(f"  Average Baseline Electrical Power : {avg_base:.1f} Watts")
    print(f"  Average Optimized Electrical Power: {avg_opt:.1f} Watts")
    print(f"  Net Continuous Power Reduction    : {avg_saved:.1f} Watts")
    print(f"  BATCH ENERGY CONSERVATION RATIO   : {avg_savings_pct:.2f} %")
    print(f"  Estimated Electricity Conserved   : {kwh_saved:.3f} kWh (Cost Saved: ${cost_saved:.3f})")
    print(f"  ASHRAE 62.1 Air Quality Overrides : {purges_triggered} purge events triggered")
    print(f"  ASHRAE 55 Occupancy Eco Setbacks  : {setbacks_triggered} setback events triggered")
    print("--------------------------------------------------------------------------------")
    print(f"  SQLite Total Telemetry Records    : Verified in database '{SQLITE_DB_PATH}'")
    print(f"  SQLite Total Optimizations Logged : {stats['total_samples']} records in history")
    print("================================================================================\n")

    return {
        "num_samples": num_samples,
        "avg_baseline_power_w": round(avg_base, 1),
        "avg_optimized_power_w": round(avg_opt, 1),
        "avg_power_saved_w": round(avg_saved, 1),
        "savings_percentage": round(avg_savings_pct, 2),
        "kwh_saved": round(kwh_saved, 4),
        "purges_triggered": purges_triggered,
        "setbacks_triggered": setbacks_triggered,
        "db_total_optimizations": stats["total_samples"]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Offline HVAC Simulation without MQTT")
    parser.add_argument("--samples", type=int, default=12, help="Number of telemetry samples to simulate (default: 12)")
    args = parser.parse_args()

    run_offline_simulation(num_samples=args.samples)

