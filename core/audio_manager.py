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


def _generate_achievement_wav() -> bytes:
    """Generates a triumphant 8-bit fanfare for achievement unlocks."""
    sample_rate = 44100
    # Notes: F5 (698Hz), A5 (880Hz), C6 (1046Hz), F6 (1396Hz), A6 (1760Hz)
    notes = [
        (698.46, 0.08),
        (880.00, 0.08),
        (1046.50, 0.08),
        (1396.91, 0.12),
        (1760.00, 0.40),
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
                decay = math.exp(-2.2 * (i / num_samples))
                val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                sample = int(val * 8500 * decay)
                frames.extend(struct.pack("<h", sample))

        wav.writeframes(frames)
    return buf.getvalue()


def _generate_crunch_wav() -> bytes:
    """Generates a retro 8-bit cute chewing/crunch sound effect in WAV format in-memory."""
    sample_rate = 44100
    # Rapid dual-munch clicks
    crunches = [(320.0, 0.045), (180.0, 0.040), (420.0, 0.050), (220.0, 0.070)]
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        for freq, duration in crunches:
            num_samples = int(sample_rate * duration)
            for i in range(num_samples):
                t = i / sample_rate
                decay = math.exp(-6.0 * (i / num_samples))
                # Triangle/square hybrid wave for crisp crunch texture
                val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                sample = int(val * 7500 * decay)
                frames.extend(struct.pack("<h", sample))
        wav.writeframes(frames)
    return buf.getvalue()


def _generate_heart_wav() -> bytes:
    """Generates a pleasant 8-bit affection / petting chime in WAV format in-memory."""
    sample_rate = 44100
    notes = [(783.99, 0.09), (1046.50, 0.28)]  # G5 -> C6
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
                decay = math.exp(-3.0 * (i / num_samples))
                # Soft sine wave
                val = math.sin(2 * math.pi * freq * t)
                sample = int(val * 8000 * decay)
                frames.extend(struct.pack("<h", sample))
        wav.writeframes(frames)
    return buf.getvalue()


def _generate_pokeball_bounce_wav() -> bytes:
    """Generates a retro 8-bit elastic bounce sound effect for Pokéball floor impact in WAV format."""
    sample_rate = 44100
    bounces = [(480.0, 0.04), (320.0, 0.05), (560.0, 0.035), (380.0, 0.045)]
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        for freq, duration in bounces:
            num_samples = int(sample_rate * duration)
            for i in range(num_samples):
                t = i / sample_rate
                decay = math.exp(-8.0 * (i / num_samples))
                val = math.sin(2 * math.pi * freq * t)
                sample = int(val * 8500 * decay)
                frames.extend(struct.pack("<h", sample))
        wav.writeframes(frames)
    return buf.getvalue()


def _generate_pokeball_release_wav() -> bytes:
    """Generates an 8-bit laser/beam release swoosh sound effect when Pokémon emerges from Pokéball."""
    sample_rate = 44100
    duration = 0.28
    num_samples = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            # Ascending frequency sweep from 450Hz to 1800Hz
            freq = 450.0 + (1350.0 * (t / duration) ** 1.8)
            decay = math.exp(-1.8 * (i / num_samples))
            val = math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(4 * math.pi * freq * t)
            sample = int(val * 6500 * decay)
            frames.extend(struct.pack("<h", sample))
        wav.writeframes(frames)
    return buf.getvalue()


# Ensure default levelup.wav, achievement.wav, crunch.wav, heart.wav, and pokeball sfx exist
LEVELUP_WAV_PATH = os.path.join(SFX_DIR, "levelup.wav")
if not os.path.exists(LEVELUP_WAV_PATH) or os.path.getsize(LEVELUP_WAV_PATH) == 0:
    try:
        with open(LEVELUP_WAV_PATH, "wb") as f:
            f.write(_generate_levelup_wav())
    except Exception:
        pass

ACHIEVEMENT_WAV_PATH = os.path.join(SFX_DIR, "achievement.wav")
if not os.path.exists(ACHIEVEMENT_WAV_PATH) or os.path.getsize(ACHIEVEMENT_WAV_PATH) == 0:
    try:
        with open(ACHIEVEMENT_WAV_PATH, "wb") as f:
            f.write(_generate_achievement_wav())
    except Exception:
        pass

CRUNCH_WAV_PATH = os.path.join(SFX_DIR, "crunch.wav")
if not os.path.exists(CRUNCH_WAV_PATH) or os.path.getsize(CRUNCH_WAV_PATH) == 0:
    try:
        with open(CRUNCH_WAV_PATH, "wb") as f:
            f.write(_generate_crunch_wav())
    except Exception:
        pass

HEART_WAV_PATH = os.path.join(SFX_DIR, "heart.wav")
if not os.path.exists(HEART_WAV_PATH) or os.path.getsize(HEART_WAV_PATH) == 0:
    try:
        with open(HEART_WAV_PATH, "wb") as f:
            f.write(_generate_heart_wav())
    except Exception:
        pass

POKEBALL_BOUNCE_WAV_PATH = os.path.join(SFX_DIR, "pokeball_bounce.wav")
if not os.path.exists(POKEBALL_BOUNCE_WAV_PATH) or os.path.getsize(POKEBALL_BOUNCE_WAV_PATH) == 0:
    try:
        with open(POKEBALL_BOUNCE_WAV_PATH, "wb") as f:
            f.write(_generate_pokeball_bounce_wav())
    except Exception:
        pass

POKEBALL_RELEASE_WAV_PATH = os.path.join(SFX_DIR, "pokeball_release.wav")
if not os.path.exists(POKEBALL_RELEASE_WAV_PATH) or os.path.getsize(POKEBALL_RELEASE_WAV_PATH) == 0:
    try:
        with open(POKEBALL_RELEASE_WAV_PATH, "wb") as f:
            f.write(_generate_pokeball_release_wav())
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
    """Plays the level-up / evolution fanfare/jingle."""
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


def play_sfx_achievement(volume: float = 0.55):
    """Plays the triumphant achievement unlock chime."""
    if not _mixer_available:
        return

    def _play():
        try:
            if os.path.exists(ACHIEVEMENT_WAV_PATH):
                sound = pygame.mixer.Sound(ACHIEVEMENT_WAV_PATH)
                sound.set_volume(max(0.0, min(1.0, volume)))
                sound.play()
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


def play_sfx_crunch(volume: float = 0.5):
    """Plays the cute retro eating crunch sound effect."""
    if not _mixer_available:
        return

    def _play():
        try:
            if os.path.exists(CRUNCH_WAV_PATH):
                sound = pygame.mixer.Sound(CRUNCH_WAV_PATH)
                sound.set_volume(max(0.0, min(1.0, volume)))
                sound.play()
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


def play_sfx_heart(volume: float = 0.5):
    """Plays the pleasant affection / petting chime."""
    if not _mixer_available:
        return

    def _play():
        try:
            if os.path.exists(HEART_WAV_PATH):
                sound = pygame.mixer.Sound(HEART_WAV_PATH)
                sound.set_volume(max(0.0, min(1.0, volume)))
                sound.play()
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


def play_sfx_pokeball_bounce(volume: float = 0.5):
    """Plays the 8-bit elastic Pokéball floor bounce sound effect."""
    if not _mixer_available:
        return

    def _play():
        try:
            if os.path.exists(POKEBALL_BOUNCE_WAV_PATH):
                sound = pygame.mixer.Sound(POKEBALL_BOUNCE_WAV_PATH)
                sound.set_volume(max(0.0, min(1.0, volume)))
                sound.play()
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


def play_sfx_pokeball_release(volume: float = 0.6):
    """Plays the 8-bit energetic beam swoosh when Pokémon emerges from Pokéball."""
    if not _mixer_available:
        return

    def _play():
        try:
            if os.path.exists(POKEBALL_RELEASE_WAV_PATH):
                sound = pygame.mixer.Sound(POKEBALL_RELEASE_WAV_PATH)
                sound.set_volume(max(0.0, min(1.0, volume)))
                sound.play()
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()
