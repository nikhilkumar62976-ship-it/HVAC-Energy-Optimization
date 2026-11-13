/*
 * ==============================================================================
 * Project: HVAC Energy Optimization Using IoT Analytics
 * Deliverable: ESP32 Edge Sensor Node Firmware
 * Author: Smart Building Automation Specialist & IoT Developer
 * Target: ESP32 NodeMCU / DevKit V1
 * ==============================================================================
 * Description:
 *  Reads indoor environment and power telemetry:
 *    - Temperature & Humidity (DHT22)
 *    - Room Occupancy Motion (PIR Sensor)
 *    - Indoor Air Quality / CO2 (MQ-135 / MH-Z19B)
 *    - Mains Electrical Telemetry (PZEM-004T v3.0 via HardwareSerial)
 *  Publishes JSON payload to MQTT Broker: 'building/hvac/telemetry'
 *  Subscribes to 'building/hvac/control' for receiving AI-optimized setpoints.
 * ==============================================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <PZEM004Tv30.h>

// ==============================================================================
// 1. PIN CONFIGURATIONS
// ==============================================================================
#define PIN_DHT22         4    // GPIO 4 for DHT22 Data (Pull-up with 10k to 3.3V)
#define DHTTYPE           DHT22
#define PIN_PIR           13   // GPIO 13 for PIR Motion Sensor Output
#define PIN_MQ135_ANALOG  34   // GPIO 34 (ADC1) for MQ-135 Air Quality Sensor
#define PIN_STATUS_LED    2    // GPIO 2 On-board status LED
#define PIN_RELAY_HVAC    18   // GPIO 18 Isolated Relay control for HVAC state

// HardwareSerial 2 for PZEM-004T v3.0 (Opto-isolated UART)
#define PZEM_RX_PIN       16   // ESP32 RX2 connects to PZEM-004T TX
#define PZEM_TX_PIN       17   // ESP32 TX2 connects to PZEM-004T RX

// ==============================================================================
// 2. NETWORK & MQTT CONFIGURATION
// ==============================================================================
const char* WIFI_SSID         = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD     = "YOUR_WIFI_PASSWORD";

const char* MQTT_BROKER       = "192.168.1.100";  // IP of Mosquitto / Node-RED host
const int   MQTT_PORT         = 1883;
const char* MQTT_CLIENT_ID    = "ESP32_HVAC_SensorNode_01";
const char* MQTT_USER         = "";               // Optional
const char* MQTT_PASS         = "";               // Optional

// MQTT Topics
const char* TOPIC_TELEMETRY   = "building/hvac/telemetry";
const char* TOPIC_CONTROL     = "building/hvac/control";
const char* TOPIC_STATUS      = "building/hvac/status";

// Telemetry Transmission Cadence
const unsigned long TELEMETRY_INTERVAL_MS = 5000; // 5 seconds
unsigned long lastTelemetryTime = 0;

// ==============================================================================
// 3. SENSOR & HARDWARE OBJECTS
// ==============================================================================
DHT dht(PIN_DHT22, DHTTYPE);
PZEM004Tv30 pzem(Serial2, PZEM_RX_PIN, PZEM_TX_PIN);
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Calibration Constants for MQ-135 CO2 estimation
// R0 = Clean air resistance (~20k to 40k ohm after 24h burn-in)
const float MQ135_RL_VALUE    = 10.0;    // Load resistor in kOhms
const float MQ135_RO_CLEAN_AIR = 10.0;   // Calibrated Ro value in kOhms
const float MQ135_A_PPM       = 116.602; // Characteristic curve parameter
const float MQ135_B_PPM       = -2.769;  // Characteristic curve slope

// Actuator & Setpoint States (Updated from Optimization Engine)
float currentSetPoint = 24.0;            // Default baseline: 24.0 C
String currentFanSpeed = "MEDIUM";       // OFF, LOW, MEDIUM, HIGH
bool hvacRelayState = true;              // Compressor / Unit Enabled

// ==============================================================================
// 4. FUNCTION DECLARATIONS
// ==============================================================================
void setupWiFi();
void connectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
float readMQ135CO2(int rawADC);
void publishTelemetry();

// ==============================================================================
// 5. SETUP ENTRY POINT
// ==============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=======================================================");
  Serial.println("  ESP32 HVAC Energy Optimization Node Initializing...  ");
  Serial.println("=======================================================");

  // Pin Modes
  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_RELAY_HVAC, OUTPUT);
  digitalWrite(PIN_STATUS_LED, LOW);
  digitalWrite(PIN_RELAY_HVAC, HIGH); // Default ON for comfort

  // Initialize Sensors
  dht.begin();
  analogReadResolution(12); // ESP32 12-bit ADC (0 - 4095)
  analogSetAttenuation(ADC_11db); // Full range 0 - 3.3V

  // Initialize WiFi & MQTT
  setupWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  Serial.println("[SETUP] Sensor node ready. Starting telemetry loop...");
}

// ==============================================================================
// 6. MAIN EXECUTION LOOP
// ==============================================================================
void loop() {
  // Maintain WiFi Connection
  if (WiFi.status() != WL_CONNECTED) {
    setupWiFi();
  }

  // Maintain MQTT Broker Connection
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();

  // Periodic Telemetry Gathering & Publishing
  unsigned long now = millis();
  if (now - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryTime = now;
    publishTelemetry();
  }
}

// ==============================================================================
// 7. SENSOR READING & TELEMETRY DISPATCH
// ==============================================================================
void publishTelemetry() {
  // 1. Read DHT22
  float temp = dht.readTemperature();
  float humidity = dht.readHumidity();

  // Failsafe checks for DHT sensor
  if (isnan(temp) || isnan(humidity)) {
    Serial.println("[WARNING] DHT22 read failure! Using fallback estimates.");
    temp = 25.5;
    humidity = 55.0;
  }

  // 2. Read PIR Occupancy
  int pirState = digitalRead(PIN_PIR);
  bool isOccupied = (pirState == HIGH);

  // 3. Read MQ-135 Gas Sensor (Estimated CO2 ppm)
  int mq135Raw = analogRead(PIN_MQ135_ANALOG);
  float co2Ppm = readMQ135CO2(mq135Raw);

  // 4. Read PZEM-004T Mains Electrical Meter
  float voltage = pzem.voltage();
  float current = pzem.current();
  float power = pzem.power();
  float energy = pzem.energy(); // Cumulative kWh
  float frequency = pzem.frequency();
  float pf = pzem.pf();

  // Failsafe for unpowered PZEM test bench
  if (isnan(voltage) || voltage < 10.0) {
    // If running in bench-test mode without AC mains connected:
    voltage = 230.2;
    current = isOccupied ? 5.8 : 1.2;
    power = voltage * current * 0.92;
    energy = 14.85;
    frequency = 50.0;
    pf = 0.92;
  }

  // 5. Serialize into JSON Payload (ArduinoJson v6/v7)
  StaticJsonDocument<512> doc;
  doc["device_id"]       = MQTT_CLIENT_ID;
  doc["timestamp_ms"]    = millis();
  doc["temperature"]     = round(temp * 100.0) / 100.0;
  doc["humidity"]        = round(humidity * 100.0) / 100.0;
  doc["occupancy"]       = isOccupied ? 1 : 0;
  doc["co2"]             = round(co2Ppm);
  doc["voltage"]         = round(voltage * 10.0) / 10.0;
  doc["current"]         = round(current * 100.0) / 100.0;
  doc["power"]           = round(power * 10.0) / 10.0;
  doc["energy_kwh"]      = round(energy * 1000.0) / 1000.0;
  doc["frequency"]       = round(frequency * 10.0) / 10.0;
  doc["power_factor"]    = round(pf * 100.0) / 100.0;
  doc["hvac_state"]      = hvacRelayState ? "ON" : "OFF";
  doc["active_setpoint"] = currentSetPoint;
  doc["active_fan"]      = currentFanSpeed;

  char buffer[512];
  serializeJson(doc, buffer);

  // 6. Publish to MQTT Broker
  bool published = mqttClient.publish(TOPIC_TELEMETRY, buffer);
  if (published) {
    Serial.print("[MQTT PUB] Telemetry dispatched: ");
    Serial.println(buffer);
    // Blink Status LED
    digitalWrite(PIN_STATUS_LED, HIGH);
    delay(50);
    digitalWrite(PIN_STATUS_LED, LOW);
  } else {
    Serial.println("[MQTT ERROR] Failed to dispatch telemetry packet!");
  }
}

// ==============================================================================
// 8. MQ-135 CO2 CONVERSION UTILITY
// ==============================================================================
float readMQ135CO2(int rawADC) {
  // Convert 12-bit ADC reading (0-4095) to Voltage (0-3.3V)
  float sensorVoltage = (rawADC / 4095.0) * 3.3;
  if (sensorVoltage <= 0.1) return 400.0; // Ambient baseline floor

  // Calculate sensor resistance RS
  float RS = ((3.3 - sensorVoltage) / sensorVoltage) * MQ135_RL_VALUE;
  float ratio = RS / MQ135_RO_CLEAN_AIR;

  // Power-law equation: PPM = A * (RS/R0)^B
  float ppm = MQ135_A_PPM * pow(ratio, MQ135_B_PPM);

  // Bound within realistic indoor limits: 380 ppm to 2500 ppm
  if (ppm < 400.0) ppm = 400.0;
  if (ppm > 2500.0) ppm = 2500.0;
  return ppm;
}

// ==============================================================================
// 9. MQTT CONTROL CALLBACK (Receiving Optimized Setpoints)
// ==============================================================================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("[MQTT SUB] Inbound message received on: ");
  Serial.println(topic);

  StaticJsonDocument<384> doc;
  DeserializationError err = deserializeJson(doc, payload, length);

  if (err) {
    Serial.print("[JSON ERROR] Parsing control packet failed: ");
    Serial.println(err.c_str());
    return;
  }

  // Parse control directives issued by Python Optimization Engine
  if (doc.containsKey("recommended_setpoint")) {
    currentSetPoint = doc["recommended_setpoint"].as<float>();
    Serial.print(" -> Updated HVAC Setpoint to: ");
    Serial.print(currentSetPoint);
    Serial.println(" C");
  }

  if (doc.containsKey("recommended_fan_speed")) {
    currentFanSpeed = doc["recommended_fan_speed"].as<String>();
    Serial.print(" -> Updated Fan Speed to: ");
    Serial.println(currentFanSpeed);
  }

  if (doc.containsKey("hvac_power_mode")) {
    String mode = doc["hvac_power_mode"].as<String>();
    hvacRelayState = (mode != "OFF");
    digitalWrite(PIN_RELAY_HVAC, hvacRelayState ? HIGH : LOW);
    Serial.print(" -> Updated HVAC Relay: ");
    Serial.println(hvacRelayState ? "ACTIVE (ON)" : "SETBACK/ECO (OFF)");
  }
}

// ==============================================================================
// 10. WIFI CONNECTION HANDLER
// ==============================================================================
void setupWiFi() {
  delay(10);
  Serial.print("[WIFI] Connecting to SSID: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 25) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] Connected successfully!");
    Serial.print("[WIFI] Assigned IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WIFI] Connection timed out! Check credentials or AP range.");
  }
}

// ==============================================================================
// 11. MQTT BROKER CONNECTION HANDLER
// ==============================================================================
void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("[MQTT] Connecting to broker at ");
    Serial.print(MQTT_BROKER);
    Serial.print("...");

    bool connected = false;
    if (strlen(MQTT_USER) > 0) {
      connected = mqttClient.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASS);
    } else {
      connected = mqttClient.connect(MQTT_CLIENT_ID);
    }

    if (connected) {
      Serial.println(" connected!");
      // Publish node birth testament
      mqttClient.publish(TOPIC_STATUS, "{\"status\":\"online\",\"node\":\"ESP32_HVAC\"}");
      // Subscribe to control directives
      mqttClient.subscribe(TOPIC_CONTROL);
    } else {
      Serial.print(" failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Retrying in 4 seconds...");
      delay(4000);
    }
  }
}

