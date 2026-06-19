import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from practice.session import PracticeSession, note_name


class PracticeSessionTest(unittest.TestCase):
    def test_note_name_converts_midi_number(self):
        self.assertEqual(note_name(60), "C4")
        self.assertEqual(note_name(61), "C#4")

    def test_song_listing_and_note_progress(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            songs_dir = Path(temp_dir)
            (songs_dir / "scale.json").write_text(
                json.dumps({"title": "Scale", "notes": [60, 62]}),
                encoding="utf-8",
            )

            session = PracticeSession(songs_dir)
            self.assertEqual(session.list_songs(), [{"id": "scale", "title": "Scale"}])

            session.load_song("scale")
            session.start()
            self.assertEqual(
                session.get_progress(),
                {
                    "title": "Scale",
                    "index": 0,
                    "total": 2,
                    "prev": None,
                    "current": "C4",
                    "next": "D4",
                    "mistakes": 0,
                },
            )

            wrong = session.handle_note(SimpleNamespace(type="note_on", note=61), 0)
            self.assertEqual(wrong, {"correct": False, "complete": False, "mistakes": 1})
            self.assertEqual(session.get_progress()["index"], 0)
            self.assertEqual(session.get_progress()["mistakes"], 1)

            correct = session.handle_note(SimpleNamespace(type="note_on", note=60), 1)
            self.assertEqual(correct, {"correct": True, "complete": False, "mistakes": 1})
            self.assertEqual(session.get_progress()["current"], "D4")

            complete = session.handle_note(SimpleNamespace(type="note_on", note=62), 2)
            self.assertEqual(complete, {"correct": True, "complete": True, "mistakes": 1})
            self.assertFalse(session.is_active)
            self.assertEqual(
                session.get_result(),
                {"title": "Scale", "mistakes": 1, "completed_notes": 2, "total": 2},
            )


if __name__ == "__main__":
    unittest.main()
