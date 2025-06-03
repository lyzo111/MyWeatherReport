#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_BME280.h>
#include <time.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server configuration
const char* serverURL = "http://YOUR_SERVER_IP:5000/esp32/data";

// Sensor configuration
Adafruit_BME280 bme; // BME280 sensor
const int sensorPower = 2; // Optional: Power pin for sensor

// Location identifier
const char* location = "ESP32_Sensor_1"; // Change this for each ESP32

// Timing
unsigned long lastSensorReading = 0;
const unsigned long sensorInterval = 30000; // Send data every 30 seconds

// NTP configuration for timestamps
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 3600; // GMT+1 (Germany)
const int daylightOffset_sec = 3600; // Daylight saving time

// Data structure
struct SensorData {
  float temperature;
  float humidity;
  float pressure;
  String timestamp;
};

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("=== ESP32 Weather Station ===");
  
  // Initialize sensor power pin
  if (sensorPower > 0) {
    pinMode(sensorPower, OUTPUT);
    digitalWrite(sensorPower, HIGH);
    delay(1000);
  }
  
  // Initialize BME280 sensor
  if (!bme.begin(0x76)) { // Try address 0x76 first
    if (!bme.begin(0x77)) { // Try address 0x77
      Serial.println("Could not find BME280 sensor!");
      while (1) delay(1000);
    }
  }
  
  Serial.println("BME280 sensor initialized successfully");
  
  // Connect to WiFi
  connectToWiFi();
  
  // Initialize time
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  waitForTimeSync();
  
  Serial.println("Setup complete. Starting data collection...");
}

void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Reconnecting...");
    connectToWiFi();
  }
  
  // Read and send sensor data
  if (millis() - lastSensorReading >= sensorInterval) {
    SensorData data = readSensorData();
    
    if (isValidData(data)) {
      sendDataToServer(data);
    } else {
      Serial.println("Invalid sensor data, skipping transmission");
    }
    
    lastSensorReading = millis();
  }
  
  delay(1000); // Small delay to prevent overwhelming the loop
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected successfully!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println();
    Serial.println("Failed to connect to WiFi. Will retry...");
  }
}

void waitForTimeSync() {
  Serial.print("Waiting for time synchronization");
  time_t now = time(nullptr);
  int attempts = 0;
  
  while (now < 8 * 3600 * 2 && attempts < 30) {
    delay(1000);
    Serial.print(".");
    now = time(nullptr);
    attempts++;
  }
  
  Serial.println();
  if (now >= 8 * 3600 * 2) {
    Serial.println("Time synchronized successfully");
    Serial.print("Current time: ");
    Serial.println(ctime(&now));
  } else {
    Serial.println("Warning: Time synchronization failed");
  }
}

SensorData readSensorData() {
  SensorData data;
  
  // Read sensor values
  data.temperature = bme.readTemperature();
  data.humidity = bme.readHumidity();
  data.pressure = bme.readPressure() / 100.0F; // Convert Pa to hPa
  
  // Generate timestamp
  data.timestamp = getCurrentTimestamp();
  
  // Print to serial for debugging
  Serial.println("--- Sensor Reading ---");
  Serial.printf("Temperature: %.2f°C\n", data.temperature);
  Serial.printf("Humidity: %.2f%%\n", data.humidity);
  Serial.printf("Pressure: %.2f hPa\n", data.pressure);
  Serial.printf("Timestamp: %s\n", data.timestamp.c_str());
  Serial.println("--------------------");
  
  return data;
}

String getCurrentTimestamp() {
  time_t now;
  struct tm timeinfo;
  char buffer[30];
  
  time(&now);
  localtime_r(&now, &timeinfo);
  
  // Format: YYYY-MM-DDTHH:MM:SS
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%S", &timeinfo);
  
  return String(buffer);
}

bool isValidData(const SensorData& data) {
  // Check for reasonable sensor ranges
  if (data.temperature < -40 || data.temperature > 85) {
    Serial.printf("Invalid temperature: %.2f\n", data.temperature);
    return false;
  }
  
  if (data.humidity < 0 || data.humidity > 100) {
    Serial.printf("Invalid humidity: %.2f\n", data.humidity);
    return false;
  }
  
  if (data.pressure < 300 || data.pressure > 1200) {
    Serial.printf("Invalid pressure: %.2f\n", data.pressure);
    return false;
  }
  
  if (data.timestamp.length() < 10) {
    Serial.println("Invalid timestamp");
    return false;
  }
  
  return true;
}

void sendDataToServer(const SensorData& data) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, cannot send data");
    return;
  }
  
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  DynamicJsonDocument doc(1024);
  doc["timestamp"] = data.timestamp;
  doc["temperature"] = data.temperature;
  doc["humidity"] = data.humidity;
  doc["air_pressure"] = data.pressure;
  doc["location"] = location;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("Sending data to server...");
  Serial.println("JSON payload: " + jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("HTTP Response: %d\n", httpResponseCode);
    Serial.println("Server response: " + response);
    
    if (httpResponseCode == 200) {
      Serial.println("✅ Data sent successfully!");
    } else {
      Serial.printf("❌ Server error: %d\n", httpResponseCode);
    }
  } else {
    Serial.printf("❌ HTTP request failed: %d\n", httpResponseCode);
    Serial.println("Error: " + http.errorToString(httpResponseCode));
  }
  
  http.end();
}

// Optional: Add deep sleep functionality for battery powered operation
void enterDeepSleep(int seconds) {
  Serial.printf("Entering deep sleep for %d seconds...\n", seconds);
  delay(100); // Give time for serial output
  
  esp_sleep_enable_timer_wakeup(seconds * 1000000); // Convert to microseconds
  esp_deep_sleep_start();
}

// Optional: Add status LED functionality
void blinkStatusLED(int pin, int times, int delayMs = 200) {
  pinMode(pin, OUTPUT);
  
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH);
    delay(delayMs);
    digitalWrite(pin, LOW);
    delay(delayMs);
  }
}