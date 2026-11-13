"""
HVAC Energy Optimization Using IoT Analytics
Machine Learning Energy Predictor Module
Trains and serves a Scikit-Learn regression model to predict HVAC electrical power
consumption as a function of thermal, ambient, occupancy, and control parameters.
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple
import warnings
import joblib
import numpy as np
import pandas as pd
from python.config import (
    MODEL_FILE_PATH,
    HVAC_BASE_COMPRESSOR_POWER_KW,
    HVAC_FAN_POWER,
    HVAC_RATED_COP
)

# Suppress all sklearn and joblib warnings during fast micro-inference
warnings.filterwarnings("ignore")

FAN_SPEED_MAP = {"OFF": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
REVERSE_FAN_MAP = {0: "OFF", 1: "LOW", 2: "MEDIUM", 3: "HIGH"}


class HVACEnergyPredictor:
    """Predicts HVAC power (Watts) using Scikit-Learn or an analytical thermodynamic model."""

    def __init__(self, model_path: str = MODEL_FILE_PATH):
        self.model_path = model_path
        self.model = None
        self.feature_names = [
            "indoor_temp",
            "outdoor_temp",
            "humidity",
            "occupancy",
            "setpoint",
            "fan_speed_code",
            "hour_of_day",
            "is_weekend"
        ]
        self._load_model()

    def _load_model(self) -> None:
        """Loads serialized scikit-learn model if available on disk."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                if hasattr(self.model, "n_jobs"):
                    self.model.n_jobs = 1  # Low-latency single-thread prediction
                print(f"[ML MODEL] Loaded trained model from {self.model_path}")
            except Exception as e:
                print(f"[ML MODEL] Could not load model file ({e}). Utilizing analytical physics fallback.")
                self.model = None
        else:
            print(f"[ML MODEL] Model file not yet present at {self.model_path}. Utilizing analytical physics fallback.")
            self.model = None

    def predict_power(
        self,
        indoor_temp: float,
        outdoor_temp: float,
        humidity: float,
        occupancy: int,
        setpoint: float,
        fan_speed: str,
        hour_of_day: int = 14,
        is_weekend: int = 0
    ) -> float:
        """
        Predicts electrical power demand (Watts) for given environmental and control conditions.
        """
        fan_code = FAN_SPEED_MAP.get(fan_speed.upper(), 2)

        # If trained ML model is available, use ML inference
        if self.model is not None:
            features = np.array([[
                indoor_temp,
                outdoor_temp,
                humidity,
                occupancy,
                setpoint,
                fan_code,
                hour_of_day,
                is_weekend
            ]], dtype=np.float64)
            try:
                pred = float(self.model.predict(features)[0])
                return max(15.0, round(pred, 1))  # Standby baseline ~ 15W
            except Exception as e:
                print(f"[ML PREDICT ERROR] Model prediction failed: {e}. Falling back to physics engine.")

        # Analytical Thermodynamic Physics Fallback Model:
        # Building Thermal Transfer Model: Q_envelope = UA * (T_out - T_set)
        # Internal Heat Gains: Q_internal = Occupants * 120W + Lighting/Equipment
        # COP variation with outdoor ambient: COP(T_out) = COP_rated * (1 - 0.02 * (T_out - 35))
        return self._physics_based_power(
            indoor_temp=indoor_temp,
            outdoor_temp=outdoor_temp,
            humidity=humidity,
            occupancy=occupancy,
            setpoint=setpoint,
            fan_speed=fan_speed
        )

    def _physics_based_power(
        self,
        indoor_temp: float,
        outdoor_temp: float,
        humidity: float,
        occupancy: int,
        setpoint: float,
        fan_speed: str
    ) -> float:
        """
        Thermodynamic calculation:
        P_total = P_compressor(thermal_load, COP) + P_fan
        """
        fan_power_w = HVAC_FAN_POWER.get(fan_speed.upper(), 0.085) * 1000.0

        # If HVAC setpoint is satisfied and room is colder than setpoint
        temp_diff = outdoor_temp - setpoint
        indoor_cooling_needed = indoor_temp - setpoint

        if indoor_cooling_needed <= -0.5:
            # Compressor can cycle off; fan circulation only
            return round(18.0 + fan_power_w, 1)

        # Thermal envelope load (kW): UA ~ 0.12 kW/C for a typical room
        ua_factor = 0.14
        envelope_load_kw = max(0.0, ua_factor * temp_diff)

        # Internal loads
        internal_load_kw = (occupancy * 0.120) + 0.150  # Occupants + electronics

        # Latent heat from humidity (>50% RH adds latent cooling load)
        latent_factor = max(0.0, (humidity - 50.0) * 0.004)

        total_cooling_load_kw = envelope_load_kw + internal_load_kw + latent_factor

        # Outdoor temperature degrades COP (higher outdoor temp = compressor works harder)
        cop = HVAC_RATED_COP * (1.0 - 0.018 * max(0.0, outdoor_temp - 30.0))
        cop = max(1.8, min(4.5, cop))

        # Compressor electrical power in Watts
        compressor_power_w = (total_cooling_load_kw / cop) * 1000.0

        # Modulation factor: Inverter AC throttles up/down based on (indoor_temp - setpoint)
        urgency = max(0.3, min(1.2, indoor_cooling_needed / 2.0))
        modulated_compressor_power_w = compressor_power_w * urgency

        total_power_w = modulated_compressor_power_w + fan_power_w
        return max(35.0, round(total_power_w, 1))
