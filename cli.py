"""
JeloPad CLI
An updated production-quality terminal client with active console sync
and direct raw HID mapping interfaces for PS4 controller emulation.
"""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

import pygame
import websockets
from websockets.exceptions import ConnectionClosed

try:
    import hid
    HID_AVAILABLE = True
except ImportError:
    HID_AVAILABLE = False

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Grid
from textual.screen import ModalScreen
from textual import events
from textual.widgets import Header, Footer, DataTable, RichLog, Static, Select, Label, Button, Input, Checkbox
from textual.reactive import reactive
from rich.text import Text
from rich.console import RenderableType

# --- Protocol Constants ---
ORBIS_PAD_BUTTON_L3        = 0x0002
ORBIS_PAD_BUTTON_R3        = 0x0004
ORBIS_PAD_BUTTON_OPTIONS   = 0x0008
ORBIS_PAD_BUTTON_UP        = 0x0010
ORBIS_PAD_BUTTON_RIGHT     = 0x0020
ORBIS_PAD_BUTTON_DOWN      = 0x0040
ORBIS_PAD_BUTTON_LEFT      = 0x0080
ORBIS_PAD_BUTTON_L2        = 0x0100
ORBIS_PAD_BUTTON_R2        = 0x0200
ORBIS_PAD_BUTTON_L1        = 0x0400
ORBIS_PAD_BUTTON_R1        = 0x0800
ORBIS_PAD_BUTTON_TRIANGLE  = 0x1000
ORBIS_PAD_BUTTON_CIRCLE    = 0x2000
ORBIS_PAD_BUTTON_CROSS     = 0x4000
ORBIS_PAD_BUTTON_SQUARE    = 0x8000
ORBIS_PAD_BUTTON_TOUCH_PAD = 0x100000

PS_BUTTON_NAMES: Dict[int, str] = {
    ORBIS_PAD_BUTTON_CROSS:     "✕ Cross",
    ORBIS_PAD_BUTTON_CIRCLE:    "○ Circle",
    ORBIS_PAD_BUTTON_TRIANGLE:  "△ Triangle",
    ORBIS_PAD_BUTTON_SQUARE:    "□ Square",
    ORBIS_PAD_BUTTON_L1:        "L1",
    ORBIS_PAD_BUTTON_R1:        "R1",
    ORBIS_PAD_BUTTON_L2:        "L2",
    ORBIS_PAD_BUTTON_R2:        "R2",
    ORBIS_PAD_BUTTON_L3:        "L3 Click",
    ORBIS_PAD_BUTTON_R3:        "R3 Click",
    ORBIS_PAD_BUTTON_OPTIONS:   "Options",
    ORBIS_PAD_BUTTON_TOUCH_PAD: "Touchpad",
    ORBIS_PAD_BUTTON_UP:        "D-Pad Up",
    ORBIS_PAD_BUTTON_DOWN:      "D-Pad Down",
    ORBIS_PAD_BUTTON_LEFT:      "D-Pad Left",
    ORBIS_PAD_BUTTON_RIGHT:     "D-Pad Right",
}

DEFAULT_JOY_MAPPING: Dict[str, str] = {
    str(ORBIS_PAD_BUTTON_CROSS): "BTN:0",
    str(ORBIS_PAD_BUTTON_CIRCLE): "BTN:1",
    str(ORBIS_PAD_BUTTON_SQUARE): "BTN:2",
    str(ORBIS_PAD_BUTTON_TRIANGLE): "BTN:3",
    str(ORBIS_PAD_BUTTON_L1): "BTN:4",
    str(ORBIS_PAD_BUTTON_R1): "BTN:5",
    str(ORBIS_PAD_BUTTON_TOUCH_PAD): "BTN:6",
    str(ORBIS_PAD_BUTTON_OPTIONS): "BTN:7",
    str(ORBIS_PAD_BUTTON_L3): "BTN:8",
    str(ORBIS_PAD_BUTTON_R3): "BTN:9",
    "LX": "AXIS:0:+",
    "LY": "AXIS:1:+",
    "RX": "AXIS:2:+",
    "RY": "AXIS:3:+",
    str(ORBIS_PAD_BUTTON_L2): "AXIS:4:+",
    str(ORBIS_PAD_BUTTON_R2): "AXIS:5:+",
    str(ORBIS_PAD_BUTTON_UP): "HAT:0:0:1",
    str(ORBIS_PAD_BUTTON_DOWN): "HAT:0:0:-1",
    str(ORBIS_PAD_BUTTON_LEFT): "HAT:0:-1:0",
    str(ORBIS_PAD_BUTTON_RIGHT): "HAT:0:1:0",
}

KB1_BUTTON_MAP: Dict[str, int] = {
    "space": ORBIS_PAD_BUTTON_CROSS, "escape": ORBIS_PAD_BUTTON_CIRCLE,
    "enter": ORBIS_PAD_BUTTON_TRIANGLE, "backspace": ORBIS_PAD_BUTTON_SQUARE,
    "q": ORBIS_PAD_BUTTON_L1, "e": ORBIS_PAD_BUTTON_R1, "1": ORBIS_PAD_BUTTON_L2, "3": ORBIS_PAD_BUTTON_R2,
    "o": ORBIS_PAD_BUTTON_OPTIONS, "u": ORBIS_PAD_BUTTON_TOUCH_PAD,
    "i": ORBIS_PAD_BUTTON_UP, "k": ORBIS_PAD_BUTTON_DOWN, "j": ORBIS_PAD_BUTTON_LEFT, "l": ORBIS_PAD_BUTTON_RIGHT,
}
KB1_AXIS_MAP: Dict[str, Tuple[int, float]] = {
    "a": (0, 0.0), "d": (0, 255.0), "w": (1, 0.0), "s": (1, 255.0),
    "left": (2, 0.0), "right": (2, 255.0), "up": (3, 0.0), "down": (3, 255.0),
}
HOLD_TIMEOUT = 0.20

@dataclass
class PadState:
    pad_index: int
    buttons: int = 0
    lx: int = 128
    ly: int = 128
    rx: int = 128
    ry: int = 128
    lt: int = 0
    rt: int = 0
    active_map: List[str] = None

    def __post_init__(self):
        if self.active_map is None:
            self.active_map = []

    def to_packet(self) -> str:
        return json.dumps({"method": "u", "params": [self.pad_index, self.buttons, self.lx, self.ly, self.rx, self.ry, self.lt, self.rt]})

    def copy_from(self, other: 'PadState') -> None:
        self.buttons = other.buttons
        self.lx, self.ly, self.rx, self.ry = other.lx, other.ly, other.rx, other.ry
        self.lt, self.rt = other.lt, other.rt

    def is_different(self, other: 'PadState') -> bool:
        return (self.buttons != other.buttons or self.lx != other.lx or self.ly != other.ly or
                self.rx != other.rx or self.ry != other.ry or self.lt != other.lt or self.rt != other.rt)

    def describe(self) -> str:
        names = [name for bit, name in PS_BUTTON_NAMES.items() if self.buttons & bit]
        return ", ".join(names) if names else "-"


class ConfigManager:
    CONFIG_FILE = "config.toml"

    def __init__(self):
        self.server_url = "ws://127.0.0.1:4263"
        self.tick_rate = 60
        self.smoothing = 0.35
        self.assignments: Dict[int, str] = {0: "Keyboard 1", 1: "None", 2: "None", 3: "None"}
        self.joy_mapping: Dict[str, str] = DEFAULT_JOY_MAPPING.copy()
        self.load()

    def load(self) -> None:
        if not os.path.exists(self.CONFIG_FILE):
            self.save()
            return
        if tomllib is None:
            logging.error("Failed to load config: no TOML library available (install 'tomli' on Python < 3.11)")
            return
        try:
            with open(self.CONFIG_FILE, "rb") as f:
                data = tomllib.load(f)
                self.server_url = data.get("network", {}).get("server_url", self.server_url)
                self.tick_rate = data.get("network", {}).get("tick_rate", self.tick_rate)
                self.smoothing = data.get("input", {}).get("smoothing", self.smoothing)
                assignments = data.get("assignments", {})
                for i in range(4):
                    self.assignments[i] = assignments.get(f"pad{i}", self.assignments[i])
                jm = data.get("joy_mapping", {})
                if jm:
                    self.joy_mapping = {str(k): str(v) for k, v in jm.items()}
        except Exception as e:
            logging.error(f"Failed to load config: {e}")

    def save(self) -> None:
        toml_content = f"""[network]
server_url = "{self.server_url}"
tick_rate = {self.tick_rate}

[input]
smoothing = {self.smoothing}

[assignments]
pad0 = "{self.assignments[0]}"
pad1 = "{self.assignments[1]}"
pad2 = "{self.assignments[2]}"
pad3 = "{self.assignments[3]}"

[joy_mapping]
"""
        for k, v in self.joy_mapping.items():
            toml_content += f'"{k}" = "{v}"\n'
        try:
            tmp_file = f"{self.CONFIG_FILE}.tmp"
            with open(tmp_file, "w") as f:
                f.write(toml_content)
            os.replace(tmp_file, self.CONFIG_FILE)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")


class InputManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        pygame.init()
        pygame.joystick.init()

        self.joysticks: Dict[int, pygame.joystick.Joystick] = {}
        self.device_names: Dict[str, str] = {"Keyboard 1": "Keyboard Profile 1", "None": "Disabled"}

        # Store custom physical HID connection descriptors
        self.hid_devices: Dict[int, Any] = {}
        self.hid_paths: Dict[int, Any] = {}
        self.target_vids = [0x0810, 0x0e8f, 0x120a, 0x1a2c]

        self.kb1_axes = [128.0, 128.0, 128.0, 128.0]
        self.kb_pressed: Dict[str, float] = {}
        self.axis_bounds = defaultdict(lambda: defaultdict(lambda: [-1.0, 1.0]))

    def note_key_event(self, key: str) -> None:
        self.kb_pressed[key] = time.perf_counter()

    def _key_is_held(self, key: str) -> bool:
        ts = self.kb_pressed.get(key)
        return ts is not None and (time.perf_counter() - ts) < HOLD_TIMEOUT

    def close_all_hid_devices(self):
        for dev in list(self.hid_devices.values()):
            try:
                dev.write(bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
                dev.write(bytes([0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
                dev.close()
            except Exception:
                pass
        self.hid_devices.clear()
        self.hid_paths.clear()

    def update_hid_connections(self):
        if not HID_AVAILABLE:
            self.close_all_hid_devices()
            return

        try:
            raw_hid_list = hid.enumerate()
        except Exception:
            return

        # Figure out which raw HID path (if any) each pad should be connected to.
        desired_paths: Dict[int, Any] = {}
        for pad_idx, dev_id in self.config.assignments.items():
            if dev_id.startswith("Joy "):
                try:
                    jid = int(dev_id.split(" ")[1])
                    if jid in self.joysticks:
                        joy = self.joysticks[jid]
                        vid = joy.get_vendor_id()
                        pid = joy.get_product_id()

                        # Capture the specific hardware handles if mapped to target VIDs
                        if vid in self.target_vids or "Gamepad" in joy.get_name():
                            for d in raw_hid_list:
                                if d['vendor_id'] == vid and d['product_id'] == pid:
                                    desired_paths[pad_idx] = d['path']
                                    break
                except (ValueError, AttributeError):
                    pass

        # Only close handles that are no longer needed, or now point at a
        # different physical device - leave already-correct connections alone
        # so we don't needlessly kick rumble motors or churn raw HID handles.
        for pad_idx in list(self.hid_devices.keys()):
            if self.hid_paths.get(pad_idx) != desired_paths.get(pad_idx):
                dev = self.hid_devices.pop(pad_idx)
                self.hid_paths.pop(pad_idx, None)
                try:
                    dev.write(bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
                    dev.write(bytes([0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
                    dev.close()
                except Exception:
                    pass

        # Open any newly-needed connections.
        for pad_idx, path in desired_paths.items():
            if pad_idx not in self.hid_devices:
                try:
                    dev = hid.device()
                    dev.open_path(path)
                    dev.set_nonblocking(True)
                    self.hid_devices[pad_idx] = dev
                    self.hid_paths[pad_idx] = path
                except Exception:
                    pass

    def detect_devices(self) -> List[str]:
        current_jids = set()
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            jid = joy.get_instance_id()
            current_jids.add(jid)
            if jid not in self.joysticks:
                self.joysticks[jid] = joy
                self.device_names[f"Joy {jid}"] = joy.get_name()

        for jid in list(self.joysticks.keys()):
            if jid not in current_jids:
                del self.joysticks[jid]
                del self.device_names[f"Joy {jid}"]
                if jid in self.axis_bounds:
                    del self.axis_bounds[jid]
                for pad, dev in self.config.assignments.items():
                    if dev == f"Joy {jid}":
                        self.config.assignments[pad] = "None"

        # Guard against stale assignments (e.g. loaded from a previous session,
        # or referencing a device id that no longer/never existed this run)
        # so downstream UI never receives a value it doesn't recognize.
        for pad, dev in list(self.config.assignments.items()):
            if dev not in self.device_names:
                self.config.assignments[pad] = "None"

        self.update_hid_connections()
        return list(self.device_names.keys())

    def process_pygame_events(self) -> List[str]:
        logs = []
        for event in pygame.event.get():
            if event.type == pygame.JOYDEVICEADDED:
                self.detect_devices()
                try:
                    name = pygame.joystick.Joystick(event.device_index).get_name()
                    logs.append(f"Controller connected: {name}")
                except Exception:
                    logs.append("Controller connected")
            elif event.type == pygame.JOYDEVICEREMOVED:
                logs.append(f"Controller disconnected (ID: {event.instance_id})")
                self.detect_devices()
        return logs

    def get_pad_state(self, pad_index: int) -> PadState:
        device_id = self.config.assignments.get(pad_index, "None")
        state = PadState(pad_index)

        if device_id.startswith("Keyboard"):
            return self._poll_keyboard(state)

        if device_id.startswith("Joy"):
            jid = int(device_id.split(" ")[1])
            if jid in self.joysticks:
                return self._poll_gamepad(state, self.joysticks[jid], jid)

        return state

    def _poll_keyboard(self, state: PadState) -> PadState:
        btn = 0
        active_map: List[str] = []
        axes = self.kb1_axes

        for key, bit in KB1_BUTTON_MAP.items():
            if self._key_is_held(key):
                btn |= bit
                active_map.append(f"KEY {key.upper()} : {PS_BUTTON_NAMES[bit]}")

        tx = ty = rx = ry = 128.0
        for key, (axis_idx, target) in KB1_AXIS_MAP.items():
            if self._key_is_held(key):
                if axis_idx == 0: tx = target
                elif axis_idx == 1: ty = target
                elif axis_idx == 2: rx = target
                elif axis_idx == 3: ry = target
                active_map.append(f"KEY {key.upper()} : Stick")

        s = self.config.smoothing
        axes[0] += (tx - axes[0]) * s
        axes[1] += (ty - axes[1]) * s
        axes[2] += (rx - axes[2]) * s
        axes[3] += (ry - axes[3]) * s

        state.buttons = btn
        state.lx, state.ly = int(axes[0]), int(axes[1])
        state.rx, state.ry = int(axes[2]), int(axes[3])
        state.lt = 255 if (btn & ORBIS_PAD_BUTTON_L2) else 0
        state.rt = 255 if (btn & ORBIS_PAD_BUTTON_R2) else 0
        state.active_map = active_map
        return state

    def _poll_gamepad(self, state: PadState, joy: pygame.joystick.Joystick, jid: int) -> PadState:
        btn = 0
        active_map: List[str] = []

        for target, src in self.config.joy_mapping.items():
            is_active = False
            analog_val = 0

            if src.startswith("BTN:"):
                idx = int(src.split(":")[1])
                if idx < joy.get_numbuttons() and joy.get_button(idx):
                    is_active = True
                    analog_val = 255

            elif src.startswith("HAT:"):
                parts = src.split(":")
                idx, hx, hy = int(parts[1]), int(parts[2]), int(parts[3])
                if idx < joy.get_numhats() and joy.get_hat(idx) == (hx, hy):
                    is_active = True
                    analog_val = 255

            elif src.startswith("AXIS:"):
                parts = src.split(":")
                idx, dir_sign = int(parts[1]), parts[2]
                if idx < joy.get_numaxes():
                    val = joy.get_axis(idx)
                    bounds = self.axis_bounds[jid][idx]
                    bounds[0] = min(bounds[0], val)
                    bounds[1] = max(bounds[1], val)

                    range_v = bounds[1] - bounds[0]
                    norm_val = ((val - bounds[0]) / range_v) * 2.0 - 1.0 if range_v > 0.01 else val

                    if target in [str(ORBIS_PAD_BUTTON_L2), str(ORBIS_PAD_BUTTON_R2)]:
                        if dir_sign == "+":
                            analog_val = int((norm_val + 1.0) / 2.0 * 255)
                        else:
                            analog_val = int((1.0 - norm_val) / 2.0 * 255)
                        analog_val = max(0, min(255, analog_val))
                        if analog_val > 50: is_active = True
                    elif target in ["LX", "LY", "RX", "RY"]:
                        if dir_sign == "-": norm_val = -norm_val
                        analog_val = max(0, min(255, int((norm_val + 1.0) / 2.0 * 255)))
                        is_active = True
                    else:
                        if dir_sign == "+" and norm_val > 0.5: is_active = True
                        elif dir_sign == "-" and norm_val < -0.5: is_active = True
                        analog_val = 255 if is_active else 0

            if target in ["LX", "LY", "RX", "RY"]:
                if src.startswith("AXIS:"):
                    setattr(state, target.lower(), analog_val)
                    if abs(analog_val - 128) > 30:
                        active_map.append(f"{src} : {target}")
            else:
                try:
                    mask = int(target)
                    if is_active:
                        btn |= mask
                        active_map.append(f"{src} : {PS_BUTTON_NAMES.get(mask, str(mask))}")
                    if mask == ORBIS_PAD_BUTTON_L2: state.lt = analog_val
                    elif mask == ORBIS_PAD_BUTTON_R2: state.rt = analog_val
                except ValueError:
                    pass

        state.buttons = btn
        state.active_map = active_map
        return state

    def handle_rumble(self, pad_index: int, low_freq: float, high_freq: float):
        """
        Dual vibration dispatcher. Maps standard DirectInput, XInput, and custom
        Macher raw output report packets.
        """
        # 1. Custom hardcoded raw USB HID driver for Twin/Macher controllers
        if pad_index in self.hid_devices:
            dev = self.hid_devices[pad_index]
            heavy_byte = int(low_freq * 255)
            light_byte = int(high_freq * 255)
            packet_1 = [0x01, 0x00, 0x00, heavy_byte, light_byte, 0x00, 0x00, 0x00]
            packet_2 = [0x02, 0x00, 0x00, heavy_byte, light_byte, 0x00, 0x00, 0x00]
            try:
                dev.write(bytes(packet_1))
                dev.write(bytes(packet_2))
                return
            except IOError:
                try:
                    dev.close()
                except Exception:
                    pass
                del self.hid_devices[pad_index]

        # 2. Native Haptic fallback for XInput/XOutput and generic OS-level API pads
        device_id = self.config.assignments.get(pad_index, "None")
        if device_id.startswith("Joy"):
            jid = int(device_id.split(" ")[1])
            if jid in self.joysticks:
                try:
                    self.joysticks[jid].rumble(low_freq, high_freq, 400)
                except Exception:
                    pass


class SetupMenuModal(ModalScreen):
    """
    JeloPad configuration menu.
    Synchronizes local user preferences and pushes console edits directly to PS4 system memory.
    """
    def __init__(self, config: ConfigManager, ps4_users: List[Dict[str, Any]], ws_conn: Optional[Any] = None):
        super().__init__()
        self.config = config
        self.ps4_users = ps4_users
        self.ws_conn = ws_conn

    def compose(self) -> ComposeResult:
        # Guard against the console returning fewer than 4 user profiles
        # (or none at all) — always pad up to 4 so indexed access below is safe.
        while len(self.ps4_users) < 4:
            i = len(self.ps4_users)
            self.ps4_users.append({"index": i, "enabled": True, "userId": 0x20000000 + i, "userName": f"Remote{i}"})

        yield Grid(
            Label("⚙️ JeloPad System Preferences", id="setup-title"),
            Label("Console WS Server:"),
            Input(value=self.config.server_url, id="input-url", placeholder="ws://ip:port"),

            # Interactive Console User Management
            Label("Configure Console Profiles:", id="users-header"),

            Label("Pad 0 Config:"),
            Horizontal(
                Checkbox(value=self.ps4_users[0]["enabled"], id="chk-u0"),
                Input(value=self.ps4_users[0]["userName"], id="name-u0", placeholder="Name"),
            ),
            Label("Pad 1 Config:"),
            Horizontal(
                Checkbox(value=self.ps4_users[1]["enabled"], id="chk-u1"),
                Input(value=self.ps4_users[1]["userName"], id="name-u1", placeholder="Name"),
            ),
            Label("Pad 2 Config:"),
            Horizontal(
                Checkbox(value=self.ps4_users[2]["enabled"], id="chk-u2"),
                Input(value=self.ps4_users[2]["userName"], id="name-u2", placeholder="Name"),
            ),
            Label("Pad 3 Config:"),
            Horizontal(
                Checkbox(value=self.ps4_users[3]["enabled"], id="chk-u3"),
                Input(value=self.ps4_users[3]["userName"], id="name-u3", placeholder="Name"),
            ),

            Horizontal(
                Button("Apply & Upload Config", variant="success", id="btn-apply"),
                Button("Discard", variant="error", id="btn-discard"),
                classes="modal-buttons"
            ),
            id="setup-dialog"
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-apply":
            self.config.server_url = self.query_one("#input-url", Input).value
            self.config.save()

            if self.ws_conn:
                for i in range(4):
                    enabled_val = self.query_one(f"#chk-u0" if i==0 else f"#chk-u1" if i==1 else f"#chk-u2" if i==2 else f"#chk-u3", Checkbox).value
                    name_val = self.query_one(f"#name-u0" if i==0 else f"#name-u1" if i==1 else f"#name-u2" if i==2 else f"#name-u3", Input).value

                    self.ps4_users[i]["enabled"] = enabled_val
                    self.ps4_users[i]["userName"] = name_val

                    payload = {
                        "id": 999 + i,
                        "method": "config.set",
                        "params": [i, enabled_val, self.ps4_users[i]["userId"], name_val]
                    }
                    try:
                        await self.ws_conn.send(json.dumps(payload))
                    except Exception:
                        pass

            self.dismiss(self.ps4_users)
        else:
            self.dismiss(None)


class AssignmentModal(ModalScreen):
    def __init__(self, config: ConfigManager, devices: Dict[str, str]):
        super().__init__()
        self.config = config
        self.devices = devices

    def compose(self) -> ComposeResult:
        options = [(v, k) for k, v in self.devices.items()]
        yield Grid(
            Label("Assign Controllers", id="modal-title"),
            Label("Pad 0:"), Select(options, value=self.config.assignments[0], id="sel0"),
            Label("Pad 1:"), Select(options, value=self.config.assignments[1], id="sel1"),
            Label("Pad 2:"), Select(options, value=self.config.assignments[2], id="sel2"),
            Label("Pad 3:"), Select(options, value=self.config.assignments[3], id="sel3"),
            Horizontal(
                Button("Save", variant="success", id="btn-save"),
                Button("Cancel", variant="error", id="btn-cancel"),
                classes="modal-buttons"
            ),
            id="assignment-dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.config.assignments[0] = self.query_one("#sel0", Select).value
            self.config.assignments[1] = self.query_one("#sel1", Select).value
            self.config.assignments[2] = self.query_one("#sel2", Select).value
            self.config.assignments[3] = self.query_one("#sel3", Select).value
            self.config.save()
            self.dismiss(True)
        else:
            self.dismiss(False)


class ButtonMapperModal(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel Mapping")]

    def __init__(self, config: ConfigManager, input_mgr: InputManager):
        super().__init__()
        self.config = config
        self.input_mgr = input_mgr

        self.buttons_to_map = [
            (str(ORBIS_PAD_BUTTON_CROSS), "Cross (✕)"),
            (str(ORBIS_PAD_BUTTON_CIRCLE), "Circle (○)"),
            (str(ORBIS_PAD_BUTTON_SQUARE), "Square (□)"),
            (str(ORBIS_PAD_BUTTON_TRIANGLE), "Triangle (△)"),
            (str(ORBIS_PAD_BUTTON_L1), "L1 Bumper"),
            (str(ORBIS_PAD_BUTTON_R1), "R1 Bumper"),
            (str(ORBIS_PAD_BUTTON_L2), "L2 Trigger"),
            (str(ORBIS_PAD_BUTTON_R2), "R2 Trigger"),
            (str(ORBIS_PAD_BUTTON_L3), "L3 Click"),
            (str(ORBIS_PAD_BUTTON_R3), "R3 Click"),
            (str(ORBIS_PAD_BUTTON_UP), "D-Pad Up"),
            (str(ORBIS_PAD_BUTTON_DOWN), "D-Pad Down"),
            (str(ORBIS_PAD_BUTTON_LEFT), "D-Pad Left"),
            (str(ORBIS_PAD_BUTTON_RIGHT), "D-Pad Right"),
            (str(ORBIS_PAD_BUTTON_OPTIONS), "Options / Start"),
            (str(ORBIS_PAD_BUTTON_TOUCH_PAD), "Touchpad / Select"),
            ("LX", "Move Left Stick RIGHT"),
            ("LY", "Move Left Stick DOWN"),
            ("RX", "Move Right Stick RIGHT"),
            ("RY", "Move Right Stick DOWN"),
        ]
        self.current_target_idx = 0
        self.new_mapping = self.config.joy_mapping.copy()
        self.joy = list(self.input_mgr.joysticks.values())[0] if self.input_mgr.joysticks else None
        self.initial_axes = []
        self.waiting_for_neutral = False
        self.start_time = time.perf_counter()

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("🎮 Auto Map Controller Layout", id="mapper-title"),
            Label("No physical controller found!" if not self.joy else "Initializing...", id="mapper-prompt"),
            Label("", id="mapper-timer"),
            Label("(Press Escape to cancel)", id="mapper-help"),
            id="mapper-dialog"
        )

    def on_mount(self) -> None:
        if not self.joy:
            self.set_timer(2.0, self._dismiss_no_controller)
            return

        self.initial_axes = [self.joy.get_axis(i) for i in range(self.joy.get_numaxes())]
        self.update_prompt()
        self.tick_timer = self.set_interval(0.05, self.check_input)

    def update_prompt(self):
        if self.current_target_idx >= len(self.buttons_to_map):
            self.finish_mapping()
            return
        _, name = self.buttons_to_map[self.current_target_idx]
        self.query_one("#mapper-prompt", Label).update(f"Action: [bold green]{name}[/bold green]")
        self.start_time = time.perf_counter()

    def _dismiss_no_controller(self) -> None:
        """Timer callback for the 'no controller found' auto-close.
        Must not return dismiss()'s awaitable (see finish_mapping note)."""
        self.dismiss()

    def get_active_input(self) -> Optional[str]:
        for i in range(self.joy.get_numbuttons()):
            if self.joy.get_button(i): return f"BTN:{i}"
        for i in range(self.joy.get_numhats()):
            hx, hy = self.joy.get_hat(i)
            if hx != 0 or hy != 0: return f"HAT:{i}:{hx}:{hy}"
        for i in range(self.joy.get_numaxes()):
            diff = self.joy.get_axis(i) - self.initial_axes[i]
            if abs(diff) > 0.5:
                direction = "+" if diff > 0 else "-"
                return f"AXIS:{i}:{direction}"
        return None

    def check_input(self):
        if not self.joy: return
        elapsed = time.perf_counter() - self.start_time
        time_left = 5.0 - elapsed
        if time_left <= 0:
            self.current_target_idx += 1
            self.waiting_for_neutral = True
            self.update_prompt()
            return

        self.query_one("#mapper-timer", Label).update(f"Hold button/axis: [yellow]{time_left:.1f}s[/yellow] (Wait to skip)")
        active = self.get_active_input()

        if self.waiting_for_neutral:
            if not active: self.waiting_for_neutral = False
            return

        if active:
            target_key, _ = self.buttons_to_map[self.current_target_idx]
            keys_to_remove = [k for k, v in self.new_mapping.items() if v == active]
            for k in keys_to_remove: del self.new_mapping[k]
            self.new_mapping[target_key] = active
            self.current_target_idx += 1
            self.waiting_for_neutral = True
            self.update_prompt()

    def finish_mapping(self):
        self.tick_timer.stop()
        self.query_one("#mapper-prompt", Label).update("[bold cyan]Mapping Complete![/bold cyan]")
        self.query_one("#mapper-timer", Label).update("Saving Configuration...")
        self.config.joy_mapping = self.new_mapping
        self.config.save()
        # NOTE: the timer callback must not return dismiss()'s awaitable object.
        # Textual's timer machinery auto-awaits whatever the callback returns,
        # and awaiting dismiss() from within this screen's own context raises
        # ScreenError ("Can't await screen.dismiss() from the screen's message
        # handler"). Using a plain helper method with no return value avoids this.
        self.set_timer(1.0, self._finish_dismiss)

    def _finish_dismiss(self) -> None:
        self.dismiss(True)

    def action_cancel(self):
        if hasattr(self, "tick_timer"): self.tick_timer.stop()
        self.dismiss(False)


class InputBarWidget(Static):
    value = reactive(128)
    def __init__(self, label: str, **kwargs):
        super().__init__(**kwargs)
        self.label = label
    def render(self) -> RenderableType:
        pct = self.value / 255.0
        bar_len = 18
        filled = int(pct * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        return Text(f"{self.label:3} | {bar} | {self.value:3}", style="cyan")


class JeloPadApp(App):
    CSS = """
    Screen { layout: vertical; background: $surface; }
    #main-content { height: 1fr; layout: horizontal; }
    #left-pane, #right-pane { width: 1fr; height: 1fr; border: solid $accent; padding: 1; }
    #bottom-pane { height: 14; layout: horizontal; border-top: heavy $accent; }
    #log-panel { width: 2fr; height: 1fr; border-right: solid $accent; }
    #stats-panel { width: 1fr; height: 1fr; padding: 1; }
    .stat-label { color: $text-muted; }
    .stat-value { color: $success; text-style: bold; }
    #monitor-mapping { height: auto; color: $warning; }

    #assignment-dialog { grid-size: 2 5; grid-gutter: 1 2; padding: 2; width: 60; height: 25; border: thick $background 80%; background: $surface; }
    #setup-dialog { grid-size: 2 7; grid-gutter: 1 2; padding: 2; width: 65; height: 36; border: thick $accent 80%; background: $surface; }
    #modal-title, #setup-title { column-span: 2; content-align: center middle; text-style: bold; }
    #users-header { column-span: 2; text-style: bold; color: $accent; margin-top: 1; }
    .modal-buttons { column-span: 2; align: center middle; }

    #mapper-dialog { padding: 2 4; width: 60; height: 15; border: thick $accent 80%; background: $surface; align: center middle; }
    #mapper-title { text-style: bold; color: $success; width: 100%; content-align: center middle; margin-bottom: 1; }
    #mapper-prompt, #mapper-timer, #mapper-help { width: 100%; content-align: center middle; margin-bottom: 1; }
    #mapper-timer { color: $warning; }
    #mapper-help { color: $text-muted; }
    """

    BINDINGS = [
        Binding("f2", "connect", "Connect"),
        Binding("f3", "disconnect", "Disconnect"),
        Binding("f4", "assignments", "Assignments"),
        Binding("f5", "setup_menu", "Console Sync Config"),
        Binding("f7", "map_buttons", "Map Gamepad"),
        Binding("f8", "cycle_monitor", "Cycle Live Pad"),
        Binding("f10", "quit", "Exit CLI"),
    ]

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.input_mgr = InputManager(self.config)
        self.ws: Optional[Any] = None
        self.connected = False
        self.monitored_pad = 0
        self.packets_sent = self.packets_dropped = 0
        self.start_time = time.time()
        self.pad_states: List[PadState] = [PadState(i) for i in range(4)]
        self.prev_states: List[PadState] = [PadState(i) for i in range(4)]
        self.loop_task: Optional[asyncio.Task] = None
        self.recv_task: Optional[asyncio.Task] = None

        # Synchronized console configuration properties
        self.ps4_users: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-content"):
            with Vertical(id="left-pane"):
                yield Label("👥 Virtual Pad Port Assignments", classes="section-title")
                yield DataTable(id="dt-players", cursor_type="row")
                yield Label(" ")
                yield Label("🔌 System Input Controllers", classes="section-title")
                yield DataTable(id="dt-controllers", cursor_type="none")
            with Vertical(id="right-pane"):
                yield Label("🎮 Live Monitor Panel (Pad 0)", id="monitor-title", classes="section-title")
                yield Label(id="monitor-btns", classes="stat-value")
                yield Static(id="monitor-mapping")
                yield InputBarWidget("LX", id="bar-lx")
                yield InputBarWidget("LY", id="bar-ly")
                yield InputBarWidget("RX", id="bar-rx")
                yield InputBarWidget("RY", id="bar-ry")
                yield InputBarWidget("LT", id="bar-lt")
                yield InputBarWidget("RT", id="bar-rt")
        with Horizontal(id="bottom-pane"):
            with Vertical(id="log-panel"):
                yield RichLog(id="rlog", highlight=True, markup=True)
            with Vertical(id="stats-panel"):
                yield Label("📊 Active Network Logs", classes="section-title")
                yield Static(id="stats-text")
        yield Footer()

    async def on_mount(self) -> None:
        self.title = "JeloPad Terminal Controller"
        self.sub_title = f"Disconnected | {self.config.server_url}"
        dt_p = self.query_one("#dt-players", DataTable)
        dt_p.add_columns("Pad Port", "Assigned Physical Input Device")
        dt_c = self.query_one("#dt-controllers", DataTable)
        dt_c.add_columns("Internal ID", "Hardware Description")

        self.log_msg("[green]Ready to connect to remote target console.[/green]")
        if not HID_AVAILABLE:
            self.log_msg("[yellow]Notice: 'hid' package not installed. Custom twin-motor rumble disabled.[/yellow]")
        self.update_tables()
        self.loop_task = asyncio.create_task(self.core_tick_loop())
        self.set_interval(0.1, self.update_stats_ui)

    def on_key(self, event: events.Key) -> None:
        self.input_mgr.note_key_event(event.key)

    def log_msg(self, msg: str) -> None:
        log = self.query_one("#rlog", RichLog)
        ts = time.strftime("%H:%M:%S")
        log.write(f"[[blue]{ts}[/blue]] {msg}")

    def update_tables(self) -> None:
        dt_p = self.query_one("#dt-players", DataTable)
        dt_p.clear()
        for i in range(4):
            dev = self.config.assignments.get(i, "None")
            name = self.input_mgr.device_names.get(dev, "Disabled")
            dt_p.add_row(f"Port {i}", name)

        if dt_p.row_count > 0:
            try:
                dt_p.move_cursor(row=self.monitored_pad)
            except Exception:
                pass

        dt_c = self.query_one("#dt-controllers", DataTable)
        dt_c.clear()
        self.input_mgr.detect_devices()
        for dev_id, name in self.input_mgr.device_names.items():
            dt_c.add_row(dev_id, name)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id == "dt-players" and event.cursor_row is not None:
            if 0 <= event.cursor_row < 4:
                self.monitored_pad = event.cursor_row
                self.query_one("#monitor-title", Label).update(f"🎮 Live Monitor Panel (Pad {self.monitored_pad})")
                self.update_stats_ui()

    def update_stats_ui(self) -> None:
        uptime = int(time.time() - self.start_time)
        stats = f"""
[dim]Connection:[/dim] {"[green]Online[/green]" if self.connected else "[red]Offline[/red]"}
[dim]Tx Packets:[/dim] {self.packets_sent}
[dim]Err/Dropped:[/dim] {self.packets_dropped}
[dim]Output Rate:[/dim] {self.config.tick_rate} Hz
[dim]Uptime:[/dim] {uptime}s
"""
        self.query_one("#stats-text", Static).update(stats)
        p_mon = self.pad_states[self.monitored_pad]
        self.query_one("#monitor-btns", Label).update(f"Mask: {p_mon.buttons:08X}   Pressed: {p_mon.describe()}")
        self.query_one("#monitor-mapping", Static).update("\n".join(p_mon.active_map) if p_mon.active_map else "[dim](Idle)[/dim]")

        self.query_one("#bar-lx", InputBarWidget).value = p_mon.lx
        self.query_one("#bar-ly", InputBarWidget).value = p_mon.ly
        self.query_one("#bar-rx", InputBarWidget).value = p_mon.rx
        self.query_one("#bar-ry", InputBarWidget).value = p_mon.ry
        self.query_one("#bar-lt", InputBarWidget).value = p_mon.lt
        self.query_one("#bar-rt", InputBarWidget).value = p_mon.rt

    async def core_tick_loop(self) -> None:
        while True:
            try:
                target_interval = 1.0 / self.config.tick_rate
                start_t = time.perf_counter()
                for msg in self.input_mgr.process_pygame_events():
                    self.log_msg(msg)
                    self.update_tables()

                for i in range(4):
                    self.pad_states[i] = self.input_mgr.get_pad_state(i)

                if self.connected and self.ws:
                    for i in range(4):
                        if self.pad_states[i].is_different(self.prev_states[i]):
                            try:
                                pkt = self.pad_states[i].to_packet()
                                await self.ws.send(pkt)
                                self.packets_sent += 1
                                self.prev_states[i].copy_from(self.pad_states[i])
                            except Exception:
                                self.packets_dropped += 1

                elapsed = time.perf_counter() - start_t
                sleep_time = target_interval - elapsed
                await asyncio.sleep(max(0, sleep_time))
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # Never let an unexpected error silently kill the whole input/output
                # loop — log it, back off briefly, and keep the app responsive.
                logging.error(f"core_tick_loop error: {e}")
                self.log_msg(f"[bold red]Internal tick-loop error (recovered):[/bold red] {e}")
                await asyncio.sleep(0.5)

    async def ws_receive_loop(self) -> None:
        if not self.ws: return
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)

                    # 1. Handle Response to Synchronized config query
                    if "result" in data and isinstance(data["result"], dict) and "users" in data["result"]:
                        self.ps4_users = data["result"]["users"]
                        self.log_msg(f"[green]Successfully synced {len(self.ps4_users)} profiles from PS4.[/green]")

                    # 2. Process active vibration packets from console
                    elif data.get("method") == "v":
                        params = data.get("params", [])
                        if len(params) >= 3:
                            pad_idx = params[0]
                            lf = params[1] / 255.0
                            sf = params[2] / 255.0
                            self.input_mgr.handle_rumble(pad_idx, lf, sf)
                            self.log_msg(f"Rumble Triggered on Pad {pad_idx} [Low: {lf:.2f} | High: {sf:.2f}]")
                except json.JSONDecodeError:
                    pass
        except ConnectionClosed:
            await self.action_disconnect()

    async def action_connect(self) -> None:
        if self.connected: return
        self.log_msg(f"[yellow]Connecting to console: {self.config.server_url}...[/yellow]")
        try:
            self.ws = await websockets.connect(self.config.server_url)
            self.connected = True
            self.sub_title = f"Connected | {self.config.server_url}"
            self.log_msg("[bold green]Link established with remote host.[/bold green]")

            # Request user setup configurations immediately after linking
            get_config_query = {
                "id": 100,
                "method": "config.get",
                "params": []
            }
            await self.ws.send(json.dumps(get_config_query))

            for p in self.prev_states: p.buttons = -1
            self.recv_task = asyncio.create_task(self.ws_receive_loop())
        except Exception as e:
            self.log_msg(f"[bold red]Connection attempt failed:[/bold red] {e}")

    async def action_disconnect(self) -> None:
        if not self.connected: return
        self.connected = False
        self.sub_title = f"Disconnected | {self.config.server_url}"
        if self.recv_task: self.recv_task.cancel()
        if self.ws:
            await self.ws.close()
            self.ws = None
        self.log_msg("[yellow]Connection closed cleanly.[/yellow]")
        self.input_mgr.close_all_hid_devices()

    def action_assignments(self) -> None:
        def on_dismiss(saved: bool):
            if saved:
                self.log_msg("[green]Pad mappings updated successfully.[/green]")
                self.input_mgr.update_hid_connections()
                self.update_tables()
        self.push_screen(AssignmentModal(self.config, self.input_mgr.device_names), on_dismiss)

    def action_setup_menu(self) -> None:
        def on_dismiss(updated_users_list: Optional[List[Dict[str, Any]]]):
            if updated_users_list:
                self.ps4_users = updated_users_list
                self.log_msg("[green]Sync complete: updated configuration variables sent to PS4.[/green]")
                self.sub_title = f"Connected | {self.config.server_url}"
        self.push_screen(SetupMenuModal(self.config, self.ps4_users, self.ws), on_dismiss)

    def action_map_buttons(self) -> None:
        def on_dismiss(mapped: bool):
            if mapped: self.log_msg("[green]Input bindings mapped to storage.[/green]")
        self.push_screen(ButtonMapperModal(self.config, self.input_mgr), on_dismiss)

    def action_cycle_monitor(self) -> None:
        self.monitored_pad = (self.monitored_pad + 1) % 4
        self.query_one("#monitor-title", Label).update(f"🎮 Live Monitor Panel (Pad {self.monitored_pad})")
        dt_p = self.query_one("#dt-players", DataTable)
        if dt_p.row_count > 0:
            try:
                dt_p.move_cursor(row=self.monitored_pad)
            except Exception:
                pass
        self.update_stats_ui()

    def action_quit(self) -> None:
        self.input_mgr.close_all_hid_devices()
        self.exit()


if __name__ == "__main__":
    app = JeloPadApp()
    app.run()
