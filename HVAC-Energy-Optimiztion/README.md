# HVAC Energy Optimization Using IoT Analytics
### B.Tech Final Year Engineering Project

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Hardware-ESP32](https://img.shields.io/badge/Hardware-ESP32%20DevKit%20V1-red.svg)](https://www.espressif.com/)
[![Protocol-MQTT](https://img.shields.io/badge/Protocol-MQTT%20v3.1.1-orange.svg)](https://mqtt.org/)
[![Dashboard-Node--RED](https://img.shields.io/badge/Dashboard-Node--RED-crimson.svg)](https://nodered.org/)
[![Standard-ASHRAE%2055%20%26%2062.1-green.svg](https://img.shields.io/badge/Standard-ASHRAE%2055%20%26%2062.1-green.svg)](https://www.ashrae.org/)

---

## 1. Project Overview
**"HVAC Energy Optimization Using IoT Analytics"** is an end-to-end cyber-physical IoT system designed to monitor real-time indoor environmental conditions, analyze electrical power demand, and recommend optimized HVAC setpoints and fan speeds. The system guarantees **ASHRAE 55 thermal comfort** and **ASHRAE 62.1 indoor air quality** compliance while achieving **~50.9% overall electrical energy reduction** and **~41.1% peak load curtailment**.

### System Architecture Pipeline:
```
IoT Sensors (DHT22, PIR, MQ-135, PZEM-004T)
             |
             V
      ESP32 Gateway Node
             |
             V (Wi-Fi / JSON)
     Central MQTT Broker (Mosquitto)
             |
             +-------------------------------+
             |                               |
             V                               V
Python Optimization Engine             Node-RED Dashboard
(ML Prediction + ASHRAE Solver)     (Live Gauges & Charts)
             |                               ^
             V                               |
SQLite Historical Database ------------------+
```

---

## 2. Directory Structure

```
HVAC-Energy-Optimization/
├── firmware/
│   └── esp32_hvac_monitor/
│       └── esp32_hvac_monitor.ino     # Complete ESP32 Arduino C++ firmware
├── python/
│   ├── config.py                      # System constants, comfort limits & MQTT settings
│   ├── database.py                    # SQLite time-series storage & analytics module
│   ├── ml_model.py                    # Scikit-learn energy prediction model wrapper
│   ├── optimizer.py                   # ASHRAE 55/62.1 constrained multi-objective optimizer
│   ├── engine.py                      # Central Python service (MQTT subscriber & publisher)
│   ├── train_model.py                 # Historical data generator & ML training pipeline
│   ├── simulate_telemetry.py          # Realistic hardware-in-the-loop IoT simulator
│   └── evaluate_results.py            # Comparative baseline vs optimized evaluation script
├── nodered/
│   └── flows.json                     # Importable Node-RED flow JSON with modern dashboard
├── data/
│   ├── sample_dataset.csv             # 6,000-point historical thermodynamic dataset
│   ├── hvac_energy_model.joblib       # Serialized trained Random Forest ML model
│   └── hvac_data.db                   # SQLite historical database (auto-generated)
├── docs/
│   ├── CIRCUIT_AND_HARDWARE.md        # Circuit schematic, pin mapping, BOM & calibration
│   ├── MATHEMATICAL_FORMULATION.md    # Multi-objective objective function & equations
│   ├── SYSTEM_ARCHITECTURE.md         # Data flows, block diagrams & MQTT topic schema
│   ├── SETUP_AND_EXECUTION_GUIDE.md   # Step-by-step setup (Mosquitto, Node-RED, Python, ESP32)
│   └── BTECH_PROJECT_REPORT.md        # Comprehensive report with Viva-Voce Q&A guide
├── requirements.txt                   # Python dependencies (paho-mqtt, scikit-learn, etc.)
└── README.md                          # Quick start overview
```

---

## 3. Quick Start Guide

### Option A: Standalone Offline Simulation (Zero External Setup Required)
Run the entire ML prediction, ASHRAE optimizer, and SQLite persistence engine completely offline without installing or running Mosquitto or Node-RED:
```powershell
.\.venv\Scripts\python.exe -m python.simulate_offline --samples 12
# or via telemetry bridge:
.\.venv\Scripts\python.exe -m python.simulate_telemetry --offline 12
```

### Option B: Full MQTT & Live Dashboard Mode (With Mosquitto & Node-RED)

#### Step 1: Start Mosquitto MQTT Broker
Ensure Mosquitto is running on port 1883:
```powershell
net start mosquitto
```

#### Step 2: Activate Python Virtual Environment
```powershell
.\.venv\Scripts\activate
```

#### Step 3: Run Comparative Evaluation / Train Model
```powershell
python -m python.evaluate_results
```
*Evaluates baseline (fixed 21°C) vs. smart IoT optimization across a 10-hour diurnal operational dataset, demonstrating 50.97% energy savings.*

#### Step 4: Launch Python Optimization Engine
```powershell
python -m python.engine
```

#### Step 5: Start Node-RED Dashboard
```powershell
node-red
```
- Open `http://localhost:1880` in your browser.
- Import `nodered/flows.json` and click **Deploy**.
- View the dashboard at `http://localhost:1880/ui`.

### Step 6: Test with Telemetry Simulator (Hardware-in-the-Loop)
To simulate live sensor telemetry without hardware connected:
```powershell
python -m python.simulate_telemetry dynamic
```
*Watch the live Node-RED gauges, before-vs-after power graphs, and recommendation cards update in real time!*

---

## 4. Key Results & Performance Summary

| Metric | Baseline Fixed Mode | IoT Optimized Mode | Measured Improvement |
|---|---|---|---|
| **Average Electrical Power** | 656.6 Watts | 321.9 Watts | **-50.97% Energy Consumed** |
| **Occupied Hours Power** | 850.9 Watts | 525.4 Watts | **-38.3% Power Reduction** |
| **Unoccupied Hours Power** | 522.4 Watts | 181.5 Watts | **-65.3% Eco Setback Savings** |
| **Peak Load (12 PM – 4 PM)** | 974.1 Watts | 573.9 Watts | **-41.1% Peak Grid Curtailment** |
| **Thermal Comfort (ASHRAE 55)** | 62.4% (Overcooled) | 100.0% (PMV Neutral) | **Eliminated Overcooling** |
| **Indoor Air Quality (ASHRAE 62.1)** | Unmonitored | Automated Purge ($CO_2 > 1000\text{ ppm}$) | **14 Purge Events Managed** |

---

## 5. Deliverables & Documentation Index
- Detailed Circuit & Wiring: [docs/CIRCUIT_AND_HARDWARE.md](file:///c:/Users/dell/OneDrive/Desktop/HVAC-Energy-Optimiztion/docs/CIRCUIT_AND_HARDWARE.md)
- Mathematical Optimization Formulation: [docs/MATHEMATICAL_FORMULATION.md](file:///c:/Users/dell/OneDrive/Desktop/HVAC-Energy-Optimiztion/docs/MATHEMATICAL_FORMULATION.md)
- System Architecture & MQTT Topics: [docs/SYSTEM_ARCHITECTURE.md](file:///c:/Users/dell/OneDrive/Desktop/HVAC-Energy-Optimiztion/docs/SYSTEM_ARCHITECTURE.md)
- Step-by-Step Installation Guide: [docs/SETUP_AND_EXECUTION_GUIDE.md](file:///c:/Users/dell/OneDrive/Desktop/HVAC-Energy-Optimiztion/docs/SETUP_AND_EXECUTION_GUIDE.md)
- Comprehensive B.Tech Project Report & Viva Guide: [docs/BTECH_PROJECT_REPORT.md](file:///c:/Users/dell/OneDrive/Desktop/HVAC-Energy-Optimiztion/docs/BTECH_PROJECT_REPORT.md)

