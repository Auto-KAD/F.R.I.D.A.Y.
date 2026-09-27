from collections import deque


class GestureStabilizer:

    def __init__(self, required_frames=6):

        self.required_frames = required_frames

        self.gesture_history = deque(
            maxlen=required_frames
        )

        self.confirmed_gesture = "UNKNOWN"

    def update(self, gesture):

        self.gesture_history.append(gesture)

        if len(self.gesture_history) < self.required_frames:
            return "UNKNOWN"

        first_gesture = self.gesture_history[0]

        if all(
            current == first_gesture
            for current in self.gesture_history
        ):

            self.confirmed_gesture = first_gesture

        return self.confirmed_gesture

    def reset(self):

        self.gesture_history.clear()

        self.confirmed_gesture = "UNKNOWN"

    def get_confirmed_gesture(self):

        return self.confirmed_gesture