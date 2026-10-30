"""
Low-latency native ALSA MIDI backend for BOSS Katana.
Communicates directly with libasound.so.2 via ctypes.
Provides auto-discovery, background reception thread, throttled transmission queue,
and Qt Signals for responsive GUI synchronization.
"""

import ctypes
import os
import time
import queue
import threading
from typing import List, Optional, Callable, Tuple

from PyQt6.QtCore import QObject, pyqtSignal

from katana_modern.core.roland_sysex import (
    SOX, EOX, create_identity_request, create_editor_handshake, parse_sysex
)


# Load ALSA library
try:
    asound = ctypes.cdll.LoadLibrary('libasound.so.2')
    asound.snd_rawmidi_open.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_char_p,
        ctypes.c_int
    ]
    asound.snd_rawmidi_open.restype = ctypes.c_int
    asound.snd_rawmidi_write.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
    asound.snd_rawmidi_write.restype = ctypes.c_ssize_t
    asound.snd_rawmidi_read.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
    asound.snd_rawmidi_read.restype = ctypes.c_ssize_t
    asound.snd_rawmidi_drain.argtypes = [ctypes.c_void_p]
    asound.snd_rawmidi_close.argtypes = [ctypes.c_void_p]
    ALSA_AVAILABLE = True
except Exception as e:
    asound = None
    ALSA_AVAILABLE = False


class KatanaMidiBackend(QObject):
    """
    Asynchronous MIDI coordinator bridging hardware ALSA MIDI to the UI.
    """
    connected_changed = pyqtSignal(bool, str)       # is_connected, device_name
    sysex_received = pyqtSignal(bytes)              # raw sysex packet
    device_list_updated = pyqtSignal(list)          # list of available device names
    error_occurred = pyqtSignal(str)                # error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._in_handle = ctypes.c_void_p()
        self._out_handle = ctypes.c_void_p()
        self._is_connected = False
        self._device_name = ""
        self._device_port = ""

        self._tx_queue = queue.Queue()
        self._running = False
        self._tx_thread: Optional[threading.Thread] = None
        self._rx_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Simulated / Offline state for demo/testing without physical amp
        self.simulation_mode = False

    def scan_devices(self) -> List[Tuple[str, str]]:
        """
        Scans ALSA for available Katana MIDI devices by reading /proc/asound/cards.
        Returns list of tuples: (display_name, port_string e.g. 'hw:1,0,0')
        """
        results = []
        if not ALSA_AVAILABLE:
            return [("Virtual Katana (Offline Mode)", "virtual")]

        active_cards = []
        try:
            with open("/proc/asound/cards", "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if parts and parts[0].isdigit():
                        card_num = int(parts[0])
                        card_id = parts[1].strip("[]:")
                        active_cards.append((card_num, card_id))
        except:
            active_cards = [(1, "KATANA")]

        katana_devices = []
        other_devices = []

        for card, card_id in active_cards:
            is_katana = "KATANA" in card_id.upper()
            for dev in range(2):
                for sub in range(4):
                    port_str = f"hw:{card},{dev},{sub}"
                    # If this port is currently connected by our own backend, consider it open and active
                    if self._is_connected and self._device_port == port_str:
                        ret = 0
                    else:
                        test_in = ctypes.c_void_p()
                        test_out = ctypes.c_void_p()
                        ret = asound.snd_rawmidi_open(
                            ctypes.byref(test_in),
                            ctypes.byref(test_out),
                            port_str.encode('utf-8'),
                            2  # SND_RAWMIDI_NONBLOCK
                        )
                        if ret == 0:
                            asound.snd_rawmidi_close(test_in)
                            asound.snd_rawmidi_close(test_out)

                    if ret == 0:
                        if is_katana:
                            if sub == 0:
                                display_name = f"KATANA MkII ({port_str})"
                            elif sub == 2:
                                display_name = f"KATANA MIDI 3 [Editor] ({port_str})"
                            else:
                                display_name = f"KATANA Port {sub+1} ({port_str})"
                            katana_devices.append((display_name, port_str))
                        else:
                            display_name = f"{card_id} ({port_str})"
                            other_devices.append((display_name, port_str))

        # Sort so primary Katana port (hw:X,0,0) is always the first choice
        katana_devices.sort(key=lambda x: (x[1] != "hw:1,0,0" and not x[1].endswith(",0,0"), x[1]))
        results = katana_devices + other_devices

        # Always offer Virtual mode as an offline fallback option at the end
        results.append(("Virtual Katana (Offline Mode)", "virtual"))
        return results

    def connect_device(self, port_str: str, name: str = "KATANA") -> bool:
        """Connects to the specified ALSA rawmidi port or virtual mode."""
        self.disconnect_device()

        if port_str == "virtual" or not ALSA_AVAILABLE:
            self.simulation_mode = True
            self._is_connected = True
            self._device_name = "Virtual Katana MkII (Simulation)"
            self._device_port = "virtual"
            self.connected_changed.emit(True, self._device_name)
            return True

        self.simulation_mode = False
        ret = asound.snd_rawmidi_open(
            ctypes.byref(self._in_handle),
            ctypes.byref(self._out_handle),
            port_str.encode('utf-8'),
            2  # SND_RAWMIDI_NONBLOCK
        )
        if ret != 0:
            self.error_occurred.emit(f"Failed to open MIDI port {port_str} (error {ret})")
            return False

        self._is_connected = True
        self._device_name = name
        self._device_port = port_str
        self._running = True

        # Start background TX and RX threads
        self._tx_thread = threading.Thread(target=self._tx_worker, daemon=True, name="Katana-MIDI-TX")
        self._rx_thread = threading.Thread(target=self._rx_worker, daemon=True, name="Katana-MIDI-RX")
        self._tx_thread.start()
        self._rx_thread.start()

        # Send Handshake sequence to unlock Boss Katana editor mode
        self.send_sysex(create_identity_request())
        self.send_sysex(create_editor_handshake())
        # Request current channel to synchronize state
        req_ch = bytes.fromhex("F0 41 00 00 00 00 33 11 00 01 00 00 00 00 00 02 FD F7")
        self.send_sysex(req_ch)

        self.connected_changed.emit(True, self._device_name)
        return True

    def disconnect_device(self):
        """Disconnects cleanly from the MIDI hardware."""
        if self._is_connected and not self.simulation_mode:
            # Switch off Katana editor mode (7F 00 00 01 = 00)
            off_cmd = bytes.fromhex("F0 41 00 00 00 00 33 12 7F 00 00 01 00 00 F7")
            try:
                if self._out_handle.value:
                    asound.snd_rawmidi_write(self._out_handle, off_cmd, len(off_cmd))
                    asound.snd_rawmidi_drain(self._out_handle)
            except Exception:
                pass

        self._running = False
        self._is_connected = False

        if self._tx_thread and self._tx_thread.is_alive():
            self._tx_queue.put(None)  # Sentinel to exit
            self._tx_thread.join(timeout=0.2)
        if self._rx_thread and self._rx_thread.is_alive():
            self._rx_thread.join(timeout=0.2)

        with self._lock:
            if self._in_handle.value:
                asound.snd_rawmidi_close(self._in_handle)
                self._in_handle = ctypes.c_void_p()
            if self._out_handle.value:
                asound.snd_rawmidi_close(self._out_handle)
                self._out_handle = ctypes.c_void_p()

        # Clear remaining queue
        while not self._tx_queue.empty():
            try:
                self._tx_queue.get_nowait()
            except:
                break

        self.connected_changed.emit(False, "")

    def is_connected(self) -> bool:
        return self._is_connected

    def get_device_name(self) -> str:
        return self._device_name

    def clear_queue(self):
        """Clears pending outgoing SysEx packets to prevent lag on rapid changes."""
        while not self._tx_queue.empty():
            try:
                self._tx_queue.get_nowait()
                self._tx_queue.task_done()
            except:
                break

    def send_sysex(self, packet: bytes):
        """Enqueue a SysEx packet for throttled transmission."""
        if not self._is_connected:
            return
        if self.simulation_mode:
            # In simulation mode, immediately echo back or accept
            return
        self._tx_queue.put(packet)

    def _tx_worker(self):
        """Worker thread pacing SysEx packets with 10ms throttle."""
        while self._running:
            try:
                packet = self._tx_queue.get(timeout=0.1)
                if packet is None or not self._running:
                    break

                with self._lock:
                    if self._out_handle.value:
                        asound.snd_rawmidi_write(self._out_handle, packet, len(packet))
                        asound.snd_rawmidi_drain(self._out_handle)

                # Hardware throttle: Katana processor needs ~8-15ms between SysEx packets
                time.sleep(0.010)
                self._tx_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.error_occurred.emit(f"TX error: {e}")

    def _rx_worker(self):
        """Worker thread continuously reading incoming SysEx frames."""
        rx_buffer = bytearray()
        buf = ctypes.create_string_buffer(256)

        while self._running:
            try:
                with self._lock:
                    if not self._in_handle.value:
                        break
                    n = asound.snd_rawmidi_read(self._in_handle, buf, 256)

                if n > 0:
                    data = buf.raw[:n]
                    for b in data:
                        if b == SOX:
                            rx_buffer = bytearray([SOX])
                        elif rx_buffer:
                            rx_buffer.append(b)
                            if b == EOX:
                                complete_packet = bytes(rx_buffer)
                                rx_buffer = bytearray()
                                self.sysex_received.emit(complete_packet)
                else:
                    time.sleep(0.005)
            except Exception as e:
                time.sleep(0.01)
