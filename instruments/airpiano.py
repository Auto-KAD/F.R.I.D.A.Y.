import cv2
import mediapipe as mp
import pygame
import numpy as np
import time

# =========================================================
# 1. INITIALIZE PYGAME SOUND
# =========================================================

pygame.mixer.init(frequency=44100, size=-16, channels=2)

sample_rate = 44100

# Piano note frequencies
frequencies = {
    "C": 261.63,
    "D": 293.66,
    "E": 329.63,
    "F": 349.23,
    "G": 392.00,
    "A": 440.00,
    "B": 493.88
}

# Create sounds
sounds = {}

for note, frequency in frequencies.items():

    duration = 0.5

    t = np.linspace(
        0,
        duration,
        int(sample_rate * duration),
        False
    )

    # Generate sine wave
    wave = np.sin(2 * np.pi * frequency * t)

    # Convert to 16-bit audio
    audio = (wave * 32767).astype(np.int16)

    # Stereo audio
    stereo_audio = np.column_stack((audio, audio))

    sounds[note] = pygame.sndarray.make_sound(stereo_audio)


# =========================================================
# 2. INITIALIZE MEDIAPIPE HAND LANDMARKER
# =========================================================

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Path to model
model_path = "hand_landmarker.task"

# MediaPipe model options
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

# Create hand detector
detector = vision.HandLandmarker.create_from_options(options)


# =========================================================
# 3. START WEBCAM
# =========================================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

# Piano keys
keys = ["C", "D", "E", "F", "G", "A", "B"]

# Previous key
previous_key = None

# Frame timestamp
start_time = time.time()


# =========================================================
# 4. MAIN LOOP
# =========================================================

while True:

    ret, frame = cap.read()

    if not ret:
        print("ERROR: Could not read webcam frame.")
        break

    # Mirror webcam
    frame = cv2.flip(frame, 1)

    height, width, _ = frame.shape

    # =====================================================
    # MEDIAPIPE DETECTION
    # =====================================================

    # OpenCV uses BGR
    # MediaPipe requires RGB
    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # Convert to MediaPipe Image
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    # Timestamp in milliseconds
    timestamp_ms = int(
        (time.time() - start_time) * 1000
    )

    # Detect hand
    results = detector.detect_for_video(
        mp_image,
        timestamp_ms
    )


    # =====================================================
    # DRAW PIANO
    # =====================================================

    key_width = width // 7
    key_height = 180

    piano_y = height - key_height

    current_key = None

    for i, key in enumerate(keys):

        x1 = i * key_width
        x2 = (i + 1) * key_width

        # Normal white key
        cv2.rectangle(
            frame,
            (x1, piano_y),
            (x2, height),
            (255, 255, 255),
            -1
        )

        # Border
        cv2.rectangle(
            frame,
            (x1, piano_y),
            (x2, height),
            (0, 0, 0),
            3
        )

        # Key name
        text_x = x1 + key_width // 2 - 10

        cv2.putText(
            frame,
            key,
            (text_x, height - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2
        )


    # =====================================================
    # PROCESS HAND
    # =====================================================

    if results.hand_landmarks:

        # First detected hand
        hand_landmarks = results.hand_landmarks[0]

        # -------------------------------------------------
        # INDEX FINGER TIP = LANDMARK 8
        # -------------------------------------------------

        fingertip = hand_landmarks[8]

        x = int(fingertip.x * width)
        y = int(fingertip.y * height)

        # -------------------------------------------------
        # DRAW HAND LANDMARKS
        # -------------------------------------------------

        # Draw all landmark points
        for landmark in hand_landmarks:

            lx = int(landmark.x * width)
            ly = int(landmark.y * height)

            cv2.circle(
                frame,
                (lx, ly),
                4,
                (0, 255, 0),
                -1
            )

        # Hand connections
        connections = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),

            (0, 5),
            (5, 6),
            (6, 7),
            (7, 8),

            (5, 9),
            (9, 10),
            (10, 11),
            (11, 12),

            (9, 13),
            (13, 14),
            (14, 15),
            (15, 16),

            (13, 17),
            (17, 18),
            (18, 19),
            (19, 20),

            (0, 17)
        ]

        for start, end in connections:

            x1 = int(hand_landmarks[start].x * width)
            y1 = int(hand_landmarks[start].y * height)

            x2 = int(hand_landmarks[end].x * width)
            y2 = int(hand_landmarks[end].y * height)

            cv2.line(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

        # -------------------------------------------------
        # DRAW FINGERTIP
        # -------------------------------------------------

        cv2.circle(
            frame,
            (x, y),
            12,
            (0, 0, 255),
            -1
        )

        # -------------------------------------------------
        # CHECK IF FINGER IS ON PIANO
        # -------------------------------------------------

        if y >= piano_y:

            key_index = x // key_width

            if 0 <= key_index < 7:

                current_key = keys[key_index]


    # =====================================================
    # HIGHLIGHT SELECTED KEY
    # =====================================================

    if current_key is not None:

        key_index = keys.index(current_key)

        x1 = key_index * key_width
        x2 = (key_index + 1) * key_width

        # Highlight selected key
        cv2.rectangle(
            frame,
            (x1, piano_y),
            (x2, height),
            (0, 200, 255),
            -1
        )

        # Border
        cv2.rectangle(
            frame,
            (x1, piano_y),
            (x2, height),
            (0, 0, 0),
            3
        )

        # Key name
        cv2.putText(
            frame,
            current_key,
            (x1 + key_width // 2 - 10, height - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2
        )


    # =====================================================
    # PLAY SOUND
    # =====================================================

    if current_key is not None:

        # Only play when changing key
        if current_key != previous_key:

            sounds[current_key].play()

            previous_key = current_key

    else:

        previous_key = None


    # =====================================================
    # TITLE
    # =====================================================

    cv2.putText(
        frame,
        "AIR PIANO",
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 0, 255),
        3
    )


    # =====================================================
    # CURRENT NOTE
    # =====================================================

    if current_key:

        cv2.putText(
            frame,
            "Note: " + current_key,
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )


    # =====================================================
    # INSTRUCTIONS
    # =====================================================

    cv2.putText(
        frame,
        "Move your index finger over the keys",
        (20, height - 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Press Q to quit",
        (20, 140),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    # =====================================================
    # SHOW FRAME
    # =====================================================

    cv2.imshow(
        "Air Piano",
        frame
    )


    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# =========================================================
# CLEANUP
# =========================================================

cap.release()

cv2.destroyAllWindows()

detector.close()

pygame.mixer.quit()