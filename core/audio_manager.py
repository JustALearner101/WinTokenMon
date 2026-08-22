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

# Audio stack initializes lazily on first playback so importing this module
# stays cheap and soundless setups never pay for mixer/WAV setup.
_audio_lock = threading.Lock()
_pygame = None
_mixer_ready = False


def _get_mixer():
    """Returns an initialized pygame module, or None when audio is unavailable."""
    global _pygame, _mixer_ready
    if _mixer_ready:
        return _pygame
    with _audio_lock:
        if _mixer_ready:
            return _pygame
        try:
            import pygame

            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            _pygame = pygame
            _mixer_ready = True
        except Exception:
            _pygame = None
            _mixer_ready = True  # resolution done; result is None
    return _pygame


def _synth_wav(
    segments: list[tuple], decay: float, amp: int, sine: bool = False, harmonic: float = 0.0
) -> bytes:
    """Renders 8-bit chime segments [(freq_hz_or_fn(t), duration_s), ...] into an in-memory WAV."""
    sample_rate = 44100
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        for spec, duration in segments:
            num_samples = int(sample_rate * duration)
            for i in range(num_samples):
                t = i / sample_rate
                freq = spec(t) if callable(spec) else spec
                val = math.sin(2 * math.pi * freq * t)
                val += harmonic * math.sin(4 * math.pi * freq * t)
                if not sine:
                    val = 1.0 if val >= 0 else -1.0
                frames.extend(
                    struct.pack("<h", int(val * amp * math.exp(-decay * (i / num_samples))))
                )
        wav.writeframes(frames)
    return buf.getvalue()


def _generate_levelup_wav() -> bytes:
    """Generates a pleasant retro 8-bit level-up arpeggio chime in WAV format in-memory."""
    return _synth_wav(
        [
            (523.25, 0.08),
            (659.25, 0.08),
            (783.99, 0.08),
            (1046.50, 0.12),
            (1318.51, 0.12),
            (1567.98, 0.35),
        ],
        decay=2.5,
        amp=8000,
    )


def _generate_achievement_wav() -> bytes:
    """Generates a triumphant 8-bit fanfare for achievement unlocks."""
    return _synth_wav(
        [
            (698.46, 0.08),
            (880.00, 0.08),
            (1046.50, 0.08),
            (1396.91, 0.12),
            (1760.00, 0.40),
        ],
        decay=2.2,
        amp=8500,
    )


def _generate_crunch_wav() -> bytes:
    """Generates a retro 8-bit cute chewing/crunch sound effect in WAV format in-memory."""
    return _synth_wav(
        [(320.0, 0.045), (180.0, 0.040), (420.0, 0.050), (220.0, 0.070)], decay=6.0, amp=7500
    )


def _generate_heart_wav() -> bytes:
    """Generates a pleasant 8-bit affection / petting chime in WAV format in-memory."""
    return _synth_wav([(783.99, 0.09), (1046.50, 0.28)], decay=3.0, amp=8000, sine=True)


def _generate_pokeball_bounce_wav() -> bytes:
    """Generates a retro 8-bit elastic bounce sound effect for Pokéball floor impact in WAV format."""
    return _synth_wav(
        [(480.0, 0.04), (320.0, 0.05), (560.0, 0.035), (380.0, 0.045)],
        decay=8.0,
        amp=8500,
        sine=True,
    )


def _generate_pokeball_release_wav() -> bytes:
    """Generates an 8-bit laser/beam release swoosh sound effect when Pokémon emerges from Pokéball."""
    duration = 0.28
    return _synth_wav(
        [(lambda t: 450.0 + (1350.0 * (t / duration) ** 1.8), duration)],
        decay=1.8,
        amp=6500,
        sine=True,
        harmonic=0.3,
    )


# SFX are synthesized once, on first playback, then cached as .wav files in APPDATA
_SFX_GENERATORS: dict[str, object] = {
    "levelup": _generate_levelup_wav,
    "achievement": _generate_achievement_wav,
    "crunch": _generate_crunch_wav,
    "heart": _generate_heart_wav,
    "pokeball_bounce": _generate_pokeball_bounce_wav,
    "pokeball_release": _generate_pokeball_release_wav,
}
SFX_WAV_PATHS: dict[str, str] = {}
_sfx_ready = False


def _ensure_sfx_files():
    global _sfx_ready
    if _sfx_ready:
        return
    with _audio_lock:
        if _sfx_ready:
            return
        for _name, _generator in _SFX_GENERATORS.items():
            _path = os.path.join(SFX_DIR, f"{_name}.wav")
            if not os.path.exists(_path) or os.path.getsize(_path) == 0:
                try:
                    with open(_path, "wb") as _f:
                        _f.write(_generator())
                except Exception:
                    pass
            SFX_WAV_PATHS[_name] = _path
        _sfx_ready = True


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


def _play_file(path: str, volume: float):
    pygame = _get_mixer()
    if pygame is None or not os.path.exists(path):
        return

    def _play():
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(max(0.0, min(1.0, volume)))
            sound.play()
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


def play_cry(species_id: int, volume: float = 0.6):
    """Asynchronously plays a Pokémon's cry."""
    if not _get_mixer() or species_id <= 0:
        return
    threading.Thread(target=lambda: _download_and_play_cry(species_id, volume), daemon=True).start()


def _download_and_play_cry(species_id: int, volume: float):
    path = get_cry_path(species_id)
    if path and os.path.exists(path):
        _play_file(path, volume)


def play_sfx(name: str, volume: float = 0.5):
    """Plays a cached SFX by name ('levelup', 'achievement', 'crunch', ...)."""
    _ensure_sfx_files()
    path = SFX_WAV_PATHS.get(name)
    if path:
        _play_file(path, volume)


def play_sfx_levelup(volume: float = 0.5):
    play_sfx("levelup", volume)


def play_sfx_achievement(volume: float = 0.55):
    play_sfx("achievement", volume)


def play_sfx_crunch(volume: float = 0.5):
    play_sfx("crunch", volume)


def play_sfx_heart(volume: float = 0.5):
    play_sfx("heart", volume)


def play_sfx_pokeball_bounce(volume: float = 0.5):
    play_sfx("pokeball_bounce", volume)


def play_sfx_pokeball_release(volume: float = 0.6):
    play_sfx("pokeball_release", volume)
