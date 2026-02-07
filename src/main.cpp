#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include "AudioTools.h"

// --- Configuration (Update with your credentials) ---
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_BACKEND_IP:8000";
const char* deviceId = "esp32-silas-01";

// Pin Definitions are handled via platformio.ini build_flags, but defined here for clarity if missing
#ifndef TFT_CS
  #define TFT_CS 15
  #define TFT_RST 4
  #define TFT_DC 2
  #define MIC_ADC_PIN 34
  #define BUTTON_TRIGGER 12
  #define BUTTON_RESET 13
  #define DAC_BCLK 26
  #define DAC_LRC 25
  #define DAC_DIN 22
#endif

// Display Object
Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);

// Audio Objects
AnalogAudioStream in; // ADC Input (MAX9814)
I2SStream out;        // I2S Output (DAC)
StreamCopy copier;
String lastThoughtSignature = "";
bool isRecording = false;

// UI Helpers
void updateDisplay(String status, uint16_t color, String message = "") {
    tft.fillScreen(ILI9341_BLACK);
    tft.setCursor(0, 40);
    tft.setTextColor(color);
    tft.setTextSize(3);
    tft.println(" SILAS V3");
    tft.drawFastHLine(0, 80, 240, ILI9341_WHITE);
    
    tft.setCursor(10, 110);
    tft.setTextSize(2);
    tft.setTextColor(ILI9341_WHITE);
    tft.print("STATUS: ");
    tft.setTextColor(color);
    tft.println(status);
    
    if (message != "") {
        tft.setCursor(10, 160);
        tft.setTextSize(1);
        tft.setTextColor(0xAD55); // Gray
        tft.println(message);
    }
}

void recoverSession() {
    updateDisplay("RECOVERING", ILI9341_ORANGE);
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(String(serverUrl) + "/session/recover");
        http.addHeader("Content-Type", "application/x-www-form-urlencoded");
        String postData = "device_id=" + String(deviceId);
        int httpResponseCode = http.POST(postData);

        if (httpResponseCode > 0) {
            String response = http.getString();
            JsonDocument doc;
            deserializeJson(doc, response);
            if (!doc["thought_signature"].isNull()) {
                lastThoughtSignature = doc["thought_signature"].as<String>();
                Serial.println("Recovered Signature: " + lastThoughtSignature);
            }
        }
        http.end();
    }
}

void playResponse(String audioUrl) {
    updateDisplay("SPEAKING", ILI9341_GREEN);
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(String(serverUrl) + audioUrl);
        int httpCode = http.GET();
        if (httpCode == HTTP_CODE_OK) {
            WiFiClient* stream = http.getStreamPtr();
            copier.copy(out, *stream);
        }
        http.end();
    }
    updateDisplay("READY", ILI9341_CYAN, "Hold GPIO 12 to interact.");
}

void setup() {
    Serial.begin(115200);
    
    // Display Init
    tft.begin();
    tft.setRotation(1); // Landscape
    updateDisplay("BOOTING", ILI9341_YELLOW, "Initializing I/O...");

    pinMode(BUTTON_TRIGGER, INPUT_PULLUP);
    pinMode(BUTTON_RESET, INPUT_PULLUP);

    // WiFi Setup
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    recoverSession();

    // ADC Mic Setup (MAX9814)
    auto configIn = in.defaultConfig(RX_MODE);
    configIn.sample_rate = 16000;
    configIn.bits_per_sample = 16;
    configIn.channels = 1;
    // The library handles ADC pin mapping via the driver
    in.begin(configIn);

    // I2S DAC Setup (MAX98357A)
    auto configOut = out.defaultConfig(TX_MODE);
    configOut.pin_bck = DAC_BCLK;
    configOut.pin_ws = DAC_LRC;
    configOut.pin_data = DAC_DIN;
    configOut.sample_rate = 16000;
    configOut.bits_per_sample = 16;
    configOut.channels = 1;
    out.begin(configOut);

    updateDisplay("READY", ILI9341_CYAN, "Hold GPIO 12 to interact.");
}

void loop() {
    // Check Manual Reset
    if (digitalRead(BUTTON_RESET) == LOW) {
        recoverSession();
        delay(500);
    }

    // Handle Interaction
    if (digitalRead(BUTTON_TRIGGER) == LOW && !isRecording) {
        isRecording = true;
        updateDisplay("LISTENING", ILI9341_RED);
        
        const int maxAudioSize = 1024 * 150; // 150KB to be safe with RAM
        uint8_t* audioBuffer = (uint8_t*)malloc(maxAudioSize);
        int audioIndex = 0;

        unsigned long start = millis();
        while (digitalRead(BUTTON_TRIGGER) == LOW && (millis() - start < 6000)) {
            size_t read = in.readBytes(audioBuffer + audioIndex, 512);
            audioIndex += read;
            if (audioIndex >= maxAudioSize - 512) break;
        }
        
        updateDisplay("THINKING", ILI9341_MAGENTA, "Analyzing logic...");
        
        if (WiFi.status() == WL_CONNECTED) {
            HTTPClient http;
            http.begin(String(serverUrl) + "/voice");
            String boundary = "----ESP32Boundary";
            http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
            
            String head = "--" + boundary + "\r\n" +
                          "Content-Disposition: form-data; name=\"device_id\"\r\n\r\n" +
                          deviceId + "\r\n" +
                          "--" + boundary + "\r\n" +
                          "Content-Disposition: form-data; name=\"audio\"; filename=\"audio.wav\"\r\n" +
                          "Content-Type: audio/wav\r\n\r\n";
            String tail = "\r\n--" + boundary + "--\r\n";
            
            int httpResponseCode = http.sendRequest("POST", (uint8_t*)head.c_str(), head.length(), 
                                                   audioBuffer, audioIndex, 
                                                   (uint8_t*)tail.c_str(), tail.length());

            if (httpResponseCode > 0) {
                String response = http.getString();
                JsonDocument doc;
                deserializeJson(doc, response);
                if (doc.containsKey("audio_url")) {
                    playResponse(doc["audio_url"].as<String>());
                }
            }
            http.end();
        }
        
        free(audioBuffer);
        isRecording = false;
        if (lastThoughtSignature == "") updateDisplay("READY", ILI9341_CYAN);
    }
}
