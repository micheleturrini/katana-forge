"""Tests for full 16-packet SysEx transmission and safe audition volume calculation."""

import unittest
from katana_modern.core.patch_model import KatanaPatchModel
from katana_modern.core.patch_transmitter import (
    get_default_template,
    build_full_patch_sysex,
    calculate_safe_audition_volume,
    DEFAULT_SYX_PATH,
)
from katana_modern.core.roland_sysex import roland_checksum, SOX, EOX


class TestPatchTransmitter(unittest.TestCase):
    def test_default_template_loading(self):
        tmpl = get_default_template()
        self.assertIsInstance(tmpl, bytearray)
        self.assertEqual(len(tmpl), 2156)

    def test_build_full_patch_sysex(self):
        model = KatanaPatchModel()
        model.set_param("chain_pattern", 3)
        model.set_param("chain_eq1_pos", 1)
        model.set_param("chain_loop_pos", 1)

        packets = build_full_patch_sysex(model)
        self.assertEqual(len(packets), 16)

        for p in packets:
            self.assertEqual(p[0], SOX)
            self.assertEqual(p[-1], EOX)
            # Verify Roland checksum
            addr_and_data = list(p[8:-2])
            expected_chk = roland_checksum(addr_and_data)
            self.assertEqual(p[-2], expected_chk)

        # Check that chain pattern was written to packet 6 (offset 12 + 32)
        pkt6 = packets[6]
        self.assertEqual(pkt6[12 + 32], 3)
        self.assertEqual(pkt6[12 + 33], 1)  # chain_loop_pos
        self.assertEqual(pkt6[12 + 34], 1)  # chain_eq1_pos

    def test_safe_volume_calculation(self):
        # High gain with loud volume is safely clamped to safe listening range
        safe_vol = calculate_safe_audition_volume(raw_volume=90, gain=85, ceiling=42, floor=36)
        self.assertLessEqual(safe_vol, 42)
        self.assertGreaterEqual(safe_vol, 36)

        # Clean tone volume is comfortably normalized
        clean_vol = calculate_safe_audition_volume(raw_volume=60, gain=30, ceiling=42, floor=36)
        self.assertLessEqual(clean_vol, 42)
        self.assertGreaterEqual(clean_vol, 36)


if __name__ == "__main__":
    unittest.main()
