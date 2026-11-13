"""
HVAC Energy Optimization Using IoT Analytics
Machine Learning Model Training Pipeline
Generates synthetic thermodynamic training data, trains Scikit-Learn regression models,
evaluates predictive accuracy (R2, RMSE, MAE), and serializes the model.
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

from python.config import (
    DATA_DIR,
    SAMPLE_DATASET_PATH,
    MODEL_FILE_PATH,
    HVAC_FAN_POWER,
    HVAC_RATED_COP
)


def generate_synthetic_hvac_dataset(num_samples: int = 5000, random_seed: int = 42) -> pd.DataFrame:
    """
    Synthesizes realistic building thermal and energy telemetry across diurnal cycles.
    """
    np.random.seed(random_seed)

    # 1. Temporal features
    hours = np.random.randint(0, 24, size=num_samples)
    is_weekend = np.random.choice([0, 1], size=num_samples, p=[0.71, 0.29])

    # 2. Outdoor ambient temperature diurnal sinusoidal cycle
    # Peak at 15:00 (3 PM), trough at 05:00 (5 AM)
    base_ambient = 32.0 + 7.0 * np.sin((hours - 9) * np.pi / 12.0)
    outdoor_temps = base_ambient + np.random.normal(0, 2.2, size=num_samples)
    outdoor_temps = np.clip(outdoor_temps, 20.0, 44.0)

    # 3. Relative Humidity (inversely correlated with temperature)
    humidity = 78.0 - (outdoor_temps - 20.0) * 1.1 + np.random.normal(0, 5.0, size=num_samples)
    humidity = np.clip(humidity, 35.0, 92.0)

    # 4. Occupancy simulation (higher probability during office/living hours on weekdays)
    occupancy_prob = np.where(
        is_weekend == 1,
        np.where((hours >= 10) & (hours <= 20), 0.45, 0.15),
        np.where((hours >= 9) & (hours <= 18), 0.85, 0.10)
    )
    occupancy = (np.random.rand(num_samples) < occupancy_prob).astype(int)

    # 5. CO2 levels (strongly driven by occupancy and ventilation)
    base_co2 = 420.0 + occupancy * np.random.uniform(250.0, 750.0, size=num_samples)
    co2 = base_co2 + np.random.normal(0, 30.0, size=num_samples)
    co2 = np.clip(co2, 400.0, 1800.0)

    # 6. HVAC Setpoint and Fan Control decisions
    # Baseline systems tend to run at 20-22 C; optimized runs at 24-28 C
    setpoints = np.random.choice([20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0], size=num_samples)
    fan_speeds = np.random.choice([0, 1, 2, 3], size=num_samples, p=[0.05, 0.25, 0.45, 0.25])
    # 0: OFF, 1: LOW, 2: MEDIUM, 3: HIGH

    # 7. Indoor Temperature responds to Setpoint + Thermal lag
    indoor_temps = setpoints + np.random.normal(0.4, 0.5, size=num_samples)
    indoor_temps = np.clip(indoor_temps, 19.0, 32.0)

    # 8. Physical Power Calculation (Ground Truth target with realistic noise)
    fan_power_map = {0: 0.0, 1: 45.0, 2: 85.0, 3: 140.0}
    fan_powers = np.array([fan_power_map[f] for f in fan_speeds])

    # Thermal load calculation
    temp_delta = np.maximum(0.0, outdoor_temps - setpoints)
    envelope_load_kw = 0.14 * temp_delta
    internal_load_kw = (occupancy * 0.12) + 0.15
    latent_load_kw = np.maximum(0.0, (humidity - 50.0) * 0.005)
    total_thermal_load_kw = envelope_load_kw + internal_load_kw + latent_load_kw

    # Variable COP as function of outdoor ambient
    cop = HVAC_RATED_COP * (1.0 - 0.016 * np.maximum(0.0, outdoor_temps - 30.0))
    cop = np.clip(cop, 1.9, 4.2)

    # Compressor Power in Watts
    compressor_power_w = (total_thermal_load_kw / cop) * 1000.0

    # If indoor temp is already below setpoint or fan is OFF
    compressor_active = np.where((fan_speeds > 0) & (indoor_temps > setpoints - 0.5), 1.0, 0.05)
    total_power_w = (compressor_power_w * compressor_active) + fan_powers
    # Add measurement noise
    total_power_w += np.random.normal(0, 35.0, size=num_samples)
    total_power_w = np.clip(total_power_w, 20.0, 3200.0)

    # Assemble DataFrame
    df = pd.DataFrame({
        "hour_of_day": hours,
        "is_weekend": is_weekend,
        "outdoor_temp": np.round(outdoor_temps, 2),
        "humidity": np.round(humidity, 1),
        "occupancy": occupancy,
        "co2": np.round(co2, 0),
        "setpoint": np.round(setpoints, 1),
        "fan_speed_code": fan_speeds,
        "indoor_temp": np.round(indoor_temps, 2),
        "power_w": np.round(total_power_w, 1)
    })

    return df


def train_and_save_model() -> None:
    """Trains a Random Forest Regressor and outputs evaluation metrics."""
    print("==================================================================")
    print("  HVAC ENERGY OPTIMIZATION: MACHINE LEARNING TRAINING PIPELINE   ")
    print("==================================================================")

    DATA_DIR.mkdir(exist_ok=True, parents=True)

    # Generate or load dataset
    print("[1/5] Synthesizing 6,000 historical thermodynamic operational data points...")
    df = generate_synthetic_hvac_dataset(num_samples=6000)
    df.to_csv(SAMPLE_DATASET_PATH, index=False)
    print(f" -> Saved synthetic dataset to: {SAMPLE_DATASET_PATH}")

    # Feature definitions
    features = [
        "indoor_temp",
        "outdoor_temp",
        "humidity",
        "occupancy",
        "setpoint",
        "fan_speed_code",
        "hour_of_day",
        "is_weekend"
    ]
    target = "power_w"

    X = df[features]
    y = df[target]

    # Split Train & Test Sets (80% / 20%)
    print("[2/5] Partitioning data into train (80%) and validation (20%) sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    # Model definition: Random Forest Regressor
    print("[3/5] Training Random Forest Regressor (100 estimators)...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=16,
        min_samples_split=4,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Model Evaluation
    print("[4/5] Evaluating model performance on unseen test data...")
    y_pred = model.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100.0

    print("------------------------------------------------------------------")
    print(f"  Coefficient of Determination (R^2 Score): {r2:.4f} ({r2*100:.2f}%)")
    print(f"  Root Mean Squared Error (RMSE)          : {rmse:.2f} Watts")
    print(f"  Mean Absolute Error (MAE)              : {mae:.2f} Watts")
    print(f"  Mean Absolute Percentage Error (MAPE)  : {mape:.2f} %")
    print("------------------------------------------------------------------")

    # Feature Importance Breakdown
    print("\nFeature Importance Breakdown:")
    importances = model.feature_importances_
    for name, imp in sorted(zip(features, importances), key=lambda x: x[1], reverse=True):
        print(f"  - {name:<16}: {imp*100:.2f}%")

    # Serialize trained model to disk
    print(f"\n[5/5] Serializing model to disk: {MODEL_FILE_PATH}")
    joblib.dump(model, MODEL_FILE_PATH)
    print(" Model training and serialization successfully completed!\n")


if __name__ == "__main__":
    train_and_save_model()

