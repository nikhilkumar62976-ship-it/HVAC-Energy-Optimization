# Comprehensive Implementation & Environment Audit Report
## Project: HVAC Energy Optimization Using IoT Analytics
**Audit Date**: 2026-10-31  
**Audit Location**: `C:\Users\dell\OneDrive\Desktop\HVAC-Energy-Optimiztion`  
**Execution Environment**: Windows 11 / PowerShell / Python 3.14.7  

---

## 1. Executive Summary & Verification Matrix

| Audit Item | Verification Status | Key Evidence / Observations |
|---|---|---|
| **Workspace Path & Layout** | **PASS** | Confirmed directory `C:\Users\dell\OneDrive\Desktop\HVAC-Energy-Optimiztion`. All 7 subdirectories and root files verified. |
| **Project Source Files Existence** | **PASS** | 20 project files confirmed present with non-zero byte lengths. |
| **Python Virtual Environment** | **PASS** | `.venv` active with Python 3.14.7 and pip 26.2.1. |
| **Python Dependencies** | **PASS** | `paho-mqtt` 2.1.0, `numpy` 2.5.4, `pandas` 3.1.0, `scikit-learn` 1.9.1, `scipy` 1.18.1, `joblib` 1.6.0 installed. |
| **Node.js & npm** | **FAIL** | Neither `node` nor `npm` are installed or found on system PATH. |
| **Node-RED Installation** | **FAIL** | `node-red` executable is missing from the system. |
| **Node-RED Flow JSON Syntax** | **PASS** | `nodered/flows.json` contains 25 valid JSON nodes; requires `node-red-dashboard` package. |
| **Local Mosquitto MQTT Broker** | **FAIL** | Mosquitto executable and Windows Service are NOT installed; port 1883 is closed. |
| **HiveMQ Cloud Configuration** | **NOT CONFIGURED** | No remote broker credentials found in environment variables or `.env`. System configured for `localhost:1883`. |
| **MQTT Connectivity** | **CONNECTION FAILED** | Local port 1883 inactive; connection refused when attempting socket connection. |
| **SQLite Database Persistence** | **PASS** | `data/hvac_data.db` operational. Table schema created, telemetry inserted and verified via unit tests. |
| **ML Model Pipeline** | **PASS** | Model file `data/hvac_energy_model.joblib` loads and generates consistent predictions. |
| **ML Metrics Reproducibility** | **PASS** | $R^2 = 0.9151$, $\text{RMSE} = 88.90\text{ W}$, $\text{MAE} = 46.53\text{ W}$ verified by script execution. |
| **Energy Savings Reproducibility** | **PASS** | $50.97\%$ overall reduction, $38.3\%$ occupied reduction, $65.3\%$ setback reduction reproduced via `evaluate_results.py`. |
| **Simulation Test Suite** | **PASS** | 6 out of 6 unit tests in `tests/test_simulation.py` executed and passed cleanly. |
| **Physical Hardware Availability** | **NOT CONNECTED** | No COM serial ports or ESP32 hardware detected on system bus. |

---

## 2. Actual Workspace Path & File Inventory

### Actual Path:
`C:\Users\dell\OneDrive\Desktop\HVAC-Energy-Optimiztion`

### Verified Files & Sizes:
| File Relative Path | Size (Bytes) | Category | Audit Findings |
|---|---|---|---|
| `requirements.txt` | 168 | Dependencies | Contains required packages; all installed in `.venv`. |
| `README.md` | 6,600 | Documentation | Overview and quick-start instructions. |
| `firmware/esp32_hvac_monitor/esp32_hvac_monitor.ino` | 12,471 | Firmware | Arduino C++ firmware. Complete logic; contains standard Wi-Fi & MQTT placeholders (`YOUR_WIFI_SSID`). |
| `python/config.py` | 2,666 | Backend Config | Central settings. Configured for `localhost:1883` unencrypted MQTT. |
| `python/database.py` | 11,060 | Database | SQLite manager with thread-safe pooling and schema indexing. |
| `python/ml_model.py` | 5,649 | ML Predictor | Random Forest predictor with thermodynamic analytical fallback. |
| `python/optimizer.py` | 9,182 | Optimizer | Grid search optimizer implementing ASHRAE 55 and ASHRAE 62.1. |
| `python/engine.py` | 9,817 | Central Service | Ingestion loop. Ready, but blocked by missing MQTT broker. |
| `python/simulate_telemetry.py` | 7,923 | Simulator | Telemetry generator. Ready, but blocked by missing MQTT broker. |
| `python/train_model.py` | 7,262 | ML Training | Synthesizes dataset and trains Random Forest model. |
| `python/evaluate_results.py` | 7,564 | Evaluation | Evaluates baseline vs. optimized operating strategies. |
| `nodered/flows.json` | 15,246 | Dashboard Flow | 25 nodes (valid JSON); uses `node-red-dashboard` UI nodes. |
| `data/sample_dataset.csv` | 261,078 | Dataset | 6,000 synthetic thermodynamic operational records. |
| `data/hvac_energy_model.joblib` | 17,970,657 | Model Artifact | Serialized Random Forest Regressor artifact. |
| `data/hvac_data.db` | 36,864 | Database File | SQLite database file with active tables. |
| `docs/CIRCUIT_AND_HARDWARE.md` | 12,947 | Documentation | Detailed pinout, BOM, safety optoisolation & calibration. |
| `docs/MATHEMATICAL_FORMULATION.md` | 7,188 | Documentation | Multi-objective cost equations & thermodynamic formulas. |
| `docs/SYSTEM_ARCHITECTURE.md` | 9,350 | Documentation | Data flow diagram, MQTT topic hierarchies & JSON schemas. |
| `docs/SETUP_AND_EXECUTION_GUIDE.md` | 6,378 | Documentation | Step-by-step setup guide for all software modules. |
| `docs/BTECH_PROJECT_REPORT.md` | 18,505 | Academic Report | Dissertation documentation with Viva-Voce Q&A. |
| `tests/test_simulation.py` | 4,200 | Verification | Automated test suite validating DB, ML, and optimizer. |

---

## 3. Software Environment Audit

| Tool / Runtime | Target Requirement | Detected Status | Evidence Command Output |
|---|---|---|---|
| **Python** | 3.10+ | **PASS** (3.14.7) | `Python 3.14.7` at `C:\Users\dell\AppData\Local\Programs\Python\Python314` |
| **pip** | 22.0+ | **PASS** (26.2.1) | `pip 26.2.1` |
| **Virtualenv (`.venv`)** | Active | **PASS** | Virtual environment exists and packages resolved. |
| **paho-mqtt** | 2.0+ | **PASS** (2.1.0) | Installed in `.venv`. |
| **numpy** | 2.0+ | **PASS** (2.5.4) | Installed in `.venv`. |
| **pandas** | 2.0+ | **PASS** (3.1.0) | Installed in `.venv`. |
| **scikit-learn** | 1.5+ | **PASS** (1.9.1) | Installed in `.venv`. |
| **scipy** | 1.10+ | **PASS** (1.18.1) | Installed in `.venv`. |
| **joblib** | 1.4+ | **PASS** (1.6.0) | Installed in `.venv`. |
| **Node.js** | 18+ | **FAIL** (Missing) | `'node' is not recognized as an operable program` |
| **npm** | 9+ | **FAIL** (Missing) | `'npm' is not recognized as an operable program` |
| **Node-RED** | 3.0+ | **FAIL** (Missing) | `'node-red' is not recognized as an operable program` |
| **Mosquitto** | 2.0+ | **FAIL** (Missing) | `'mosquitto' is not recognized as an operable program` |
| **SQLite3 CLI** | 3.x | **BLOCKED** (CLI missing) | CLI tool missing from PATH; Python `sqlite3` driver works properly. |

---

## 4. MQTT Broker & Connectivity Audit

1. **Local Mosquitto Broker**:
   - Status: **FAIL (Not Installed & Not Running)**.
   - Verification: No Windows service exists matching `mosquitto` or `mqtt`. Port 1883 has no active listening socket.
2. **HiveMQ Cloud / Remote Broker**:
   - Status: **NOT CONFIGURED**.
   - Verification: No remote broker URLs, tokens, or credentials exist in environment variables or `.env`. The project defaults to `MQTT_BROKER_HOST = "localhost"` on port 1883 without TLS.
3. **MQTT Topics Defined in Code**:
   - Telemetry Stream: `building/hvac/telemetry`
   - Recommendation Stream: `building/hvac/recommendations`
   - Hardware Control Directives: `building/hvac/control`
   - Node Heartbeat / Birth Testament: `building/hvac/status`
4. **Current Impact**:
   - Running `python -m python.engine` or `python -m python.simulate_telemetry` fails with a TCP connection refusal (`WinError 10061`) until an MQTT broker is started.

---

## 5. Simulation Mode & Python Component Verification

A standalone test suite [`tests/test_simulation.py`](file:///c:/Users/dell/OneDrive/Desktop/HVAC-Energy-Optimiztion/tests/test_simulation.py) was executed to verify simulation capabilities without requiring live MQTT or physical hardware:

```
test_01_database_persistence ... ok
test_02_ml_prediction_pipeline ... ok
test_03_optimizer_occupied_comfort ... ok
test_04_optimizer_unoccupied_setback ... ok
test_05_optimizer_co2_ventilation_override ... ok
test_06_energy_savings_math ... ok
----------------------------------------------------------------------
Ran 6 tests in 5.574s

OK
```

### Specific Verification Results:
1. **SQLite Persistence**: Successfully inserted a 14-parameter telemetry dictionary. Readback matched recorded temperature ($25.4^\circ\text{C}$) and power ($1080.0\text{ W}$) with zero data corruption.
2. **Thermodynamic Monotonicity**: Model correctly predicted:
   - Fixed Baseline ($21^\circ\text{C}$, HIGH fan): **1,850.0 Watts**
   - Optimized Comfort ($24.5^\circ\text{C}$, MEDIUM fan): **1,210.0 Watts**
   - Unoccupied Setback ($28^\circ\text{C}$, LOW fan): **480.0 Watts**
   - $P_{baseline} > P_{optimized} > P_{unoccupied}$ held strictly true.
3. **Occupancy Setback Verification**: Under $Occ = 0$, setpoint dynamically adjusted to $28.0^\circ\text{C}$ with fan set to `LOW`, achieving $65.3\%$ energy reduction.
4. **Ventilation Override Verification**: Under $CO_2 = 1250\text{ ppm} > 1000\text{ ppm}$, optimizer immediately escalated fan speed to `HIGH` and logged `VENTILATION_PURGE` mode to protect occupant safety.

---

## 6. Verification of Reported Machine Learning Results

### Claimed Figures from Prior Report:
- $R^2 = 0.9151$ (91.51%)
- $\text{RMSE} = 88.90\text{ Watts}$
- $\text{MAE} = 46.53\text{ Watts}$
- Overall Energy Savings $= 50.97\%$

### Audit Assessment:
- **Reproducibility Classification**: **Category A (Reproduced by executing the actual code)**.
- **Verification Evidence**:
  - Executing `python -m python.train_model` using fixed random seed 42 reproduced:
    - $R^2 = 0.9151$
    - $\text{RMSE} = 88.90\text{ W}$
    - $\text{MAE} = 46.53\text{ W}$
    - $\text{MAPE} = 22.28\%$
  - Executing `python -m python.evaluate_results` across 120 diurnal intervals (10 operating hours) reproduced:
    - Baseline Energy: $6.57\text{ kWh}$
    - Optimized Energy: $3.22\text{ kWh}$
    - Conserved Energy: $3.35\text{ kWh}$
    - **Overall Savings: 50.97%**
    - Peak load curtailment (12 PM – 4 PM): $41.1\%$ ($400.2\text{ W}$ shaved)
- **Critical Limitations & Data Integrity Notes**:
  - The dataset [`data/sample_dataset.csv`](file:///c:/Users/dell/OneDrive/Desktop/HVAC-Energy-Optimiztion/data/sample_dataset.csv) was generated synthetically using building thermodynamic formulas (heat transfer across envelope, COP degradation with ambient heat, internal metabolic gains).
  - The model fits the data with high fidelity because both training data and ground truth stem from identical physical differential relationships with injected Gaussian noise ($\sigma = 35\text{ W}$).
  - These results represent **idealized thermodynamic simulation performance**, not measured empirical readings from an active physical commercial building.

---

## 7. Node-RED Dashboard Verification

1. **Runtime Accessibility**: **FAIL**. Node.js, npm, and Node-RED are not installed on the host machine.
2. **Flow File Integrity**: **PASS**. [`nodered/flows.json`](file:///c:/Users/dell/OneDrive/Desktop/HVAC-Energy-Optimiztion/nodered/flows.json) is valid JSON (25 nodes).
3. **Dashboard Node Dependency**: The flow utilizes nodes from the `node-red-dashboard` palette:
   - `ui_tab`, `ui_group`, `ui_base`
   - `ui_gauge` (Temperature, Humidity, $CO_2$, Power, Energy Savings %)
   - `ui_chart` (Before-vs-After real-time load comparison)
   - `ui_text` (Voltage, Current, Cumulative kWh, Setpoint, Fan Speed)
   - `ui_template` (Custom CSS-styled Occupancy badge & Engineering Justification callout card)
4. **Current Status**: The dashboard **cannot be launched or viewed** until Node.js and Node-RED are installed.

---

## 8. Physical Hardware & Sensor Verification

1. **Connected Microcontrollers**: **NONE DETECTED**. Windows Device Manager and CIM queries report no active COM/serial ports.
2. **Physical Sensors**: **NOT CONNECTED**. DHT22, PIR, MQ-135, and PZEM-004T are not currently physically wired to the host PC.
3. **Firmware Status**: [`firmware/esp32_hvac_monitor/esp32_hvac_monitor.ino`](file:///c:/Users/dell/OneDrive/Desktop/HVAC-Energy-Optimiztion/firmware/esp32_hvac_monitor/esp32_hvac_monitor.ino) is ready for compilation in the Arduino IDE, but requires flashing onto an ESP32 board once hardware is connected.

---

## 9. Deficiencies, Blockers & Exact Errors

| Component | Nature of Issue | Error Message / Symptom | Impact |
|---|---|---|---|
| **Mosquitto** | Missing Broker | `[WinError 10061] No connection could be made because the target machine actively refused it` | Prevents live MQTT communication between Python engine, simulator, and ESP32. |
| **Node-RED** | Missing Runtime | `'node-red' is not recognized as an operable program` | Prevents hosting and opening the web dashboard at `http://localhost:1880/ui`. |
| **Node.js** | Missing Dependency | `'node' is not recognized as an operable program` | Prerequisite for Node-RED is missing. |
| **Hardware** | Unconnected Device | No COM port detected | ESP32 cannot be flashed or tested over physical USB yet. |

---

## 10. Recommended Next Steps

1. **Option A (Zero Installation / Standalone Simulation Mode)**:
   - Run the system in offline mode by writing a lightweight in-memory MQTT mock broker or local socket bridge so `python/engine.py` and `python/simulate_telemetry.py` can communicate without needing Mosquitto.
2. **Option B (Install Missing Host Prerequisite Software)**:
   - Install **Node.js 20 LTS** (which includes npm).
   - Install **Node-RED** (`npm install -g --unsafe-perm node-red`) and `node-red-dashboard`.
   - Install **Eclipse Mosquitto** Windows Broker and start the Windows service.
3. **Option C (Cloud MQTT Setup)**:
   - Configure a free HiveMQ Cloud or EMQX Cloud broker URL in `python/config.py` with TLS enabled, allowing the Python engine and ESP32 to communicate over the internet without installing a local Mosquitto service.

