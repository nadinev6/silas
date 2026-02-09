# Troubleshooting Guide: Project Silas

If you encounter issues while setting up the simulation or the backend, please refer to the solutions below.

### 1. Localtunnel Subdomain "Unavailable"
If you see an error stating the subdomain is taken, another user or judge may be testing the project.
* **Solution:** Change the subdomain in your terminal command:
  `npx localtunnel --port 8000 --subdomain silas-test-[yourname]`
* **Note:** If you change this, you must update the connection URL in the firmware configuration to match your new tunnel link.

### 2. "Connection Refused" in Wokwi Terminal
This usually happens if the ESP32 tries to connect before the tunnel is fully "awake" or if the backend server is offline.
* **Solution:** 1. Ensure your FastAPI server is running on **Port 8000**.
  2. Refresh the verification link (**https://silas-agent-v1.loca.lt**) in your browser and click "Click to Continue."
  3. Restart the Wokwi simulation by clicking the red Stop button and then the green Play button.

### 3. Audio Jitter or "Robotic" Voice
Because this demo runs in a browser-based simulation (**Wokwi**), network latency can occasionally disrupt the I2S audio stream.
* **Solution:** 1. Close unnecessary browser tabs to free up CPU cycles for the simulation.
  2. Ensure you aren't running a VPN, as this can add significant overhead to the `localtunnel` connection.

### 4. Silas is "Thinking" but No Audio is Playing
* **Solution:** 1. Check the **Silas Dashboard**. If the "Internal Monologue" is scrolling, the backend is working correctly.
  2. Ensure your system volume is up and the Wokwi browser tab isn't muted.
  3. **Crucial:** Browsers require a "user gesture" to play audio. Click anywhere inside the Wokwi simulation window once the code starts running to "unlock" the audio context.

### 5. "404 Not Found" or "504 Gateway Timeout"
* **Solution:** Ensure you have accessed the tunnel URL at least once in your browser to bypass the automated "friendly reminder" landing page from localtunnel. If the server is unreachable, restart the Python backend first, then the tunnel.

---
*Still stuck? Please ensure your Node.js version is 16+ for the best `localtunnel` stability.*