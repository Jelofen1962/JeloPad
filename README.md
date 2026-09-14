
# JeloPad

JeloPad is an updated virtual controller bridge for jailbroken PlayStation 4 consoles running GoldHEN. This project allows you to emulate and route controller inputs to your console over local networks or direct USB connections. 

Originally based on the `remote_gamepad` plugin by xfangfang, this fork has been updated and is maintained by **Jelofen1962**, featuring a completely rewritten Python Textual CLI client, real-time remote configuration synchronization, optimized background processing, and dedicated raw HID driver integration.

With JeloPad, local multiplayer games no longer require multiple DualShock 4 controllers; you can connect third-party gamepads, keyboard configurations, mobile web clients, or generic controllers directly to your console.

---

## Key Improvements & Updates in JeloPad

### 1. Brand New Companion CLI Client (Built by Jelofen1962)
* **Interactive Textual TUI:** A polished terminal user interface featuring multi-port controller assignment tables, live input monitors, system logs, and network telemetry.
* **Bi-directional Console Sync:** Instantly queries the console to fetch logged-in PSN profiles and active ports over the WebSocket interface, enabling live changes on the console.
* **Unified Hardware Mappings:** Dynamic assignment of keyboards or connected controllers (using the HTML5 Gamepad API inside Pygame) mapped straight to virtual console slots.

### 2. Custom Dual-Motor Vibration Bridge
* **Raw HID Packets:** Translates floating-point vibration values sent from the PS4 back into raw byte arrays containing Report IDs `0x01` and `0x02` for custom twin-motor gamepads (including Macher MR58 under VIDs: `0x0810`, `0x0e8f`, `0x120a`, `0x1a2c`).
* **Seamless Fallback:** Intelligently switches back to standard OS controller haptics if custom hardware is not detected.

### 3. True Console Independence (Live RPC Configuration API)
* **Configuration Sync:** Added WebSocket endpoints (`config.get` and `config.set`) directly into the PS4 network thread.
* **Zero FTP Editing:** Modify controller ports, toggle profile visibility, and edit console usernames live from your computer's CLI or mobile browser. The PS4 plugin writes these updates directly to `/data/GoldHEN/remote_pad.ini` on the console.

### 4. CPU & Threading Optimizations
* **Lower CPU Overhead:** Tuned the background Mongoose server polling interval within the plugin from a aggressive `4ms` to `10ms`. This significantly lowers background thread CPU usage on the PS4's Jaguar cores without impacting input response times.
* **Global Scope Access:** Refactored local static variables into globally accessible pointers, enabling cleaner integration between the system hook interfaces and the WebSocket server.

### 5. Rebuilt Web Client Interface
* **Haptic & Lightbar Tracking:** Upgraded the embedded web client layout (`client/index.html`) with active dual-rumble triggers and dynamic visual styling. The touchpad border changes its glow using active RGB color values retrieved directly from the PS4.

---

## How to Use

Both the PS4 GoldHEN plugin and the companion PC controller tools are distributed together inside the GitHub Releases.

1. **Deploying the Plugin:**
   * Download `jelopad.prx` from the latest release.
   * Transfer it to `/data/GoldHEN/plugins/` on your PS4.
   * Register the plugin to boot automatically on your console by adding the path below inside your `/data/GoldHEN/plugins.ini` under the `[system]` section:
     ```ini
     [system]
     /data/GoldHEN/plugins/remote_pad.prx
     ```
   * Reboot your console. A system notification will display the server IP address once active on Port `4263`.

2. **Starting the CLI Client:**

   **The Simple Way (Recommended):**
   * Pre-compiled executables are available on the Releases page, meaning you do not need to install Python or configure dependencies manually:
     * **Windows:** Download and run the compiled `.exe` file.
     * **Linux:** Download the `.bin` executable, mark it as executable (`chmod +x`), and run it.
   * Enter the IP address displayed on your console, establish the connection, and map your controllers.

   **The Manual Way (Running from Source):**
   * If you prefer to run the client directly from source, ensure you have Python 3.10+ installed.
   * Install the required packages using your terminal:
     ```shell
     pip install pygame websockets textual
     # Optional: install python-hid for generic/Macher raw controller haptics
     pip install hidapi
     ```
   * Launch the terminal client:
     ```shell
     python main.py
     ```
   * Input the IP address shown on your console, connect, and map your input controllers.

3. **Starting the Web Client:**
   * Open any browser on your phone, tablet, or PC on the same network and navigate to:
     ```
     http://<your_ps4_ip>:4263
     ```

---

## Download

* **Compiled Releases:** All binaries, including the console plugin (`remote_pad.prx`) and the companion terminal code, are published under [GitHub Releases](https://github.com/Jelofen1962/JeloPad/releases/latest).

---

## Development & Building From Source

### Requirements
* [LLVM / Clang 10+](https://llvm.org/)  
* [OpenOrbis PS4 SDK Toolchain](https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain)

To compile the console plugin locally, use the following build steps:

```shell
cmake -B build -DCMAKE_TOOLCHAIN_FILE=cmake/ps4.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for more details.

---

## Acknowledgements & Credits
* Original `remote_gamepad` plugin implementation by [xfangfang](https://github.com/xfangfang).
* Special thanks to [jocover](https://github.com/jocover) for technical assistance and advice during the initial SDK implementation.
```