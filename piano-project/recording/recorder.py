# recording/recorder.py

import os
import re
import time
import threading
from datetime import datetime

import mido


class Recorder:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.is_recording = False
        self._events = []  # [(msg, timestamp), ...]
        self._start_time = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            self._events = []
            self._start_time = time.time()
            self.is_recording = True

    def handle_note(self, msg, ts):
        """midi_io.on_note 콜백으로 등록"""
        if not self.is_recording:
            return
        with self._lock:
            self._events.append((msg, ts))

    def stop(self, filename=None):
        with self._lock:
            self.is_recording = False
            events = self._events
            start_time = self._start_time

        filename = self._resolve_filename(filename)
        path = os.path.join(self.output_dir, filename)
        self._save(path, events, start_time)
        return filename

    def _resolve_filename(self, filename):
        if not filename:
            filename = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = re.sub(r"[^A-Za-z0-9_\-가-힣]", "_", filename)

        if not filename.endswith(".mid"):
            filename += ".mid"
        return filename

    def _save(self, path, events, start_time):
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        tempo = mido.bpm2tempo(120)
        track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))

        last_time = start_time or time.time()
        for msg, ts in events:
            delta_sec = max(0, ts - last_time)
            delta_ticks = int(mido.second2tick(delta_sec, mid.ticks_per_beat, tempo))
            track.append(msg.copy(time=delta_ticks))
            last_time = ts

        mid.save(path)

    def list_recordings(self):
        files = [f for f in os.listdir(self.output_dir) if f.endswith(".mid")]
        files.sort(reverse=True)
        return files