import math


class GestureClassifier:

    def distance(self, point1, point2):

        return math.sqrt(
            (point1.x - point2.x) ** 2 +
            (point1.y - point2.y) ** 2 +
            (point1.z - point2.z) ** 2
        )

    def classify(self, fingers, hand_landmarks=None):

        thumb = fingers["THUMB"]
        index = fingers["INDEX"]
        middle = fingers["MIDDLE"]
        ring = fingers["RING"]
        pinky = fingers["PINKY"]

        # PINCH
        if hand_landmarks is not None:

            thumb_tip = hand_landmarks[4]
            index_tip = hand_landmarks[8]

            pinch_distance = self.distance(
                thumb_tip,
                index_tip
            )

            palm_width = self.distance(
                hand_landmarks[5],
                hand_landmarks[17]
            )

            if palm_width > 0 and pinch_distance / palm_width < 0.42:
                return "PINCH"

        # OPEN PALM
        if (
            thumb
            and index
            and middle
            and ring
            and pinky
        ):
            return "OPEN_PALM"

        # FIST
        if (
            not thumb
            and not index
            and not middle
            and not ring
            and not pinky
        ):
            return "FIST"

        # POINT
        if (
            index
            and not middle
            and not ring
            and not pinky
        ):
            return "POINT"

        # TWO FINGER
        if (
            index
            and middle
            and not ring
            and not pinky
        ):
            return "TWO_FINGER"

        # THUMBS UP
        if (
            thumb
            and not index
            and not middle
            and not ring
            and not pinky
        ):
            return "THUMBS_UP"

        raised_finger_count = sum(fingers.values())
        if raised_finger_count == 3:
            return "THREE_FINGER"

        if raised_finger_count == 4:
            return "FOUR_FINGER"

        return "UNKNOWN"