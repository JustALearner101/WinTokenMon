"""
Unit tests for audio generation, synthesizer, and animation cadence formulas.
"""

import io
import math
import os
import unittest
import wave

from PIL import Image

from core.audio_manager import _generate_levelup_wav
from core.poke_api import STARTER_GENERATIONS, get_sprite_path
from ui.desktop_pet import create_egg_image


class TestAudioAndAnimations(unittest.TestCase):
    def test_levelup_wav_synthesizer(self):
        """Tests that the in-memory 8-bit levelup chime produces a valid WAV audio file."""
        wav_bytes = _generate_levelup_wav()
        self.assertTrue(len(wav_bytes) > 0)
        self.assertTrue(wav_bytes.startswith(b"RIFF"))

        # Verify parsing with wave module
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as w:
            self.assertEqual(w.getnchannels(), 1)  # Mono
            self.assertEqual(w.getsampwidth(), 2)  # 16-bit PCM
            self.assertEqual(w.getframerate(), 44100)  # 44.1kHz
            self.assertTrue(w.getnframes() > 1000)

    def test_walking_cadence_step_hop_formula(self):
        """Tests footstep hop vertical displacement stays grounded and bounds within 6px."""
        for step in range(30):
            hop_y = -abs(int(6.0 * math.sin(step * 0.55)))
            sway_x = int(2.5 * math.sin(step * 0.27))

            # Hop must always be upwards (negative or zero)
            self.assertLessEqual(hop_y, 0)
            self.assertGreaterEqual(hop_y, -6)

            # Sway must stay within +-3px
            self.assertGreaterEqual(sway_x, -3)
            self.assertLessEqual(sway_x, 3)

    def test_bounce_damped_sine_decay(self):
        """Tests that damped sine bounce starts high and settles to zero."""
        amp = 14
        total_frames = 15

        displacements = []
        for i in range(total_frames):
            t = i / total_frames
            y = -int(amp * math.sin(math.pi * t) * math.exp(-2.5 * t))
            displacements.append(y)

        # Initial peak should be negative (upwards)
        self.assertLess(min(displacements), 0)
        # Final value near end approaches 0
        self.assertAlmostEqual(displacements[-1], 0, delta=2)

    def test_bundled_starter_sprites_exist(self):
        """Tests that all 30 curated starter Pokémon sprites exist in assets/sprites."""
        for gen_name, species_ids in STARTER_GENERATIONS.items():
            for sid in species_ids:
                path = get_sprite_path(sid)
                self.assertTrue(bool(path), f"Sprite for #{sid} in {gen_name} should resolve.")
                self.assertTrue(os.path.exists(path), f"Sprite file for #{sid} must exist.")
                self.assertGreater(os.path.getsize(path), 0)

    def test_create_egg_image_returns_valid_image(self):
        """Tests that create_egg_image returns a valid PIL Image with expected dimensions and RGBA mode."""
        egg_img = create_egg_image((110, 110))
        self.assertIsNotNone(egg_img)
        self.assertIsInstance(egg_img, Image.Image)
        self.assertEqual(egg_img.size, (110, 110))
        self.assertEqual(egg_img.mode, "RGBA")

    def test_create_pokeball_image_returns_valid_image(self):
        """Tests that create_pokeball_image generates valid RGBA PIL Images for closed and open states."""
        from ui.desktop_pet import create_pokeball_image

        ball_closed = create_pokeball_image((64, 64), is_open=False)
        self.assertIsNotNone(ball_closed)
        self.assertEqual(ball_closed.size, (64, 64))
        self.assertEqual(ball_closed.mode, "RGBA")

        ball_open = create_pokeball_image((64, 64), is_open=True)
        self.assertIsNotNone(ball_open)
        self.assertEqual(ball_open.size, (64, 64))
        self.assertEqual(ball_open.mode, "RGBA")

    def test_pokeball_bounce_and_release_wav_synthesizers(self):
        """Tests that in-memory Pokéball audio synthesizers produce valid RIFF WAV audio data."""
        from core.audio_manager import (
            _generate_crunch_wav,
            _generate_heart_wav,
            _generate_pokeball_bounce_wav,
            _generate_pokeball_release_wav,
        )

        for gen_fn in (
            _generate_crunch_wav,
            _generate_heart_wav,
            _generate_pokeball_bounce_wav,
            _generate_pokeball_release_wav,
        ):
            data = gen_fn()
            self.assertTrue(len(data) > 0)
            self.assertTrue(data.startswith(b"RIFF"))
            buf = io.BytesIO(data)
            with wave.open(buf, "rb") as w:
                self.assertEqual(w.getnchannels(), 1)
                self.assertEqual(w.getsampwidth(), 2)
                self.assertEqual(w.getframerate(), 44100)
                self.assertTrue(w.getnframes() > 100)


if __name__ == "__main__":
    unittest.main()
