# 🗜️ Project Silas: Ghost in the Machine

> **"Fix your wiring before you talk to me."** — Silas

A physical AI agent powered by **Gemini 3 Flash**, designed to bridge the gap between "Stateless Chatbots" and "Reasoning Hardware Engineers." Silas doesn't just respond; he simulates your circuit logic using Gemini 3's native **High Thinking** capabilities.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Gemini 3](https://img.shields.io/badge/Model-Gemini%203%20Flash-blue)](https://deepmind.google/technologies/gemini/)

---

## 🎙️ The Persona: Silas
Silas is a grumpy, veteran senior hardware engineer from the UK. He's cynical, blunt, and thinks your wiring is probably a fire hazard. However, he's deeply competent and will help you solve complex hardware bugs—while complaining about it the whole time.

## 📁 Repository Structure
```
ESP32-Gemini3-Agent/
├── backend/           # FastAPI server, Logic Router, and Database
├── firmware/          # PlatformIO ESP32 project
├── wokwi/             # Wokwi simulation files (sketch, diagram)
├── dashboard/         # Web-based "Glass Box" interface
├── prompts/           # Silas's system instructions
├── docs/              # Detailed hardware/behavior documentation
├── tools/             # Utility scripts (e.g., local TTS client)
└── README.md
```

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph ESP32 ["Physical Device - ESP32"]
        HW1[MAX9814 Analogue Mic] --> HW2[WAV Capture ADC]
        HW3[Buttons GPIO 12/13] --> HW2
        HW2 --> HW4[WiFi Client]
        HW4 --> HW6[WAV Playback]
        HW6 --> HW5[MAX98357A I2S DAC]
        HW4 --> HW7[ILI9341 TFT SPI]
    end

    subgraph Backend ["FastAPI Backend"]
        HW4 -- "/voice POST" --> B1[Audio Handler]
        B1 --> B2[Logic Router]
        B2 -- "Determine Level" --> B3[Gemini 3 Manager]
        B3 -- "Persistence" --> B4[(SQLite DB)]
        B3 --> B5["Google Cloud TTS (Studio-B)"]
        B5 -- "Audio Response" --> B1
        
        B1 -- "Socket.IO" --> B6[Spectral Core HUD]
    end

    subgraph AI ["Google Gemini 3"]
        B3 -- "Prompt + Signature" --> AI1[Flash Preview]
        AI1 -- "Reasoning + JSON" --> B3
    end

    subgraph Dashboard ["Full-Page Spectral HUD"]
        B6 -- "new_thought" --> D1[Internal Monologue]
        B6 -- "thoughts" --> D2[Memory Log]
    end
```

---

## 💻 Software Setup

### Backend (Python)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your credentials in `.env.local`:
   ```bash
   GEMINI_API_KEY="your_api_key_here"
   GOOGLE_APPLICATION_CREDENTIALS="/path/to/project-silas-key.json"
   SILAS_VOICE="en-GB-Studio-B"
   ```
3. Run the server (from root):
   ```bash
   python -m backend.server
   ```
4. **Expose with localtunnel (Required for Wokwi)**:
   In a new terminal, run:
   ```bash
   npx localtunnel --port 8000 --subdomain silas-agent-v1
   ```

### Firmware (C++)
1. Open the **`firmware/`** folder in **PlatformIO**.
2. Configure `WiFi` and `serverUrl` in `src/main.cpp`.
3. Build and upload to your ESP32.

### 🧪 Simulating in Wokwi (Zero Hardware Required)
1. Open the [Wokwi project](https://wokwi.com/projects/455303685950683137).
2. Open the **Serial Monitor** in Wokwi.
3. Type your message (e.g., *"Why is my I2C buffer overflowing?"*) and press **Enter**.
4. Silas will process your text, respond on the TFT, and speak through your speakers via the server-side TTS.

---
[!IMPORTANT]
**Disclaimer**: This project utilizes Gemini 3 Flash’s native thinking capabilities. Silas's 'Internal Monologue' is not a pre-written script; it is a real-time summary of the model's logical steps.

## 👥 Credits & Acknowledgments
* **Lead Developer**: Nadine van der Haar
* **Core Intelligence**: Powered by **Google Gemini 3 Flash**
* **Code Orchestration**: Developed with **Antigravity**
* **Voice Synthesis**: **Google Cloud Text-to-Speech** (Studio-grade)

---
*Built for the 2026 Gemini 3 Hackathon*