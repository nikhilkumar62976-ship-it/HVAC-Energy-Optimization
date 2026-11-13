# Installation & Execution Guide
## Project: HVAC Energy Optimization Using IoT Analytics

---

## 1. System Requirements & Prerequisites

Ensure the following tools are installed on your host machine:

| Component | Minimum Version | Installation Link / Command |
|---|---|---|
| **Python** | 3.10+ (tested on Python 3.14) | [python.org](https://www.python.org/downloads/) |
| **Mosquitto MQTT Broker** | 2.0+ | [mosquitto.org](https://mosquitto.org/download/) |
| **Node.js & Node-RED** | Node 18+, Node-RED 3.0+ | `npm install -g --unsafe-perm node-red` |
| **Node-RED Dashboard** | 3.6+ | `npm install node-red-dashboard` (inside `~/.node-red`) |
| **Arduino IDE** | 2.0+ | [arduino.cc](https://www.arduino.cc/en/software) |

---

## 2. Step 1: Setting up Mosquitto MQTT Broker

### On Windows:
1. Download and run the Eclipse Mosquitto Windows installer.
2. Open `C:\Program Files\mosquitto\mosquitto.conf` in a text editor (as Administrator) and ensure the following two lines exist at the end of the file:
   ```conf
   listener 1883
   allow_anonymous true
   ```
3. Start Mosquitto from an Administrator PowerShell / Command Prompt:
   ```powershell
   net start mosquitto
   # or run directly:
   & "C:\Program Files\mosquitto\mosquitto.exe" -v -c "C:\Program Files\mosquitto\mosquitto.conf"
   ```

### On Linux (Ubuntu / Debian / Raspberry Pi):
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients -y
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

---

## 3. Step 2: Python Environment & Machine Learning Setup

1. Open PowerShell or Command Prompt in the project root directory:
   ```powershell
   cd c:\Users\dell\OneDrive\Desktop\HVAC-Energy-Optimiztion
   ```

2. Activate the pre-configured virtual environment:
   ```powershell
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # (If script execution is disabled: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)

   # Windows Command Prompt (cmd):
   .\.venv\Scripts\activate.bat
   ```

3. Install project dependencies (if not already installed):
   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Train the Machine Learning Energy Prediction Model:
   ```powershell
   python -m python.train_model
   ```
   *Expected Output*: Generates `data/sample_dataset.csv`, trains a `RandomForestRegressor`, evaluates $R^2 \approx 91.5\%$, and outputs `data/hvac_energy_model.joblib`.

5. Run the Comparative Evaluation Script:
   ```powershell
   python -m python.evaluate_results
   ```
   *Expected Output*: Prints the comparative 10-hour baseline vs. optimized evaluation showing ~50.9% overall energy savings.

---

## 4. Step 3: Launching Node-RED Dashboard

1. Launch Node-RED in a new terminal window:
   ```powershell
   node-red
   ```

2. Open your web browser and navigate to the Node-RED Flow Editor:
   ```
   http://localhost:1880
   ```

3. Install the Dashboard palette if not already present:
   - Click the hamburger menu (top right) $\rightarrow$ **Manage palette** $\rightarrow$ **Install** tab.
   - Search for `node-red-dashboard` and click **Install**.

4. Import the Project Flow:
   - Click the hamburger menu $\rightarrow$ **Import**.
   - Click **select a file to import** and choose `nodered/flows.json` (located in `c:\Users\dell\OneDrive\Desktop\HVAC-Energy-Optimiztion\nodered\flows.json`).
   - Click **Import**, then click the red **Deploy** button in the top-right corner.

5. Access the Interactive Smart Building Dashboard:
   ```
   http://localhost:1880/ui
   ```

---

## 5. Step 4: Running the Python Optimization Engine

In a new terminal window (with the `.venv` activated):

```powershell
python -m python.engine
```

The engine connects to `localhost:1883`, listens for telemetry packets on `building/hvac/telemetry`, applies the ASHRAE 55/62.1 optimization algorithm, logs decisions to SQLite, and publishes optimization recommendations to `building/hvac/recommendations`.

---

## 6. Step 5: Testing with Telemetry Generator (Hardware-in-the-Loop)

If the physical ESP32 breadboard is not yet connected, run the hardware simulator in another terminal window to simulate realistic live telemetry:

```powershell
python -m python.simulate_telemetry dynamic
```

### Available Simulation Scenarios:
- `python -m python.simulate_telemetry dynamic`: Continuously cycles between normal occupied, high CO2 purge, and empty room setback.
- `python -m python.simulate_telemetry occupied`: Simulates steady human occupancy at 24°C comfort.
- `python -m python.simulate_telemetry unoccupied`: Demonstrates the eco setback (28°C) and shows instantaneous ~65% energy reduction.
- `python -m python.simulate_telemetry co2_spike`: Simulates a crowded room ($CO_2 > 1100 \text{ ppm}$) triggering an automated ventilation purge.

Observe the Node-RED dashboard at `http://localhost:1880/ui` instantly updating with live gauges, graphs, and energy-saving metrics!

---

## 7. Step 6: Flashing ESP32 Firmware (Hardware Deployment)

1. Open **Arduino IDE** (version 2.0+).
2. Go to **File** $\rightarrow$ **Preferences** $\rightarrow$ **Additional Boards Manager URLs** and add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Go to **Tools** $\rightarrow$ **Board** $\rightarrow$ **Boards Manager**, search for `esp32`, and install `esp32 by Espressif Systems`.
4. Install Required Libraries via **Tools** $\rightarrow$ **Manage Libraries**:
   - `PubSubClient` by Nick O'Leary
   - `ArduinoJson` by Benoit Blanchon (version 6.x or 7.x)
   - `DHT sensor library` by Adafruit
   - `Adafruit Unified Sensor`
   - `PZEM004Tv30` by Jakub Mandula
5. Open the project firmware file:
   `c:\Users\dell\OneDrive\Desktop\HVAC-Energy-Optimiztion\firmware\esp32_hvac_monitor\esp32_hvac_monitor.ino`
6. Update your Wi-Fi credentials and host IP address:
   ```cpp
   const char* WIFI_SSID     = "Your_WiFi_Name";
   const char* WIFI_PASSWORD = "Your_WiFi_Password";
   const char* MQTT_BROKER   = "192.168.1.100"; // Replace with your laptop's local IP address
   ```
7. Select Board: **ESP32 Dev Module** or **DOIT ESP32 DEVKIT V1**.
8. Connect the ESP32 board via micro-USB, select the corresponding COM port, and click **Upload**.
9. Open the Serial Monitor at **115200 baud** to view real-time Wi-Fi connection, sensor data, and MQTT transmissions.

