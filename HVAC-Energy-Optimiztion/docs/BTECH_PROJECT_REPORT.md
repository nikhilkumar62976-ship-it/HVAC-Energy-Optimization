# B.Tech Final Year Project Documentation
# HVAC Energy Optimization Using IoT Analytics

---

## Project Metadata
- **Project Title**: HVAC Energy Optimization Using IoT Analytics
- **Domain**: Internet of Things (IoT), Smart Building Automation, Machine Learning, Embedded Systems
- **Target Microcontroller**: Espressif ESP32 DevKit V1
- **Communication Protocol**: MQTT (Message Queuing Telemetry Transport)
- **Data Analytics & Engine**: Python 3, Scikit-Learn, Pandas, NumPy
- **Database Engine**: SQLite 3 (Time-Series & Telemetry Store)
- **User Interface & Dashboard**: Node-RED & Node-RED Dashboard

---

## Abstract
Modern commercial and residential buildings consume an immense portion of global electrical energy, with Heating, Ventilation, and Air Conditioning (HVAC) systems accounting for approximately 40% to 60% of total building electrical demand. Most legacy HVAC installations rely on static thermostatic control—maintaining invariant setpoints (e.g., 20°C–21°C) with continuous high fan operation regardless of real-time occupancy, ambient diurnal fluctuations, or indoor air quality. This operational rigidity results in substantial energy wastage and unnecessary grid stress.

This project presents a cyber-physical IoT system designed to optimize HVAC electrical energy consumption dynamically while rigorously preserving human thermal comfort (ASHRAE Standard 55) and indoor air quality (ASHRAE Standard 62.1). An ESP32 microcontroller interfaces with a DHT22 temperature and humidity sensor, an HC-SR501 PIR occupancy sensor, an MQ-135 air quality sensor, and a PZEM-004T v3.0 opto-isolated energy metering module with a split-core current transformer. Telemetry is serialized as JSON and published over Wi-Fi using the lightweight MQTT protocol. A Python-based optimization engine combines an empirically trained Machine Learning model (Random Forest Regressor, $R^2 = 91.5\%$) with a constrained multi-objective optimization algorithm to dynamically compute optimal temperature setpoints and fan speeds. Historical data is persisted in a thread-safe SQLite database, and real-time visualization is hosted on a Node-RED dashboard. Experimental evaluation across representative diurnal cycles demonstrates an **overall electrical energy reduction of 50.97%**, with a **41.1% peak electrical grid curtailment**, all while guaranteeing 100% compliance with indoor thermal comfort standards.

**Keywords**: HVAC Optimization, Internet of Things (IoT), ESP32, MQTT Protocol, Machine Learning, Random Forest, ASHRAE 55, ASHRAE 62.1, Node-RED, Energy Conservation.

---

## Chapter 1: Introduction & Problem Statement

### 1.1 Motivation
Global energy consumption in buildings is surging due to urbanization, changing climate patterns, and higher standards of living. In tropical and temperate climates, refrigeration and space cooling represent the largest component of peak summer electrical utility demand. Conventional building thermostats operate as simple open-loop or bang-bang hysteresis controllers without knowledge of human presence, metabolic thermal load, or ambient temperature trajectories. Spaces are frequently overcooled during periods of vacancy, and fixed high-speed fans run continuously, leading to significant electrical waste.

### 1.2 Problem Statement
Existing HVAC control installations suffer from the following critical engineering limitations:
1. **Absence of Occupancy-Aware Modulation**: AC units cool unoccupied conference rooms, offices, and residential spaces identically to fully populated spaces.
2. **Fixed Low Setpoints**: Users routinely select 20°C–21°C, well below the ASHRAE 55 neutral comfort band (23.5°C–25.0°C), increasing compressor electrical workload non-linearly.
3. **Decoupled Air Quality Control**: Mechanical ventilation is either operated continuously at maximum throughput (wasting conditioned air) or neglected entirely (causing dangerous indoor $CO_2$ accumulation >1200 ppm).
4. **Lack of Real-Time Energy Visibility**: Facility managers lack granular, phase-accurate telemetry showing real-time power, energy accumulation, and before-vs-after savings.

### 1.3 Project Objectives
The engineering objectives of this project are:
1. Construct an edge IoT sensor node using the ESP32 microcontroller to monitor temperature, humidity, occupancy, $CO_2$, AC voltage, current, active power, and energy accumulation.
2. Establish secure, low-latency, bi-directional telemetry transmission via the MQTT protocol.
3. Develop a Python data processing and optimization engine combining a trained Machine Learning model for HVAC power prediction with a constrained multi-objective optimization algorithm.
4. Integrate ASHRAE Standard 55 thermal comfort indices and ASHRAE Standard 62.1 indoor air quality ventilation thresholds into the optimization loop.
5. Engineer a modern, intuitive, responsive dashboard using Node-RED for real-time monitoring, historical comparison, and recommendation tracking.
6. Quantify real-world energy conservation through comparative baseline vs. optimized evaluation.

---

## Chapter 2: Theoretical Background & Standards

### 2.1 ASHRAE Standard 55: Thermal Environmental Conditions for Human Occupancy
ASHRAE Standard 55 defines conditions that provide acceptable thermal comfort for at least 80% of occupants. Thermal comfort is quantified using P.O. Fanger’s **Predicted Mean Vote (PMV)** and **Predicted Percentage of Dissatisfied (PPD)** indices.
- PMV scales from -3 (cold) to +3 (hot), with $0$ representing thermal neutrality.
- The standard comfort envelope corresponds to $-0.5 \le \text{PMV} \le +0.5$.
- At typical indoor clothing levels (0.5–1.0 clo) and sedentary activity (1.0–1.2 met), a dry-bulb temperature range of **23.5°C to 25.5°C** at **40% to 60% Relative Humidity** satisfies the neutral comfort requirement. Cooling an indoor space to 20°C induces localized overcooling discomfort, increased draft complaints, and a 6% to 10% increase in energy consumption per degree Celsius lowered.

### 2.2 ASHRAE Standard 62.1: Indoor Air Quality & Ventilation
ASHRAE Standard 62.1 establishes minimum ventilation rates to dilute human-generated bio-effluents and indoor contaminants.
- Atmospheric baseline $CO_2 \approx 415 \text{ ppm}$.
- Human exhalation releases approximately $0.3 \text{ L/min}$ of $CO_2$ per person at rest.
- An indoor $CO_2$ concentration exceeding **1000 ppm** signals inadequate air exchange, causing cognitive degradation, headaches, and drowsiness.
- Our optimization algorithm incorporates an **automated ventilation override constraint**: whenever $CO_2 \ge 1000 \text{ ppm}$, the system elevates fan speed to `HIGH` and activates ventilation dampers, prioritizing occupant health over energy savings.

---

## Chapter 3: System Architecture & Hardware Design

### 3.1 Hardware Block Diagram
The cyber-physical hardware layer consists of:
1. **ESP32 Microcontroller**: Tensilica Xtensa dual-core processor @ 240 MHz handling sensor acquisition and MQTT client connectivity.
2. **DHT22**: Capacitive relative humidity and NTC thermistor element communicating via a digital single-bus protocol.
3. **HC-SR501 PIR Sensor**: Passive infrared pyroelectric detector that senses thermal radiation movement from human bodies.
4. **MQ-135 Gas Sensor**: Metal oxide semiconductor sensor calibrated for $CO_2$ equivalent ppm detection.
5. **PZEM-004T v3.0 Energy Module**: Specialized digital energy metering IC communicating via hardware UART (Serial2) equipped with onboard PC817 optocouplers.
6. **100A/100mA Split-Core Current Transformer**: Non-invasive magnetic induction clamp installed around the HVAC live phase line.

### 3.2 Electrical Pin Mapping

```
ESP32 DevKit V1
+--------------------------------------------------------+
| GPIO 4  <--> DHT22 Data (with 10k Pull-Up to 3.3V)     |
| GPIO 13 <--> HC-SR501 PIR Output Digital Signal        |
| GPIO 34 <--> MQ-135 Analog Voltage Output (ADC1)       |
| GPIO 16 <--> PZEM-004T TX (HardwareSerial2 RX2)        |
| GPIO 17 <--> PZEM-004T RX (HardwareSerial2 TX2)        |
| GPIO 18 <--> Opto-Isolated Relay Control Pin (HVAC)    |
| GPIO 2  <--> Built-in Status LED                       |
| 3.3V    <--> Sensor VCC (DHT22)                        |
| VIN(5V) <--> Sensor VCC (PIR, MQ-135, PZEM-004T)       |
| GND     <--> Common System Ground                      |
+--------------------------------------------------------+
```

### 3.3 Electrical Isolation & Safety
The high-voltage mains AC supply (230V AC) is completely separated from the ESP32 low-voltage digital domain:
- **Optical Barrier**: Dual PC817 optocouplers within the PZEM-004T module ensure that no galvanic connection exists between the AC mains and the microcontroller serial pins.
- **Inductive Sensing**: Current measurement occurs via electromagnetic induction across the insulated outer jacket of the phase conductor, eliminating exposed live conductor splices.

---

## Chapter 4: Software Implementation & Machine Learning

### 4.1 Machine Learning Energy Prediction Model
To predict HVAC active power consumption for arbitrary combinations of setpoint and ambient variables, a **Random Forest Regressor** (100 estimators) was trained on 6,000 thermodynamic operational records.

#### Feature Matrix:
$$X = \left[ T_{in}, T_{out}, RH, Occ, T_{set}, S_{fan}, Hour, Weekend \right]$$

#### Target:
$$y = P_{HVAC} \quad (\text{Electrical Power in Watts})$$

#### Predictive Performance Metrics:
- **Coefficient of Determination ($R^2$)**: **0.9151 (91.51%)**
- **Root Mean Squared Error (RMSE)**: **88.90 Watts**
- **Mean Absolute Error (MAE)**: **46.53 Watts**
- **Mean Absolute Percentage Error (MAPE)**: **22.28%**

#### Feature Importance Ranking:
1. `outdoor_temp`: **66.92%** (primary driver of refrigeration condensing pressure and thermodynamic heat transfer across the envelope)
2. `fan_speed_code`: **16.44%** (direct motor power demand)
3. `setpoint`: **10.58%** (determines required evaporating temperature and compressor runtime)
4. `indoor_temp`: **4.82%**
5. `humidity`: **0.61%**
6. `hour_of_day`: **0.35%**
7. `occupancy`: **0.21%**
8. `is_weekend`: **0.07%**

### 4.2 Constrained Multi-Objective Optimization Algorithm
The optimization engine solves the following constrained problem at each telemetry interval:

$$\min_{T_{set}, S_{fan}} \mathcal{J} = 0.60 \left(\frac{P_{pred}}{2200}\right) + 0.30 \cdot \mathcal{P}_{comfort}(T_{set}, T_{in}, RH) + 0.10 \cdot \mathcal{P}_{IAQ}(CO_2, S_{fan})$$

Subject to:
- If $Occ = 1$: $T_{set} \in [23.0^\circ\text{C}, 25.5^\circ\text{C}]$
- If $Occ = 0$: $T_{set} \in [27.0^\circ\text{C}, 29.5^\circ\text{C}]$ (Eco Setback)
- If $CO_2 \ge 1000 \text{ ppm}$: $S_{fan} = \text{HIGH}$ (Ventilation Purge)
- Compressor minimum dwell time: $\Delta t \ge 180 \text{ seconds}$

---

## Chapter 5: Experimental Testing, Results & Discussion

### 5.1 Comparative Testing Setup
The system was evaluated across a standardized 10-hour diurnal operational dataset comprising occupied working hours, lunch recess vacancy, peak afternoon heat (outdoor temperatures up to 39°C), and room occupancy variations.

- **Strategy A (Conventional Baseline)**: Static thermostat at 21.0°C with continuous `HIGH` fan speed.
- **Strategy B (IoT Smart Optimized)**: Dynamic setpoints (23.5°C–25.0°C occupied, 28.0°C setback unoccupied, adaptive fan speed modulation, and $CO_2$ purge).

### 5.2 Summary of Experimental Findings

| Performance Metric | Baseline Fixed Operation | IoT-Optimized Operation | Absolute Difference | Relative Improvement |
|---|---|---|---|---|
| **Average Electrical Power** | 656.6 Watts | 321.9 Watts | **-334.7 Watts** | **50.97% Reduction** |
| **Total Energy Consumed (10 hrs)** | 6.57 kWh | 3.22 kWh | **-3.35 kWh** | **50.97% Savings** |
| **Occupied Period Power** | 850.9 Watts | 525.4 Watts | **-325.5 Watts** | **38.3% Savings** |
| **Unoccupied Period Power** | 522.4 Watts | 181.5 Watts | **-340.9 Watts** | **65.3% Savings** |
| **Peak Demand (12 PM – 4 PM)** | 974.1 Watts | 573.9 Watts | **-400.2 Watts** | **41.1% Curtailment** |
| **ASHRAE 55 Comfort Compliance** | 62.4% (Overcooled) | 100.0% (Neutral) | +37.6% | **Optimal Comfort** |
| **ASHRAE 62.1 IAQ Purges Handled** | 0 (No IAQ awareness) | 14 Purging Events | 14 Events | **Health Compliant** |

### 5.3 Discussion of Results
1. **Occupancy-Based Energy Savings (65.3%)**: During unoccupied intervals, the baseline unit continued cooling to 21°C. By contrast, the IoT optimizer recognized the absence of human presence via the PIR sensor and transitioned into `ECO_SETBACK` mode (raising setpoint to 28°C and reducing fan speed to `LOW`), avoiding unnecessary compressor cycles.
2. **Occupied Comfort Optimization (38.3%)**: During occupied periods, raising the setpoint from an overcooled 21°C to an ASHRAE-compliant 24.5°C reduced compressor lift pressure and elevated the evaporating temperature, yielding substantial continuous electrical savings while maintaining PMV neutrality.
3. **Peak Grid Load Shaving (41.1%)**: Between 12:00 PM and 4:00 PM (peak utility tariff hours), ambient heat causes maximum compressor stress. The optimization engine throttled demand from 974.1W down to 573.9W, demonstrating immense utility demand-response potential.

---

## Chapter 6: Industrial Reliability & Fail-Safe Architecture

1. **Anti-Short Cycling Protection**: Rapid cycling on and off of refrigeration compressors damages compressor motor windings, causes mechanical piston stress, and depletes oil reserves. The optimization engine enforces a software dwell time of 180 seconds (3 minutes) between setpoint modifications.
2. **Dual-Mode Operation (Recommendation vs. Actuation)**:
   - In **Recommendation-Only Mode**, the system acts as an expert advisory tool for building managers, displaying optimal operating parameters on the dashboard without modifying hardware.
   - In **Autonomous Control Mode**, recommendations drive the isolated relay module or interface directly with digital HVAC protocols (Modbus / BACnet / IR blast).
3. **Network Disconnection Failsafe**: If Wi-Fi or MQTT connectivity is severed, the ESP32 firmware autonomously falls back to a comfortable baseline (24.0°C, MEDIUM fan), preventing room overheating or freeze conditions.

---

## Chapter 7: Conclusion & Future Scope

### 7.1 Conclusion
The "HVAC Energy Optimization Using IoT Analytics" project successfully demonstrates an end-to-end, working cyber-physical system capable of monitoring, predicting, and optimizing HVAC energy usage in real time. By fusing edge sensing (ESP32, DHT22, PIR, MQ-135, PZEM-004T), MQTT communications, Scikit-Learn predictive modeling, and ASHRAE 55/62.1 multi-objective optimization, the project achieves an **overall energy reduction of 50.97%** and a **41.1% peak load reduction**. The implementation is practical, cost-effective, and directly deployable across educational institutions, office complexes, and smart homes.

### 7.2 Future Scope
1. **Edge AI / TinyML Deployment**: Quantize and deploy the Random Forest or an artificial neural network directly onto the ESP32 using TensorFlow Lite for Microcontrollers (TFLM), eliminating dependency on an external Python server.
2. **Building Management System (BMS) Interoperability**: Implement native BACnet/IP and Modbus-TCP gateways for commercial chiller plant integration.
3. **Predictive Weather Integration**: Incorporate real-time OpenWeatherMap API forecasting to precool buildings during low-tariff off-peak night hours in anticipation of daytime heatwaves.

---

## Appendix: Viva-Voce Questions & Model Answers

### Q1. Why did you choose the ESP32 over the Arduino Uno or Raspberry Pi?
**Model Answer**: The ESP32 provides built-in 2.4 GHz Wi-Fi and Bluetooth, a dual-core 240 MHz Xtensa processor, multiple hardware UARTs (necessary for the PZEM-004T), and low power consumption at an economical cost. An Arduino Uno lacks onboard wireless connectivity and has only 2 KB of SRAM, making JSON parsing and MQTT handling unreliable. A Raspberry Pi, while powerful, is significantly more expensive, consumes 5–10W continuously, and is prone to SD card corruption upon unexpected power outages.

### Q2. How does raising the setpoint from 21°C to 24°C save energy thermodynamically?
**Model Answer**: The rate of conductive heat gain through the building envelope is proportional to the temperature differential: $Q = U \cdot A \cdot (T_{outdoor} - T_{indoor})$. When indoor temperature is maintained at 21°C on a 36°C day, $\Delta T = 15^\circ\text{C}$. Raising the setpoint to 24.5°C reduces $\Delta T$ to $11.5^\circ\text{C}$—a 23.3% reduction in thermal heat gain. Furthermore, a higher evaporating temperature increases the Coefficient of Performance (COP) of the refrigeration cycle, reducing compressor electrical workload by approximately 6% to 8% per degree Celsius.

### Q3. How do you measure AC mains current safely without electrocution risk?
**Model Answer**: We utilize a split-core current transformer (CT clamp). The CT clamp snaps magnetically around the insulated Phase line. Current is measured via electromagnetic induction across an internal burden resistor without cutting, stripping, or tapping into the live copper conductor. Furthermore, the PZEM-004T module features PC817 optocouplers that isolate the 230V AC terminal from the 5V/3.3V serial pins connected to the ESP32.

### Q4. What happens if the room is occupied but CO₂ exceeds 1000 ppm? Does the system still save energy?
**Model Answer**: No, the system deliberately prioritizes occupant health and safety over energy conservation. Under ASHRAE Standard 62.1, $CO_2 > 1000 \text{ ppm}$ causes lethargy and impaired decision-making. The optimization engine applies a high penalty function ($\mathcal{P}_{IAQ}$), triggering a `VENTILATION_PURGE` mode that forces the fan to `HIGH` to exhaust stale air and introduce fresh outdoor oxygen until $CO_2$ drops below 800 ppm.

### Q5. Why is a 3-minute dwell time enforced in the optimization algorithm?
**Model Answer**: This is an anti-short cycling safeguard. In commercial and residential HVAC compressors, rapid on/off cycling creates severe mechanical stress, overheats the motor windings due to repeated high starting inrush currents (Locked Rotor Amps), and prevents lubricating oil from returning to the compressor sump. Enforcing a 180-second minimum dwell time ensures mechanical reliability and equipment longevity.

