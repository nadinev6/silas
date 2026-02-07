---
description: How to start the Silas backend with a public URL using localtunnel
---

1. Start the FastAPI backend:
   ```bash
   python server.py
   ```

2. Open a second terminal and start localtunnel:
   // turbo
   ```bash
   npx localtunnel --port 8000
   ```

3. Note the public URL (e.g., `https://grumpy-silas-rocks.loca.lt`).
4. Paste this URL into the `serverUrl` field in `src/main.cpp` before flashing.
