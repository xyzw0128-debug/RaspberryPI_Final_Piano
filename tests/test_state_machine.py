import unittest

from core.state_machine import Event, State, StateMachine


class PracticeOnlyStateMachineTest(unittest.TestCase):
    def test_states_are_practice_only(self):
        self.assertEqual([state.value for state in State], ["sleep", "idle", "practice"])
        self.assertFalse(hasattr(State, "RECORDING"))

    def test_events_exclude_recording_commands(self):
        self.assertEqual(
            [event.value for event in Event],
            [
                "pir_detected",
                "cmd_wake",
                "cmd_sleep",
                "cmd_start_practice",
                "cmd_stop_practice",
                "practice_complete",
                "practice_start_failed",
            ],
        )
        self.assertFalse(hasattr(Event, "CMD_START_RECORD"))
        self.assertFalse(hasattr(Event, "CMD_STOP_RECORD"))

    def test_practice_flow(self):
        sm = StateMachine()

        self.assertEqual(sm.handle(Event.CMD_WAKE), (State.IDLE, True))
        self.assertEqual(sm.handle(Event.CMD_START_PRACTICE), (State.PRACTICE, True))
        self.assertEqual(sm.handle(Event.PIR_DETECTED), (State.PRACTICE, False))
        self.assertEqual(sm.handle(Event.CMD_STOP_PRACTICE), (State.IDLE, True))
        self.assertEqual(sm.handle(Event.CMD_SLEEP), (State.SLEEP, True))


if __name__ == "__main__":
    unittest.main()
