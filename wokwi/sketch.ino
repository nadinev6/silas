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

// Pre-defined questions for button press demo
const char* demoQuestions[] = {
  "Why is my I2S clock jittering?",
  "How do I fix ADC noise on GPIO 34?",
  "Is my pull-up resistor value correct?",
  "Debug my SPI timing issues"
};
int questionIndex = 0;

String askSilas(String userText) {
  HTTPClient http;
  http.useHTTP10(true);
  http.setTimeout(15000);
  
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
    DynamicJsonDocument doc(4096);
    DeserializationError error = deserializeJson(doc, payload);
    
    if (!error && doc.containsKey("text")) {
      result = doc["text"].as<String>();
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
  
  // Show thinking status
  tft.setTextColor(ILI9341_MAGENTA);
  tft.println("SILAS IS THINKING...");
  
  // Get response
  String response = askSilas(question);
  
  // Clear and show response
  tft.fillScreen(ILI9341_BLACK);
  tft.setCursor(0, 0);
  tft.setTextColor(ILI9341_CYAN);
  tft.setTextSize(2);
  tft.println("SILAS:");
  tft.setTextSize(1);
  tft.println();
  
  if (response.length() > 0) {
    tft.setTextColor(ILI9341_GREEN);
    tft.setTextWrap(true);
    // Print character by character to ensure it displays
    for (int i = 0; i < response.length() && i < 400; i++) {
      tft.print(response[i]);
    }
  } else {
    tft.setTextColor(ILI9341_RED);
    tft.println("No response received.");
  }
  
  Serial.println("<< Silas: " + response);
}

void setup() {
  Serial.begin(115200);
  pinMode(BTN_PIN, INPUT_PULLUP);

  WiFi.begin(ssid, password, 6);

  tft.begin();
  tft.setRotation(1);
  tft.fillScreen(ILI9341_BLACK);

  tft.setTextColor(ILI9341_WHITE);
  tft.setTextSize(2);
  tft.println("SILAS v1.2");
  tft.setTextSize(1);
  tft.print("\nConnecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(100);
    tft.print(".");
  }

  tft.setTextColor(ILI9341_GREEN);
  tft.print("\nOK! IP=");
  tft.println(WiFi.localIP());
  
  tft.setTextColor(ILI9341_YELLOW);
  tft.println("\n\nPress BUTTON or type in");
  tft.println("Serial Monitor to talk.");
  
  Serial.println("=== SILAS Ready ===");
  Serial.println("Type a question and press Enter.");
}

void loop() {
  // Button press - cycle through demo questions
  if (digitalRead(BTN_PIN) == LOW) {
    String question = demoQuestions[questionIndex];
    questionIndex = (questionIndex + 1) % 4;
    Serial.println(">> You (button): " + question);
    showSilasResponse(question);
    delay(500);
  }
  
  // Serial input - custom questions
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