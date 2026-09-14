
# JeloPad

> A modern virtual controller bridge for jailbroken PlayStation 4 consoles running GoldHEN.

JeloPad allows you to use **PC gamepads, keyboards, mice, mobile devices, and other compatible input devices** as virtual controllers on a jailbroken PlayStation 4.

It consists of two main components:

- **JeloPad PS4 Plugin** — runs directly on the PS4 under GoldHEN.
- **JeloPad Client** — runs on Windows or Linux and sends controller input to the PS4 over WebSocket.

A browser-based controller is also included in the PS4 plugin, allowing phones, tablets, or other devices on the same network to control the console without installing the desktop client.

---

## Table of Contents

### English

- [Overview](#overview)
- [Features](#features)
- [How JeloPad Works](#how-jelopad-works)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [1. Install the PS4 Plugin](#1-install-the-ps4-plugin)
- [2. Start the Desktop Client](#2-start-the-desktop-client)
- [3. Connect to the PS4](#3-connect-to-the-ps4)
- [4. Assign Controllers](#4-assign-controllers)
- [5. Configure Controller Mapping](#5-configure-controller-mapping)
- [6. Use the Keyboard](#6-use-the-keyboard)
- [7. Use the Mouse](#7-use-the-mouse)
- [8. Use the Web Client](#8-use-the-web-client)
- [9. Console Configuration](#9-console-configuration)
- [10. Vibration / Rumble](#10-vibration--rumble)
- [CLI Controls](#cli-controls)
- [Configuration File](#configuration-file)
- [Network Architecture](#network-architecture)
- [Troubleshooting](#troubleshooting)
- [Running From Source](#running-from-source)
- [Building the PS4 Plugin](#building-the-ps4-plugin)
- [Project Structure](#project-structure)
- [Development](#development)
- [Credits](#credits)
- [License](#license)

### فارسی

- [معرفی](#معرفی)
- [ویژگی‌ها](#ویژگیها)
- [نحوه کار JeloPad](#نحوه-کار-jelopad)
- [پیش‌نیازها](#پیشنیازها)
- [شروع سریع](#شروع-سریع)
- [۱. نصب پلاگین PS4](#۱-نصب-پلاگین-ps4)
- [۲. اجرای کلاینت دسکتاپ](#۲-اجرای-کلاینت-دسکتاپ)
- [۳. اتصال به PS4](#۳-اتصال-به-ps4)
- [۴. اختصاص کنترلرها](#۴-اختصاص-کنترلرها)
- [۵. تنظیم Mapping کنترلر](#۵-تنظیم-mapping-کنترلر)
- [۶. استفاده از کیبورد](#۶-استفاده-از-کیبورد)
- [۷. استفاده از ماوس](#۷-استفاده-از-ماوس)
- [۸. استفاده از Web Client](#۸-استفاده-از-web-client)
- [۹. تنظیمات کنسول](#۹-تنظیمات-کنسول)
- [۱۰. لرزش و Rumble](#۱۰-لرزش-و-rumble)
- [کلیدهای میانبر CLI](#کلیدهای-میانبر-cli)
- [فایل تنظیمات](#فایل-تنظیمات)
- [معماری شبکه](#معماری-شبکه)
- [رفع مشکلات](#رفع-مشکلات)
- [اجرای پروژه از Source](#اجرای-پروژه-از-source)
- [Build پلاگین PS4](#build-پلاگین-ps4)
- [ساختار پروژه](#ساختار-پروژه)
- [توسعه](#توسعه)
- [اعتبارات](#اعتبارات)
- [لایسنس](#لایسنس)

---

# English

## Overview

JeloPad is an updated and extended version of the original `remote_gamepad` concept.

The project provides a bridge between external input devices and a jailbroken PlayStation 4 running GoldHEN.

Instead of requiring a physical DualShock 4 for every player, JeloPad can create up to **four virtual controller ports** and route input from supported devices to those ports.

For example:

```text
PC Gamepad ──────┐
Keyboard ────────┤
Mouse ───────────┼──> JeloPad Client ──WebSocket──> PS4 Plugin ──> Virtual Pad
Mobile Browser ──┘
````

This makes JeloPad useful for:

* Local multiplayer
* Custom controller setups
* Keyboard-based gaming
* Generic USB controllers
* Alternative gamepads
* Mobile-device controller input
* Controller testing
* Custom HID hardware

---

# Features

## 🎮 Multi-Port Virtual Controllers

JeloPad supports four virtual controller ports:

```text
Pad 0
Pad 1
Pad 2
Pad 3
```

Each port can independently be assigned to:

* A physical gamepad
* Keyboard Profile 1
* Mouse Profile 1
* Disabled

---

## 🖥️ Windows and Linux Client

Pre-built releases are provided for desktop users.

### Windows

Download the Windows x64 release and run the included executable.

### Linux

Download the Linux x64 release, extract it, make the binary executable, and run it.

No Python installation is required when using the pre-built releases.

---

## 🧰 Interactive Terminal UI

The desktop client provides a Textual-based terminal interface containing:

* Controller assignments
* Connected hardware
* Live controller monitoring
* Button state information
* Analog stick values
* Trigger values
* Network statistics
* Connection status
* Packet statistics
* Rumble status
* System logs

The interface is designed to let you configure and monitor JeloPad without manually editing configuration files.

---

## 🔄 Live Console Synchronization

The client communicates with the PS4 plugin through WebSocket RPC.

The client can retrieve and update console controller profiles without requiring FTP access.

Supported configuration includes:

* Virtual pad enable/disable state
* Console profile names
* Remote controller configuration
* Server connection settings

The PS4 plugin stores console configuration in:

```text
/data/GoldHEN/remote_pad.ini
```

---

## 🎮 Automatic Controller Mapping

JeloPad includes an automatic controller-mapping tool.

The mapper can detect:

* Buttons
* D-Pad / hats
* Analog axes
* Trigger axes

and assign them to the corresponding PS4 controls.

This is especially useful for generic controllers whose button layout does not match the expected PlayStation layout.

---

## ⌨️ Keyboard Input

A built-in keyboard profile can emulate a complete controller.

The default keyboard layout is:

| Keyboard    | PS4 Control |
| ----------- | ----------- |
| `Space`     | Cross       |
| `Escape`    | Circle      |
| `Enter`     | Triangle    |
| `Backspace` | Square      |
| `Q`         | L1          |
| `E`         | R1          |
| `1`         | L2          |
| `3`         | R2          |
| `O`         | Options     |
| `U`         | Touchpad    |
| `I`         | D-Pad Up    |
| `K`         | D-Pad Down  |
| `J`         | D-Pad Left  |
| `L`         | D-Pad Right |

### Left Stick

| Key | Direction        |
| --- | ---------------- |
| `W` | Left Stick Up    |
| `S` | Left Stick Down  |
| `A` | Left Stick Left  |
| `D` | Left Stick Right |

### Right Stick

| Key           | Direction         |
| ------------- | ----------------- |
| `Arrow Up`    | Right Stick Up    |
| `Arrow Down`  | Right Stick Down  |
| `Arrow Left`  | Right Stick Left  |
| `Arrow Right` | Right Stick Right |

Keyboard analog movement is converted into PS4-compatible analog values.

---

## 🖱️ Mouse Input

JeloPad can also use the terminal application's mouse as a virtual controller.

Default mouse mapping:

| Mouse        | PS4 Control |
| ------------ | ----------- |
| Left Click   | Cross       |
| Right Click  | Circle      |
| Middle Click | R1          |
| Wheel Up     | D-Pad Up    |
| Wheel Down   | D-Pad Down  |

---

## 📱 Browser-Based Controller

The PS4 plugin contains an embedded web controller.

A phone, tablet, laptop, or another computer can connect through a normal browser.

No additional application is required.

Open:

```text
http://<PS4-IP>:4263
```

Example:

```text
http://192.168.1.50:4263
```

The device must be able to reach the PS4 over the local network.

The web interface supports controller input and provides visual feedback for features such as:

* Buttons
* Analog controls
* Touchpad
* Triggers
* Lightbar information
* Rumble activity

---

# How JeloPad Works

JeloPad is divided into three layers.

```text
┌─────────────────────────────┐
│       Input Device          │
│                             │
│ Gamepad / Keyboard / Mouse  │
│ Mobile Browser              │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      JeloPad Client         │
│                             │
│ Input Processing            │
│ Mapping                     │
│ Virtual Pad Assignment      │
│ Rumble Handling             │
│ WebSocket Communication     │
└──────────────┬──────────────┘
               │
          WebSocket
          Port 4263
               │
               ▼
┌─────────────────────────────┐
│       PS4 JeloPad Plugin    │
│                             │
│ GoldHEN Plugin              │
│ Network Server              │
│ Virtual Controller Bridge   │
│ Console Configuration       │
└──────────────┬──────────────┘
               │
               ▼
        PlayStation 4
```

The desktop client continuously reads input devices and sends only changed controller states to the PS4.

This prevents unnecessary network traffic and avoids building a large packet backlog during temporary network congestion.

---

# Requirements

## PS4

You need:

* A jailbroken PlayStation 4
* GoldHEN
* GoldHEN plugin support
* Local network connectivity

JeloPad is intended for PS4 systems capable of loading GoldHEN plugins.

---

## PC

For pre-built releases:

* Windows x64 or Linux x64
* Local network access to the PS4
* A compatible controller if you intend to use a physical gamepad

For running from source:

* Python 3.10+
* `pygame`
* `websockets`
* `textual`
* `rich`

Optional:

* `hidapi`

---

# Quick Start

The easiest setup is:

```text
1. Install jelopad.prx on the PS4
2. Restart the PS4
3. Find the PS4 IP address
4. Start JeloPad on Windows/Linux
5. Enter the PS4 IP
6. Press F2 to connect
7. Assign your controller
8. Start playing
```

---

# 1. Install the PS4 Plugin

Download the plugin from the latest GitHub Release:

```text
jelopad.prx
```

Copy it to:

```text
/data/GoldHEN/plugins/
```

Your final path should be:

```text
/data/GoldHEN/plugins/jelopad.prx
```

---

## Register the Plugin

Open:

```text
/data/GoldHEN/plugins.ini
```

Under the `[system]` section, add:

```ini
[system]
/data/GoldHEN/plugins/jelopad.prx
```

Make sure the filename exactly matches the file installed on your PS4.

For example, if the file is:

```text
jelopad.prx
```

do **not** register:

```text
remote_pad.prx
```

---

## Restart the PS4

Restart the console after installing or registering the plugin.

When JeloPad starts successfully, it will expose its network service on:

```text
Port: 4263
```

The PS4 should provide its network address through the plugin notification.

For example:

```text
JeloPad Server
192.168.1.50:4263
```

Write down the IP address.

You will need it on your PC or mobile device.

---

# 2. Start the Desktop Client

## Windows

Download:

```text
JeloPad-Windows-x64.zip
```

Extract the archive.

Run the included JeloPad executable.

No Python installation is required for the pre-built release.

---

## Linux

Download:

```text
JeloPad-Linux-x64-bin.zip
```

Extract it.

Open a terminal in the extracted directory and run:

```bash
chmod +x ./JeloPad
```

Then:

```bash
./JeloPad
```

If the release uses a different executable filename, use that filename instead.

---

# 3. Connect to the PS4

The client stores the server address in:

```text
config.toml
```

By default, the client uses:

```text
ws://127.0.0.1:4263
```

For a remote PS4, change it to your console address:

```text
ws://192.168.1.50:4263
```

You can also configure the address from the client's configuration interface.

Once the address is correct:

```text
Press F2
```

to connect.

The status should change from:

```text
Disconnected
```

to:

```text
Connected
```

The client will then request the current console configuration and synchronize available profiles.

---

# 4. Assign Controllers

Press:

```text
F4
```

to open the controller assignment menu.

Each virtual controller port can be assigned independently.

Example:

```text
Pad 0 → Xbox Controller
Pad 1 → Keyboard Profile 1
Pad 2 → None
Pad 3 → None
```

Available input sources include:

* Connected gamepads
* Keyboard Profile 1
* Mouse Profile 1
* Disabled

Save the configuration when finished.

The assignment is stored in:

```text
config.toml
```

---

# 5. Configure Controller Mapping

If your controller has an unusual layout, use the automatic mapper.

Press:

```text
F7
```

The mapping wizard will guide you through the PS4 controls.

The mapper checks:

* Buttons
* Hats / D-Pad
* Analog axes
* Axis direction

For each requested PS4 action, press or move the corresponding control on your physical controller.

If an action is not available, wait for the mapping timeout to skip it.

Press:

```text
Escape
```

to cancel the mapping process.

When mapping is completed, the new configuration is automatically saved.

---

# 6. Use the Keyboard

Keyboard Profile 1 is available even if no physical controller is connected.

Assign:

```text
Pad 0 → Keyboard Profile 1
```

Then use the default keyboard layout.

### Buttons

```text
Space      → Cross
Escape     → Circle
Enter      → Triangle
Backspace  → Square

Q          → L1
E          → R1
1          → L2
3          → R2

O          → Options
U          → Touchpad

I          → D-Pad Up
K          → D-Pad Down
J          → D-Pad Left
L          → D-Pad Right
```

### Left Stick

```text
W → Up
A → Left
S → Down
D → Right
```

### Right Stick

```text
↑ → Up
← → Left
↓ → Down
→ → Right
```

---

# 7. Use the Mouse

Assign:

```text
Pad 0 → Mouse Profile 1
```

Mouse input is translated into a simple controller profile.

```text
Left Click   → Cross
Right Click  → Circle
Middle Click → R1

Wheel Up     → D-Pad Up
Wheel Down   → D-Pad Down
```

The mouse profile is primarily intended for simple controller interaction and testing.

---

# 8. Use the Web Client

The web client is useful when you do not want to install the desktop application.

Make sure the phone, tablet, or computer is connected to a network that can reach the PS4.

Open:

```text
http://<PS4-IP>:4263
```

Example:

```text
http://192.168.1.50:4263
```

If the page does not open:

1. Confirm the PS4 IP address.
2. Confirm the plugin is running.
3. Confirm port `4263` is reachable.
4. Confirm both devices are on the same network or otherwise have routing between them.

---

# 9. Console Configuration

Press:

```text
F5
```

to open:

```text
JeloPad System Preferences
```

The configuration interface allows you to:

* Change the PS4 WebSocket address
* View console profiles
* Enable/disable virtual controller profiles
* Rename profiles
* Upload the updated configuration to the console

The client communicates with the plugin using:

```text
config.get
config.set
```

The console stores the relevant configuration at:

```text
/data/GoldHEN/remote_pad.ini
```

This means you do not need to manually edit the configuration through FTP for normal configuration changes.

---

# 10. Vibration / Rumble

JeloPad supports bidirectional rumble communication.

The PS4 sends vibration intensity information back to the client.

The client can then attempt to reproduce the vibration using:

1. A direct HID controller profile
2. Generic HID vibration packets
3. SDL/Pygame rumble as a fallback

---

## HID Rumble

Some controllers can receive raw HID vibration reports directly.

The client contains profiles for several common devices, including examples such as:

* Xbox 360 wired controllers
* Xbox One / Series wired controllers
* DualShock 3
* DualShock 4
* Several generic HID devices

Generic HID support also includes common vendor IDs such as:

```text
0x0810
0x0E8F
0x120A
0x1A2C
```

Hardware support can vary depending on the exact controller model and firmware.

---

## Optional HID Dependency

If the `hid` Python package is not installed, the client will still work for normal controller input.

However, direct HID rumble support will be disabled.

Install it with:

```bash
python -m pip install hidapi
```

---

# CLI Controls

The JeloPad terminal client provides the following keyboard shortcuts:

| Key   | Action                        |
| ----- | ----------------------------- |
| `F2`  | Connect                       |
| `F3`  | Disconnect                    |
| `F4`  | Controller Assignments        |
| `F5`  | Console Sync / Configuration  |
| `F7`  | Automatic Gamepad Mapping     |
| `F8`  | Cycle Live Controller Monitor |
| `F10` | Exit                          |

---

## Live Monitor

The live monitor displays the current state of the selected virtual controller.

It can show:

* Pressed buttons
* Button mask
* Left stick X/Y
* Right stick X/Y
* Left trigger
* Right trigger
* Active input mapping
* Rumble status

Use:

```text
F8
```

to cycle between:

```text
Pad 0
Pad 1
Pad 2
Pad 3
```

---

# Configuration File

The desktop client automatically creates:

```text
config.toml
```

The configuration contains several sections.

Example:

```toml
[network]
server_url = "ws://192.168.1.50:4263"
tick_rate = 120

[input]
smoothing = 1.0

[assignments]
pad0 = "Keyboard 1"
pad1 = "None"
pad2 = "None"
pad3 = "None"

[joy_mapping]
```

---

## Network Settings

```toml
[network]
server_url = "ws://192.168.1.50:4263"
tick_rate = 120
```

### `server_url`

The WebSocket endpoint of the PS4.

Example:

```text
ws://192.168.1.50:4263
```

### `tick_rate`

Controls the client input update frequency.

The default is:

```text
120 Hz
```

Higher values can increase update frequency but may also increase CPU/network activity.

---

## Input Smoothing

```toml
[input]
smoothing = 1.0
```

`1.0` provides immediate keyboard analog movement.

Values below `1.0` can be used to smooth keyboard-to-analog transitions.

---

# Network Architecture

JeloPad uses WebSocket communication between the desktop client and the PS4 plugin.

```text
Desktop Client
      │
      │ WebSocket
      │ TCP 4263
      ▼
JeloPad PS4 Plugin
      │
      ├── Controller Input
      ├── Rumble Events
      ├── Profile Configuration
      └── Console State
```

The client sends controller updates using the JeloPad protocol.

Controller state contains values for:

```text
Virtual Pad
Buttons
LX
LY
RX
RY
L2
R2
```

The client also uses a loss-tolerant latest-state queue so outdated controller packets do not build up when the network is temporarily busy.

---

# Troubleshooting

## The PS4 plugin does not load

Check:

```text
/data/GoldHEN/plugins/jelopad.prx
```

exists.

Then verify:

```text
/data/GoldHEN/plugins.ini
```

contains:

```ini
[system]
/data/GoldHEN/plugins/jelopad.prx
```

Make sure the filename is identical.

Restart the PS4 after changing the plugin configuration.

---

## The client cannot connect

Verify the WebSocket address.

For example:

```text
ws://192.168.1.50:4263
```

Check that:

* The PS4 is powered on.
* GoldHEN is running.
* JeloPad is loaded.
* The IP address is correct.
* Port `4263` is reachable.
* Your network allows communication between the devices.

---

## The web page does not open

Try:

```text
http://192.168.1.50:4263
```

If it fails:

1. Check the PS4 IP.
2. Check that the plugin loaded.
3. Try the address from another device on the same network.
4. Verify that the PS4 is reachable using its IP address.

---

## The controller is detected but buttons are wrong

Open the automatic mapper:

```text
F7
```

and map the controller again.

The mapping is saved to:

```text
config.toml
```

---

## The controller does not appear

Make sure the controller is recognized by the operating system.

Then restart or reconnect JeloPad.

The client periodically refreshes connected controller devices.

---

## Rumble does not work

Normal input operation does not require HID support.

If direct HID rumble is required, install:

```bash
python -m pip install hidapi
```

Some controllers may not have a supported HID rumble profile.

When direct HID rumble is unavailable, JeloPad attempts to use the controller's normal SDL/Pygame rumble interface when supported.

---

## The keyboard works but analog movement feels wrong

The keyboard converts digital keys into analog stick values.

Try adjusting:

```toml
[input]
smoothing = 0.5
```

or another value below `1.0`.

For immediate movement:

```toml
smoothing = 1.0
```

---

# Running From Source

If you want to run the Python client directly from the repository, use Python 3.10 or newer.

Clone the repository:

```bash
git clone https://github.com/Jelofen1962/JeloPad.git
cd JeloPad
```

Create a virtual environment:

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install the project's requirements:

```bash
python -m pip install -r requirements.txt
```

The client also uses Textual and Rich for its terminal interface. If they are not already included in your environment, install them with:

```bash
python -m pip install textual rich
```

For optional HID support:

```bash
python -m pip install hidapi
```

Run the client:

```bash
python cli.py
```

---

## Python Dependencies

The core project requirements include:

```text
pygame
websockets
```

The CLI also uses:

```text
textual
rich
```

Optional HID support uses:

```text
hidapi
```

Python 3.11+ includes `tomllib` in the standard library.

For older supported Python versions where a TOML parser is unavailable, the client can use the `tomli` compatibility package.

---

# Building the PS4 Plugin

Building the PS4 plugin requires a PS4 development environment.

## Requirements

You need:

* CMake 3.10+
* LLVM / Clang
* OpenOrbis PS4 Toolchain
* The repository submodules
* A suitable PS4 SDK development environment

The project expects the following environment variable:

```text
OO_PS4_TOOLCHAIN
```

For example:

```bash
export OO_PS4_TOOLCHAIN=/path/to/PS4Toolchain
```

The build system will stop if this variable is not configured.

---

## Initialize Submodules

Clone the repository:

```bash
git clone --recursive https://github.com/Jelofen1962/JeloPad.git
cd JeloPad
```

If the repository was cloned without submodules:

```bash
git submodule update --init --recursive
```

---

## Configure the Build

Run:

```bash
cmake -B build \
  -DCMAKE_TOOLCHAIN_FILE=cmake/ps4.cmake \
  -DCMAKE_BUILD_TYPE=Release
```

Then build:

```bash
cmake --build build
```

The build system packages the embedded web client into the plugin during the build process.

---

## Optional: Send the Plugin Directly to the PS4

The CMake project provides an optional `DEVICE_IP` setting.

Example:

```bash
cmake -B build \
  -DCMAKE_TOOLCHAIN_FILE=cmake/ps4.cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DDEVICE_IP=192.168.1.50
```

The project can then provide a target for sending the generated PRX to:

```text
/data/GoldHEN/plugins/
```

through the PS4 FTP service on port `2121`.

Only use this if FTP is enabled and reachable on your PS4.

---

# Project Structure

```text
JeloPad/
├── .github/
│   └── workflows/
│
├── client/
│   └── index.html
│
├── cmake/
│   └── ps4.cmake
│
├── include/
│
├── lib/
│
├── src/
│   ├── *.c
│   └── pad/
│
├── CMakeLists.txt
├── Dockerfile
├── cli.py
├── requirements.txt
├── LICENSE
└── README.md
```

### `client/`

Contains the embedded browser controller.

### `src/`

Contains the PS4 plugin implementation.

### `include/`

Contains project headers.

### `lib/`

Contains project dependencies and supporting libraries.

### `cmake/`

Contains the PS4-specific CMake toolchain configuration.

### `cli.py`

Contains the Windows/Linux terminal client.

### `requirements.txt`

Contains the Python dependencies used by the project.

---

# Development

JeloPad is split between native PS4 code and a Python desktop client.

## PS4 Side

The PS4 plugin is responsible for:

* Receiving controller input
* Providing the WebSocket server
* Managing virtual controller state
* Providing console configuration RPC
* Serving the embedded web client
* Sending rumble information to connected clients
* Integrating with GoldHEN / PS4 APIs

---

## Desktop Side

The desktop client is responsible for:

* Detecting controllers
* Reading gamepad input
* Reading keyboard input
* Reading mouse input
* Mapping physical controls
* Assigning devices to virtual ports
* Sending controller states
* Receiving rumble events
* Synchronizing console configuration
* Displaying diagnostics

---

# Performance

JeloPad is designed to keep input processing responsive while avoiding unnecessary background CPU usage.

The PS4 plugin uses a background server polling interval of approximately:

```text
10 ms
```

The desktop client uses a default input update rate of:

```text
120 Hz
```

Controller states are sent when they change rather than continuously building a backlog of outdated packets.

This architecture prioritizes current controller state over stale network messages.

---

# Security & Network Notes

JeloPad is designed primarily for use on a trusted local network.

The server uses the PS4's network interface and port:

```text
4263
```

The project does not provide authentication or encryption for the local WebSocket protocol.

Therefore:

> **Do not expose JeloPad's port directly to the public Internet.**

Use JeloPad on a trusted LAN or an appropriately secured private network.

---

# Compatibility

JeloPad is designed for:

```text
PlayStation 4
GoldHEN
```

Desktop client:

```text
Windows x64
Linux x64
```

The exact behavior of individual controllers depends on:

* Operating system support
* SDL/Pygame compatibility
* Controller firmware
* HID report format
* Available rumble implementation

Generic controllers may require manual mapping.

---

# Releases

Pre-built releases are available on the GitHub Releases page.

Typical release assets include:

| File                        | Platform      | Purpose        |
| --------------------------- | ------------- | -------------- |
| `JeloPad-Windows-x64.zip`   | Windows x64   | Desktop client |
| `JeloPad-Linux-x64-bin.zip` | Linux x64     | Desktop client |
| `jelopad.prx`               | PS4 / GoldHEN | Console plugin |

Always use the plugin and client from the same release when possible.

---

# Credits

JeloPad is based on the original:

`remote_gamepad`

project by:

**xfangfang**

Special thanks to:

**jocover**

for technical assistance and advice during the initial PS4 SDK implementation.

JeloPad is maintained and further developed by:

**Jelofen1962**

---

# License

JeloPad is licensed under the:

**MIT License**

See [`LICENSE`](LICENSE) for the complete license text.

---

# Disclaimer

JeloPad is an independent open-source project.

PlayStation, PlayStation 4, DualShock, GoldHEN, and related trademarks belong to their respective owners.

JeloPad is not affiliated with or endorsed by Sony Interactive Entertainment.

Use the software responsibly and only on systems and networks you are authorized to modify and operate.

---

# Contributing

Contributions, bug reports, controller compatibility reports, and improvements are welcome.

When reporting a controller issue, please include:

* Operating system
* Controller name
* Controller connection type
* Controller VID/PID if known
* Whether normal input works
* Whether rumble works
* Relevant JeloPad logs
* PS4 / GoldHEN information where relevant

Avoid posting personal information, network credentials, or public IP addresses.

---

# Support

Before opening an issue:

1. Read the installation instructions.
2. Confirm the plugin is loaded.
3. Confirm the PS4 IP address.
4. Confirm port `4263` is reachable.
5. Test the web client.
6. Check the JeloPad CLI logs.
7. Try the automatic controller mapper.

If the problem remains, open an issue with the relevant technical information.

---

# JeloPad

**One PS4.
Multiple input devices.
One simple bridge.**

---

<br>

# فارسی

# JeloPad

> یک پل مدرن برای تبدیل کنترلرهای مختلف به کنترلر مجازی PlayStation 4 با استفاده از GoldHEN.

JeloPad به شما اجازه می‌دهد از **گیم‌پدهای کامپیوتر، کیبورد، ماوس، موبایل و سایر کنترلرهای سازگار** به‌عنوان کنترلر مجازی روی یک PS4 جیلبریک‌شده استفاده کنید.

JeloPad از دو بخش اصلی تشکیل شده است:

* **JeloPad PS4 Plugin** — روی PS4 و تحت GoldHEN اجرا می‌شود.
* **JeloPad Client** — روی Windows یا Linux اجرا شده و ورودی کنترلر را از طریق WebSocket به PS4 ارسال می‌کند.

همچنین یک **Web Client** داخل پلاگین PS4 قرار دارد که امکان استفاده از موبایل، تبلت یا کامپیوتر را به‌عنوان کنترلر از طریق مرورگر فراهم می‌کند.

---

# معرفی

JeloPad نسخه توسعه‌یافته و به‌روزشده ایده پروژه اصلی `remote_gamepad` است.

هدف پروژه ایجاد یک پل بین دستگاه‌های ورودی مختلف و PlayStation 4 است.

به‌جای اینکه برای هر بازیکن یک DualShock 4 فیزیکی داشته باشید، JeloPad می‌تواند تا **چهار Virtual Controller Port** ایجاد کند و ورودی دستگاه‌های مختلف را به این پورت‌ها منتقل کند.

برای مثال:

```text
Gamepad ─────────┐
Keyboard ────────┤
Mouse ───────────┼──> JeloPad Client ──WebSocket──> PS4 Plugin
Mobile Browser ──┘
```

این قابلیت برای موارد زیر کاربرد دارد:

* بازی چندنفره محلی
* استفاده از کنترلرهای متفرقه
* بازی با کیبورد
* استفاده از کنترلرهای USB
* استفاده از موبایل به‌عنوان کنترلر
* تست کنترلر
* سخت‌افزارهای HID سفارشی

---

# ویژگی‌ها

## 🎮 چهار کنترلر مجازی

JeloPad چهار Virtual Pad دارد:

```text
Pad 0
Pad 1
Pad 2
Pad 3
```

هر Pad را می‌توان به‌صورت جداگانه به یکی از موارد زیر اختصاص داد:

* کنترلر فیزیکی
* Keyboard Profile 1
* Mouse Profile 1
* Disabled

---

## 🖥️ کلاینت Windows و Linux

نسخه‌های آماده برای کاربران عادی ارائه می‌شوند.

### Windows

فایل Release ویندوز را دانلود و فایل اجرایی را اجرا کنید.

### Linux

فایل Linux x64 را دانلود کنید، از حالت فشرده خارج کنید و فایل اجرایی را اجرا کنید.

در نسخه‌های آماده نیازی به نصب Python نیست.

---

# رابط کاربری ترمینال

کلاینت JeloPad یک رابط کاربری تعاملی در ترمینال دارد.

این رابط اطلاعات زیر را نمایش می‌دهد:

* اختصاص کنترلرها
* دستگاه‌های متصل
* وضعیت زنده کنترلر
* دکمه‌های فشرده‌شده
* مقدار Analog Stick
* Triggerها
* وضعیت اتصال
* آمار شبکه
* تعداد Packetها
* وضعیت Rumble
* Log سیستم

---

# همگام‌سازی با PS4

کلاینت و پلاگین PS4 از WebSocket و RPC برای ارتباط استفاده می‌کنند.

بنابراین می‌توانید بدون ویرایش دستی فایل از طریق FTP، تنظیمات مربوط به کنترلرهای مجازی را تغییر دهید.

موارد قابل تنظیم شامل:

* فعال/غیرفعال کردن Padها
* نام Profileها
* تنظیمات Remote Controller
* آدرس سرور

تنظیمات PS4 در مسیر زیر ذخیره می‌شوند:

```text
/data/GoldHEN/remote_pad.ini
```

---

# Mapping خودکار کنترلر

JeloPad دارای ابزار Auto Mapping است.

این ابزار می‌تواند موارد زیر را شناسایی کند:

* Button
* D-Pad / Hat
* Analog Axis
* جهت Axis
* Trigger

بنابراین اگر کنترلر شما Layout متفاوتی داشته باشد، لازم نیست Mapping را دستی در فایل وارد کنید.

---

# Keyboard Controller

JeloPad دارای Keyboard Profile داخلی است.

Mapping پیش‌فرض:

| کیبورد      | کنترل PS4   |
| ----------- | ----------- |
| `Space`     | Cross       |
| `Escape`    | Circle      |
| `Enter`     | Triangle    |
| `Backspace` | Square      |
| `Q`         | L1          |
| `E`         | R1          |
| `1`         | L2          |
| `3`         | R2          |
| `O`         | Options     |
| `U`         | Touchpad    |
| `I`         | D-Pad Up    |
| `K`         | D-Pad Down  |
| `J`         | D-Pad Left  |
| `L`         | D-Pad Right |

### آنالوگ چپ

```text
W → بالا
A → چپ
S → پایین
D → راست
```

### آنالوگ راست

```text
↑ → بالا
← → چپ
↓ → پایین
→ → راست
```

---

# Mouse Controller

ماوس نیز می‌تواند به‌عنوان یک Virtual Controller استفاده شود.

Mapping پیش‌فرض:

| ماوس         | کنترل PS4  |
| ------------ | ---------- |
| Left Click   | Cross      |
| Right Click  | Circle     |
| Middle Click | R1         |
| Wheel Up     | D-Pad Up   |
| Wheel Down   | D-Pad Down |

---

# Web Client

اگر نمی‌خواهید روی موبایل یا کامپیوتر برنامه‌ای نصب کنید، می‌توانید از Web Client استفاده کنید.

مرورگر را باز کرده و وارد شوید:

```text
http://<PS4-IP>:4263
```

مثال:

```text
http://192.168.1.50:4263
```

دستگاه باید بتواند به PS4 از طریق شبکه دسترسی داشته باشد.

Web Client برای مواردی مانند موارد زیر طراحی شده است:

* Button Input
* Analog Stick
* Trigger
* Touchpad
* Lightbar information
* Rumble

---

# نحوه کار JeloPad

معماری کلی:

```text
┌─────────────────────────────┐
│       Input Device          │
│                             │
│ Gamepad / Keyboard / Mouse  │
│ Mobile Browser              │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      JeloPad Client         │
│                             │
│ Input Processing            │
│ Mapping                     │
│ Controller Assignment       │
│ Rumble Handling             │
│ WebSocket                   │
└──────────────┬──────────────┘
               │
          WebSocket
          Port 4263
               │
               ▼
┌─────────────────────────────┐
│       PS4 Plugin            │
│                             │
│ GoldHEN                     │
│ Network Server              │
│ Virtual Controller Bridge   │
│ Console Configuration       │
└─────────────────────────────┘
```

کلاینت ورودی‌ها را دریافت می‌کند و وضعیت کنترلر را به PS4 ارسال می‌کند.

برای کاهش ترافیک و جلوگیری از ایجاد صف Packetهای قدیمی، وضعیت‌های جدید کنترلر نسبت به وضعیت قبلی مدیریت می‌شوند.

---

# پیش‌نیازها

## PS4

نیاز دارید:

* PlayStation 4 جیلبریک‌شده
* GoldHEN
* امکان اجرای Plugin
* اتصال شبکه

---

## کامپیوتر

برای نسخه‌های آماده:

* Windows x64 یا Linux x64
* دسترسی شبکه به PS4
* کنترلر سازگار در صورت استفاده از Gamepad

برای اجرای Source:

* Python 3.10+
* pygame
* websockets
* textual
* rich

اختیاری:

```text
hidapi
```

---

# شروع سریع

مراحل کلی:

```text
1. نصب jelopad.prx روی PS4
2. Restart کردن PS4
3. پیدا کردن IP کنسول
4. اجرای JeloPad روی Windows/Linux
5. وارد کردن IP
6. فشردن F2
7. اتصال کنترلر
8. شروع بازی
```

---

# ۱. نصب پلاگین PS4

فایل زیر را از Release دانلود کنید:

```text
jelopad.prx
```

آن را در مسیر زیر قرار دهید:

```text
/data/GoldHEN/plugins/
```

در نتیجه باید داشته باشید:

```text
/data/GoldHEN/plugins/jelopad.prx
```

---

## ثبت Plugin در GoldHEN

فایل زیر را باز کنید:

```text
/data/GoldHEN/plugins.ini
```

در قسمت `[system]` اضافه کنید:

```ini
[system]
/data/GoldHEN/plugins/jelopad.prx
```

نام فایل باید دقیقاً با Plugin شما یکسان باشد.

اگر فایل شما:

```text
jelopad.prx
```

است، نباید در `plugins.ini` بنویسید:

```text
remote_pad.prx
```

---

# Restart کردن PS4

پس از نصب Plugin، PS4 را Restart کنید.

JeloPad از Port زیر استفاده می‌کند:

```text
4263
```

پس از اجرای موفق Plugin باید IP کنسول را مشاهده کنید.

برای مثال:

```text
192.168.1.50:4263
```

IP را یادداشت کنید.

---

# ۲. اجرای کلاینت دسکتاپ

## Windows

فایل:

```text
JeloPad-Windows-x64.zip
```

را دانلود کنید.

آن را Extract کرده و فایل اجرایی را اجرا کنید.

در نسخه Release نیازی به نصب Python ندارید.

---

## Linux

فایل:

```text
JeloPad-Linux-x64-bin.zip
```

را دانلود و Extract کنید.

سپس:

```bash
chmod +x ./JeloPad
```

و:

```bash
./JeloPad
```

را اجرا کنید.

اگر نام فایل اجرایی در Release متفاوت است، همان نام را استفاده کنید.

---

# ۳. اتصال به PS4

کلاینت از فایل زیر برای ذخیره تنظیمات استفاده می‌کند:

```text
config.toml
```

برای مثال:

```text
ws://192.168.1.50:4263
```

آدرس باید به PS4 اشاره کند.

سپس:

```text
F2
```

را فشار دهید.

در صورت اتصال موفق، وضعیت باید به:

```text
Connected
```

تغییر کند.

کلاینت سپس تنظیمات و Profileهای کنسول را دریافت می‌کند.

---

# ۴. اختصاص کنترلرها

برای باز کردن منوی Controller Assignment:

```text
F4
```

را فشار دهید.

مثال:

```text
Pad 0 → Xbox Controller
Pad 1 → Keyboard Profile 1
Pad 2 → None
Pad 3 → None
```

گزینه‌های قابل استفاده:

* Gamepad
* Keyboard
* Mouse
* Disabled

پس از انتخاب، تنظیمات را Save کنید.

---

# ۵. تنظیم Mapping کنترلر

برای اجرای Auto Mapper:

```text
F7
```

را فشار دهید.

برنامه از شما می‌خواهد کنترل مربوط به هر Action را فشار دهید.

موارد قابل Mapping:

* Cross
* Circle
* Square
* Triangle
* L1
* R1
* L2
* R2
* L3
* R3
* D-Pad
* Options
* Touchpad
* Left Stick
* Right Stick

اگر یک Action را نمی‌خواهید تنظیم کنید، منتظر پایان زمان آن مرحله بمانید.

برای لغو:

```text
Escape
```

را فشار دهید.

پس از پایان Mapping، تنظیمات در:

```text
config.toml
```

ذخیره می‌شوند.

---

# ۶. استفاده از کیبورد

ابتدا:

```text
Pad 0 → Keyboard Profile 1
```

را انتخاب کنید.

سپس از Mapping پیش‌فرض استفاده کنید.

```text
Space      → Cross
Escape     → Circle
Enter      → Triangle
Backspace  → Square

Q          → L1
E          → R1
1          → L2
3          → R2

O          → Options
U          → Touchpad

I          → Up
K          → Down
J          → Left
L          → Right
```

### آنالوگ چپ

```text
W A S D
```

### آنالوگ راست

```text
Arrow Keys
```

---

# ۷. استفاده از ماوس

اختصاص دهید:

```text
Pad 0 → Mouse Profile 1
```

سپس:

```text
Left Click   → Cross
Right Click  → Circle
Middle Click → R1

Wheel Up     → D-Pad Up
Wheel Down   → D-Pad Down
```

---

# ۸. استفاده از Web Client

در مرورگر وارد شوید:

```text
http://<PS4-IP>:4263
```

مثال:

```text
http://192.168.1.50:4263
```

اگر صفحه باز نشد:

1. IP را بررسی کنید.
2. مطمئن شوید Plugin اجرا شده است.
3. Port `4263` را بررسی کنید.
4. مطمئن شوید دستگاه و PS4 امکان ارتباط شبکه‌ای دارند.

---

# ۹. تنظیمات کنسول

برای باز کردن تنظیمات:

```text
F5
```

را فشار دهید.

می‌توانید موارد زیر را تنظیم کنید:

* Server Address
* نام Profileها
* فعال/غیرفعال کردن Profileها
* ارسال تنظیمات به PS4

تنظیمات PS4 در:

```text
/data/GoldHEN/remote_pad.ini
```

ذخیره می‌شوند.

---

# ۱۰. لرزش و Rumble

JeloPad اطلاعات Rumble را از PS4 دریافت می‌کند و تلاش می‌کند آن را به کنترلر متصل‌شده منتقل کند.

اولویت به‌صورت کلی:

```text
Direct HID
     ↓
Generic HID
     ↓
SDL/Pygame Rumble
```

کنترلرهای مختلف ممکن است رفتار متفاوتی داشته باشند.

برای فعال کردن Direct HID:

```bash
python -m pip install hidapi
```

---

# کلیدهای میانبر CLI

| کلید  | عملکرد                 |
| ----- | ---------------------- |
| `F2`  | Connect                |
| `F3`  | Disconnect             |
| `F4`  | Controller Assignments |
| `F5`  | Console Configuration  |
| `F7`  | Automatic Mapping      |
| `F8`  | تغییر Live Monitor     |
| `F10` | خروج                   |

---

# Live Monitor

Live Monitor وضعیت کنترلر انتخاب‌شده را نمایش می‌دهد.

شامل:

* Button Mask
* Buttonهای فعال
* LX
* LY
* RX
* RY
* LT
* RT
* Mapping فعال
* Rumble Status

با:

```text
F8
```

بین Padها جابه‌جا شوید.

---

# فایل تنظیمات

فایل:

```text
config.toml
```

نمونه:

```toml
[network]
server_url = "ws://192.168.1.50:4263"
tick_rate = 120

[input]
smoothing = 1.0

[assignments]
pad0 = "Keyboard 1"
pad1 = "None"
pad2 = "None"
pad3 = "None"

[joy_mapping]
```

---

## Network

```toml
[network]
server_url = "ws://192.168.1.50:4263"
tick_rate = 120
```

`server_url` آدرس WebSocket کنسول است.

`tick_rate` نرخ بررسی و ارسال وضعیت ورودی است.

مقدار پیش‌فرض:

```text
120 Hz
```

---

## Input Smoothing

```toml
[input]
smoothing = 1.0
```

مقدار `1.0` یعنی حرکت سریع و مستقیم.

مقادیر کمتر از `1.0` می‌توانند برای نرم‌تر شدن حرکت Keyboard Analog استفاده شوند.

---

# معماری شبکه

ارتباط اصلی:

```text
JeloPad Client
      │
      │ WebSocket
      │ TCP 4263
      ▼
JeloPad PS4 Plugin
      │
      ├── Controller Input
      ├── Rumble
      ├── Configuration
      └── Console State
```

---

# رفع مشکلات

## Plugin اجرا نمی‌شود

این مسیر را بررسی کنید:

```text
/data/GoldHEN/plugins/jelopad.prx
```

سپس:

```text
/data/GoldHEN/plugins.ini
```

باید شامل:

```ini
[system]
/data/GoldHEN/plugins/jelopad.prx
```

باشد.

بعد PS4 را Restart کنید.

---

## Client وصل نمی‌شود

آدرس باید شبیه این باشد:

```text
ws://192.168.1.50:4263
```

موارد زیر را بررسی کنید:

* PS4 روشن است.
* GoldHEN فعال است.
* Plugin اجرا شده است.
* IP صحیح است.
* Port `4263` در دسترس است.
* دستگاه و PS4 امکان ارتباط شبکه‌ای دارند.

---

## Web Client باز نمی‌شود

آدرس را به شکل زیر وارد کنید:

```text
http://192.168.1.50:4263
```

اگر باز نشد:

1. IP را بررسی کنید.
2. Plugin را بررسی کنید.
3. از یک دستگاه دیگر تست کنید.
4. دسترسی شبکه به PS4 را بررسی کنید.

---

## Mapping کنترلر اشتباه است

`F7` را فشار دهید و Mapping را دوباره انجام دهید.

---

## کنترلر شناسایی نمی‌شود

ابتدا مطمئن شوید سیستم‌عامل کنترلر را می‌شناسد.

سپس JeloPad را Restart کنید.

---

## Rumble کار نمی‌کند

برای Direct HID:

```bash
python -m pip install hidapi
```

برخی کنترلرها ممکن است HID Rumble سازگار نداشته باشند.

در این حالت JeloPad در صورت پشتیبانی کنترلر تلاش می‌کند از SDL/Pygame Rumble استفاده کند.

---

# اجرای پروژه از Source

Python نسخه 3.10 یا جدیدتر نصب کنید.

Repository را Clone کنید:

```bash
git clone https://github.com/Jelofen1962/JeloPad.git
cd JeloPad
```

Virtual Environment بسازید.

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Dependencies را نصب کنید:

```bash
python -m pip install -r requirements.txt
```

در صورت نیاز:

```bash
python -m pip install textual rich
```

برای HID:

```bash
python -m pip install hidapi
```

سپس:

```bash
python cli.py
```

---

# Build پلاگین PS4

برای Build پلاگین PS4 به محیط توسعه مناسب PS4 نیاز دارید.

پیش‌نیازها:

* CMake 3.10+
* LLVM / Clang
* OpenOrbis PS4 Toolchain
* Git Submodules
* محیط مناسب توسعه PS4

متغیر زیر باید تنظیم شود:

```text
OO_PS4_TOOLCHAIN
```

مثال:

```bash
export OO_PS4_TOOLCHAIN=/path/to/PS4Toolchain
```

---

## دریافت Repository

```bash
git clone --recursive https://github.com/Jelofen1962/JeloPad.git
cd JeloPad
```

اگر Repository بدون Submodule دانلود شده است:

```bash
git submodule update --init --recursive
```

---

## Configure

```bash
cmake -B build \
  -DCMAKE_TOOLCHAIN_FILE=cmake/ps4.cmake \
  -DCMAKE_BUILD_TYPE=Release
```

سپس:

```bash
cmake --build build
```

در هنگام Build، Web Client نیز داخل Plugin قرار می‌گیرد.

---

# ارسال مستقیم Plugin به PS4

در صورت فعال بودن FTP روی PS4 می‌توانید IP را هنگام Configure مشخص کنید:

```bash
cmake -B build \
  -DCMAKE_TOOLCHAIN_FILE=cmake/ps4.cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DDEVICE_IP=192.168.1.50
```

سیستم Build می‌تواند Plugin ساخته‌شده را از طریق FTP روی مسیر:

```text
/data/GoldHEN/plugins/
```

ارسال کند.

FTP از Port:

```text
2121
```

استفاده می‌کند.

---

# ساختار پروژه

```text
JeloPad/
├── .github/
│   └── workflows/
│
├── client/
│   └── index.html
│
├── cmake/
│   └── ps4.cmake
│
├── include/
│
├── lib/
│
├── src/
│   ├── *.c
│   └── pad/
│
├── CMakeLists.txt
├── Dockerfile
├── cli.py
├── requirements.txt
├── LICENSE
└── README.md
```

---

# توسعه

JeloPad از دو بخش اصلی تشکیل شده است:

## PS4 Plugin

مسئول:

* دریافت Controller Input
* WebSocket Server
* Virtual Controller
* Console Configuration
* Web Client
* Rumble Events
* GoldHEN Integration

## Desktop Client

مسئول:

* شناسایی کنترلرها
* دریافت Input
* Keyboard
* Mouse
* Controller Mapping
* Controller Assignment
* ارسال وضعیت
* دریافت Rumble
* Configuration Sync
* نمایش اطلاعات Debug

---

# Performance

JeloPad برای Input سریع و مصرف منطقی منابع طراحی شده است.

Plugin از یک Polling Interval حدود:

```text
10 ms
```

استفاده می‌کند.

کلاینت دسکتاپ به‌صورت پیش‌فرض با:

```text
120 Hz
```

کار می‌کند.

همچنین وضعیت‌های جدید Controller نسبت به وضعیت قبلی مدیریت می‌شوند تا Packetهای قدیمی در صف باقی نمانند.

---

# امنیت شبکه

JeloPad برای استفاده در شبکه محلی طراحی شده است.

Port اصلی:

```text
4263
```

است.

ارتباط WebSocket به‌صورت پیش‌فرض Authentication یا Encryption ندارد.

بنابراین:

> **Port JeloPad را مستقیماً روی اینترنت عمومی قرار ندهید.**

از JeloPad در یک شبکه محلی یا شبکه خصوصی امن استفاده کنید.

---

# سازگاری

هدف اصلی:

```text
PlayStation 4
GoldHEN
```

کلاینت دسکتاپ:

```text
Windows x64
Linux x64
```

سازگاری کنترلرها به موارد زیر بستگی دارد:

* پشتیبانی سیستم‌عامل
* SDL/Pygame
* Firmware کنترلر
* HID Report
* Rumble implementation

برخی کنترلرهای Generic ممکن است نیاز به Mapping دستی داشته باشند.

---

# فایل‌های Release

Releaseهای آماده معمولاً شامل:

| فایل                        | پلتفرم        | کاربرد         |
| --------------------------- | ------------- | -------------- |
| `JeloPad-Windows-x64.zip`   | Windows x64   | Desktop Client |
| `JeloPad-Linux-x64-bin.zip` | Linux x64     | Desktop Client |
| `jelopad.prx`               | PS4 / GoldHEN | PS4 Plugin     |

بهتر است همیشه Plugin و Client مربوط به یک Release یکسان را استفاده کنید.

---

# اعتبارات

JeloPad بر اساس پروژه اصلی:

```text
remote_gamepad
```

ساخته شده است.

نویسنده اصلی پروژه:

**xfangfang**

تشکر ویژه از:

**jocover**

برای کمک‌های فنی و راهنمایی در مراحل اولیه توسعه PS4 SDK.

توسعه و نگهداری فعلی JeloPad توسط:

**Jelofen1962**

انجام می‌شود.

---

# لایسنس

JeloPad تحت:

**MIT License**

منتشر شده است.

برای متن کامل لایسنس فایل زیر را ببینید:

```text
LICENSE
```

---

# Disclaimer

JeloPad یک پروژه مستقل و Open Source است.

نام‌های PlayStation، PlayStation 4، DualShock، GoldHEN و سایر علائم تجاری متعلق به صاحبان مربوطه هستند.

JeloPad وابسته به Sony Interactive Entertainment نیست و توسط این شرکت تأیید یا حمایت نمی‌شود.

این نرم‌افزار را فقط روی سیستم‌ها و شبکه‌هایی استفاده کنید که اجازه قانونی برای مدیریت و تغییر آن‌ها را دارید.

---

# مشارکت

گزارش Bug، گزارش سازگاری کنترلر، پیشنهاد و Pull Request پذیرفته می‌شود.

در هنگام گزارش مشکل، در صورت امکان موارد زیر را ارسال کنید:

* سیستم‌عامل
* نام کنترلر
* نوع اتصال کنترلر
* VID/PID در صورت اطلاع
* اینکه Input معمولی کار می‌کند یا خیر
* اینکه Rumble کار می‌کند یا خیر
* Log مربوط به JeloPad
* اطلاعات PS4 و GoldHEN در صورت مرتبط بودن

اطلاعات خصوصی، رمز عبور، IP عمومی یا اطلاعات حساس شبکه را ارسال نکنید.

---

# پشتیبانی

قبل از ایجاد Issue:

1. مراحل نصب را دوباره بررسی کنید.
2. مطمئن شوید Plugin اجرا شده است.
3. IP کنسول را بررسی کنید.
4. Port `4263` را بررسی کنید.
5. Web Client را تست کنید.
6. Logهای CLI را بررسی کنید.
7. Auto Mapper را امتحان کنید.

اگر مشکل باقی ماند، یک Issue با اطلاعات فنی مرتبط ایجاد کنید.

---

# JeloPad

**یک PS4.
چندین دستگاه ورودی.
یک پل ساده و قدرتمند.**

```

### چند نکته مهمی که در این نسخه اصلاح کردم

- `main.py` را به **`cli.py`** اصلاح کردم؛ فایل فعلی پروژه واقعاً `cli.py` است. :contentReference[oaicite:1]{index=1}
- Dependencyهای واقعی CLI یعنی **Textual و Rich** را هم مستند کردم؛ `requirements.txt` فعلی فقط `pygame` و `websockets` را اعلام می‌کند، بنابراین README جدید این تفاوت را شفاف می‌کند. :contentReference[oaicite:2]{index=2}
- `OO_PS4_TOOLCHAIN` را به‌عنوان پیش‌نیاز Build آوردم؛ CMake فعلی اگر این متغیر وجود نداشته باشد Build را متوقف می‌کند. :contentReference[oaicite:3]{index=3}
- قابلیت‌های واقعی `F2/F3/F4/F5/F7/F8/F10` را مستند کردم. :contentReference[oaicite:4]{index=4}
- Auto Mapping، Keyboard، Mouse، چهار Pad، Live Monitor و Configuration Sync را مطابق پیاده‌سازی فعلی توضیح دادم. :contentReference[oaicite:5]{index=5}
- Rumble را دقیق‌تر نوشتم؛ کد فعلی هم HID profileهای مشخص دارد و هم در صورت امکان به SDL/Pygame fallback می‌کند. :contentReference[oaicite:6]{index=6}
- بخش Security را اضافه کردم چون سرویس WebSocket روی شبکه محلی بدون authentication/encryption مستند شده و بهتر است کاربر بداند نباید Port `4263` را عمومی کند.
- مهم‌تر از همه، تناقض `jelopad.prx` / `remote_pad.prx` را در مستندات برطرف کردم. خود repository فعلی فایل release را `jelopad.prx` معرفی می‌کند، در حالی که README فعلی در مثال `plugins.ini` نام قدیمی `remote_pad.prx` را دارد. :contentReference[oaicite:7]{index=7}

این نسخه برای قرار گرفتن مستقیم به‌عنوان **`README.md` اصلی GitHub** آماده است و عمداً بخش English را اول گذاشته‌ام تا صفحه پروژه برای کاربران بین‌المللی خواناتر باشد.
```

[1]: https://github.com/Jelofen1962/JeloPad "GitHub - Jelofen1962/JeloPad · GitHub"
