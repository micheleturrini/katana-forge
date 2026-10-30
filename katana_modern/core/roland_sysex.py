"""
Roland SysEx Protocol implementation for BOSS Katana MkII.
Handles packet framing, Roland 7-bit checksums, DT1 data setting, and RQ1 data requesting.
"""

from typing import List, Tuple, Optional


ROLAND_MANUFACTURER_ID = 0x41
KATANA_MODEL_HEADER = [0x00, 0x00, 0x00, 0x33]
CMD_RQ1 = 0x11  # Request Data 1
CMD_DT1 = 0x12  # Data Set 1
SOX = 0xF0
EOX = 0xF7

# Address Base
ADDR_TEMP_BUFFER_MK2 = [0x60, 0x00, 0x00, 0x00]
ADDR_EDITOR_HANDSHAKE = [0x7F, 0x00, 0x00, 0x01]
ADDR_CURRENT_CHANNEL = [0x00, 0x01, 0x00, 0x00]


def roland_checksum(data_bytes: List[int]) -> int:
    """Calculate Roland 7-bit checksum: (128 - (sum % 128)) & 0x7F"""
    total = sum(data_bytes) % 128
    return (128 - total) & 0x7F


def create_identity_request() -> bytes:
    """Standard Universal Identity Request: F0 7E 7F 06 01 F7"""
    return bytes([SOX, 0x7E, 0x7F, 0x06, 0x01, EOX])


def create_editor_handshake(device_id: int = 0x00) -> bytes:
    """Send Editor Comm Mode enable (7F 00 00 01 = 01)"""
    payload = ADDR_EDITOR_HANDSHAKE + [0x01]
    chk = roland_checksum(payload)
    packet = [SOX, ROLAND_MANUFACTURER_ID, device_id] + KATANA_MODEL_HEADER + [CMD_DT1] + payload + [chk, EOX]
    return bytes(packet)


def create_dt1(address: List[int], data: List[int], device_id: int = 0x00) -> bytes:
    """
    Create a Roland DT1 (Data Set 1) packet.
    address: 4 bytes (e.g. [0x60, 0x00, hex1, hex3])
    data: list of data bytes
    """
    assert len(address) == 4, "Address must be 4 bytes"
    payload = address + data
    chk = roland_checksum(payload)
    packet = [SOX, ROLAND_MANUFACTURER_ID, device_id] + KATANA_MODEL_HEADER + [CMD_DT1] + payload + [chk, EOX]
    return bytes(packet)


def create_rq1(address: List[int], size: List[int], device_id: int = 0x00) -> bytes:
    """
    Create a Roland RQ1 (Request Data 1) packet.
    address: 4 bytes
    size: 4 bytes
    """
    assert len(address) == 4, "Address must be 4 bytes"
    assert len(size) == 4, "Size must be 4 bytes"
    payload = address + size
    chk = roland_checksum(payload)
    packet = [SOX, ROLAND_MANUFACTURER_ID, device_id] + KATANA_MODEL_HEADER + [CMD_RQ1] + payload + [chk, EOX]
    return bytes(packet)


def parse_sysex(packet: bytes) -> Optional[Tuple[str, List[int], List[int], bool]]:
    """
    Parses a raw SysEx packet.
    Returns: (cmd_type: 'DT1'|'RQ1'|'IDENTITY'|'OTHER', address, data, is_valid_checksum)
    """
    if len(packet) < 6 or packet[0] != SOX or packet[-1] != EOX:
        return None

    # Check for Identity Reply: F0 7E <dev> 06 02 41 33 03 ... F7
    if packet[1] == 0x7E and len(packet) >= 15 and packet[3] == 0x06 and packet[4] == 0x02:
        return ('IDENTITY', [], list(packet[5:-1]), True)

    if len(packet) < 14:
        return ('OTHER', [], list(packet[1:-1]), False)

    # Check Roland header
    if packet[1] != ROLAND_MANUFACTURER_ID:
        return ('OTHER', [], list(packet[1:-1]), False)

    cmd = packet[7]  # 0x12 for DT1, 0x11 for RQ1
    payload = list(packet[8:-2])  # Address + Data
    received_chk = packet[-2]
    expected_chk = roland_checksum(payload)
    valid_chk = (received_chk == expected_chk)

    addr = payload[:4]
    data = payload[4:]
    cmd_name = 'DT1' if cmd == CMD_DT1 else ('RQ1' if cmd == CMD_RQ1 else f'CMD_{cmd:02X}')

    return (cmd_name, addr, data, valid_chk)
