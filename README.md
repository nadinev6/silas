# 🛠️ Project Silas: The World's First Thinking Hardware Agent

> **"Fix your wiring before you talk to me."** — Silas

A physical AI agent powered by **Gemini 3 Flash**, designed to bridge the gap between "Stateless Chatbots" and "Reasoning Hardware Engineers." Silas doesn't just respond; he simulates your circuit logic using Gemini 3's native **High Thinking** capabilities.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Gemini 3](https://img.shields.io/badge/Model-Gemini%203%20Flash-blue)](https://deepmind.google/technologies/gemini/)

---

## 🎙️ The Persona: Silas
Silas is a grumpy, veteran senior hardware engineer. He's cynical, blunt, and thinks your wiring is probably a fire hazard. However, he's deeply competent and will help you solve complex hardware bugs—while complaining about it the whole time.

## 🧠 The "Unfair Advantage": Why Gemini 3?
We chose Gemini 3 Flash over older models for three mission-critical reasons:

1. **Dynamic Thinking Levels**: We implemented a `Logic Router` that triggers `thinking_level: high` for technical debugging. This allows Silas to "pre-simulate" I2S clock timings before speaking.
2. **Thought Signatures**: Silas is persistent. We store cryptographic **Thought Signatures** in SQLite. If the ESP32 reboots, Silas recovers his last "train of thought," ensuring the debugging session never loses context.
3. **Agentic Code Generation**: Using **Google Antigravity**, Silas can directly suggest and refactor firmware code based on his internal reasoning process.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph ESP32 ["Physical Device (ESP32)"]
        A[MAX9814 Analogue Mic] --> B[WAV Capture (ADC)]
        C[Buttons GPIO 12/13] --> B
        B --> D[WiFi Client]
        E[MAX98357A I2S DAC] <-- F[WAV Playback]
        F <-- D
        G[ILI9341 TFT SPI] <-- B
        G <-- I
    end

    subgraph Backend ["FastAPI Backend"]
        D -- "/voice (POST)" --> H[Audio Handler]
        H --> I[Logic Router]
        I -- "Determine Level" --> J[Gemini 3 Manager]
        J -- "Persistence" --> K[(SQLite DB)]
        
        H -- "Socket.IO" --> L[Glass Box Dashboard]
    end

    subgraph AI ["Google Gemini 3"]
        I -- "Prompt + Signature" --> L[Flash Model]
        L -- "Reasoning/Transcription" --> I
    end

    subgraph Dashboard ["Web Dashboard (CRT)"]
        K -- "new_thought" --> M[Internal Monologue]
        K -- "thoughts" --> N[Hardware State Viz]
    end
```

### **Hardware Stack**
* **Core:** ESP32 DevKit V1
* **Audio In:** MAX9814 Analogue Microphone (ADC1_CH6 / GPIO 34)
* **Audio Out:** MAX98357A I2S DAC (DIN:22, BCLK:26, LRC:25)
* **Display:** 2.8" ILI9341 SPI TFT (CS:15, DC:2, RST:4, MOSI:23, SCK:18)
* **Trigger:** Dual Tactile Buttons (GPIO 12 and 13)

---

## 🚀 Future Roadmap: Scaling Silas

To move from a Hackathon MVP to a production-ready industrial tool, our roadmap includes:

### Phase 1: Multimodal "Vision" Integration (Q2 2026)
* **ESP32-CAM Support**: Integrate low-resolution image capture so Silas can "see" the circuit.
* **Gemini 3 Multimodal Reasoning**: Use `media_resolution: high` to allow Silas to identify burnt components or misaligned pins via visual inspection.

### Phase 2: Edge-Cloud Hybrid Logic (Q3 2026)
* **On-Device VAD (Voice Activity Detection)**: Use a small TensorFlow Lite model on the ESP32 to handle wake-word detection, reducing idle server costs.
* **Local Thinking**: Offload "Minimal Thinking" tasks to the edge for 100ms latency responses.

### Phase 3: Industrial Multi-Agent Orchestration (2027)
* **Swarm Debugging**: Deploy multiple Silas agents across a factory floor that share **Thought Signatures** to correlate hardware failures across different machines.

---

## 💻 Software Setup

### Backend (Python)
1. Install dependencies:
   ```bash
   pip install edge-tts google-genai fastapi uvicorn python-socketio sqlalchemy python-dotenv
   ```
2. Set your Gemini API Key:
   ```bash
   # Create a .env file or export directly
   export GEMINI_API_KEY="your_api_key_here"
   ```
3. Run the server:
   ```bash
   python server.py
   ```
4. **Expose with localtunnel (Required for Wokwi)**:
   In a new terminal, run:
   ```bash
   npx localtunnel --port 8000 --subdomain silas-agent-v1
   ```
   or
   ```bash
   lt --port 8000 --subdomain silas-agent-v1
   ```


   *Copy the generated `https://silas-agent-v1.loca.lt/dashboard`*

### Firmware (C++)
1. Open the project in **PlatformIO**.
2. Configure `WiFi` and `serverUrl` in `src/main.cpp`.
3. Build and upload to your ESP32.

### Dashboard (Web)
1. Open `dashboard/index.html` in any modern browser while the backend is running.

---
[!IMPORTANT]
**Disclaimer**: This project utilizes Gemini 3 Flash’s native thinking capabilities. Silas's 'Internal Monologue' is not a pre-written script; it is a real-time summary of the model's logical steps as it analyzes the hardware configuration provided in the prompt context.

## 👥 Credits & Acknowledgments

* **Lead Developer**: Nadine van der Haar
* **Core Intelligence**: Powered by **Google Gemini 3 Flash** (2026 Reasoning Preview)
* **Code Orchestration**: Developed with **Antigravity**
* **Inspiration**: Every prompt engineer who ever sighed while looking at a breadboard.

---
*Built for the 2026 Gemini 3 Hackathon*