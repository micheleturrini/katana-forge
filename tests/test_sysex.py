"""Tests for Roland Katana SysEx protocols and checksums."""

import unittest
from katana_modern.core.roland_sysex import (
    roland_checksum,
    create_dt1,
    create_rq1,
    SOX,
    EOX,
    ADDR_CURRENT_CHANNEL,
    ROLAND_MANUFACTURER_ID,
    KATANA_MODEL_HEADER,
)


class TestRolandSysEx(unittest.TestCase):
    def test_roland_checksum_calculation(self):
        # Known test vector: address 00 00 00, data 00 -> (128 - 0) & 0x7F = 0
        self.assertEqual(roland_checksum([0x00, 0x00, 0x00, 0x00]), 0x00)

        # Vector: sum % 128 = 20 -> (128 - 20) & 0x7F = 108 (0x6C)
        self.assertEqual(roland_checksum([0x10, 0x04]), (128 - 20) & 0x7F)

        # Standard Roland boundary check
        chk = roland_checksum([0x60, 0x00, 0x00, 0x01, 0x08])
        self.assertTrue(0 <= chk <= 127)

    def test_create_dt1(self):
        msg = create_dt1([0x60, 0x00, 0x00, 0x01], [0x08])
        self.assertEqual(msg[0], SOX)
        self.assertEqual(msg[-1], EOX)
        # Roland manufacturer ID (0x41) + device ID (0x00) + model header
        self.assertEqual(msg[1], ROLAND_MANUFACTURER_ID)
        self.assertEqual(msg[2], 0x00)
        self.assertEqual(msg[3:7], bytes(KATANA_MODEL_HEADER))
        # Command DT1 = 0x12
        self.assertEqual(msg[7], 0x12)
        # Address
        self.assertEqual(msg[8:12], bytes([0x60, 0x00, 0x00, 0x01]))
        # Data
        self.assertEqual(msg[12], 0x08)
        # Checksum calculation matches
        expected_chk = roland_checksum([0x60, 0x00, 0x00, 0x01, 0x08])
        self.assertEqual(msg[13], expected_chk)

    def test_create_rq1(self):
        msg = create_rq1([0x60, 0x00, 0x00, 0x00], [0x00, 0x00, 0x01, 0x00])
        self.assertEqual(msg[0], SOX)
        self.assertEqual(msg[-1], EOX)
        self.assertEqual(msg[7], 0x11)  # RQ1 command
        self.assertEqual(msg[8:12], bytes([0x60, 0x00, 0x00, 0x00]))
        self.assertEqual(msg[12:16], bytes([0x00, 0x00, 0x01, 0x00]))

    def test_current_channel_address(self):
        self.assertEqual(ADDR_CURRENT_CHANNEL, [0x00, 0x01, 0x00, 0x00])


if __name__ == "__main__":
    unittest.main()
