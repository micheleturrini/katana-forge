"""Tests for TSL preset parsing, loading, and serialization."""

import os
import unittest
from katana_modern.core.patch_model import KatanaPatchModel
from katana_modern.core.tsl_manager import get_tsl_patches, load_tsl


class TestTslManager(unittest.TestCase):
    def test_load_mk2_tsl(self):
        # Test loading a known single patch or bundle
        test_file = "saved_patches/acoustasonic.tsl"
        if os.path.exists(test_file):
            patches = get_tsl_patches(test_file)
            self.assertGreater(len(patches), 0)
            self.assertIn("name", patches[0])

            model = KatanaPatchModel()
            success = load_tsl(test_file, model, patch_index=0)
            self.assertTrue(success)
            self.assertTrue(len(model.patch_name) > 0)

    def test_load_bundle_tsl(self):
        bundle_file = "saved_patches/KATANA MkII top ten by James Ryan.tsl"
        if os.path.exists(bundle_file):
            patches = get_tsl_patches(bundle_file)
            self.assertEqual(len(patches), 10)
            for p in patches:
                self.assertTrue(len(p["name"]) > 0)


if __name__ == "__main__":
    unittest.main()
