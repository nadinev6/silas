/*
  ESP32 Silas Voice Agent - Wokwi Simulation
  
  Press the button OR type in Serial Monitor to talk to Silas.
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>

const char* ssid = "Wokwi-GUEST";
const char* password = "";

// !!! IMPORTANT: Replace with your active localtunnel URL !!!
const char* serverUrl = "https://silas-agent-v1.loca.lt";
const char* deviceId = "wokwi-silas-01";

#define BTN_PIN 5
#define TFT_DC 2
#define TFT_CS 15
Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC);

// Global reasoning metrics
int lastThoughtTokens = 0;
String lastThinkingLevel = "LOW";

// Pre-defined questions for button press demo
const char* demoQuestions[] = {
  "Why is my I2S clock jittering?",
  "How do I fix ADC noise on GPIO 34?",
  "Is my pull-up resistor value correct?",
  "Debug my SPI timing issues"
};
int questionIndex = 0;

String askSilas(String userText) {
  // Visual Feedback: Accessing Signature
  tft.setTextColor(ILI9341_WHITE);
  tft.setTextSize(1);
  tft.setCursor(0, 50);
  tft.println("STATUS: ACCESSING THOUGHT SIGNATURE...");
  
  HTTPClient http;
  http.useHTTP10(true);
  http.setTimeout(45000); // 45 second timeout for Deep Reasoning
  
  String url = String(serverUrl) + "/chat";
  http.begin(url);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  http.addHeader("Bypass-Tunnel-Reminder", "true");
  
  userText.replace(" ", "%20");
  String postData = "device_id=" + String(deviceId) + "&user_text=" + userText;
  
  int httpCode = http.POST(postData);
  String result = "";
  
  if (httpCode > 0) {
    String payload = http.getString();
    DynamicJsonDocument doc(16384); // Increased buffer for very long reasoning sessions
    DeserializationError error = deserializeJson(doc, payload);
    
    if (!error && doc.containsKey("text")) {
      result = doc["text"].as<String>();
      lastThoughtTokens = doc["thought_tokens"] | 0;
      lastThinkingLevel = doc["thinking_level"].as<String>();
    }
  }
  
  http.end();
  return result;
}

void showSilasResponse(String question) {
  tft.fillScreen(ILI9341_BLACK);
  tft.setCursor(0, 0);
  
  // Show question
  tft.setTextColor(ILI9341_YELLOW);
  tft.setTextSize(1);
  tft.println("YOU:");
  tft.setTextColor(ILI9341_WHITE);
  tft.println(question);
  tft.println();
  
  // Show initial thinking status
  tft.setTextColor(ILI9341_MAGENTA);
  tft.println("SILAS IS ANALYSING...");
  
  // Get response
  String response = askSilas(question);
  
  // Clear and show response
  tft.fillScreen(ILI9341_BLACK);
  tft.setCursor(0, 0);
  
  // Header with Reasoning Metrics
  tft.setTextColor(ILI9341_CYAN);
  tft.setTextSize(2);
  tft.print("SILAS ");
  tft.setTextSize(1);
  tft.setTextColor(ILI9341_LIGHTGREY);
  tft.print("[");
  tft.print(lastThinkingLevel);
  tft.print(" THINKING]");
  tft.println();
  
  tft.setTextColor(ILI9341_WHITE);
  tft.print("Reasoning Tokens: ");
  tft.println(lastThoughtTokens);
  tft.println("------------------------------------");
  tft.println();
  
  if (response.length() > 0) {
    tft.setTextColor(ILI9341_GREEN);
    tft.setTextWrap(true);
    // Increased character limit and better wrapping
    // 320px width gives ~53 chars per line at text size 1
    for (int i = 0; i < response.length() && i < 800; i++) {
        tft.print(response[i]);
    }
  } else {
    tft.setTextColor(ILI9341_RED);
    tft.println("No response received.");
  }
  
  Serial.println("<< Silas: " + response);
  Serial.printf("[Reasoning] Tokens: %d, Level: %s\n", lastThoughtTokens, lastThinkingLevel.c_str());
}

void setup() {
  Serial.begin(115200);
  pinMode(BTN_PIN, INPUT_PULLUP);

  WiFi.begin(ssid, password, 6);

  tft.begin();
  tft.setRotation(1); // Landscape
  tft.fillScreen(ILI9341_BLACK);

  tft.setTextColor(ILI9341_WHITE);
  tft.setTextSize(2);
  tft.println("SILAS v1.6");
  tft.setTextSize(1);
  tft.print("\nReasoning Mode Enabled");
  tft.print("\nConnecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(100);
    tft.print(".");
  }

  tft.setTextColor(ILI9341_GREEN);
  tft.print("\nOK! IP=");
  tft.println(WiFi.localIP());
  
  tft.setTextColor(ILI9341_YELLOW);
  tft.println("\n\nReady for Hardware Debug.");
  
  Serial.println("=== SILAS Reasoning Enabled ===");
}

void loop() {
  if (digitalRead(BTN_PIN) == LOW) {
    String question = demoQuestions[questionIndex];
    questionIndex = (questionIndex + 1) % 4;
    Serial.println(">> You (button): " + question);
    showSilasResponse(question);
    delay(1000); 
  }
  
  if (Serial.available() > 0) {
    String userInput = Serial.readStringUntil('\n');
    userInput.trim();
    if (userInput.length() > 0) {
      Serial.println(">> You: " + userInput);
      showSilasResponse(userInput);
    }
  }

  delay(100);
}