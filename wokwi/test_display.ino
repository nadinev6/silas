#include "SPI.h"
#include "Adafruit_GFX.h"
#include "Adafruit_ILI9341.h"

// Pin Definitions - MUST match diagram.json
#define TFT_CS    5   // D5
#define TFT_DC    2   // D2
#define TFT_RST   4   // D4

Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);

void setup() {
  Serial.begin(115200);
  Serial.println("Starting...");
  
  tft.begin();
  tft.setRotation(1);
  tft.fillScreen(ILI9341_BLUE);
  
  tft.setCursor(50, 100);
  tft.setTextColor(ILI9341_WHITE);
  tft.setTextSize(3);
  tft.println("HELLO SILAS!");
  
  Serial.println("Display test complete.");
}

void loop() {
  // Nothing needed
}
