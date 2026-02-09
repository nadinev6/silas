# 🗜️ Project Silas: The Silicon Savant

> **"Fix your wiring before you talk to me."** — Silas

A physical AI agent powered by **Gemini 3 Flash**, designed to bridge the gap between "Stateless Chatbots" and "Reasoning Hardware Engineers." Silas doesn't just respond; he simulates your circuit logic using Gemini 3's native **High Thinking** capabilities.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Gemini 3](https://img.shields.io/badge/Model-Gemini%203%20Flash-blue)](https://deepmind.google/technologies/gemini/)

---

<p align="center">
  <a href="https://player.mux.com/7TjOUyG3ZJH01pnBBjeioq2EOoC01O01x3tlG75yb5LqoY">
    <img src="docs/images/Video.png" width="100%" alt="Watch Project Silas Demo">
  </a>
</p>

## 🎙️ The Persona: Silas
Silas is a grumpy, veteran senior hardware engineer from the UK. He's cynical, blunt, and thinks your wiring is probably a fire hazard. However, he's deeply competent and will help you solve complex hardware bugs—while complaining about it the whole time.

## 📁 Repository Structure
```
ESP32-Gemini3-Agent/
├── backend/           # FastAPI server, Logic Router, and Database
├── firmware/          # PlatformIO ESP32 project
├── wokwi/             # Wokwi simulation files (sketch, diagram)
├── dashboard/         # Web-based "Glass Box" interface
├── docs/              # Detailed documentation & guides
│   ├── BEHAVIOR.md    # AI personality & rules
│   ├── HARDWARE.md    # Wiring & component specs
│   ├── TROUBLESHOOTING.md # Fixes for common setup issues
│   └── images/        # Documentation assets
├── firmware/          # PlatformIO ESP32 project
├── prompts/           # Silas's system instructions
└── README.md
```

---

## 🏗️ System Architecture

```mermaid
graph TD
    %% Define Styles
    classDef hardware fill:#0a1a1a,stroke:#00f2ff,stroke-width:2px,color:#fff;
    classDef backend fill:#111,stroke:#555,stroke-width:1px,color:#ccc;
    classDef ai fill:#1a0a1a,stroke:#ff00ff,stroke-width:2px,color:#fff;
    classDef database fill:#222,stroke:#aaa,stroke-width:1px,stroke-dasharray: 5 5;
    classDef dashboard fill:#000,stroke:#00f2ff,stroke-width:1px,color:#00f2ff;

    subgraph ESP32 ["Physical Device - ESP32"]
        HW1[MAX9814 Analogue Mic]:::hardware --> HW2[WAV Capture ADC]:::hardware
        HW3[Buttons GPIO 12/13]:::hardware --> HW2
        HW2 --> HW4[WiFi Client]:::hardware
        HW4 --> HW6[WAV Playback]:::hardware
        HW6 --> HW5[MAX98357A I2S DAC]:::hardware
        HW4 --> HW7[ILI9341 TFT SPI]:::hardware
    end

    subgraph Backend ["FastAPI Backend"]
        HW4 -- "/voice POST" --> B1[Audio Handler]:::backend
        B1 --> B2[Logic Router]:::backend
        B2 -- "Determine Level" --> B3[Gemini 3 Manager]:::backend
        B3 -- "Persistence" --> B4[(SQLite DB)]:::database
        B3 --> B5["Google Cloud TTS (Studio-B)"]:::backend
        B5 -- "Audio Response" --> B1
        
        B1 -- "Socket.IO" --> B6[Spectral Core HUD]:::backend
    end

    subgraph AI ["Google Gemini 3"]
        B3 -- "Prompt + Signature" --> AI1[Flash Preview]:::ai
        AI1 -- "Reasoning + JSON" --> B3
    end

    subgraph Dashboard ["Full-Page Spectral HUD"]
        B6 -- "new_thought" --> D1[Internal Monologue]:::dashboard
        B6 -- "thoughts" --> D2[Memory Log]:::dashboard
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
   # Note: Ensure the JSON key file is in the root directory and excluded via .gitignore.
   
3. Run the server (from root):
   ```bash
   python -m backend.server
   ```
4. **Expose with localtunnel (Required for Wokwi)**:
   In a new terminal, run:
   ```bash
   npx localtunnel --port 8000 --subdomain silas-agent-v1
   ```

   ![Software Configuration Guide](docs/images/Config.jpg)
 
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

## 🛠️ Support & Troubleshooting
Having issues with the tunnel, audio, or simulation? Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

## 👥 Credits & Acknowledgments
* **Lead Developer**: Nadine van der Haar
* **Core Intelligence**: Powered by **Google Gemini 3 Flash**
* **Code Orchestration**: Developed with **Antigravity**
* **Voice Synthesis**: **Google Cloud Text-to-Speech** (Studio-grade)

---
*Built for the 2026 Gemini 3 Hackathon*