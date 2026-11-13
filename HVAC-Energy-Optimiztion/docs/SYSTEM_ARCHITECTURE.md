# System Architecture & MQTT Communications Specification
## Project: HVAC Energy Optimization Using IoT Analytics

---

## 1. End-to-End System Workflow

```
+---------------------------------------------------------------------------------------------------+
|                                      PHYSICAL EDGE SENSING LAYER                                  |
|                                                                                                   |
|  +--------------------+  +--------------------+  +--------------------+  +---------------------+  |
|  |       DHT22        |  |     HC-SR501 PIR   |  |       MQ-135       |  |    PZEM-004T v3.0   |  |
|  |  (Temp & Humidity) |  |    (Occupancy)     |  |    (CO2 & IAQ)     |  | (V, I, Power, kWh)  |  |
|  +---------+----------+  +---------+----------+  +---------+----------+  +----------+----------+  |
+------------|-----------------------|-----------------------|------------------------|-------------+
             | GPIO 4 (1-Wire)       | GPIO 13 (Digital)     | GPIO 34 (ADC1)         | GPIO 16/17 (UART)
             V                       V                       V                        V
+---------------------------------------------------------------------------------------------------+
|                                  ESP32 EDGE PROCESSING GATEWAY                                    |
|                                                                                                   |
|  - Sensor sampling at 5-second non-blocking intervals (`millis()`).                               |
|  - Analog voltage to PPM conversion & calibration curve calculation.                             |
|  - JSON serialization via `ArduinoJson`.                                                          |
|  - Wi-Fi 802.11 b/g/n client management & auto-reconnect logic.                                   |
|  - MQTT client dispatching telemetry packets.                                                     |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  | Wi-Fi (TCP/IP)
                                                  | Topic: building/hvac/telemetry
                                                  V
+---------------------------------------------------------------------------------------------------+
|                                   CENTRAL MQTT MESSAGE BROKER                                     |
|                                  (Eclipse Mosquitto / Port 1883)                                  |
|                                                                                                   |
|  Publishes & Subscribes:                                                                          |
|    - `building/hvac/telemetry`       <-- Telemetry stream from ESP32 & Simulator                  |
|    - `building/hvac/recommendations` --> Analytical packets sent to Node-RED Dashboard           |
|    - `building/hvac/control`         --> Setpoints & fan commands to ESP32 / Actuators            |
|    - `building/hvac/status`          --> Node online/offline heartbeat status                     |
+----------------------+----------------------------------------------------+-----------------------+
                       |                                                    |
                       | Telemetry Stream                                   | Recommendations Stream
                       V                                                    V
+----------------------------------------------------+    +-----------------------------------------+
|             PYTHON OPTIMIZATION ENGINE             |    |           NODE-RED DASHBOARD            |
|                                                    |    |                                         |
|  1. Ingestion: Subscribes to telemetry stream.     |    |  1. Environmental Gauges:               |
|  2. Storage: Persists raw records to SQLite DB.    |    |     - Temperature, Humidity, CO2        |
|  3. ML Inference: Predicts electrical power        |    |  2. Occupancy Indicator Card:           |
|     using trained Random Forest Regressor.         |    |     - Dynamic Human Presence Badge      |
|  4. Optimizer: Evaluates ASHRAE 55 thermal comfort |    |  3. Electrical Monitoring:              |
|     and ASHRAE 62.1 ventilation constraints.       |    |     - Real-Time Power (W), V, I, kWh    |
|  5. Anti-cycling: Prevents rapid motor oscillation |    |  4. AI Recommendation Panel:            |
|     via 3-minute dwell constraint.                 |    |     - Optimal Setpoint & Fan Speed      |
|  6. Savings Quantification: Compares baseline      |    |     - Operating Mode & Justification    |
|     vs optimized predicted power demand.           |    |  5. Energy Conservation Analytics:      |
|  7. Dispatch: Publishes JSON recommendation        |    |     - % Energy Savings Gauge            |
|     packet back to MQTT broker.                    |    |     - Before-vs-After Comparison Chart  |
+----------------------+-----------------------------+    +-----------------------------------------+
                       |
                       V
+----------------------------------------------------+
|               HISTORICAL SQLITE DATABASE           |
|                                                    |
|  - `telemetry` (raw timestamped IoT sensor logs)   |
|  - `optimizations` (decisions & power comparisons) |
|  - `hourly_analytics` (rolling energy & cost data) |
+----------------------------------------------------+
```

---

## 2. MQTT Topic Architecture

| Topic Identifier | Publisher | Subscribers | QoS | Retained | Purpose |
|---|---|---|---|---|---|
| `building/hvac/telemetry` | ESP32 Sensor Node / Telemetry Simulator | Python Optimization Engine, Node-RED | 0 | False | Dispatches real-time indoor environmental and electrical power readings every 5 seconds |
| `building/hvac/recommendations` | Python Optimization Engine | Node-RED Dashboard | 0 | True | Broadcasts processed analytics, recommended setpoints, fan speeds, savings, and justifications |
| `building/hvac/control` | Python Optimization Engine / Dashboard UI | ESP32 Actuator Node | 1 | True | Transmits direct control commands (setpoint, fan speed, power relay) to the HVAC unit |
| `building/hvac/status` | ESP32 Node, Python Engine | System Monitor | 1 | True | Heartbeat topic reporting node health status (`ONLINE` / `OFFLINE`) |

---

## 3. MQTT JSON Payload Schemas

### A. Raw Telemetry Payload (`building/hvac/telemetry`)
Dispatched by the ESP32 hardware node every 5 seconds:

```json
{
  "device_id": "ESP32_HVAC_SensorNode_01",
  "timestamp_ms": 1740825600000,
  "temperature": 24.8,
  "humidity": 58.2,
  "occupancy": 1,
  "co2": 720.0,
  "voltage": 230.4,
  "current": 5.42,
  "power": 1152.0,
  "energy_kwh": 14.862,
  "frequency": 50.0,
  "power_factor": 0.92,
  "hvac_state": "ON",
  "active_setpoint": 24.0,
  "active_fan": "MEDIUM"
}
```

### B. Optimization & Recommendation Payload (`building/hvac/recommendations`)
Dispatched by the Python Optimization Engine to the Node-RED Dashboard:

```json
{
  "timestamp": "2026-10-31T07:35:00.000Z",
  "indoor_temperature": 24.8,
  "outdoor_temperature": 36.2,
  "humidity": 58.2,
  "occupancy": "OCCUPIED",
  "co2_ppm": 720.0,
  "voltage": 230.4,
  "current": 5.42,
  "realtime_power_w": 1152.0,
  "cumulative_energy_kwh": 14.862,
  "baseline_setpoint": 21.0,
  "baseline_fan": "HIGH",
  "baseline_power_w": 1820.0,
  "recommended_setpoint": 24.5,
  "recommended_fan_speed": "MEDIUM",
  "predicted_power_w": 1210.0,
  "power_saved_w": 610.0,
  "savings_percentage": 33.5,
  "cost_saved_usd": 4.12,
  "total_kwh_saved": 27.46,
  "optimization_mode": "OCCUPIED_COMFORT",
  "comfort_status": "COMFORTABLE",
  "iaq_status": "GOOD",
  "justification": "Occupied Comfort Mode: Setpoint 24.5 C satisfies ASHRAE 55 PMV neutral comfort range while conserving fan/compressor power."
}
```

### C. Actuation Directives Payload (`building/hvac/control`)
Dispatched by Python Engine to the ESP32 Actuator:

```json
{
  "recommended_setpoint": 24.5,
  "recommended_fan_speed": "MEDIUM",
  "hvac_power_mode": "ON"
}
```

---

## 4. Reliability & Fail-Safe Architecture

1. **Recommendation-Only vs. Automatic Closed-Loop Mode**:
   - The system is architected to operate initially in **Recommendation-Only Mode**, displaying optimal settings on the dashboard without modifying hardware actuators until validated.
   - When configured in **Closed-Loop Mode**, recommendations are converted into physical control signals via the isolated relay and infrared/Modbus HVAC interface.
2. **Network Disconnection Failsafe**:
   - If the ESP32 loses Wi-Fi or MQTT connectivity, the firmware automatically reverts to an autonomous, local fail-safe mode:
     - Maintains a safe, comfortable default setpoint (24.0°C).
     - Keeps the HVAC compressor enabled if occupied, or set to eco mode.
   - The device continuously attempts to reconnect in the background without blocking sensor reading tasks.
3. **Database Integrity**:
   - SQLite uses WAL (Write-Ahead Logging) and thread-safe connection pooling to prevent database locking during rapid multi-client access.

