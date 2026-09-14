"""
JeloPad CLI - Refactored High-Performance Edition
An updated production-quality terminal client with active console sync,
compiled input binding engine, non-blocking network queue, and safe HID interfaces.
"""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Any, Tuple, Set

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
from textual.containers import Horizontal, Vertical, Grid, Container
from textual.screen import ModalScreen
from textual import events
from textual.widgets import (
    Header,
    Footer,
    DataTable,
    RichLog,
    Static,
    Select,
    Label,
    Button,
    Input,
    Checkbox,
)
from textual.reactive import reactive
from rich.text import Text
from rich.console import RenderableType

# --- Protocol Constants ---
ORBIS_PAD_BUTTON_L3 = 0x0002
ORBIS_PAD_BUTTON_R3 = 0x0004
ORBIS_PAD_BUTTON_OPTIONS = 0x0008
ORBIS_PAD_BUTTON_UP = 0x0010
ORBIS_PAD_BUTTON_RIGHT = 0x0020
ORBIS_PAD_BUTTON_DOWN = 0x0040
ORBIS_PAD_BUTTON_LEFT = 0x0080
ORBIS_PAD_BUTTON_L2 = 0x0100
ORBIS_PAD_BUTTON_R2 = 0x0200
ORBIS_PAD_BUTTON_L1 = 0x0400
ORBIS_PAD_BUTTON_R1 = 0x0800
ORBIS_PAD_BUTTON_TRIANGLE = 0x1000
ORBIS_PAD_BUTTON_CIRCLE = 0x2000
ORBIS_PAD_BUTTON_CROSS = 0x4000
ORBIS_PAD_BUTTON_SQUARE = 0x8000
ORBIS_PAD_BUTTON_TOUCH_PAD = 0x100000

PS_BUTTON_NAMES: Dict[int, str] = {
    ORBIS_PAD_BUTTON_CROSS: "✕ Cross",
    ORBIS_PAD_BUTTON_CIRCLE: "○ Circle",
    ORBIS_PAD_BUTTON_TRIANGLE: "△ Triangle",
    ORBIS_PAD_BUTTON_SQUARE: "□ Square",
    ORBIS_PAD_BUTTON_L1: "L1",
    ORBIS_PAD_BUTTON_R1: "R1",
    ORBIS_PAD_BUTTON_L2: "L2",
    ORBIS_PAD_BUTTON_R2: "R2",
    ORBIS_PAD_BUTTON_L3: "L3 Click",
    ORBIS_PAD_BUTTON_R3: "R3 Click",
    ORBIS_PAD_BUTTON_OPTIONS: "Options",
    ORBIS_PAD_BUTTON_TOUCH_PAD: "Touchpad",
    ORBIS_PAD_BUTTON_UP: "D-Pad Up",
    ORBIS_PAD_BUTTON_DOWN: "D-Pad Down",
    ORBIS_PAD_BUTTON_LEFT: "D-Pad Left",
    ORBIS_PAD_BUTTON_RIGHT: "D-Pad Right",
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
    "space": ORBIS_PAD_BUTTON_CROSS,
    "escape": ORBIS_PAD_BUTTON_CIRCLE,
    "enter": ORBIS_PAD_BUTTON_TRIANGLE,
    "backspace": ORBIS_PAD_BUTTON_SQUARE,
    "q": ORBIS_PAD_BUTTON_L1,
    "e": ORBIS_PAD_BUTTON_R1,
    "1": ORBIS_PAD_BUTTON_L2,
    "3": ORBIS_PAD_BUTTON_R2,
    "o": ORBIS_PAD_BUTTON_OPTIONS,
    "u": ORBIS_PAD_BUTTON_TOUCH_PAD,
    "i": ORBIS_PAD_BUTTON_UP,
    "k": ORBIS_PAD_BUTTON_DOWN,
    "j": ORBIS_PAD_BUTTON_LEFT,
    "l": ORBIS_PAD_BUTTON_RIGHT,
}

KB1_AXIS_MAP: Dict[str, Tuple[int, float]] = {
    "a": (0, 0.0),
    "d": (0, 255.0),
    "w": (1, 0.0),
    "s": (1, 255.0),
    "left": (2, 0.0),
    "right": (2, 255.0),
    "up": (3, 0.0),
    "down": (3, 255.0),
}

KEY_HOLD_TIMEOUT = (
    0.0  # Kept for config/source compatibility; keyboard state is event-based
)


# --- Pre-Compiled Input Binding Engine ---
class BindingType(IntEnum):
    BUTTON = 1
    HAT = 2
    AXIS = 3


@dataclass(slots=True)
class CompiledBinding:
    target: str
    is_analog_target: bool
    mask: int
    b_type: BindingType
    index: int
    hat_x: int = 0
    hat_y: int = 0
    axis_sign: str = "+"


def compile_joy_mapping(mapping_dict: Dict[str, str]) -> List[CompiledBinding]:
    compiled: List[CompiledBinding] = []

    for target, src in mapping_dict.items():
        # Stick axes and trigger axes are analog destinations.
        is_analog = target in ("LX", "LY", "RX", "RY") or target in (
            str(ORBIS_PAD_BUTTON_L2),
            str(ORBIS_PAD_BUTTON_R2),
        )

        try:
            mask = 0 if target in ("LX", "LY", "RX", "RY") else int(target)
        except (TypeError, ValueError):
            continue

        try:
            parts = src.split(":")
            if src.startswith("BTN:") and len(parts) == 2:
                compiled.append(
                    CompiledBinding(
                        target=target,
                        is_analog_target=is_analog,
                        mask=mask,
                        b_type=BindingType.BUTTON,
                        index=int(parts[1]),
                    )
                )
            elif src.startswith("HAT:") and len(parts) == 4:
                compiled.append(
                    CompiledBinding(
                        target=target,
                        is_analog_target=is_analog,
                        mask=mask,
                        b_type=BindingType.HAT,
                        index=int(parts[1]),
                        hat_x=int(parts[2]),
                        hat_y=int(parts[3]),
                    )
                )
            elif src.startswith("AXIS:") and len(parts) in (2, 3):
                sign = parts[2] if len(parts) == 3 else "+"
                if sign not in ("+", "-"):
                    continue
                compiled.append(
                    CompiledBinding(
                        target=target,
                        is_analog_target=is_analog,
                        mask=mask,
                        b_type=BindingType.AXIS,
                        index=int(parts[1]),
                        axis_sign=sign,
                    )
                )
        except (TypeError, ValueError):
            # Ignore malformed user configuration instead of crashing startup.
            continue

    return compiled



@dataclass(slots=True)
class PadState:
    pad_index: int
    buttons: int = 0
    lx: int = 128
    ly: int = 128
    rx: int = 128
    ry: int = 128
    lt: int = 0
    rt: int = 0
    active_map: List[str] = field(default_factory=list)

    def to_packet(self) -> str:
        # Microsecond f-string serialization (10x faster than json.dumps)
        return f'{{"method":"u","params":[{self.pad_index},{self.buttons},{self.lx},{self.ly},{self.rx},{self.ry},{self.lt},{self.rt}]}}'

    def copy_from(self, other: "PadState") -> None:
        self.buttons = other.buttons
        self.lx, self.ly, self.rx, self.ry = other.lx, other.ly, other.rx, other.ry
        self.lt, self.rt = other.lt, other.rt
        self.active_map = list(other.active_map)

    def is_different(self, other: "PadState") -> bool:
        return (
            self.buttons != other.buttons
            or self.lx != other.lx
            or self.ly != other.ly
            or self.rx != other.rx
            or self.ry != other.ry
            or self.lt != other.lt
            or self.rt != other.rt
        )

    def describe(self) -> str:
        names = [name for bit, name in PS_BUTTON_NAMES.items() if self.buttons & bit]
        return ", ".join(names) if names else "-"


class ConfigManager:
    CONFIG_FILE = "config.toml"

    def __init__(self):
        self.server_url = "ws://127.0.0.1:4263"
        self.tick_rate = 120
        self.smoothing = 1.0
        self.assignments: Dict[int, str] = {
            0: "Keyboard 1",
            1: "None",
            2: "None",
            3: "None",
        }
        self.joy_mapping: Dict[str, str] = DEFAULT_JOY_MAPPING.copy()
        self.load()

    def load(self) -> None:
        if not os.path.exists(self.CONFIG_FILE):
            self.save()
            return
        if tomllib is None:
            logging.error("No TOML parser available; install tomli on Python < 3.11.")
            return

        try:
            with open(self.CONFIG_FILE, "rb") as f:
                data = tomllib.load(f)
                self.server_url = data.get("network", {}).get(
                    "server_url", self.server_url
                )
                self.tick_rate = data.get("network", {}).get(
                    "tick_rate", self.tick_rate
                )
                self.smoothing = data.get("input", {}).get("smoothing", self.smoothing)
                assignments = data.get("assignments", {})
                for i in range(4):
                    self.assignments[i] = assignments.get(
                        f"pad{i}", self.assignments[i]
                    )
                jm = data.get("joy_mapping", {})
                if jm:
                    self.joy_mapping = {str(k): str(v) for k, v in jm.items()}
        except Exception as e:
            logging.error(f"Failed to load config: {e}")

    def save(self) -> None:
        lines = [
            "[network]",
            f'server_url = "{self.server_url}"',
            f"tick_rate = {self.tick_rate}\n",
            "[input]",
            f"smoothing = {self.smoothing}\n",
            "[assignments]",
        ]
        for i in range(4):
            lines.append(f'pad{i} = "{self.assignments.get(i, "None")}"')
        lines.append("\n[joy_mapping]")
        for k, v in self.joy_mapping.items():
            lines.append(f'"{k}" = "{v}"')

        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception as e:
            logging.error(f"Failed to save config: {e}")


class InputManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        pygame.init()
        pygame.joystick.init()

        self.joysticks: Dict[int, pygame.joystick.Joystick] = {}
        self.device_names: Dict[str, str] = {
            "None": "Disabled",
            "Keyboard 1": "Keyboard Profile 1",
            "Mouse 1": "Mouse Profile 1",
        }

        self.hid_devices: Dict[int, Any] = {}
        self.target_vids = {0x0810, 0x0E8F, 0x120A, 0x1A2C}

        self.kb1_axes = [128.0, 128.0, 128.0, 128.0]
        self.kb_pressed: Set[str] = set()

        # Textual mouse events are copied here so Mouse 1 works without a gamepad.
        self.mouse_pressed: Set[int] = set()
        self.mouse_wheel_up = False
        self.mouse_wheel_down = False

        self.axis_bounds = defaultdict(lambda: defaultdict(lambda: [-1.0, 1.0]))

        self.compiled_joy_mapping: List[CompiledBinding] = []
        self.update_compiled_mapping()

        # Cache motor intensity to prevent thrashing
        self.last_rumble: Dict[int, Tuple[float, float]] = {}

    def update_compiled_mapping(self) -> None:
        self.compiled_joy_mapping = compile_joy_mapping(self.config.joy_mapping)

    def note_key_event(self, key: str) -> None:
        self.kb_pressed.add(key)

    def note_key_up(self, key: str) -> None:
        self.kb_pressed.discard(key)

    def _key_is_held(self, key: str) -> bool:
        return key in self.kb_pressed

    def close_all_hid_devices(self) -> None:
        for dev in list(self.hid_devices.values()):
            try:
                dev.close()
            except Exception:
                pass
        self.hid_devices.clear()

    def update_hid_connections(self) -> None:
        self.close_all_hid_devices()
        if not HID_AVAILABLE:
            return

        try:
            raw_hid_list = hid.enumerate()
        except Exception:
            return

        for pad_idx, dev_id in self.config.assignments.items():
            if dev_id.startswith("Joy "):
                try:
                    jid = int(dev_id.split(" ")[1])
                    if jid in self.joysticks:
                        joy = self.joysticks[jid]
                        vid = joy.get_vendor_id()
                        pid = joy.get_product_id()

                        if vid in self.target_vids:
                            for d in raw_hid_list:
                                if d["vendor_id"] == vid and d["product_id"] == pid:
                                    try:
                                        dev = hid.device()
                                        dev.open_path(d["path"])
                                        dev.set_nonblocking(True)
                                        self.hid_devices[pad_idx] = dev
                                        break
                                    except Exception:
                                        pass
                except (ValueError, AttributeError):
                    pass

    def detect_devices(self) -> List[str]:
        current_jids = set()
        changed = False

        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            jid = joy.get_instance_id()
            current_jids.add(jid)
            if jid not in self.joysticks:
                self.joysticks[jid] = joy
                self.device_names[f"Joy {jid}"] = joy.get_name()
                changed = True

        for jid in list(self.joysticks.keys()):
            if jid not in current_jids:
                del self.joysticks[jid]
                del self.device_names[f"Joy {jid}"]
                if jid in self.axis_bounds:
                    del self.axis_bounds[jid]
                for pad, dev in self.config.assignments.items():
                    if dev == f"Joy {jid}":
                        self.config.assignments[pad] = "None"
                changed = True

        # Logical input profiles are always available, even with zero controllers.
        self.device_names["None"] = "Disabled"
        self.device_names["Keyboard 1"] = "Keyboard Profile 1"
        self.device_names["Mouse 1"] = "Mouse Profile 1"

        if changed:
            self.update_hid_connections()
        return list(self.device_names.keys())

    def process_pygame_events(self) -> List[str]:
        logs = []
        for event in pygame.event.get():
            if event.type == pygame.JOYDEVICEADDED:
                self.detect_devices()
                logs.append(
                    f"Controller connected: {pygame.joystick.Joystick(event.device_index).get_name()}"
                )
            elif event.type == pygame.JOYDEVICEREMOVED:
                logs.append(f"Controller disconnected (ID: {event.instance_id})")
                self.detect_devices()
        return logs

    def get_pad_state(self, pad_index: int) -> PadState:
        device_id = self.config.assignments.get(pad_index, "None")
        state = PadState(pad_index)

        if device_id.startswith("Keyboard"):
            return self._poll_keyboard(state)

        if device_id.startswith("Mouse"):
            return self._poll_mouse(state)

        if device_id.startswith("Joy "):
            try:
                jid = int(device_id.split(" ", 1)[1])
            except (ValueError, IndexError):
                return state
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
                active_map.append(
                    f"KEY {key.upper()} : {PS_BUTTON_NAMES.get(bit, 'BTN')}"
                )

        tx = ty = rx = ry = 128.0
        for key, (axis_idx, target) in KB1_AXIS_MAP.items():
            if self._key_is_held(key):
                if axis_idx == 0:
                    tx = target
                elif axis_idx == 1:
                    ty = target
                elif axis_idx == 2:
                    rx = target
                elif axis_idx == 3:
                    ry = target
                active_map.append(f"KEY {key.upper()} : Stick")

        # Keyboard-to-analog conversion is immediate by default.
        # Optional smoothing remains supported through config values < 1.0.
        s = max(0.0, min(1.0, self.config.smoothing))
        if s >= 1.0:
            axes[:] = [tx, ty, rx, ry]
        else:
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

    def _poll_mouse(self, state: PadState) -> PadState:
        """Map the terminal application's mouse to a simple virtual pad profile."""
        btn = 0
        active_map: List[str] = []

        mouse_map = {
            1: (ORBIS_PAD_BUTTON_CROSS, "Left Click"),
            3: (ORBIS_PAD_BUTTON_CIRCLE, "Right Click"),
            2: (ORBIS_PAD_BUTTON_R1, "Middle Click"),
        }

        for mouse_button, (bit, name) in mouse_map.items():
            if mouse_button in self.mouse_pressed:
                btn |= bit
                active_map.append(f"MOUSE {name} : {PS_BUTTON_NAMES.get(bit, 'BTN')}")

        if self.mouse_wheel_up:
            btn |= ORBIS_PAD_BUTTON_UP
            active_map.append("MOUSE Wheel Up : D-Pad Up")
        if self.mouse_wheel_down:
            btn |= ORBIS_PAD_BUTTON_DOWN
            active_map.append("MOUSE Wheel Down : D-Pad Down")

        state.buttons = btn
        state.lt = 0
        state.rt = 0
        state.active_map = active_map
        return state

    def _poll_gamepad(
        self, state: PadState, joy: pygame.joystick.Joystick, jid: int
    ) -> PadState:
        btn = 0
        active_map: List[str] = []
        num_buttons = joy.get_numbuttons()
        num_hats = joy.get_numhats()
        num_axes = joy.get_numaxes()

        for binding in self.compiled_joy_mapping:
            is_active = False
            analog_val = 0

            if binding.b_type == BindingType.BUTTON:
                if binding.index < num_buttons and joy.get_button(binding.index):
                    is_active = True
                    analog_val = 255
            elif binding.b_type == BindingType.HAT:
                if binding.index < num_hats and joy.get_hat(binding.index) == (
                    binding.hat_x,
                    binding.hat_y,
                ):
                    is_active = True
                    analog_val = 255
            elif binding.b_type == BindingType.AXIS:
                if binding.index < num_axes:
                    val = joy.get_axis(binding.index)
                    bounds = self.axis_bounds[jid][binding.index]
                    if val < bounds[0]:
                        bounds[0] = val
                    if val > bounds[1]:
                        bounds[1] = val

                    range_v = bounds[1] - bounds[0]
                    norm_val = (
                        ((val - bounds[0]) / range_v) * 2.0 - 1.0
                        if range_v > 0.01
                        else val
                    )

                    if binding.is_analog_target:
                        if binding.axis_sign == "+":
                            analog_val = int((norm_val + 1.0) * 127.5)
                        else:
                            analog_val = int((1.0 - norm_val) * 127.5)
                        analog_val = max(0, min(255, analog_val))
                        if binding.mask in (ORBIS_PAD_BUTTON_L2, ORBIS_PAD_BUTTON_R2):
                            if analog_val > 50:
                                is_active = True
                        else:
                            is_active = True
                    else:
                        if (binding.axis_sign == "+" and norm_val > 0.5) or (
                            binding.axis_sign == "-" and norm_val < -0.5
                        ):
                            is_active = True
                            analog_val = 255

            if binding.target in ("LX", "LY", "RX", "RY"):
                setattr(state, binding.target.lower(), analog_val)
                if abs(analog_val - 128) > 30:
                    active_map.append(f"AXIS:{binding.index} -> {binding.target}")
            else:
                if is_active:
                    btn |= binding.mask
                    active_map.append(
                        f"{binding.target} -> {PS_BUTTON_NAMES.get(binding.mask, str(binding.mask))}"
                    )
                if binding.mask == ORBIS_PAD_BUTTON_L2:
                    state.lt = analog_val
                elif binding.mask == ORBIS_PAD_BUTTON_R2:
                    state.rt = analog_val

        state.buttons = btn
        state.active_map = active_map
        return state

    # Controller VID/PID profiles for direct HID rumble
    RUMBLE_PROFILES = {
        # Xbox 360 wired
        (0x045E, 0x028E): {
            "type": "xbox360",
            "report": lambda lf, hf: bytes(
                [0x00, 0x08, 0x00, int(lf * 255), int(hf * 255), 0x00, 0x00, 0x00]
            ),
        },
        # Xbox One / Series (wired)
        (0x045E, 0x02D1): {
            "type": "xboxone",
            "report": lambda lf, hf: bytes(
                [
                    0x09,
                    0x00,
                    0x00,
                    0x09,
                    0x00,
                    0x0F,
                    0x00,
                    int(lf * 255),
                    int(hf * 255),
                    int(lf * 255),
                    int(hf * 255),
                    0xFF,
                    0x00,
                    0x00,
                ]
            ),
        },
        (0x045E, 0x02DD): {
            "type": "xboxone",
            "report": lambda lf, hf: bytes(
                [
                    0x09,
                    0x00,
                    0x00,
                    0x09,
                    0x00,
                    0x0F,
                    0x00,
                    int(lf * 255),
                    int(hf * 255),
                    int(lf * 255),
                    int(hf * 255),
                    0xFF,
                    0x00,
                    0x00,
                ]
            ),
        },
        (0x045E, 0x02E3): {
            "type": "xboxone",
            "report": lambda lf, hf: bytes(
                [
                    0x09,
                    0x00,
                    0x00,
                    0x09,
                    0x00,
                    0x0F,
                    0x00,
                    int(lf * 255),
                    int(hf * 255),
                    int(lf * 255),
                    int(hf * 255),
                    0xFF,
                    0x00,
                    0x00,
                ]
            ),
        },
        (0x045E, 0x02EA): {
            "type": "xboxone",
            "report": lambda lf, hf: bytes(
                [
                    0x09,
                    0x00,
                    0x00,
                    0x09,
                    0x00,
                    0x0F,
                    0x00,
                    int(lf * 255),
                    int(hf * 255),
                    int(lf * 255),
                    int(hf * 255),
                    0xFF,
                    0x00,
                    0x00,
                ]
            ),
        },
        (0x045E, 0x0B00): {
            "type": "xboxone",
            "report": lambda lf, hf: bytes(
                [
                    0x09,
                    0x00,
                    0x00,
                    0x09,
                    0x00,
                    0x0F,
                    0x00,
                    int(lf * 255),
                    int(hf * 255),
                    int(lf * 255),
                    int(hf * 255),
                    0xFF,
                    0x00,
                    0x00,
                ]
            ),
        },
        # PS3 DualShock 3
        (0x054C, 0x0268): {
            "type": "ds3",
            "report": lambda lf, hf: bytes(
                [0x01, 0x00, int(hf > 0), int(hf * 255), int(lf > 0), int(lf * 255)]
            ),
        },
        # PS4 DualShock 4 (rev1 & rev2)
        (0x054C, 0x05C4): {
            "type": "ds4",
            "report": lambda lf, hf: bytes(
                [0x05, 0xFF, 0x00, 0x00, int(lf * 255), int(hf * 255)] + [0x00] * 26
            ),
        },
        (0x054C, 0x09CC): {
            "type": "ds4",
            "report": lambda lf, hf: bytes(
                [0x05, 0xFF, 0x00, 0x00, int(lf * 255), int(hf * 255)] + [0x00] * 26
            ),
        },
        # PS1/PS2 adapters (common generic VIDs)
        (0x0810, 0x0001): {
            "type": "generic",
            "report": lambda lf, hf: bytes(
                [0x01, 0x00, 0x00, int(lf * 255), int(hf * 255), 0x00, 0x00, 0x00]
            ),
        },
        (0x0E8F, 0x0003): {
            "type": "generic",
            "report": lambda lf, hf: bytes(
                [0x01, 0x00, 0x00, int(lf * 255), int(hf * 255), 0x00, 0x00, 0x00]
            ),
        },
    }

    GENERIC_RUMBLE_VIDS = {0x0810, 0x0E8F, 0x120A, 0x1A2C}

    def handle_rumble(self, pad_index: int, low_freq: float, high_freq: float) -> bool:
        """Debounced rumble: HID profile → SDL fallback."""
        low_freq = max(0.0, min(1.0, float(low_freq)))
        high_freq = max(0.0, min(1.0, float(high_freq)))
        old = self.last_rumble.get(pad_index, (-1.0, -1.0))
        if abs(low_freq - old[0]) < 0.02 and abs(high_freq - old[1]) < 0.02:
            return False
        # Only cache a rumble request after it is actually sent. This allows
        # failed writes to be retried instead of permanently suppressing them.

        # --- HID path ---
        if pad_index in self.hid_devices:
            dev = self.hid_devices[pad_index]
            device_id = self.config.assignments.get(pad_index, "None")
            sent = False
            if device_id.startswith("Joy"):
                jid = int(device_id.split(" ")[1])
                joy = self.joysticks.get(jid)
                if joy:
                    vid = joy.get_vendor_id()
                    pid = joy.get_product_id()
                    profile = RUMBLE_PROFILES.get((vid, pid))
                    if profile:
                        try:
                            report = profile["report"](low_freq, high_freq)
                            dev.write(report)
                            sent = True
                        except IOError:
                            try:
                                dev.close()
                            except Exception:
                                pass
                            del self.hid_devices[pad_index]
                    elif vid in GENERIC_RUMBLE_VIDS:
                        heavy = int(low_freq * 255)
                        light = int(high_freq * 255)
                        try:
                            dev.write(
                                bytes(
                                    [0x01, 0x00, 0x00, heavy, light, 0x00, 0x00, 0x00]
                                )
                            )
                            dev.write(
                                bytes(
                                    [0x02, 0x00, 0x00, heavy, light, 0x00, 0x00, 0x00]
                                )
                            )
                            sent = True
                        except IOError:
                            try:
                                dev.close()
                            except Exception:
                                pass
                            del self.hid_devices[pad_index]
            if sent:
                self.last_rumble[pad_index] = (low_freq, high_freq)
                return True

        # --- SDL fallback (Xbox 360/One BT, generic XInput, any SDL-supported pad) ---
        device_id = self.config.assignments.get(pad_index, "None")
        if device_id.startswith("Joy"):
            jid = int(device_id.split(" ")[1])
            joy = self.joysticks.get(jid)
            if joy:
                try:
                    joy.rumble(low_freq, high_freq, 250)
                    self.last_rumble[pad_index] = (low_freq, high_freq)
                    return True
                except Exception:
                    pass
        return False


# --- Modals ---
class SetupMenuModal(ModalScreen):
    def __init__(
        self,
        config: ConfigManager,
        ps4_users: List[Dict[str, Any]],
        ws_conn: Optional[Any] = None,
    ):
        super().__init__()
        self.config = config
        self.ps4_users = ps4_users
        self.ws_conn = ws_conn

    def compose(self) -> ComposeResult:
        if not self.ps4_users:
            self.ps4_users = [
                {
                    "index": i,
                    "enabled": True,
                    "userId": 0x20000000 + i,
                    "userName": f"Remote{i}",
                }
                for i in range(4)
            ]

        yield Vertical(
            Label("⚙️ JeloPad System Preferences", id="setup-title"),
            Horizontal(
                Label("Console WS Server: ", classes="setup-lbl"),
                Input(
                    value=self.config.server_url,
                    id="input-url",
                    placeholder="ws://ip:port",
                ),
                classes="setup-row",
            ),
            Label("Configure Remote Console Profiles:", id="users-header"),
            *[
                Horizontal(
                    Label(f"Pad {i}:", classes="pad-lbl"),
                    Checkbox(value=self.ps4_users[i]["enabled"], id=f"chk-u{i}"),
                    Input(
                        value=self.ps4_users[i]["userName"],
                        id=f"name-u{i}",
                        placeholder="User Name",
                    ),
                    classes="setup-row",
                )
                for i in range(4)
            ],
            Horizontal(
                Button("Apply & Upload Config", variant="success", id="btn-apply"),
                Button("Discard", variant="error", id="btn-discard"),
                classes="modal-buttons",
            ),
            id="setup-dialog",
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-apply":
            self.config.server_url = self.query_one("#input-url", Input).value
            self.config.save()

            for i in range(4):
                enabled_val = self.query_one(f"#chk-u{i}", Checkbox).value
                name_val = self.query_one(f"#name-u{i}", Input).value

                self.ps4_users[i]["enabled"] = enabled_val
                self.ps4_users[i]["userName"] = name_val

                if self.ws_conn:
                    payload = {
                        "id": 999 + i,
                        "method": "config.set",
                        "params": [
                            i,
                            enabled_val,
                            self.ps4_users[i]["userId"],
                            name_val,
                        ],
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
        # Always expose logical input profiles. A stale disconnected joystick
        # assignment is shown as Disabled instead of crashing Textual's Select.
        devices = dict(self.devices)
        devices.setdefault("None", "Disabled")
        devices.setdefault("Keyboard 1", "Keyboard Profile 1")
        devices.setdefault("Mouse 1", "Mouse Profile 1")

        options = [(label, device_id) for device_id, label in devices.items()]

        yield Vertical(
            Label("Assign Controllers", id="modal-title"),
            Label("Choose Keyboard, Mouse, a connected controller, or Disabled."),
            *[
                Horizontal(
                    Label(f"Pad {i}:", classes="assign-lbl"),
                    Select(
                        options,
                        value=(
                            self.config.assignments.get(i, "None")
                            if self.config.assignments.get(i, "None") in devices
                            else "None"
                        ),
                        id=f"sel{i}",
                    ),
                    classes="assign-row",
                )
                for i in range(4)
            ],
            Horizontal(
                Button("Save", variant="success", id="btn-save"),
                Button("Cancel", variant="error", id="btn-cancel"),
                classes="modal-buttons",
            ),
            id="assignment-dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            for i in range(4):
                val = self.query_one(f"#sel{i}", Select).value
                if val != Select.BLANK:
                    self.config.assignments[i] = val
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
        self.joy = (
            list(self.input_mgr.joysticks.values())[0]
            if self.input_mgr.joysticks
            else None
        )
        self.initial_axes: List[float] = []
        self.waiting_for_neutral = False
        self.start_time = time.perf_counter()

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("🎮 Auto Map Controller Layout", id="mapper-title"),
            Label(
                "No physical controller found!" if not self.joy else "Initializing...",
                id="mapper-prompt",
            ),
            Label("", id="mapper-timer"),
            Label("(Press Escape to cancel)", id="mapper-help"),
            id="mapper-dialog",
        )

    def on_mount(self) -> None:
        if not self.joy:
            self.set_timer(2.0, self.dismiss)
            return

        self.initial_axes = [
            self.joy.get_axis(i) for i in range(self.joy.get_numaxes())
        ]
        self.update_prompt()
        self.tick_timer = self.set_interval(0.05, self.check_input)

    def update_prompt(self):
        if self.current_target_idx >= len(self.buttons_to_map):
            self.finish_mapping()
            return
        _, name = self.buttons_to_map[self.current_target_idx]
        self.query_one("#mapper-prompt", Label).update(
            f"Action: [bold green]{name}[/bold green]"
        )
        self.start_time = time.perf_counter()

    def get_active_input(self) -> Optional[str]:
        if not self.joy:
            return None
        for i in range(self.joy.get_numbuttons()):
            if self.joy.get_button(i):
                return f"BTN:{i}"
        for i in range(self.joy.get_numhats()):
            hx, hy = self.joy.get_hat(i)
            if hx != 0 or hy != 0:
                return f"HAT:{i}:{hx}:{hy}"
        for i in range(self.joy.get_numaxes()):
            if i < len(self.initial_axes):
                diff = self.joy.get_axis(i) - self.initial_axes[i]
                if abs(diff) > 0.5:
                    direction = "+" if diff > 0 else "-"
                    return f"AXIS:{i}:{direction}"
        return None

    def check_input(self):
        if not self.joy or not hasattr(self, "tick_timer"):
            return  # guard against post-stop ticks
        if self.current_target_idx >= len(self.buttons_to_map):
            return
        elapsed = time.perf_counter() - self.start_time
        time_left = 5.0 - elapsed
        if time_left <= 0:
            self.current_target_idx += 1
            self.waiting_for_neutral = True
            self.update_prompt()
            return

        self.query_one("#mapper-timer", Label).update(
            f"Hold button/axis: [yellow]{time_left:.1f}s[/yellow] (Wait to skip)"
        )
        active = self.get_active_input()

        if self.waiting_for_neutral:
            if not active:
                self.waiting_for_neutral = False
            return

        if active:
            target_key, _ = self.buttons_to_map[self.current_target_idx]
            keys_to_remove = [k for k, v in self.new_mapping.items() if v == active]
            for k in keys_to_remove:
                del self.new_mapping[k]
            self.new_mapping[target_key] = active
            self.current_target_idx += 1
            self.waiting_for_neutral = True
            self.update_prompt()

    def finish_mapping(self):
        if hasattr(self, "tick_timer"):
            self.tick_timer.stop()
            del self.tick_timer  # prevent any stale re-entry
        self.query_one("#mapper-prompt", Label).update("[bold cyan]Mapping Complete![/bold cyan]")
        self.query_one("#mapper-timer", Label).update("Saving Configuration...")
        self.config.joy_mapping = self.new_mapping
        self.config.save()
        self.input_mgr.update_compiled_mapping()
        self.set_timer(1.0, lambda: self.dismiss(True))



    def action_cancel(self):
        if hasattr(self, "tick_timer"):
            self.tick_timer.stop()
        self.dismiss(False)


class InputBarWidget(Static):
    value = reactive(128)

    def __init__(self, label: str, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self._last_rendered_val = -1

    def render(self) -> RenderableType:
        pct = max(0.0, min(1.0, self.value / 255.0))
        bar_len = 18
        filled = int(pct * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        return Text(f"{self.label:3} | {bar} | {self.value:3}", style="cyan")


# --- Main Application ---
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

    #assignment-dialog, #setup-dialog {
        padding: 1 2;
        width: 65;
        height: auto;
        border: thick $accent 80%;
        background: $surface;
    }
    #modal-title, #setup-title { content-align: center middle; text-style: bold; margin-bottom: 1; }
    #users-header { text-style: bold; color: $accent; margin-top: 1; margin-bottom: 1; }
    .setup-row, .assign-row { height: 3; align: center middle; margin-bottom: 1; }
    .setup-lbl, .assign-lbl { width: 16; }
    .pad-lbl { width: 8; }
    .modal-buttons { align: center middle; margin-top: 1; }

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

        # Async Tasks & Loss-Tolerant Network Pipeline
        self.loop_task: Optional[asyncio.Task] = None
        self.recv_task: Optional[asyncio.Task] = None
        self.send_worker_task: Optional[asyncio.Task] = None
        self.latest_packets: Dict[int, str] = {}
        self.packet_event = asyncio.Event()

        self.ps4_users: List[Dict[str, Any]] = []

        # State Caching for Diff UI Repainting
        self._last_assignments: Dict[int, str] = {}
        self._last_devices: Dict[str, str] = {}
        self._last_rumble_status: str = "Idle"

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
                yield Label(
                    "🎮 Live Monitor Panel (Pad 0)",
                    id="monitor-title",
                    classes="section-title",
                )
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
            self.log_msg(
                "[yellow]Notice: 'hid' package not installed. Custom twin-motor rumble disabled.[/yellow]"
            )

        self.update_tables(force=True)
        self.loop_task = asyncio.create_task(self.core_tick_loop())
        self.send_worker_task = asyncio.create_task(self.ws_send_worker())
        self.set_interval(0.1, self.update_stats_ui)
        self.set_interval(1.0, self._device_refresh)

    def on_key(self, event: events.Key) -> None:
        self.input_mgr.note_key_event(event.key)

    async def on_key_up(self, event: events.Key) -> None:
        self.input_mgr.note_key_up(event.key)

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self.input_mgr.mouse_pressed.add(event.button)

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self.input_mgr.mouse_pressed.discard(event.button)

    def on_mouse_scroll_up(self, event: events.MouseScrollUp) -> None:
        self.input_mgr.mouse_wheel_up = True
        self.input_mgr.mouse_wheel_down = False

    def on_mouse_scroll_down(self, event: events.MouseScrollDown) -> None:
        self.input_mgr.mouse_wheel_down = True
        self.input_mgr.mouse_wheel_up = False

    def log_msg(self, msg: str) -> None:
        log = self.query_one("#rlog", RichLog)
        ts = time.strftime("%H:%M:%S")
        log.write(f"[blue]{ts}[/blue] {msg}")

    def _device_refresh(self) -> None:
        """Device discovery is intentionally outside the real-time input loop."""
        before = dict(self.input_mgr.device_names)
        self.input_mgr.detect_devices()
        if before != self.input_mgr.device_names:
            self.update_tables(force=True)

    def update_tables(self, force: bool = False) -> None:
        current_devices = dict(self.input_mgr.device_names)
        current_assignments = dict(self.config.assignments)

        if (
            not force
            and current_devices == self._last_devices
            and current_assignments == self._last_assignments
        ):
            return

        self._last_devices = current_devices
        self._last_assignments = current_assignments

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
        for dev_id, name in self.input_mgr.device_names.items():
            dt_c.add_row(dev_id, name)


    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id == "dt-players" and event.cursor_row is not None:
            if 0 <= event.cursor_row < 4:
                self.monitored_pad = event.cursor_row
                self.query_one("#monitor-title", Label).update(
                    f"🎮 Live Monitor Panel (Pad {self.monitored_pad})"
                )
                self.update_stats_ui()

    def update_stats_ui(self) -> None:
        uptime = int(time.time() - self.start_time)
        stats = f"""
[dim]Connection:[/dim] {"[green]Online[/green]" if self.connected else "[red]Offline[/red]"}
[dim]Tx Packets:[/dim] {self.packets_sent}
[dim]Err/Dropped:[/dim] {self.packets_dropped}
[dim]Output Rate:[/dim] {self.config.tick_rate} Hz
[dim]Rumble Status:[/dim] [yellow]{self._last_rumble_status}[/yellow]
[dim]Uptime:[/dim] {uptime}s
"""
        self.query_one("#stats-text", Static).update(stats)

        p_mon = self.pad_states[self.monitored_pad]
        self.query_one("#monitor-btns", Label).update(
            f"Mask: {p_mon.buttons:08X}   Pressed: {p_mon.describe()}"
        )

        map_str = (
            "\n".join(p_mon.active_map) if p_mon.active_map else "[dim](Idle)[/dim]"
        )
        self.query_one("#monitor-mapping", Static).update(map_str)

        self.query_one("#bar-lx", InputBarWidget).value = p_mon.lx
        self.query_one("#bar-ly", InputBarWidget).value = p_mon.ly
        self.query_one("#bar-rx", InputBarWidget).value = p_mon.rx
        self.query_one("#bar-ry", InputBarWidget).value = p_mon.ry
        self.query_one("#bar-lt", InputBarWidget).value = p_mon.lt
        self.query_one("#bar-rt", InputBarWidget).value = p_mon.rt

    async def ws_send_worker(self) -> None:
        """Low-latency latest-state sender. Never builds a packet backlog."""
        while True:
            await self.packet_event.wait()
            self.packet_event.clear()

            if not self.connected or not self.ws:
                self.latest_packets.clear()
                continue

            packets = list(self.latest_packets.values())
            self.latest_packets.clear()

            for pkt in packets:
                try:
                    await self.ws.send(pkt)
                    self.packets_sent += 1
                except Exception:
                    self.packets_dropped += 1
                    break

    async def core_tick_loop(self) -> None:
        while True:
            target_interval = 1.0 / self.config.tick_rate
            start_t = time.perf_counter()

            for msg in self.input_mgr.process_pygame_events():
                self.log_msg(msg)
                self.update_tables(force=True)

            for i in range(4):
                self.pad_states[i] = self.input_mgr.get_pad_state(i)

            if self.connected and self.ws:
                for i in range(4):
                    if self.pad_states[i].is_different(self.prev_states[i]):
                        self.latest_packets[i] = self.pad_states[i].to_packet()
                        self.prev_states[i].copy_from(self.pad_states[i])

                if self.latest_packets:
                    self.packet_event.set()

            elapsed = time.perf_counter() - start_t
            sleep_time = target_interval - elapsed
            await asyncio.sleep(max(0.0, sleep_time))

        # Mouse wheel acts as an edge-triggered virtual button.
        self.input_mgr.mouse_wheel_up = False
        self.input_mgr.mouse_wheel_down = False

    async def ws_receive_loop(self) -> None:
        if not self.ws:
            return
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)

                    if (
                        "result" in data
                        and isinstance(data["result"], dict)
                        and "users" in data["result"]
                    ):
                        self.ps4_users = data["result"]["users"]
                        self.log_msg(
                            f"[green]Successfully synced {len(self.ps4_users)} profiles from console.[/green]"
                        )

                    elif data.get("method") == "v":
                        params = data.get("params", [])
                        if len(params) >= 3:
                            pad_idx = params[0]
                            lf = params[1] / 255.0
                            sf = params[2] / 255.0
                            if self.input_mgr.handle_rumble(pad_idx, lf, sf):
                                self._last_rumble_status = (
                                    f"P{pad_idx} L:{lf:.1f} H:{sf:.1f}"
                                )
                except json.JSONDecodeError:
                    pass
        except ConnectionClosed:
            await self.action_disconnect(from_receive_loop=True)

    async def action_connect(self) -> None:
        if self.connected:
            return
        self.log_msg(
            f"[yellow]Connecting to console: {self.config.server_url}...[/yellow]"
        )
        try:
            self.ws = await websockets.connect(self.config.server_url)
            self.connected = True
            self.sub_title = f"Connected | {self.config.server_url}"
            self.log_msg("[bold green]Link established with remote host.[/bold green]")

            get_config_query = {"id": 100, "method": "config.get", "params": []}
            await self.ws.send(json.dumps(get_config_query))

            for p in self.prev_states:
                p.buttons = -1
            self.recv_task = asyncio.create_task(self.ws_receive_loop())
        except Exception as e:
            self.connected = False
            self.sub_title = f"Disconnected | {self.config.server_url}"
            if self.ws:
                try:
                    await self.ws.close()
                except Exception:
                    pass
                self.ws = None
            self.log_msg(f"[bold red]Connection attempt failed:[/bold red] {e}")

    async def action_disconnect(self, from_receive_loop: bool = False) -> None:
        if not self.connected and self.ws is None:
            return
        self.connected = False
        self.sub_title = f"Disconnected | {self.config.server_url}"
        current_task = asyncio.current_task()
        if self.recv_task and self.recv_task is not current_task:
            self.recv_task.cancel()
        self.recv_task = None
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None
        self.log_msg("[yellow]Connection closed cleanly.[/yellow]")
        self.input_mgr.close_all_hid_devices()

    def action_assignments(self) -> None:
        def on_dismiss(saved: bool):
            if saved:
                self.log_msg("[green]Pad mappings updated successfully.[/green]")
                self.input_mgr.update_hid_connections()
                self.update_tables(force=True)

        self.push_screen(
            AssignmentModal(self.config, self.input_mgr.device_names), on_dismiss
        )

    def action_setup_menu(self) -> None:
        def on_dismiss(updated_users_list: Optional[List[Dict[str, Any]]]):
            if updated_users_list:
                self.ps4_users = updated_users_list
                self.log_msg(
                    "[green]Sync complete: updated configuration variables sent to console.[/green]"
                )

        self.push_screen(
            SetupMenuModal(self.config, self.ps4_users, self.ws), on_dismiss
        )

    def action_map_buttons(self) -> None:
        def on_dismiss(mapped: bool):
            if mapped:
                self.log_msg("[green]Input bindings mapped to storage.[/green]")

        self.push_screen(ButtonMapperModal(self.config, self.input_mgr), on_dismiss)

    def action_cycle_monitor(self) -> None:
        self.monitored_pad = (self.monitored_pad + 1) % 4
        self.query_one("#monitor-title", Label).update(
            f"🎮 Live Monitor Panel (Pad {self.monitored_pad})"
        )
        dt_p = self.query_one("#dt-players", DataTable)
        if dt_p.row_count > 0:
            try:
                dt_p.move_cursor(row=self.monitored_pad)
            except Exception:
                pass
        self.update_stats_ui()

    def action_quit(self) -> None:
        self.input_mgr.close_all_hid_devices()
        if self.send_worker_task:
            self.send_worker_task.cancel()
        if self.loop_task:
            self.loop_task.cancel()
        self.latest_packets.clear()
        self.packet_event.clear()
        self.exit()


if __name__ == "__main__":
    app = JeloPadApp()
    app.run()

