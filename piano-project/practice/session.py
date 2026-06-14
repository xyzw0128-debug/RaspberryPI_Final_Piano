# practice/session.py

import os
import json

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_name(midi_note):
    """MIDI note number -> 음이름 (예: 60 -> 'C4')"""
    name = NOTE_NAMES[midi_note % 12]
    octave = midi_note // 12 - 1
    return f"{name}{octave}"


class PracticeSession:
    def __init__(self, songs_dir):
        self.songs_dir = songs_dir
        self.song = None
        self.index = 0
        self.is_active = False

    def list_songs(self):
        """곡 목록: [{"id": "twinkle", "title": "Twinkle Twinkle Little Star"}, ...]"""
        if not os.path.isdir(self.songs_dir):
            return []

        result = []
        for f in os.listdir(self.songs_dir):
            if not f.endswith(".json"):
                continue
            song_id = f[:-5]
            try:
                with open(os.path.join(self.songs_dir, f), encoding="utf-8") as fp:
                    data = json.load(fp)
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(data, dict):
                continue
            result.append({"id": song_id, "title": data.get("title", song_id)})
        return result

    def load_song(self, song_id):
        if not song_id:
            raise ValueError("song_id가 필요합니다.")

        safe_song_id = os.path.basename(song_id)
        path = os.path.join(self.songs_dir, f"{safe_song_id}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"곡 파일을 찾을 수 없습니다: {safe_song_id}")

        with open(path, encoding="utf-8") as fp:
            self.song = json.load(fp)

        notes = self.song.get("notes")
        if not isinstance(notes, list) or not notes:
            raise ValueError("곡 notes는 비어 있지 않은 리스트여야 합니다.")

        self.index = 0
        self.is_active = False

    def start(self):
        if not self.song:
            raise RuntimeError("곡이 로드되지 않았습니다.")
        self.index = 0
        self.is_active = True

    def stop(self):
        self.is_active = False

    def handle_note(self, msg, ts):
        """
        midi_io.on_note 콜백으로 등록.
        반환: {"correct": bool, "complete": bool} 또는 None (비활성/무시)
        """
        if not self.is_active:
            return None
        if msg.type != "note_on":
            return None

        expected = self.song["notes"][self.index]
        correct = (msg.note == expected)

        if correct:
            self.index += 1
            complete = self.index >= len(self.song["notes"])
            if complete:
                self.is_active = False
            return {"correct": True, "complete": complete}

        # 틀린 음 - 진행도는 유지, 오답 피드백만 반환 (범위 밖: 리셋/채점 없음)
        return {"correct": False, "complete": False}

    def get_progress(self):
        if not self.song:
            return None
        notes = self.song["notes"]
        total = len(notes)
        idx = self.index

        return {
            "title": self.song.get("title", "Unknown"),
            "index": idx,
            "total": total,
            "prev": note_name(notes[idx - 1]) if idx > 0 else None,
            "current": note_name(notes[idx]) if idx < total else None,
            "next": note_name(notes[idx + 1]) if idx + 1 < total else None,
        }
