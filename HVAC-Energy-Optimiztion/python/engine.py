"""
HVAC Energy Optimization Using IoT Analytics
Central Python Optimization Engine Service
Subscribes to ESP32 telemetry over MQTT, manages SQLite persistence,
runs the ML energy prediction and ASHRAE optimization, and dispatches
energy-saving recommendations to Node-RED and hardware actuators.
"""

import sys
import os
import json
import time
import signal
import datetime
from typing import Dict, Any

import paho.mqtt.client as mqtt

from python.config import (
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_KEEPALIVE,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    TOPIC_TELEMETRY,
    TOPIC_RECOMMENDATIONS,
    TOPIC_CONTROL,
    TOPIC_STATUS
)
from python.database import HVACDatabase
from python.ml_model import HVACEnergyPredictor
from python.optimizer import HVACOptimizer


class HVACOptimizationEngine:
    """Core daemon coordinating MQTT telemetry ingestion, DB storage, and optimization."""

    def __init__(self):
        print("\n=======================================================")
        print("  HVAC ENERGY OPTIMIZATION ANALYTICS ENGINE (PYTHON)   ")
        print("=======================================================")

        self.db = HVACDatabase()
        self.predictor = HVACEnergyPredictor()
        self.optimizer = HVACOptimizer(self.predictor)

        # Initialize MQTT Client with MQTT v5 / v3.1.1 protocol
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="Python_HVAC_Optimization_Engine"
        )

        if MQTT_USERNAME:
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.is_running = False

    def _estimate_outdoor_temp(self) -> float:
        """
        Estimates outdoor ambient temperature based on time of day (diurnal cycle)
        if an external weather sensor or API is unavailable.
        """
        current_hour = datetime.datetime.now().hour
        # Diurnal curve: lowest at 5 AM (~26 C), highest at 3 PM (~38 C) in summer
        base_ambient = 32.0 + 6.0 * (1.0 - (abs(current_hour - 15) / 10.0))
        return round(max(24.0, min(42.0, base_ambient)), 1)

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback invoked upon successful MQTT connection."""
        if rc == 0:
            print(f"[MQTT] Connected successfully to Broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
            client.subscribe(TOPIC_TELEMETRY)
            print(f"[MQTT] Subscribed to telemetry topic: '{TOPIC_TELEMETRY}'")

            # Publish engine status
            status_payload = {
                "engine_status": "ONLINE",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "mode": "ACTIVE_RECOMMENDATION"
            }
            client.publish(TOPIC_STATUS, json.dumps(status_payload), retain=True)
        else:
            print(f"[MQTT ERROR] Connection failed with code: {rc}")

    def _on_disconnect(self, client, userdata, disconnect_flags, rc, properties=None):
        print(f"[MQTT WARNING] Disconnected from broker (rc={rc}). Auto-reconnecting...")

    def _on_message(self, client, userdata, msg):
        """Processes inbound IoT sensor packets from ESP32 or simulator."""
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)
        except Exception as e:
            print(f"[ERROR] Failed to decode incoming JSON on {msg.topic}: {e}")
            return

        # 1. Extract Telemetry Fields with validation
        indoor_temp = float(data.get("temperature", 25.0))
        humidity = float(data.get("humidity", 55.0))
        occupancy = int(data.get("occupancy", 0))
        co2 = float(data.get("co2", 500.0))
        voltage = float(data.get("voltage", 230.0))
        current = float(data.get("current", 0.0))
        power = float(data.get("power", 0.0))
        energy_kwh = float(data.get("energy_kwh", 0.0))
        current_setpoint = float(data.get("active_setpoint", 24.0))
        current_fan = str(data.get("active_fan", "MEDIUM"))

        # Outdoor temperature: use sensor value if present, else diurnal estimate
        outdoor_temp = float(data.get("outdoor_temperature", self._estimate_outdoor_temp()))

        # 2. Persist Raw Telemetry to Database
        telemetry_record = {
            "device_id": data.get("device_id", "ESP32_HVAC_NODE"),
            "temperature": indoor_temp,
            "humidity": humidity,
            "occupancy": occupancy,
            "co2": co2,
            "voltage": voltage,
            "current": current,
            "power": power,
            "energy_kwh": energy_kwh,
            "frequency": data.get("frequency", 50.0),
            "power_factor": data.get("power_factor", 0.92),
            "hvac_state": data.get("hvac_state", "ON"),
            "active_setpoint": current_setpoint,
            "active_fan": current_fan
        }
        self.db.insert_telemetry(telemetry_record)

        # 3. Execute Constrained Optimization Engine
        rec = self.optimizer.optimize(
            indoor_temp=indoor_temp,
            outdoor_temp=outdoor_temp,
            humidity=humidity,
            occupancy=occupancy,
            co2=co2,
            current_power_w=power,
            current_setpoint=current_setpoint,
            current_fan=current_fan
        )

        # 4. Save Optimization Decision
        opt_record = {
            "baseline_setpoint": rec["baseline_setpoint"],
            "baseline_fan": rec["baseline_fan"],
            "baseline_power_w": rec["baseline_power_w"],
            "recommended_setpoint": rec["recommended_setpoint"],
            "recommended_fan_speed": rec["recommended_fan_speed"],
            "predicted_power_w": rec["predicted_power_w"],
            "power_saved_w": rec["power_saved_w"],
            "savings_percentage": rec["savings_percentage"],
            "occupancy_state": occupancy,
            "co2_level": co2,
            "indoor_temp": indoor_temp,
            "outdoor_temp": outdoor_temp,
            "optimization_mode": rec["optimization_mode"],
            "justification": rec["justification"]
        }
        self.db.insert_optimization(opt_record)

        # 5. Fetch Cumulative Lifetime / Today's Stats from Database
        stats = self.db.get_overall_energy_stats()

        # 6. Build Comprehensive JSON Recommendation Packet for Node-RED Dashboard
        rec_packet = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "indoor_temperature": indoor_temp,
            "outdoor_temperature": outdoor_temp,
            "humidity": humidity,
            "occupancy": "OCCUPIED" if occupancy == 1 else "UNOCCUPIED",
            "co2_ppm": co2,
            "voltage": voltage,
            "current": current,
            "realtime_power_w": power,
            "cumulative_energy_kwh": energy_kwh,
            # Baseline vs Optimized Comparison
            "baseline_setpoint": rec["baseline_setpoint"],
            "baseline_fan": rec["baseline_fan"],
            "baseline_power_w": rec["baseline_power_w"],
            "recommended_setpoint": rec["recommended_setpoint"],
            "recommended_fan_speed": rec["recommended_fan_speed"],
            "predicted_power_w": rec["predicted_power_w"],
            "power_saved_w": rec["power_saved_w"],
            "savings_percentage": rec["savings_percentage"],
            "cost_saved_usd": round(stats["total_kwh_saved"] * 0.15, 2),
            "total_kwh_saved": stats["total_kwh_saved"],
            "optimization_mode": rec["optimization_mode"],
            "comfort_status": rec["comfort_status"],
            "iaq_status": rec["iaq_status"],
            "justification": rec["justification"]
        }

        # 7. Publish to Dashboard & Control Topics
        self.client.publish(TOPIC_RECOMMENDATIONS, json.dumps(rec_packet))

        # Direct Control Packet for ESP32 Actuator
        control_packet = {
            "recommended_setpoint": rec["recommended_setpoint"],
            "recommended_fan_speed": rec["recommended_fan_speed"],
            "hvac_power_mode": rec["hvac_power_mode"]
        }
        self.client.publish(TOPIC_CONTROL, json.dumps(control_packet))

        # 8. Console Logging for Demonstration & Debugging
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
              f"T_in: {indoor_temp:4.1f}C | Occ: {occupancy} | CO2: {int(co2):4d}ppm | "
              f"Base: {rec['baseline_power_w']:5.0f}W -> Opt: {rec['predicted_power_w']:5.0f}W | "
              f"Save: {rec['power_saved_w']:4.0f}W ({rec['savings_percentage']:4.1f}%) | "
              f"SP: {rec['recommended_setpoint']}C [{rec['recommended_fan_speed']}]")

    def start(self):
        """Starts the engine MQTT event loop."""
        self.is_running = True
        try:
            print(f"[ENGINE] Connecting to MQTT Broker: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
            self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEPALIVE)
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"[ENGINE ERROR] Unexpected exception: {e}")
            self.stop()

    def stop(self):
        """Gracefully halts the engine."""
        print("\n[ENGINE] Shutting down HVAC Optimization Service...")
        self.is_running = False
        self.client.publish(TOPIC_STATUS, json.dumps({"engine_status": "OFFLINE"}), retain=True)
        self.client.disconnect()
        print("[ENGINE] Done.")


if __name__ == "__main__":
    engine = HVACOptimizationEngine()
    engine.start()

