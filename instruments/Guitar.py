import cv2
import mediapipe as mp
import pygame
import numpy as np
import time

# =====================================================
# 1. INITIALIZE PYGAME
# =====================================================

pygame.mixer.init(frequency=44100, size=-16, channels=2)

sample_rate = 44100

# Guitar open-string frequencies
# E A D G B E
frequencies = {
    "E_low": 82.41,
    "A": 110.00,
    "D": 146.83,
    "G": 196.00,
    "B": 246.94,
    "E_high": 329.63
}

sounds = {}

# Generate guitar-like sounds
for note, frequency in frequencies.items():

    duration = 0.8

    t = np.linspace(
        0,
        duration,
        int(sample_rate * duration),
        False
    )

    # Guitar-like tone using harmonics
    wave = (
        np.sin(2 * np.pi * frequency * t)
        + 0.5 * np.sin(2 * np.pi * frequency * 2 * t)
        + 0.25 * np.sin(2 * np.pi * frequency * 3 * t)
        + 0.12 * np.sin(2 * np.pi * frequency * 4 * t)
    )

    # Fade out
    envelope = np.exp(-3 * t)

    wave = wave * envelope

    # Normalize
    wave = wave / np.max(np.abs(wave))

    audio = (wave * 32767).astype(np.int16)

    stereo_audio = np.column_stack(
        (audio, audio)
    )

    sounds[note] = pygame.sndarray.make_sound(
        stereo_audio
    )


# =====================================================
# 2. MEDIAPIPE HAND LANDMARKER
# =====================================================

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

model_path = "hand_landmarker.task"

base_options = python.BaseOptions(
    model_asset_path=model_path
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7,
    running_mode=vision.RunningMode.VIDEO
)

detector = vision.HandLandmarker.create_from_options(
    options
)


# =====================================================
# 3. START WEBCAM
# =====================================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open webcam")
    exit()

# Guitar strings
strings = [
    ("E", 82.41),
    ("A", 110.00),
    ("D", 146.83),
    ("G", 196.00),
    ("B", 246.94),
    ("E", 329.63)
]

string_names = [
    "E",
    "A",
    "D",
    "G",
    "B",
    "E"
]

previous_string = None

start_time = time.time()


# =====================================================
# 4. MAIN LOOP
# =====================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Mirror webcam
    frame = cv2.flip(frame, 1)

    height, width, _ = frame.shape

    # =================================================
    # MEDIAPIPE
    # =================================================

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    timestamp_ms = int(
        (time.time() - start_time) * 1000
    )

    results = detector.detect_for_video(
        mp_image,
        timestamp_ms
    )


    # =================================================
    # DRAW GUITAR
    # =================================================

    guitar_x1 = 100
    guitar_x2 = width - 100

    guitar_y1 = 180
    guitar_y2 = height - 120

    # Guitar body
    cv2.rectangle(
        frame,
        (guitar_x1, guitar_y1),
        (guitar_x2, guitar_y2),
        (80, 80, 80),
        -1
    )

    # Guitar neck
    cv2.rectangle(
        frame,
        (150, 220),
        (width - 150, height - 170),
        (120, 120, 120),
        -1
    )


    # =================================================
    # DRAW 6 STRINGS
    # =================================================

    string_positions = []

    string_spacing = 45

    center_y = height // 2

    for i in range(6):

        y = center_y - 2 * string_spacing + i * string_spacing

        string_positions.append(y)

        cv2.line(
            frame,
            (150, y),
            (width - 150, y),
            (220, 220, 220),
            3
        )

        # String label
        cv2.putText(
            frame,
            string_names[i],
            (width - 130, y + 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )


    # =================================================
    # DETECT HAND
    # =================================================

    current_string = None

    if results.hand_landmarks:

        hand = results.hand_landmarks[0]

        # Index finger tip = landmark 8
        fingertip = hand[8]

        x = int(fingertip.x * width)
        y = int(fingertip.y * height)


        # =================================================
        # DRAW HAND LANDMARKS
        # =================================================

        for landmark in hand:

            lx = int(landmark.x * width)
            ly = int(landmark.y * height)

            cv2.circle(
                frame,
                (lx, ly),
                4,
                (0, 255, 0),
                -1
            )


        # Draw fingertip
        cv2.circle(
            frame,
            (x, y),
            12,
            (0, 0, 255),
            -1
        )


        # =================================================
        # CHECK STRING
        # =================================================

        if 150 <= x <= width - 150:

            for i, string_y in enumerate(
                string_positions
            ):

                if abs(y - string_y) < 15:

                    current_string = string_names[i]

                    break


    # =================================================
    # PLAY GUITAR SOUND
    # =================================================

    if current_string is not None:

        if current_string != previous_string:

            # Map E strings separately
            if current_string == "E":

                if string_positions.index(
                    min(
                        string_positions,
                        key=lambda p: abs(p - y)
                    )
                ) == 0:

                    sounds["E_low"].play()

                else:

                    sounds["E_high"].play()

            else:

                sounds[current_string].play()

            previous_string = current_string

    else:

        previous_string = None


    # =================================================
    # TITLE
    # =================================================

    cv2.putText(
        frame,
        "AIR GUITAR",
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 0, 255),
        3
    )


    # =================================================
    # NOTE DISPLAY
    # =================================================

    if current_string:

        cv2.putText(
            frame,
            "String: " + current_string,
            (20, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )


    cv2.putText(
        frame,
        "Move index finger across strings",
        (20, height - 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    # =================================================
    # DISPLAY
    # =================================================

    cv2.imshow(
        "Air Guitar",
        frame
    )


    # Press Q
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# =====================================================
# CLEANUP
# =====================================================

cap.release()

cv2.destroyAllWindows()

detector.close()

pygame.mixer.quit()