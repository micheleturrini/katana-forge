"""Tests for Gemini AI Tone preset prompt engine and JSON parser."""

import unittest
from katana_modern.core.patch_model import KatanaPatchModel
from katana_modern.core.ai_preset_engine import (
    build_gemini_prompt,
    parse_gemini_preset,
    apply_ai_preset_to_model,
)


class TestAiPresetEngine(unittest.TestCase):
    def test_build_gemini_prompt(self):
        prompt = build_gemini_prompt("Comfortably Numb - Solo", "Fender Stratocaster with single coils")
        self.assertIn("Comfortably Numb - Solo", prompt)
        self.assertIn("Fender Stratocaster", prompt)
        self.assertIn("JSON", prompt)
        self.assertIn("amp", prompt)
        self.assertIn("booster", prompt)

    def test_parse_and_apply_ai_preset(self):
        sample_json = """
        ```json
        {
          "katana_ai_preset": {
            "name": "Pink Solo",
            "amp": {
              "type": "Lead",
              "gain": 70,
              "bass": 50,
              "middle": 65,
              "treble": 60,
              "presence": 55,
              "volume": 42
            },
            "booster": {
              "enabled": true,
              "type": "Blues Driver",
              "drive": 45,
              "tone": 50
            },
            "delay": {
              "enabled": true,
              "type": "Analog Delay",
              "time_ms": 420,
              "feedback": 35,
              "level": 30
            }
          }
        }
        ```
        """
        success, data, err = parse_gemini_preset(sample_json)
        self.assertTrue(success)
        self.assertIsNotNone(data)
        self.assertEqual(data.get("name"), "Pink Solo")

        model = KatanaPatchModel()
        ok = apply_ai_preset_to_model(data, model, safe_guard=True)
        self.assertTrue(ok)
        self.assertEqual(model.patch_name, "Pink Solo")
        self.assertEqual(model.get_param("preamp_gain"), 70)
        self.assertEqual(model.get_param("booster_sw"), 1)
        self.assertEqual(model.get_param("delay1_sw"), 1)
        self.assertLessEqual(model.get_param("preamp_volume"), model.safe_volume_ceiling)


if __name__ == "__main__":
    unittest.main()
