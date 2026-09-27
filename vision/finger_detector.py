import math


class FingerDetector:

    def __init__(self):

        self.finger_names = [
            "THUMB",
            "INDEX",
            "MIDDLE",
            "RING",
            "PINKY"
        ]

    def distance(self, point1, point2):

        return math.sqrt(
            (point1.x - point2.x) ** 2 +
            (point1.y - point2.y) ** 2 +
            (point1.z - point2.z) ** 2
        )

    def detect_fingers(self, hand_landmarks):

        fingers = {
            "THUMB": False,
            "INDEX": False,
            "MIDDLE": False,
            "RING": False,
            "PINKY": False
        }

        if hand_landmarks is None:
            return fingers

        # INDEX
        index_tip = hand_landmarks[8]
        index_pip = hand_landmarks[6]

        if index_tip.y < index_pip.y:
            fingers["INDEX"] = True

        # MIDDLE
        middle_tip = hand_landmarks[12]
        middle_pip = hand_landmarks[10]

        if middle_tip.y < middle_pip.y:
            fingers["MIDDLE"] = True

        # RING
        ring_tip = hand_landmarks[16]
        ring_pip = hand_landmarks[14]

        if ring_tip.y < ring_pip.y:
            fingers["RING"] = True

        # PINKY
        pinky_tip = hand_landmarks[20]
        pinky_pip = hand_landmarks[18]

        if pinky_tip.y < pinky_pip.y:
            fingers["PINKY"] = True

        # THUMB
        thumb_tip = hand_landmarks[4]
        thumb_ip = hand_landmarks[3]

        thumb_tip_distance = self.distance(
            thumb_tip,
            hand_landmarks[0]
        )

        thumb_ip_distance = self.distance(
            thumb_ip,
            hand_landmarks[0]
        )

        if thumb_tip_distance > thumb_ip_distance * 1.15:
            fingers["THUMB"] = True

        return fingers

    def count_fingers(self, fingers):

        return sum(
            fingers.values()
        )

    def get_finger_state(self, fingers):

        return [
            1 if fingers[name] else 0
            for name in self.finger_names
        ]