import hashlib
import json
import math
import os
import re
import struct
import sys

import numpy as np
from PyQt6 import QtCore, QtMultimedia, QtWidgets


SAMPLE_RATE = 44100
CACHE_VERSION = "v1"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "piano_cache", CACHE_VERSION)
NOTE_CACHE_DIR = os.path.join(CACHE_DIR, "notes")
MELODY_CACHE_DIR = os.path.join(CACHE_DIR, "melodies")

NOTE_ORDER = {
    "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
    "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11,
}

NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B",
]

FLATS = {
    "Db": "C#", "Eb": "D#", "Gb": "F#",
    "Ab": "G#", "Bb": "A#",
}

PIANO_NOTES = [
    f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"
    for midi in range(21, 109)
]

WHITE_KEYS = [note for note in PIANO_NOTES if "#" not in note]

NOTE_KEYS = {
    "C4": "A", "C#4": "W", "D4": "S", "D#4": "E", "E4": "D",
    "F4": "F", "F#4": "T", "G4": "G", "G#4": "Y", "A4": "H",
    "A#4": "U", "B4": "J", "C5": "K",
}

KEYS = {
    QtCore.Qt.Key.Key_A: "C4", QtCore.Qt.Key.Key_W: "C#4",
    QtCore.Qt.Key.Key_S: "D4", QtCore.Qt.Key.Key_E: "D#4",
    QtCore.Qt.Key.Key_D: "E4", QtCore.Qt.Key.Key_F: "F4",
    QtCore.Qt.Key.Key_T: "F#4", QtCore.Qt.Key.Key_G: "G4",
    QtCore.Qt.Key.Key_Y: "G#4", QtCore.Qt.Key.Key_H: "A4",
    QtCore.Qt.Key.Key_U: "A#4", QtCore.Qt.Key.Key_J: "B4",
    QtCore.Qt.Key.Key_K: "C5",
}

DEFAULT_TIMED_MELODY = """
0.000000 | D4(1.636362), F#5(0.272727)
0.272727 | F#4(0.272727), C#5(0.272727)
0.545454 | A4(0.272727), F#5(0.272727)
0.818181 | F#4(0.272727), C#5(0.272727)
1.090908 | A4(0.272727), F#5(0.272727)
1.363635 | F#4(0.272727), C#5(0.272727)
1.636362 | D4(1.636362), F#5(0.272727)
1.909089 | F#4(0.272727), C#5(0.272727)
2.181816 | A4(0.272727), F#5(0.272727)
2.454543 | F#4(0.272727), C#5(0.272727)
2.727270 | A4(0.272727), F#5(0.272727)
2.999997 | F#4(0.272727), C#5(0.272727)

3.272724 | B3(1.636362), B4(0.272727)
3.545451 | Eb4(0.272727), A4(0.272727)
3.818178 | F#4(0.272727), C#5(0.545454)
4.090905 | Eb4(0.272727)
4.363632 | F#4(0.272727), A4(0.272727)
4.636359 | Eb4(0.272727), B4(0.272727)

4.909086 | B3(1.636362), E5(0.272727)
5.181813 | Eb4(0.272727), Eb5(0.272727)
5.454540 | F#4(0.272727), E5(0.272727)
5.727267 | Eb4(0.272727), F#5(0.272727)
5.999994 | F#4(0.272727), Eb5(0.272727)
6.272721 | Eb4(0.272727), B4(0.272727)

6.545448 | G3(1.636362), F#5(0.272727)
6.818175 | B3(0.272727), B4(0.272727)
7.090902 | D4(0.272727), F#5(0.272727)
7.363629 | B3(0.272727), B4(0.272727)
7.636356 | D4(0.272727), F#5(0.272727)
7.909083 | B3(0.272727), B4(0.272727)

8.181810 | G3(1.636362), F#5(0.272727)
8.454537 | A#3(0.272727), A#4(0.272727)
8.727264 | D4(0.272727), F#5(0.272727)
8.999991 | A#3(0.272727), A#4(0.272727)
9.272718 | D4(0.272727), G5(0.545454)
9.545445 | A#3(0.272727), A#4(0.272727)

9.818172 | D4(1.636362), F#5(0.272727)
10.090899 | F#4(0.272727), D5(0.272727)
10.363626 | A4(0.272727), F#5(0.272727)
10.636353 | F#4(0.272727), D5(0.272727)
10.909080 | A4(0.272727), E5(0.272727)
11.181807 | F#4(0.272727), F#5(0.272727)

11.454534 | C#4(1.636362), E5(0.545454)
11.727261 | E4(0.272727)
11.999988 | A4(0.272727), D5(0.545454)
12.272715 | E4(0.272727)
12.545442 | A4(0.272727), C#5(0.545454)
12.818169 | E4(0.272727)
"""


def ensure_dirs():
    os.makedirs(NOTE_CACHE_DIR, exist_ok=True)
    os.makedirs(MELODY_CACHE_DIR, exist_ok=True)


def normalize_note(note):
    note = note.strip()
    note = note.replace("♭", "b").replace("♯", "#")

    match = re.fullmatch(r"([A-G](?:#|b)?)(-?\d*)", note)

    if not match:
        return note

    name, octave = match.groups()
    name = FLATS.get(name, name)

    if not octave:
        octave = "4"

    return f"{name}{octave}"


def note_to_midi(note):
    note = normalize_note(note)
    match = re.fullmatch(r"([A-G]#?)(-?\d+)", note)

    if not match:
        raise ValueError(f"Неверная нота: {note}")

    name, octave = match.groups()
    return 12 * (int(octave) + 1) + NOTE_ORDER[name]


def midi_to_note(midi):
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def note_to_freq(note):
    midi = note_to_midi(note)
    return 440 * 2 ** ((midi - 69) / 12)


def note_in_range(note):
    midi = note_to_midi(note)
    return 21 <= midi <= 108


def parse_timed_melody(text):
    result = []

    for line in text.splitlines():
        line = line.strip()

        if not line or "|" not in line:
            continue

        left, right = line.split("|", 1)

        try:
            delay = int(round(float(left.strip()) * 1000))
        except ValueError:
            continue

        found = re.findall(
            r"([A-G](?:#|b)?-?\d*)\(([\d.]+)\)",
            right,
        )

        notes = []
        durations = []

        for raw_note, raw_duration in found:
            note = normalize_note(raw_note)

            try:
                if not note_in_range(note):
                    continue
            except ValueError:
                continue

            notes.append(note)
            durations.append(int(round(float(raw_duration) * 1000)))

        if notes:
            result.append({
                "notes": notes,
                "delay": delay,
                "durations": durations,
            })

    return result


def synth_lengths(note_seconds, sustain):
    if note_seconds is None:
        note_len = 1.15 if sustain else 0.55
        release = 0.28 if sustain else 0.08
    else:
        note_len = max(0.04, float(note_seconds))
        release = 0.12 if sustain else 0.045

    return note_len, note_len + release


def envelope_array(t, note_len, total, sustain):
    attack = 0.006
    decay = 1.6 if sustain else 4.8
    main = np.exp(-decay * np.minimum(t, note_len))
    env = main.copy()

    attack_mask = t < attack
    env[attack_mask] = t[attack_mask] / attack

    release_mask = t > note_len

    if np.any(release_mask):
        tail = (total - t[release_mask]) / max(0.001, total - note_len)
        tail = np.clip(tail, 0, 1)
        env[release_mask] = main[release_mask] * tail * tail

    return env


def piano_wave(freq, t, detune, soft):
    if soft:
        harmonics = (
            (1, 1.00), (2, 0.20), (3, 0.075),
            (4, 0.024), (5, 0.010),
        )
    else:
        harmonics = (
            (1, 1.00), (2, 0.34), (3, 0.145),
            (4, 0.055), (5, 0.024), (6, 0.010),
        )

    value = np.zeros_like(t, dtype=np.float32)

    for number, power in harmonics:
        stretch = 1 + 0.00026 * number * number
        current = freq * number * stretch * detune
        value += power * np.sin(2 * np.pi * current * t)

    return value


def hammer_noise(freq, t, soft):
    volume = 0.008 if soft else 0.018
    result = np.zeros_like(t, dtype=np.float32)
    mask = t <= 0.012

    if not np.any(mask):
        return result

    tm = t[mask]
    power = 1 - tm / 0.012

    noise = np.sin(2 * np.pi * freq * 10.2 * tm)
    noise += 0.16 * np.sin(2 * np.pi * freq * 14.8 * tm)

    result[mask] = noise * power * volume
    return result


def generate_note_array(freq, sustain=False, soft=False, note_seconds=None):
    note_len, total = synth_lengths(note_seconds, sustain)
    samples = max(1, int(SAMPLE_RATE * total))
    t = np.arange(samples, dtype=np.float32) / SAMPLE_RATE

    base = piano_wave(freq, t, 1.0000, soft)

    left = base * 0.87
    left += piano_wave(freq, t, 0.9998, soft) * 0.13
    left += hammer_noise(freq, t, soft)

    right = base * 0.87
    right += piano_wave(freq, t, 1.0002, soft) * 0.13
    right += hammer_noise(freq, t, soft)

    amp = envelope_array(t, note_len, total, sustain)
    volume = 0.11 if soft else 0.15

    left = np.clip(left * amp * volume, -1, 1)
    right = np.clip(right * amp * volume, -1, 1)

    stereo = np.empty((samples, 2), dtype=np.int16)
    stereo[:, 0] = (left * 32767).astype(np.int16)
    stereo[:, 1] = (right * 32767).astype(np.int16)

    return stereo, total


def safe_note_name(note):
    return note.replace("#", "s").replace("-", "m")


def note_cache_path(note, sustain, soft):
    name = f"{safe_note_name(note)}_{int(sustain)}_{int(soft)}.raw"
    return os.path.join(NOTE_CACHE_DIR, name)


def sequence_hash(sequence, sustain, soft):
    payload = {
        "sequence": sequence,
        "sustain": sustain,
        "soft": soft,
        "sample_rate": SAMPLE_RATE,
        "cache_version": CACHE_VERSION,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    return hashlib.md5(raw).hexdigest()


def melody_cache_paths(sequence, sustain, soft):
    digest = sequence_hash(sequence, sustain, soft)
    raw_path = os.path.join(MELODY_CACHE_DIR, f"{digest}.raw")
    meta_path = os.path.join(MELODY_CACHE_DIR, f"{digest}.json")
    return raw_path, meta_path


def load_json_sequence(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    tempo = data.get("metadata", {}).get("tempo_bpm", 120) or 120
    beat_ms = 60000 / tempo
    sequence = []

    if "grouped" in data:
        for group in data["grouped"]:
            notes = []
            durations = []

            raw_notes = group.get("notes", [])
            raw_durations = group.get("durations_beats", [])

            for index, raw_note in enumerate(raw_notes):
                note = normalize_note(raw_note)

                try:
                    if not note_in_range(note):
                        continue
                except ValueError:
                    continue

                if index < len(raw_durations):
                    duration = raw_durations[index] * beat_ms
                else:
                    duration = 0.5 * beat_ms

                notes.append(note)
                durations.append(max(60, int(duration)))

            if not notes:
                continue

            delay = int(group.get("start_beats", 0) * beat_ms)

            sequence.append({
                "notes": notes,
                "delay": delay,
                "durations": durations,
            })

        return sequence

    if "flat" in data:
        delay = 0
        step = 380

        for raw_note in data["flat"]:
            note = normalize_note(raw_note)

            try:
                if not note_in_range(note):
                    continue
            except ValueError:
                continue

            sequence.append({
                "notes": [note],
                "delay": delay,
                "durations": [step],
            })
            delay += step

        return sequence

    raise ValueError("В JSON не найдены поля grouped или flat.")


def read_var_len(data, pos):
    value = 0

    while True:
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)

        if not byte & 0x80:
            break

    return value, pos


def tick_to_ms_func(tempo_events, ppq):
    tempo_events = sorted(tempo_events)

    if not tempo_events or tempo_events[0][0] != 0:
        tempo_events.insert(0, (0, 500000))

    def convert(tick):
        total_us = 0
        last_tick = 0
        current_tempo = tempo_events[0][1]

        for event_tick, tempo in tempo_events[1:]:
            if event_tick >= tick:
                break

            total_us += (event_tick - last_tick) * current_tempo / ppq
            last_tick = event_tick
            current_tempo = tempo

        total_us += (tick - last_tick) * current_tempo / ppq
        return total_us / 1000

    return convert


def parse_midi(path):
    with open(path, "rb") as file:
        data = file.read()

    if data[:4] != b"MThd":
        raise ValueError("Это не MIDI-файл.")

    header_len = struct.unpack(">I", data[4:8])[0]
    _, tracks, ppq = struct.unpack(">HHH", data[8:14])
    pos = 8 + header_len

    tempo_events = [(0, 500000)]
    note_events = []

    for _ in range(tracks):
        if data[pos:pos + 4] != b"MTrk":
            raise ValueError("Ошибка структуры MIDI-трека.")

        track_len = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        pos += 8
        end = pos + track_len
        tick = 0
        running = None
        active = {}

        while pos < end:
            delta, pos = read_var_len(data, pos)
            tick += delta
            status = data[pos]

            if status < 0x80:
                if running is None:
                    raise ValueError("Некорректный running status в MIDI.")
                status = running
            else:
                pos += 1
                running = status

            if status == 0xFF:
                meta_type = data[pos]
                pos += 1
                length, pos = read_var_len(data, pos)
                payload = data[pos:pos + length]
                pos += length

                if meta_type == 0x51 and length == 3:
                    tempo = int.from_bytes(payload, "big")
                    tempo_events.append((tick, tempo))

                continue

            if status in (0xF0, 0xF7):
                length, pos = read_var_len(data, pos)
                pos += length
                continue

            event_type = status & 0xF0
            channel = status & 0x0F

            if event_type in (0x80, 0x90):
                note = data[pos]
                velocity = data[pos + 1]
                pos += 2
                key = (channel, note)

                if event_type == 0x90 and velocity > 0:
                    active.setdefault(key, []).append(tick)
                else:
                    starts = active.get(key)

                    if starts:
                        start = starts.pop(0)

                        if tick > start:
                            note_events.append((start, tick, note))

            elif event_type in (0xA0, 0xB0, 0xE0):
                pos += 2
            elif event_type in (0xC0, 0xD0):
                pos += 1
            else:
                raise ValueError("Неподдерживаемое MIDI-событие.")

    if not note_events:
        raise ValueError("В MIDI не найдены ноты.")

    tick_to_ms = tick_to_ms_func(tempo_events, ppq)
    groups = {}

    for start, end, midi_note in note_events:
        if midi_note < 21 or midi_note > 108:
            continue

        delay = int(tick_to_ms(start))
        duration = max(60, int(tick_to_ms(end) - tick_to_ms(start)))
        note = midi_to_note(midi_note)

        groups.setdefault(delay, {"notes": [], "durations": []})
        groups[delay]["notes"].append(note)
        groups[delay]["durations"].append(duration)

    sequence = []

    for delay in sorted(groups):
        sequence.append({
            "notes": groups[delay]["notes"],
            "delay": delay,
            "durations": groups[delay]["durations"],
        })

    return sequence


class AudioMixer(QtCore.QIODevice):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.voices = []
        self.mutex = QtCore.QMutex()

    def add_voice(self, data, gain=1.0, tag="note"):
        if not data:
            return

        samples = np.frombuffer(data, dtype=np.int16).reshape(-1, 2)
        locker = QtCore.QMutexLocker(self.mutex)

        try:
            self.voices.append({
                "data": samples,
                "pos": 0,
                "gain": gain,
                "tag": tag,
            })

            while len(self.voices) > 64:
                index = 0

                for i, voice in enumerate(self.voices):
                    if voice["tag"] != "melody":
                        index = i
                        break

                del self.voices[index]

        finally:
            del locker

    def stop_tag(self, tag):
        locker = QtCore.QMutexLocker(self.mutex)

        try:
            self.voices = [
                voice for voice in self.voices
                if voice["tag"] != tag
            ]
        finally:
            del locker

    def clear(self):
        locker = QtCore.QMutexLocker(self.mutex)

        try:
            self.voices.clear()
        finally:
            del locker

    def readData(self, maxlen):
        frame_size = 4
        frames = maxlen // frame_size

        if frames <= 0:
            return b""

        output = np.zeros((frames, 2), dtype=np.float32)
        locker = QtCore.QMutexLocker(self.mutex)

        try:
            alive = []

            for voice in self.voices:
                data = voice["data"]
                pos = voice["pos"]
                remaining = len(data) - pos

                if remaining <= 0:
                    continue

                count = min(frames, remaining)
                chunk = data[pos:pos + count].astype(np.float32)
                output[:count] += chunk * voice["gain"]
                voice["pos"] = pos + count

                if voice["pos"] < len(data):
                    alive.append(voice)

            self.voices = alive

        finally:
            del locker

        output = np.tanh(output / 18000) * 18000
        output = np.clip(output, -32767, 32767).astype(np.int16)

        raw = output.tobytes()

        if len(raw) < maxlen:
            raw += b"\x00" * (maxlen - len(raw))

        return raw

    def writeData(self, data):
        return -1

    def bytesAvailable(self):
        return 16384 + super().bytesAvailable()


class PianoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = {}
        self.white_w = 42
        self.black_w = 28
        self.white_h = 320
        self.black_h = 195

        self.create_white_keys()
        self.create_black_keys()
        self.update_keys_geometry()

    def create_white_keys(self):
        for note in WHITE_KEYS:
            button = QtWidgets.QPushButton(self)
            key = NOTE_KEYS.get(note, "")
            text = f"\n\n\n\n\n\n\n{note}"

            if key:
                text += f"\n{key}"

            button.setText(text)
            button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            self.buttons[note] = button

    def create_black_keys(self):
        for note in PIANO_NOTES:
            if "#" not in note:
                continue

            button = QtWidgets.QPushButton(self)
            key = NOTE_KEYS.get(note, "")
            text = note

            if key:
                text += f"\n{key}"

            button.setText(text)
            button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            self.buttons[note] = button
            button.raise_()

    def set_key_size(self, white_w, white_h):
        self.white_w = white_w
        self.black_w = max(20, int(white_w * 0.66))
        self.white_h = white_h
        self.black_h = int(white_h * 0.62)
        self.update_keys_geometry()

    def update_keys_geometry(self):
        self.setFixedSize(
            len(WHITE_KEYS) * self.white_w,
            self.white_h + 15,
        )

        white_positions = {}

        for index, note in enumerate(WHITE_KEYS):
            white_positions[note] = index
            button = self.buttons[note]
            button.setGeometry(
                index * self.white_w,
                0,
                self.white_w,
                self.white_h,
            )
            button.setStyleSheet(self.white_style())

        for note in PIANO_NOTES:
            if "#" not in note:
                continue

            left_white = self.previous_white(note)

            if left_white not in white_positions:
                continue

            x_pos = (
                white_positions[left_white] * self.white_w
                + self.white_w
                - self.black_w // 2
            )

            button = self.buttons[note]
            button.setGeometry(x_pos, 0, self.black_w, self.black_h)
            button.setStyleSheet(self.black_style())
            button.raise_()

    def previous_white(self, note):
        previous = {
            "C#": "C", "D#": "D", "F#": "F",
            "G#": "G", "A#": "A",
        }

        return previous[note[:-1]] + note[-1]

    def white_style(self):
        font_size = max(10, min(16, self.white_w // 3))

        return f"""
        QPushButton {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #ffffff,
                stop:1 #d8d8d8
            );
            color: #111111;
            border: 1px solid #222222;
            font-size: {font_size}px;
            font-weight: bold;
        }}

        QPushButton:pressed {{
            background: #c8c8c8;
            padding-top: 8px;
        }}
        """

    def black_style(self):
        font_size = max(8, min(13, self.black_w // 3))

        return f"""
        QPushButton {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #222222,
                stop:1 #000000
            );
            color: #ffffff;
            border: 1px solid #000000;
            font-size: {font_size}px;
            font-weight: bold;
        }}

        QPushButton:pressed {{
            background: #444444;
            padding-top: 6px;
        }}
        """


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        ensure_dirs()

        self.setWindowTitle("Фортепиано")
        self.resize(1250, 650)
        self.setMinimumSize(900, 520)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        self.piano = PianoWidget()
        self.note_cache = {}
        self.clip_cache = {}
        self.already_scrolled = False

        self.melodies = {
            "Встроенная мелодия": parse_timed_melody(DEFAULT_TIMED_MELODY),
        }

        self.current_melody_name = "Встроенная мелодия"
        self.sequence = self.melodies[self.current_melody_name]

        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.setInterval(16)
        self.animation_timer.timeout.connect(self.update_animation)

        self.animation_clock = QtCore.QElapsedTimer()
        self.animation_sequence = []
        self.animation_index = 0
        self.animation_pressed = {}

        self.audio_format = QtMultimedia.QAudioFormat()
        self.audio_format.setSampleRate(SAMPLE_RATE)
        self.audio_format.setChannelCount(2)
        self.audio_format.setSampleFormat(
            QtMultimedia.QAudioFormat.SampleFormat.Int16
        )

        self.audio_device = QtMultimedia.QMediaDevices.defaultAudioOutput()
        self.mixer = AudioMixer(self)

        self.audio_sink = QtMultimedia.QAudioSink(
            self.audio_device,
            self.audio_format,
            self,
        )
        self.audio_sink.setBufferSize(32768)
        self.audio_sink.setVolume(0.8)

        self.mixer.open(QtCore.QIODevice.OpenModeFlag.ReadOnly)
        self.audio_sink.start(self.mixer)

        self.create_ui()
        self.preload_notes()
        self.prepare_current_melody()
        self.connect_buttons()

        QtWidgets.QApplication.instance().installEventFilter(self)

    def create_ui(self):
        title = QtWidgets.QLabel("Фортепиано")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
        QLabel {
            font-size: 28px;
            font-weight: bold;
            color: #f2f2f2;
        }
        """)

        info = QtWidgets.QLabel(
            "88 клавиш: A0 — C8 | "
            "A W S E D F T G Y H U J K | "
            "F11 — полный экран | Пробел — Sustain | Shift — Soft"
        )
        info.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #cfcfcf; font-size: 14px;")

        self.melody_combo = QtWidgets.QComboBox()
        self.melody_combo.addItems(self.melodies.keys())
        self.melody_combo.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidget(self.piano)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setMinimumHeight(360)
        self.scroll_area.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.scroll_area.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.melody_btn = QtWidgets.QPushButton("Сыграть выбранную")
        self.load_btn = QtWidgets.QPushButton("Загрузить MIDI/JSON")
        self.stop_btn = QtWidgets.QPushButton("Стоп")
        self.fullscreen_btn = QtWidgets.QPushButton("Во весь экран")

        self.sustain_box = QtWidgets.QPushButton("Sustain: OFF")
        self.soft_box = QtWidgets.QPushButton("Soft: OFF")

        for button in (self.sustain_box, self.soft_box):
            button.setCheckable(True)
            button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            button.setFixedWidth(110)
            button.setObjectName("toggleButton")

        self.sustain_box.toggled.connect(
            lambda checked: self.sustain_box.setText(
                "Sustain: ON" if checked else "Sustain: OFF"
            )
        )

        self.soft_box.toggled.connect(
            lambda checked: self.soft_box.setText(
                "Soft: ON" if checked else "Soft: OFF"
            )
        )

        self.volume_slider = QtWidgets.QSlider(
            QtCore.Qt.Orientation.Horizontal
        )
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        for widget in (
            self.melody_btn, self.load_btn,
            self.stop_btn, self.fullscreen_btn,
        ):
            widget.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        melody_layout = QtWidgets.QHBoxLayout()
        melody_layout.addWidget(QtWidgets.QLabel("Мелодия:"))
        melody_layout.addWidget(self.melody_combo)

        controls = QtWidgets.QHBoxLayout()
        controls.addWidget(self.melody_btn)
        controls.addWidget(self.load_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.fullscreen_btn)
        controls.addWidget(self.sustain_box)
        controls.addWidget(self.soft_box)
        controls.addWidget(QtWidgets.QLabel("Громкость:"))
        controls.addWidget(self.volume_slider)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(info)
        layout.addLayout(melody_layout)
        layout.addSpacing(10)
        layout.addWidget(self.scroll_area, stretch=1)
        layout.addSpacing(10)
        layout.addLayout(controls)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setStyleSheet("""
        QWidget {
            background: #181818;
            color: white;
        }

        QScrollArea {
            border: 1px solid #333333;
        }

        QComboBox {
            background: #2e2e2e;
            color: white;
            border: 1px solid #777777;
            border-radius: 6px;
            padding: 5px;
            font-size: 14px;
        }

        QPushButton {
            background: #3a3a3a;
            color: white;
            border: 1px solid #777777;
            border-radius: 8px;
            font-size: 14px;
            padding: 6px;
        }

        QPushButton:hover {
            background: #4a4a4a;
        }

        QPushButton:pressed {
            background: #222222;
        }

        QPushButton#toggleButton:checked {
            background: #7b4bb3;
            border: 1px solid #d8b4ff;
            color: white;
        }

        QLabel {
            font-size: 14px;
        }
        """)

        self.setCentralWidget(widget)

    def preload_notes(self):
        modes = [
            (False, False),
            (True, False),
            (False, True),
            (True, True),
        ]

        total = len(PIANO_NOTES) * len(modes)

        progress = QtWidgets.QProgressDialog(
            "Загрузка звуков фортепиано...",
            None,
            0,
            total,
            self,
        )
        progress.setWindowTitle("Загрузка")
        progress.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()

        done = 0

        for sustain, soft in modes:
            for note in PIANO_NOTES:
                self.load_or_generate_note(note, sustain, soft)
                done += 1

                progress.setLabelText(
                    f"Загрузка звука: {note} | "
                    f"{'Sustain' if sustain else 'Normal'} | "
                    f"{'Soft' if soft else 'Hard'}"
                )
                progress.setValue(done)
                QtWidgets.QApplication.processEvents()

        progress.close()

    def load_or_generate_note(self, note, sustain, soft):
        note = normalize_note(note)
        key = (note, sustain, soft)

        if key in self.note_cache:
            return self.note_cache[key]

        path = note_cache_path(note, sustain, soft)
        _, duration = synth_lengths(None, sustain)

        if os.path.exists(path):
            with open(path, "rb") as file:
                data = file.read()

            self.note_cache[key] = (data, duration)
            return data, duration

        freq = note_to_freq(note)
        raw, duration = generate_note_array(freq, sustain, soft)
        data = raw.tobytes()

        with open(path, "wb") as file:
            file.write(data)

        self.note_cache[key] = (data, duration)
        return data, duration

    def prepare_current_melody(self):
        self.get_rendered_sequence(show_progress=True)

    def get_clip_array(self, note, duration_ms, sustain, soft):
        note = normalize_note(note)
        duration_ms = int(round(duration_ms))
        key = (note, duration_ms, sustain, soft)

        if key in self.clip_cache:
            return self.clip_cache[key]

        freq = note_to_freq(note)
        clip, duration = generate_note_array(
            freq,
            sustain,
            soft,
            duration_ms / 1000,
        )
        self.clip_cache[key] = (clip, duration)
        return clip, duration

    def get_rendered_sequence(self, show_progress=False):
        sustain = self.sustain_box.isChecked()
        soft = self.soft_box.isChecked()

        raw_path, meta_path = melody_cache_paths(
            self.sequence,
            sustain,
            soft,
        )

        if os.path.exists(raw_path) and os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as file:
                meta = json.load(file)

            with open(raw_path, "rb") as file:
                data = file.read()

            return data, meta["duration"]

        data, duration = self.render_sequence(
            self.sequence,
            sustain,
            soft,
            show_progress,
        )

        with open(raw_path, "wb") as file:
            file.write(data)

        with open(meta_path, "w", encoding="utf-8") as file:
            json.dump({"duration": duration}, file)

        return data, duration

    def render_sequence(self, sequence, sustain, soft, show_progress=False):
        total_notes = sum(len(group["notes"]) for group in sequence)
        total_notes = max(1, total_notes)

        progress = None

        if show_progress:
            progress = QtWidgets.QProgressDialog(
                "Быстрый рендер мелодии...",
                None,
                0,
                total_notes,
                self,
            )
            progress.setWindowTitle("Рендер")
            progress.setWindowModality(
                QtCore.Qt.WindowModality.ApplicationModal
            )
            progress.setCancelButton(None)
            progress.setMinimumDuration(0)
            progress.show()

        clips = []
        total_frames = 0
        done = 0

        for group in sequence:
            start = int(group["delay"] / 1000 * SAMPLE_RATE)

            for index, note in enumerate(group["notes"]):
                duration_ms = group["durations"][min(
                    index,
                    len(group["durations"]) - 1,
                )]

                clip, _ = self.get_clip_array(
                    note,
                    duration_ms,
                    sustain,
                    soft,
                )

                clips.append((clip, start))
                total_frames = max(total_frames, start + len(clip))
                done += 1

                if progress:
                    progress.setLabelText(f"Подготовка: {note}")
                    progress.setValue(done)
                    QtWidgets.QApplication.processEvents()

        if total_frames <= 0:
            if progress:
                progress.close()

            return b"", 0

        mix = np.zeros((total_frames, 2), dtype=np.float32)

        for clip, start in clips:
            end = min(start + len(clip), total_frames)
            length = end - start

            if length > 0:
                mix[start:end] += clip[:length].astype(np.float32)

        peak = np.max(np.abs(mix))

        if peak > 0:
            mix *= min(1.0, 18000 / peak)

        mix = np.tanh(mix / 18000) * 18000
        result = np.clip(mix, -32767, 32767).astype(np.int16)

        if progress:
            progress.setValue(total_notes)
            progress.close()

        return result.tobytes(), total_frames / SAMPLE_RATE

    def connect_buttons(self):
        for note, button in self.piano.buttons.items():
            button.pressed.connect(lambda n=note: self.play_group([n]))

        self.melody_combo.currentTextChanged.connect(self.select_melody)
        self.melody_btn.clicked.connect(self.play_melody)
        self.load_btn.clicked.connect(self.load_custom_melody)
        self.stop_btn.clicked.connect(self.stop_all)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.volume_slider.valueChanged.connect(
            lambda value: self.audio_sink.setVolume(value / 100)
        )

    def select_melody(self, name):
        if name not in self.melodies:
            return

        self.current_melody_name = name
        self.sequence = self.melodies[name]

    def load_custom_melody(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Загрузить MIDI или JSON",
            BASE_DIR,
            "MIDI/JSON (*.mid *.midi *.json)",
        )

        if not path:
            return

        try:
            if path.lower().endswith(".json"):
                sequence = load_json_sequence(path)
            else:
                sequence = parse_midi(path)

            if not sequence:
                raise ValueError("В файле не найдено подходящих нот.")

            name = os.path.basename(path)
            self.melodies[name] = sequence

            self.melody_combo.blockSignals(True)
            self.melody_combo.addItem(name)
            self.melody_combo.setCurrentText(name)
            self.melody_combo.blockSignals(False)

            self.current_melody_name = name
            self.sequence = sequence
            self.prepare_current_melody()

            QtWidgets.QMessageBox.information(
                self,
                "Готово",
                f"Мелодия загружена:\n{name}",
            )

        except Exception as error:
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить файл:\n{error}",
            )

    def get_note_bytes(self, note):
        sustain = self.sustain_box.isChecked()
        soft = self.soft_box.isChecked()
        return self.load_or_generate_note(note, sustain, soft)

    def play_buffer(self, data, duration=None, melody=False):
        if melody:
            self.stop_melody()
            self.mixer.add_voice(data, gain=0.75, tag="melody")
        else:
            self.mixer.add_voice(data, gain=0.65, tag="note")

    def play_note(self, note):
        data, duration = self.get_note_bytes(note)
        self.play_buffer(data, duration)

    def flash_note(self, note, ms=110):
        note = normalize_note(note)
        button = self.piano.buttons.get(note)

        if not button:
            return

        button.setDown(True)
        QtCore.QTimer.singleShot(ms, lambda: button.setDown(False))

    def flash_group(self, notes):
        for note in notes:
            self.flash_note(note)

    def play_group(self, notes):
        if len(notes) == 1:
            self.play_note(notes[0])
        else:
            sequence = [{
                "notes": notes,
                "delay": 0,
                "durations": [400 for _ in notes],
            }]
            data, duration = self.render_sequence(
                sequence,
                self.sustain_box.isChecked(),
                self.soft_box.isChecked(),
                False,
            )
            self.play_buffer(data, duration)

        self.flash_group(notes)

    def play_melody(self):
        data, duration = self.get_rendered_sequence(show_progress=True)
        self.play_buffer(data, duration, melody=True)
        self.start_animation(self.sequence)

    def start_animation(self, sequence):
        self.stop_animation()

        self.animation_sequence = sorted(
            sequence,
            key=lambda group: group["delay"],
        )
        self.animation_index = 0
        self.animation_pressed = {}
        self.animation_clock.restart()
        self.animation_timer.start()

    def update_animation(self):
        elapsed = self.animation_clock.elapsed()

        while self.animation_index < len(self.animation_sequence):
            group = self.animation_sequence[self.animation_index]

            if group["delay"] > elapsed:
                break

            durations = group.get("durations") or [110]

            for index, note in enumerate(group["notes"]):
                note = normalize_note(note)
                button = self.piano.buttons.get(note)

                if not button:
                    continue

                duration = durations[min(index, len(durations) - 1)]
                press_time = max(70, min(150, duration))
                button.setDown(True)
                self.animation_pressed[note] = elapsed + press_time

            self.animation_index += 1

        for note, until in list(self.animation_pressed.items()):
            if elapsed < until:
                continue

            button = self.piano.buttons.get(note)

            if button:
                button.setDown(False)

            del self.animation_pressed[note]

        finished = self.animation_index >= len(self.animation_sequence)

        if finished and not self.animation_pressed:
            self.animation_timer.stop()

    def stop_animation(self):
        self.animation_timer.stop()

        for note in list(self.animation_pressed):
            button = self.piano.buttons.get(note)

            if button:
                button.setDown(False)

        self.animation_pressed.clear()
        self.animation_index = 0
        self.animation_sequence = []

    def stop_melody(self):
        self.stop_animation()
        self.mixer.stop_tag("melody")

    def stop_all(self):
        self.stop_animation()
        self.mixer.clear()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("Во весь экран")
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("Выйти из полного экрана")

    def resize_piano(self):
        if not hasattr(self, "scroll_area"):
            return

        view_w = self.scroll_area.viewport().width() - 20
        view_h = self.scroll_area.viewport().height() - 20

        white_w = int(view_w / len(WHITE_KEYS))
        white_w = max(30, min(64, white_w))

        white_h = int(white_w * 8.4)
        white_h = max(270, min(560, white_h, int(view_h * 0.92)))

        self.piano.set_key_size(white_w, white_h)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QtCore.QTimer.singleShot(0, self.resize_piano)

    def showEvent(self, event):
        super().showEvent(event)
        self.resize_piano()

        if self.already_scrolled:
            return

        self.already_scrolled = True

        button = self.piano.buttons.get("C4")

        if not button:
            return

        x_pos = button.x()
        half_width = self.scroll_area.viewport().width() // 2
        self.scroll_area.horizontalScrollBar().setValue(x_pos - half_width)

    def eventFilter(self, source, event):
        if event.type() != QtCore.QEvent.Type.KeyPress:
            return False

        if event.isAutoRepeat():
            return True

        if event.key() == QtCore.Qt.Key.Key_F11:
            self.toggle_fullscreen()
            return True

        if event.key() == QtCore.Qt.Key.Key_Space:
            self.sustain_box.setChecked(not self.sustain_box.isChecked())
            return True

        if event.key() == QtCore.Qt.Key.Key_Shift:
            self.soft_box.setChecked(not self.soft_box.isChecked())
            return True

        note = KEYS.get(event.key())

        if note:
            self.play_group([note])
            return True

        return False

    def closeEvent(self, event):
        self.audio_sink.stop()
        self.mixer.close()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())