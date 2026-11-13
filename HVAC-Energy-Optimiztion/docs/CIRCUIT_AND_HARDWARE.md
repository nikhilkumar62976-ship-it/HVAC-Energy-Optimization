# Hardware Implementation & Circuit Design Guide
## Project: HVAC Energy Optimization Using IoT Analytics

---

## 1. Component Bill of Materials (BOM) & Technical Specifications

| S.No. | Component | Model / Part No. | Operating Voltage | Interface / Protocol | Key Electrical Specifications | Function in System |
|---|---|---|---|---|---|---|
| **1** | Microcontroller | ESP32 DevKit V1 (30-pin) | 3.3V Logic (5V USB/VIN) | Wi-Fi 802.11 b/g/n, BLE, UART, I2C, SPI | Dual-core Tensilica Xtensa LX6 @ 240 MHz, 520 KB SRAM, 4 MB Flash | Central IoT edge processor, telemetry publisher, local setpoint manager |
| **2** | Temperature & Humidity Sensor | DHT22 (AM2302) | 3.3V – 5.5V DC | 1-Wire Single-bus Digital | Temp: -40°C to +80°C (±0.5°C accuracy); Humidity: 0–100% RH (±2% accuracy) | Continuous indoor thermal comfort monitoring |
| **3** | Passive Infrared Occupancy Sensor | HC-SR501 PIR | 5V DC (3.3V output logic) | Digital Output (Active HIGH) | Detection angle <120°, detection range 3 to 7 meters (adjustable), dual-element pyroelectric | Real-time human presence detection for setback automation |
| **4** | Indoor Air Quality / CO₂ Sensor | MQ-135 / MH-Z19B | 5V DC (Heater & Logic) | Analog ADC (0–3.3V) & UART | Detection range: 400 to 2000 ppm CO₂ / NH₃ / Benzene; SnO₂ semiconductor | Indoor Air Quality (IAQ) monitoring & ASHRAE 62.1 ventilation override |
| **5** | Mains Electrical Monitoring Module | PZEM-004T v3.0 | 80V – 260V AC (Mains) / 5V Logic | Opto-isolated UART (TTL) | Voltage: 80–260V (±0.5%); Current: 0–100A (via CT clamp); Active Power: 0–23 kW; Energy: 0–9999 kWh; Frequency: 45–65 Hz; PF: 0.00–1.00 | Isolated AC electrical telemetry measurement |
| **6** | Split-Core Current Transformer (CT) | 100A / 100mA CT Clamp | AC Induction | Analog secondary coil | Current ratio: 1000:1, non-invasive snap-around phase wire clamp | Safe, non-invasive AC current induction without breaking live mains |
| **7** | Solid State Relay / Isolated Relay Module | 1-Channel 5V Relay with Optocoupler | 5V Coil / 250VAC Contact | Active LOW / Active HIGH Digital Input | Contact rating: 10A @ 250VAC / 30VDC; Optical isolation: PC817 optocoupler | HVAC compressor / fan interlock actuator interface |
| **8** | Regulated Power Supply | 5V 2A DC Adapter | 100–240V AC to 5V DC | Micro-USB / Terminal | Ripple < 50mV, Short-circuit & overcurrent protection | Clean DC power supply for ESP32 and peripheral sensors |
| **9** | Passive Components | Resistors, Breadboard & Wires | — | — | 10 kΩ pull-up resistor (for DHT22), jumper cables | Circuit signal conditioning and prototype assembly |

---

## 2. ESP32 Pin Mapping Table

| ESP32 GPIO Pin | Physical Pin | Connected Component | Signal Type | Direction | Wiring Notes / Safeguards |
|---|---|---|---|---|---|
| **GPIO 4** | D4 | DHT22 Data Pin | Digital (1-Wire) | Bi-directional | Requires 10 kΩ pull-up resistor connected between GPIO 4 and 3.3V rail |
| **GPIO 13** | D13 | HC-SR501 PIR Output | Digital | Input | Connects directly to PIR OUT pin (output is 3.3V logic, safe for ESP32) |
| **GPIO 34** | D34 | MQ-135 Analog AOUT | Analog (ADC1_CH6) | Input | GPIO 34 is an input-only ADC1 channel with no internal pull-up/pull-down |
| **GPIO 16 (RX2)** | RX2 | PZEM-004T TX Pin | UART Digital (TTL) | Input | HardwareSerial Serial2 RX. Connects to PZEM optocoupler output |
| **GPIO 17 (TX2)** | TX2 | PZEM-004T RX Pin | UART Digital (TTL) | Output | HardwareSerial Serial2 TX. Connects to PZEM optocoupler input |
| **GPIO 18** | D18 | Isolated Relay Control Pin | Digital | Output | Drives optocoupled transistor on relay module (Active HIGH) |
| **GPIO 2** | D2 | Built-in Status LED | Digital | Output | Pulses during successful MQTT telemetry transmission |
| **VIN** | VIN | +5V Rail | Power | Power In | Powered by external 5V 2A DC supply |
| **3V3** | 3V3 | +3.3V Power Rail | Power | Power Out | Supplies DHT22 and pull-up resistor |
| **GND** | GND | Common System Ground | Ground | Common | All sensor grounds and DC supply ground tied together |

---

## 3. Circuit Schematic & Interconnection Diagram

```
                              +-------------------------------------------+
                              |         EXTERNAL 5V DC POWER SUPPLY       |
                              +--------------------+----------------------+
                                                   | +5V (VCC)
                                                   | 
                     +-----------------------------+-----------------------------+
                     |                             |                             |
                     V                             V                             V
             +---------------+             +---------------+             +---------------+
             |  ESP32 DevKit |             |  HC-SR501 PIR |             |    MQ-135     |
             |  NodeMCU V1   |             |  Motion Sensor|             |  Gas Sensor   |
             +---------------+             +---------------+             +---------------+
             | VIN       GND |             | VCC  OUT  GND |             | VCC  AOUT GND |
             +---------------+             +---+---+---+---+             +---+---+---+---+
               |          |                    |   |     |                   |   |     |
               |          |                    +---|-----+                   +---|-----+
               |          |                        |                             |
               |          +------------------------+-----------------------------+---> COMMON GND
               |
               |-- GPIO 13 (Input) <---------------+ (PIR Digital Signal)
               |-- GPIO 34 (ADC1)  <---------------------------------------------+ (Analog IAQ Signal)
               |
               |                     +-----------------------------+
               |-- 3.3V Out -------> |  10k Pull-up Resistor       |
               |                     +--------------+--------------+
               |                                    |
               |-- GPIO 4 (1-Wire) <----------------+--------------+ (DHT22 DATA PIN)
               |                                                   |
               |                                           +-------+-------+
               |                                           |     DHT22     |
               |                                           |  Temp/Humid   |
               |                                           +-------+-------+
               |                                           | 3.3V  |  GND  |
               |                                           +---+---+---+---+
               |                                               |       |
               +-----------------------------------------------+       +---> COMMON GND
               |
               |-- GPIO 16 (RX2) <-----------------+ (TTL Opto TX)
               |-- GPIO 17 (TX2) ----------------->| (TTL Opto RX)
               |-- 5V VCC ------------------------>| (Low Voltage VCC)
               |-- GND --------------------------->| (Low Voltage GND)
               |                             +-----+-----------------------+
               |                             |   PZEM-004T v3.0 METER      |
               |                             |   (Optically Isolated)      |
               |                             +-----+-----------------------+
               |                                   | (High-Voltage Terminal)
               |                                   | L     N    CT1   CT2
               |                                   +-+-----+-----+-----+---+
               |                                     |     |     |     |
               |-- GPIO 18 (Relay Out)               |     |     +-----+
               |        |                            |     |        |
               |        V                            |     |        | (Split-Core Current
               |   +----+----------+                 |     |        |  Transformer Clamp)
               |   | Opto-Isolated |                 |     |        |
               |   | Relay Module  |                 |     |        V
               |   +----+----------+                 |     |   ============
               |        | Switch Contact             |     |   [ HVAC PHASE ]
               |        |                            |     |   ============
               |        V                            |     |        |
               |   +----+----------+                 |     |        |
               +---| HVAC Control  |                 |     |        |
                   | Interlock     |                 |     |        |
                   +---------------+                 |     |        |
                                                     |     |        |
             ========================================|=====|========|========================
             MAINS 230V AC SUPPLY (L) ---------------+     |        |
             MAINS 230V AC NEUTRAL (N) --------------------+        |
             MAINS HVAC COMPRESSOR LOAD ----------------------------+ (Current Measured by CT)
             ================================================================================
```

---

## 4. Electrical Safety & Mains Isolation Architecture

> [!CAUTION]
> Mains electricity (230V AC) is potentially lethal. Under no circumstances should 230V AC conductors be connected directly to any ESP32 GPIO pin.

This project strictly adheres to industrial safety standards through a **two-tier galvanically isolated design**:

1. **Non-Invasive Current Measurement**:
   - The AC phase conductor is **not severed or stripped**.
   - Current is measured using a **split-core current transformer (CT clamp)** that snaps magnetically around the insulated Phase line. The current is induced across an internal burden resistor, keeping high voltage completely isolated from the measuring circuit.
2. **Optical Isolation on PZEM-004T v3.0**:
   - The PZEM-004T module features built-in PC817 optocouplers separating its high-voltage AC metering IC from the 5V/3.3V low-voltage TTL serial UART interface.
   - The ESP32 communicates exclusively with the safe, low-voltage side of the optocouplers.
3. **Opto-Isolated Relay Interlocking**:
   - The HVAC actuator control signal from GPIO 18 passes through an onboard optocoupler driving a physical mechanical relay. The relay contacts act as a dry-contact switch rated for 10A @ 250VAC.
4. **Anti-Shock Installation Guidelines**:
   - Enclose the PZEM-004T module inside a flame-retardant ABS junction box.
   - Install a 1A fast-acting fuse on the voltage reference line feeding the PZEM terminals.
   - Ensure earth ground is securely bonded to the building chassis and electrical distribution box.

---

## 5. Sensor Calibration Procedures

### A. DHT22 (Temperature & Humidity)
1. **Verification**: Connect sensor and verify reading against a calibrated laboratory hygrometer/thermometer.
2. **Pull-Up Resistor**: Ensure a 10 kΩ resistor is installed between pin 2 (DATA) and pin 1 (3.3V). Omitting the pull-up causes intermittent `nan` read failures.
3. **Sampling Rate**: DHT22 requires a minimum sampling period of 2.0 seconds between reads. Our firmware polls at 5.0-second intervals to prevent internal capacitive sensor self-heating.

### B. MQ-135 Gas Sensor Calibration
The MQ-135 uses a Tin Dioxide ($SnO_2$) sensing element whose electrical resistance ($R_S$) changes in the presence of air contaminants.
1. **Pre-heating Burn-In**: Run the sensor powered continuously for 24 hours to clear ambient humidity and volatile residues from the heating element.
2. **Determining $R_0$ in Clean Outdoor Air**:
   - Clean outdoor air baseline CO₂ concentration is approximately $415 \text{ ppm}$.
   - Read the analog voltage in clean outdoor air ($V_{clean}$).
   - Calculate sensor resistance:
     $$R_S = \frac{V_{in} - V_{clean}}{V_{clean}} \cdot R_L$$
     Where $R_L = 10 \text{ k}\Omega$ (load resistor on module board).
   - Compute clean air reference resistance:
     $$R_0 = \frac{R_S}{3.6}$$
   - Program the calculated $R_0$ into `MQ135_RO_CLEAN_AIR` in the ESP32 firmware.

### C. PZEM-004T v3.0 Energy Monitor Calibration
1. **Zeroing Energy Accumulator**:
   - To reset accumulated kilowatt-hours (kWh) before starting a trial run, execute the hardware reset function:
     ```cpp
     pzem.resetEnergy();
     ```
2. **Phase Orientation**: Ensure the current transformer clamp is snapped onto the **Phase (Live)** wire only. Snapping around both Live and Neutral simultaneously cancels the magnetic fields, producing a zero current reading.
3. **Power Factor Verification**: For resistive loads (incandescent bulb), PF should read $0.99 - 1.00$. For inductive HVAC compressor loads, PF typically ranges between $0.85 - 0.94$.

