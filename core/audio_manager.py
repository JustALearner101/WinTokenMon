"""
Audio manager for WinTokenMon — handles Pokémon cries and sound effects.
Uses pygame.mixer for .ogg / .wav playback. Gracefully degrades if audio device is missing.
"""

import io
import math
import os
import struct
import threading
import urllib.request
import wave

DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "WinTokenMon")
CRIES_DIR = os.path.join(DATA_DIR, "cries")
SFX_DIR = os.path.join(DATA_DIR, "sfx")
os.makedirs(CRIES_DIR, exist_ok=True)
os.makedirs(SFX_DIR, exist_ok=True)

CRY_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/{species_id}.ogg"
)

_mixer_available = False
try:
    import pygame

    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    _mixer_available = True
except Exception:
    _mixer_available = False


def _generate_levelup_wav() -> bytes:
    """Generates a pleasant retro 8-bit level-up arpeggio chime in WAV format in-memory."""
    sample_rate = 44100
    # Notes: C5 (523Hz), E5 (659Hz), G5 (784Hz), C6 (1046Hz), E6 (1318Hz), G6 (1568Hz)
    notes = [
        (523.25, 0.08),
        (659.25, 0.08),
        (783.99, 0.08),
        (1046.50, 0.12),
        (1318.51, 0.12),
        (1567.98, 0.35),
    ]

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        frames = bytearray()
        for freq, duration in notes:
            num_samples = int(sample_rate * duration)
            for i in range(num_samples):
                t = i / sample_rate
                # Square wave with envelope decay
                decay = math.exp(-2.5 * (i / num_samples))
                val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                sample = int(val * 8000 * decay)
                frames.extend(struct.pack("<h", sample))

        wav.writeframes(frames)
    return buf.getvalue()


# Ensure default levelup.wav exists in sfx dir
LEVELUP_WAV_PATH = os.path.join(SFX_DIR, "levelup.wav")
if not os.path.exists(LEVELUP_WAV_PATH) or os.path.getsize(LEVELUP_WAV_PATH) == 0:
    try:
        with open(LEVELUP_WAV_PATH, "wb") as f:
            f.write(_generate_levelup_wav())
    except Exception:
        pass


def get_cry_path(species_id: int) -> str | None:
    """Returns local path to cached .ogg Pokémon cry, downloading if needed."""
    if species_id <= 0:
        return None
    local_path = os.path.join(CRIES_DIR, f"{species_id}.ogg")
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return local_path

    try:
        url = CRY_URL_TEMPLATE.format(species_id=species_id)
        req = urllib.request.Request(url, headers={"User-Agent": "WinTokenMon/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            if len(data) > 0:
                with open(local_path, "wb") as out_file:
                    out_file.write(data)
                return local_path
    except Exception:
        pass
    return None


def play_cry(species_id: int, volume: float = 0.6):
    """Asynchronously plays a Pokémon's cry."""
    if not _mixer_available or species_id <= 0:
        return

    def _play():
        path = get_cry_path(species_id)
        if not path or not os.path.exists(path):
            return
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(max(0.0, min(1.0, volume)))
            sound.play()
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


def play_sfx_levelup(volume: float = 0.5):
    """Plays the level-up / evolution fanfar/jingle."""
    if not _mixer_available:
        return

    def _play():
        try:
            if os.path.exists(LEVELUP_WAV_PATH):
                sound = pygame.mixer.Sound(LEVELUP_WAV_PATH)
                sound.set_volume(max(0.0, min(1.0, volume)))
                sound.play()
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()
