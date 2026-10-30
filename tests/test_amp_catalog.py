"""Tests for Boss Katana MkII model catalog, Sneaky Amps, and Chain Routes."""

import unittest
from katana_modern.core.amp_catalog import (
    PREAMP_MODELS,
    BOOSTER_MODELS,
    MOD_MODELS,
    FX_MODELS,
    DELAY_MODELS,
    REVERB_MODELS,
    CHAIN_ROUTES,
)


class TestAmpCatalog(unittest.TestCase):
    def test_standard_and_sneaky_amps(self):
        # Must contain standard 5 amps
        standard_ids = [0x01, 0x08, 0x0B, 0x18, 0x17]
        for sid in standard_ids:
            self.assertIn(sid, PREAMP_MODELS)
            self.assertEqual(PREAMP_MODELS[sid].category, "Standard")

        # Must contain MkII variations
        var_ids = [0x1C, 0x1D, 0x1E, 0x1F, 0x20]
        for vid in var_ids:
            self.assertIn(vid, PREAMP_MODELS)
            self.assertEqual(PREAMP_MODELS[vid].category, "MkII Variation")

        # Must contain famous 28 sneaky amps
        sneaky_count = sum(1 for m in PREAMP_MODELS.values() if m.category.startswith("Sneaky"))
        self.assertGreaterEqual(sneaky_count, 20)
        # Check specific famous sneaky models
        self.assertIn(0x09, PREAMP_MODELS)  # Clean Twin
        self.assertIn(0x12, PREAMP_MODELS)  # MS-1959 I Plexi
        self.assertIn(0x15, PREAMP_MODELS)  # R-Fier Modern

    def test_booster_models(self):
        # Check classic Boss drives
        self.assertIn(0x00, BOOSTER_MODELS)  # Mid Boost
        self.assertIn(0x01, BOOSTER_MODELS)  # Clean Boost
        self.assertIn(0x04, BOOSTER_MODELS)  # Blues Driver (BD-2)
        self.assertIn(0x05, BOOSTER_MODELS)  # Overdrive (OD-1)
        self.assertIn(0x06, BOOSTER_MODELS)  # T-Scream (TS-9)
        self.assertIn(0x13, BOOSTER_MODELS)  # Muff Fuzz

    def test_chain_routes_hardware_topologies(self):
        self.assertEqual(len(CHAIN_ROUTES), 7)
        for idx, route in enumerate(CHAIN_ROUTES):
            self.assertEqual(route["id"], idx)
            self.assertIn("name", route)
            self.assertIn("summary", route)
            self.assertIn("blocks", route)
            self.assertTrue(len(route["blocks"]) >= 8)


if __name__ == "__main__":
    unittest.main()
