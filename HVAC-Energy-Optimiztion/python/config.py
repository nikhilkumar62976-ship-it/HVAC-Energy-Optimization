"""
HVAC Energy Optimization Using IoT Analytics
Configuration Module
Defines system parameters, MQTT broker setup, comfort limits, and database paths.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

# Database Configuration
SQLITE_DB_PATH = str(DATA_DIR / "hvac_data.db")
SAMPLE_DATASET_PATH = str(DATA_DIR / "sample_dataset.csv")
MODEL_FILE_PATH = str(DATA_DIR / "hvac_energy_model.joblib")

# MQTT Broker Configuration
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
MQTT_KEEPALIVE = 60
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

# MQTT Topic Hierarchy
TOPIC_TELEMETRY = "building/hvac/telemetry"
TOPIC_RECOMMENDATIONS = "building/hvac/recommendations"
TOPIC_CONTROL = "building/hvac/control"
TOPIC_STATUS = "building/hvac/status"
TOPIC_SIMULATION_TRIGGER = "building/hvac/simulate"

# HVAC Physical & Economic Parameters
DEFAULT_ELECTRICITY_TARIFF_PER_KWH = 0.15  # USD / kWh (or 8.5 INR / kWh)
HVAC_RATED_COOLING_CAPACITY_KW = 5.2       # 1.5 Ton AC ~ 5.2 kW thermal
HVAC_RATED_COP = 3.4                       # Coefficient of Performance (EER ~ 11.6)
HVAC_BASE_COMPRESSOR_POWER_KW = 1.5        # Base electric power at rated conditions
HVAC_FAN_POWER = {
    "OFF": 0.0,
    "LOW": 0.045,    # 45 Watts
    "MEDIUM": 0.085, # 85 Watts
    "HIGH": 0.140    # 140 Watts
}

# ASHRAE Standard 55 & 62.1 Thermal Comfort & Air Quality Thresholds
COMFORT_BOUNDS_OCCUPIED = {
    "temp_min": 23.0,     # C - Lower comfort boundary
    "temp_max": 25.5,     # C - Upper comfort boundary (ideal 24 C)
    "humidity_min": 40.0, # % RH
    "humidity_max": 65.0  # % RH
}

# Unoccupied Energy-Saving Setback Bounds
COMFORT_BOUNDS_UNOCCUPIED = {
    "temp_min": 28.0,     # C - Eco setback
    "temp_max": 30.0,     # C - Maximum safe setback
    "fan_speed": "LOW"
}

# Ventilation & Air Quality Parameters (ASHRAE 62.1)
CO2_COMFORT_TARGET_PPM = 700.0   # Fresh outdoor air ~ 420 ppm
CO2_VENTILATION_ALERT_PPM = 1000.0 # Exceeded: Fan must be forced HIGH or Vent damper opened
CO2_CRITICAL_PPM = 1400.0        # Stale air, drowsiness risk

# Optimization Multi-Objective Weights
WEIGHT_ENERGY = 0.60    # Weight for minimizing kWh cost
WEIGHT_COMFORT = 0.30   # Weight for thermal discomfort penalty
WEIGHT_AIR_QUALITY = 0.10 # Weight for ventilation / CO2 penalty

# Anti-cycling Safeguard (prevent mechanical wear on compressor)
MIN_CYCLE_TIME_SECONDS = 180 # 3 minutes minimum dwell time between setpoint changes

