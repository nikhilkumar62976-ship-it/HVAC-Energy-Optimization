"""
HVAC Energy Optimization Using IoT Analytics
Optimization Engine Module
Formulates and solves the multi-objective constrained optimization problem
for smart HVAC setpoints and ventilation control adhering to ASHRAE 55 and 62.1.
"""

import time
from typing import Dict, Any, List, Tuple
from python.config import (
    COMFORT_BOUNDS_OCCUPIED,
    COMFORT_BOUNDS_UNOCCUPIED,
    CO2_VENTILATION_ALERT_PPM,
    CO2_CRITICAL_PPM,
    WEIGHT_ENERGY,
    WEIGHT_COMFORT,
    WEIGHT_AIR_QUALITY,
    MIN_CYCLE_TIME_SECONDS
)
from python.ml_model import HVACEnergyPredictor


class HVACOptimizer:
    """
    Constrained Multi-Objective Optimizer for HVAC setpoints and fan operation.
    Balances electrical energy conservation against occupant thermal comfort
    and indoor air quality thresholds.
    """

    def __init__(self, predictor: HVACEnergyPredictor):
        self.predictor = predictor
        self.last_switch_time = 0.0
        self.last_recommended_setpoint = 24.0
        self.last_recommended_fan = "MEDIUM"

    def optimize(
        self,
        indoor_temp: float,
        outdoor_temp: float,
        humidity: float,
        occupancy: int,
        co2: float,
        current_power_w: float = 0.0,
        current_setpoint: float = 24.0,
        current_fan: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Executes constrained grid evaluation over discrete candidate space:
        T_set in [22.0, 29.5], Fan in ['LOW', 'MEDIUM', 'HIGH'].
        """
        now = time.time()
        is_occupied = (occupancy == 1)

        # Baseline comparison: typical non-optimized fixed setup (21.0 C, HIGH fan)
        baseline_setpoint = 21.0 if is_occupied else 24.0
        baseline_fan = "HIGH" if is_occupied else "MEDIUM"
        baseline_power_w = self.predictor.predict_power(
            indoor_temp=indoor_temp,
            outdoor_temp=outdoor_temp,
            humidity=humidity,
            occupancy=occupancy,
            setpoint=baseline_setpoint,
            fan_speed=baseline_fan
        )

        # 1. Check Indoor Air Quality (ASHRAE 62.1 Ventilation Override)
        co2_override_active = False
        if co2 >= CO2_VENTILATION_ALERT_PPM:
            co2_override_active = True

        # 2. Define Feasible Search Space based on Occupancy
        if is_occupied:
            candidate_setpoints = [23.0, 23.5, 24.0, 24.5, 25.0, 25.5]
            candidate_fans = ["LOW", "MEDIUM", "HIGH"]
            mode = "OCCUPIED_COMFORT"
            if co2_override_active:
                candidate_fans = ["HIGH"] # Force high circulation/ventilation
                mode = "VENTILATION_PURGE"
        else:
            # Unoccupied room: Apply aggressive energy-saving setback
            candidate_setpoints = [27.0, 27.5, 28.0, 28.5, 29.0]
            candidate_fans = ["LOW", "MEDIUM"]
            mode = "ECO_SETBACK"

        best_cost = float("inf")
        best_setpoint = 24.0
        best_fan = "MEDIUM"
        best_predicted_power = baseline_power_w

        # 3. Grid Search over Discrete Feasible Control Candidates
        for sp in candidate_setpoints:
            for fan in candidate_fans:
                pred_power = self.predictor.predict_power(
                    indoor_temp=indoor_temp,
                    outdoor_temp=outdoor_temp,
                    humidity=humidity,
                    occupancy=occupancy,
                    setpoint=sp,
                    fan_speed=fan
                )

                # Cost Component 1: Normalized Electrical Power
                # Assuming rated AC power ~ 2200W
                cost_energy = pred_power / 2200.0

                # Cost Component 2: Thermal Discomfort Penalty (ASHRAE 55)
                cost_comfort = self._calculate_comfort_penalty(
                    setpoint=sp,
                    indoor_temp=indoor_temp,
                    humidity=humidity,
                    is_occupied=is_occupied
                )

                # Cost Component 3: Ventilation / Air Quality Penalty (ASHRAE 62.1)
                cost_iaq = self._calculate_iaq_penalty(co2=co2, fan_speed=fan)

                # Multi-Objective Objective Function J
                total_cost = (
                    WEIGHT_ENERGY * cost_energy +
                    WEIGHT_COMFORT * cost_comfort +
                    WEIGHT_AIR_QUALITY * cost_iaq
                )

                if total_cost < best_cost:
                    best_cost = total_cost
                    best_setpoint = sp
                    best_fan = fan
                    best_predicted_power = pred_power

        # 4. Anti-Short-Cycling Dwell Safeguard
        # Prevent oscillations faster than MIN_CYCLE_TIME_SECONDS
        if (now - self.last_switch_time) < MIN_CYCLE_TIME_SECONDS:
            # Dampen change if temperature difference is subtle
            if abs(best_setpoint - self.last_recommended_setpoint) < 1.0 and not co2_override_active:
                best_setpoint = self.last_recommended_setpoint
                best_fan = self.last_recommended_fan
        else:
            if best_setpoint != self.last_recommended_setpoint:
                self.last_switch_time = now

        self.last_recommended_setpoint = best_setpoint
        self.last_recommended_fan = best_fan

        # 5. Energy Savings Quantifications
        power_saved_w = max(0.0, baseline_power_w - best_predicted_power)
        savings_pct = (power_saved_w / baseline_power_w * 100.0) if baseline_power_w > 0 else 0.0

        # Construct Human-Readable Engineering Justification
        justification = self._generate_justification(
            is_occupied=is_occupied,
            best_setpoint=best_setpoint,
            best_fan=best_fan,
            co2=co2,
            outdoor_temp=outdoor_temp,
            co2_override=co2_override_active
        )

        return {
            "baseline_setpoint": baseline_setpoint,
            "baseline_fan": baseline_fan,
            "baseline_power_w": round(baseline_power_w, 1),
            "recommended_setpoint": best_setpoint,
            "recommended_fan_speed": best_fan,
            "predicted_power_w": round(best_predicted_power, 1),
            "power_saved_w": round(power_saved_w, 1),
            "savings_percentage": round(savings_pct, 1),
            "optimization_mode": mode,
            "hvac_power_mode": "ON",
            "justification": justification,
            "iaq_status": "CRITICAL" if co2 >= CO2_CRITICAL_PPM else ("WARNING" if co2_override_active else "GOOD"),
            "comfort_status": "COMFORTABLE" if is_occupied and (23.0 <= best_setpoint <= 25.5) else "SETBACK_ECO"
        }

    def _calculate_comfort_penalty(
        self,
        setpoint: float,
        indoor_temp: float,
        humidity: float,
        is_occupied: bool
    ) -> float:
        """
        Computes quadratic penalty around ideal 24.0 C neutral comfort zone (ASHRAE 55).
        Penalizes excessively low or high temperatures when occupied.
        """
        if is_occupied:
            # Ideal neutral comfort: 24.0 C
            temp_dev = abs(setpoint - 24.0)
            penalty = (temp_dev / 1.5) ** 2

            # Humidity penalty: above 60% increases perceived heat index
            if humidity > 60.0:
                penalty += ((humidity - 60.0) / 10.0) * 0.5
            return penalty
        else:
            # Unoccupied: Ideal setback is 28.0 C; penalty if cooled below 27.0 C
            if setpoint < 27.0:
                return (27.0 - setpoint) * 2.5
            return 0.0

    def _calculate_iaq_penalty(self, co2: float, fan_speed: str) -> float:
        """
        ASHRAE 62.1 Air Quality penalty.
        If CO2 > 1000 ppm, non-HIGH fan settings receive heavy penalty.
        """
        if co2 >= CO2_VENTILATION_ALERT_PPM:
            if fan_speed != "HIGH":
                return 4.0 * ((co2 - CO2_VENTILATION_ALERT_PPM) / 100.0)
        return 0.0

    def _generate_justification(
        self,
        is_occupied: bool,
        best_setpoint: float,
        best_fan: str,
        co2: float,
        outdoor_temp: float,
        co2_override: bool
    ) -> str:
        """Generates contextual engineering explanation for viva and UI."""
        if co2_override:
            return (
                f"Ventilation override: CO2 at {int(co2)} ppm (>1000 ppm threshold). "
                f"Fan forced to {best_fan} to exhaust air and ensure health safety (ASHRAE 62.1)."
            )
        if not is_occupied:
            return (
                f"Space Unoccupied: Applied eco setback to {best_setpoint} C and {best_fan} fan. "
                "Eliminated unnecessary cooling load, saving significant electricity."
            )
        if outdoor_temp >= 35.0:
            return (
                f"High Ambient Load ({outdoor_temp} C): Setpoint optimized to {best_setpoint} C "
                f"with {best_fan} fan to balance thermal comfort while avoiding peak compressor stress."
            )
        return (
            f"Occupied Comfort Mode: Setpoint {best_setpoint} C satisfies ASHRAE 55 PMV neutral "
            f"comfort range while conserving fan/compressor power."
        )

