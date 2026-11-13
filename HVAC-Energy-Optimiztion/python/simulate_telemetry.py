"""
HVAC Energy Optimization Using IoT Analytics
IoT Telemetry Simulator / Test-Bench Utility
Emulates the ESP32 Hardware Node by publishing realistic sensor telemetry to MQTT.
Allows testing the complete pipeline, Node-RED dashboard, and optimization engine
with or without physical breadboard hardware.
"""

import sys
import time
import json
import random
import datetime
import paho.mqtt.client as mqtt

from python.config import (
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    TOPIC_TELEMETRY,
    TOPIC_CONTROL
)

# Active State tracking (updated if optimizer sends control directives back)
simulated_state = {
    "setpoint": 24.0,
    "fan_speed": "MEDIUM",
    "hvac_state": "ON",
    "cumulative_energy_kwh": 14.85
}


def on_control_message(client, userdata, msg):
    """Listens for setpoint updates dispatched by Python Optimization Engine."""
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        if "recommended_setpoint" in data:
            simulated_state["setpoint"] = float(data["recommended_setpoint"])
        if "recommended_fan_speed" in data:
            simulated_state["fan_speed"] = str(data["recommended_fan_speed"])
        if "hvac_power_mode" in data:
            simulated_state["hvac_state"] = str(data["hvac_power_mode"])
        print(f"[SIMULATOR RECEIVED FEEDBACK] Actuator adjusted -> Setpoint: {simulated_state['setpoint']}C | Fan: {simulated_state['fan_speed']}")
    except Exception as e:
        pass


def run_simulation(interval_seconds: float = 3.0, scenario: str = "dynamic"):
    """
    Publishes continuous telemetry packets simulating realistic indoor & electrical conditions.
    Scenarios:
      - 'dynamic'   : Alternates through realistic occupied, unoccupied, and high CO2 cycles.
      - 'occupied'  : Simulates standard occupied room with steady human presence.
      - 'unoccupied': Demonstrates eco setback energy conservation.
      - 'co2_spike' : Demonstrates indoor air quality ventilation purge trigger.
    """
    print("\n=======================================================")
    print("  ESP32 TELEMETRY HARDWARE EMULATOR / TEST BENCH       ")
    print(f"  Target Broker: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    print(f"  Topic: {TOPIC_TELEMETRY}")
    print(f"  Cadence: {interval_seconds}s per sample | Mode: {scenario.upper()}")
    print("=======================================================\n")

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="ESP32_Hardware_Simulator"
    )

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.on_message = on_control_message

    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        client.subscribe(TOPIC_CONTROL)
        client.loop_start()
    except Exception as e:
        print(f"[FATAL] Cannot connect simulator to MQTT Broker ({e}). Check if Mosquitto is active.")
        sys.exit(1)

    step = 0
    current_temp = 25.8
    current_co2 = 550.0

    try:
        while True:
            step += 1
            now = datetime.datetime.now()
            hour = now.hour

            # Scenario state machine
            if scenario == "dynamic":
                # Cycle every 10 steps (~30 seconds):
                cycle_phase = (step // 8) % 3
                if cycle_phase == 0:
                    # Occupied, Normal Comfort
                    is_occupied = 1
                    target_co2 = 680.0
                    target_indoor_temp = simulated_state["setpoint"] + 0.4
                    mode_label = "OCCUPIED_NORMAL"
                elif cycle_phase == 1:
                    # High CO2 ventilation alert
                    is_occupied = 1
                    target_co2 = 1180.0
                    target_indoor_temp = simulated_state["setpoint"] + 0.6
                    mode_label = "HIGH_CO2_EVENT"
                else:
                    # Empty room (lunch break or evening)
                    is_occupied = 0
                    target_co2 = 450.0
                    target_indoor_temp = 28.2
                    mode_label = "UNOCCUPIED_SETBACK"
            elif scenario == "occupied":
                is_occupied = 1
                target_co2 = 720.0
                target_indoor_temp = simulated_state["setpoint"] + 0.3
                mode_label = "OCCUPIED_STEADY"
            elif scenario == "unoccupied":
                is_occupied = 0
                target_co2 = 430.0
                target_indoor_temp = 28.5
                mode_label = "UNOCCUPIED_ECO"
            else:  # co2_spike
                is_occupied = 1
                target_co2 = 1350.0
                target_indoor_temp = 25.0
                mode_label = "CO2_PURGE_TEST"

            # Outdoor ambient temperature
            outdoor_temp = 34.0 + 5.0 * random.uniform(-0.4, 0.4)
            humidity = 58.0 + random.uniform(-3.0, 3.0)

            # Smoothly drift indoor temperature toward target
            current_temp += (target_indoor_temp - current_temp) * 0.15 + random.uniform(-0.08, 0.08)
            current_co2 += (target_co2 - current_co2) * 0.20 + random.uniform(-8.0, 8.0)

            # Electrical telemetry modeling (PZEM-004T)
            voltage = 230.0 + random.uniform(-2.5, 2.5)
            # Active power drawn depends on temperature difference and fan speed
            if simulated_state["hvac_state"] == "OFF":
                power_w = 12.0
            else:
                cooling_delta = max(0.0, current_temp - simulated_state["setpoint"])
                fan_w = {"LOW": 45.0, "MEDIUM": 85.0, "HIGH": 140.0}.get(simulated_state["fan_speed"], 85.0)
                compressor_w = 400.0 + cooling_delta * 320.0 if cooling_delta > 0.2 else 80.0
                power_w = compressor_w + fan_w + random.uniform(-20.0, 20.0)

            power_w = max(15.0, round(power_w, 1))
            power_factor = 0.93 + random.uniform(-0.02, 0.02)
            current_a = round(power_w / (voltage * power_factor), 2)

            # Accumulate kWh
            simulated_state["cumulative_energy_kwh"] += (power_w * (interval_seconds / 3600.0)) / 1000.0

            # Telemetry Payload matching ESP32 firmware schema
            packet = {
                "device_id": "ESP32_HVAC_SIMULATOR",
                "timestamp_ms": int(time.time() * 1000),
                "temperature": round(current_temp, 2),
                "humidity": round(humidity, 1),
                "occupancy": is_occupied,
                "co2": round(current_co2, 0),
                "voltage": round(voltage, 1),
                "current": current_a,
                "power": power_w,
                "energy_kwh": round(simulated_state["cumulative_energy_kwh"], 3),
                "frequency": 50.0,
                "power_factor": round(power_factor, 2),
                "hvac_state": simulated_state["hvac_state"],
                "active_setpoint": simulated_state["setpoint"],
                "active_fan": simulated_state["fan_speed"],
                "outdoor_temperature": round(outdoor_temp, 1),
                "sim_scenario": mode_label
            }

            json_str = json.dumps(packet)
            client.publish(TOPIC_TELEMETRY, json_str)

            print(f"[TX #{step:03d} | {mode_label:<18}] "
                  f"Tin: {current_temp:4.1f}C | Tout: {outdoor_temp:4.1f}C | "
                  f"Occ: {is_occupied} | CO2: {int(current_co2):4d}ppm | "
                  f"Power: {power_w:5.0f}W | {voltage:5.1f}V | {current_a:4.2f}A")

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n[SIMULATOR] Simulation stopped by user.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["--offline", "offline"]:
        from python.simulate_offline import run_offline_simulation
        samples = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 12
        run_offline_simulation(num_samples=samples)
    else:
        mode = "dynamic"
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
        run_simulation(interval_seconds=3.0, scenario=mode)

