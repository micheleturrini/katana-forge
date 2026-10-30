"""Tests for KatanaPatchModel, safe volume guard, templates, and dynamic chain blocks."""

import unittest
from katana_modern.core.patch_model import KatanaPatchModel


class TestKatanaPatchModel(unittest.TestCase):
    def setUp(self):
        self.model = KatanaPatchModel()

    def test_default_initialization(self):
        self.assertEqual(self.model.patch_name, "Clean Katana")
        self.assertFalse(self.model.is_dirty)
        self.assertTrue(self.model.safe_audition_enabled)
        self.assertLessEqual(self.model.get_param("preamp_volume"), 55)

    def test_parameter_change_and_dirty_tracking(self):
        dirty_states = []
        self.model.dirty_changed.connect(lambda d: dirty_states.append(d))

        self.model.set_param("preamp_gain", 85)
        self.assertEqual(self.model.get_param("preamp_gain"), 85)
        self.assertTrue(self.model.is_dirty)
        self.assertIn(True, dirty_states)

    def test_safe_audition_guard_clamping(self):
        # When guard is active, setting dangerously high volume is clamped to <= 55
        self.model.safe_audition_enabled = True
        self.model.set_param("preamp_volume", 100)
        self.assertLessEqual(self.model.get_param("preamp_volume"), 55)

        # In templates, volume is strictly clamped to safe_volume_ceiling (<= 42)
        self.model.create_new_profile("Test Safe", "lead")
        self.assertLessEqual(self.model.get_param("preamp_volume"), self.model.safe_volume_ceiling)

    def test_undo_redo(self):
        self.model.set_param("preamp_bass", 70)
        self.assertEqual(self.model.get_param("preamp_bass"), 70)

        self.model.set_param("preamp_bass", 90)
        self.assertEqual(self.model.get_param("preamp_bass"), 90)

        self.model.undo()
        self.assertEqual(self.model.get_param("preamp_bass"), 70)

        self.model.redo()
        self.assertEqual(self.model.get_param("preamp_bass"), 90)

    def test_create_new_profile_templates(self):
        templates = ["clean", "crunch", "lead", "ambient", "acoustic", "blank", "duplicate"]
        for tpl in templates:
            self.model.create_new_profile(f"My {tpl.title()}", tpl)
            self.assertEqual(self.model.patch_name, f"My {tpl.title()}")
            self.assertLessEqual(self.model.get_param("preamp_volume"), self.model.safe_volume_ceiling)

    def test_dynamic_chain_blocks_ordering(self):
        # Chain 1: Standard (In -> Boost -> Amp -> Mod -> EQ -> FX -> Delay -> Rev -> NS -> Master)
        self.model.set_param("chain_pattern", 0)
        blocks = self.model.get_active_chain_blocks()
        self.assertEqual(blocks[0], "in")
        self.assertEqual(blocks[-1], "master")
        self.assertIn("amp", blocks)
        self.assertIn("booster", blocks)

        # Chain 2-2: Mod-First (In -> Mod -> Boost -> Amp ...)
        self.model.set_param("chain_pattern", 4)
        b2 = self.model.get_active_chain_blocks()
        self.assertLess(b2.index("mod"), b2.index("booster"))
        self.assertLess(b2.index("booster"), b2.index("amp"))


if __name__ == "__main__":
    unittest.main()
