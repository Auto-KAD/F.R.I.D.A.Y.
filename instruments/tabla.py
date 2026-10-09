import cv2
import mediapipe as mp
import pygame
import numpy as np
import time

# =====================================================
# 1. INITIALIZE PYGAME
# =====================================================

pygame.mixer.init(
    frequency=44100,
    size=-16,
    channels=2
)

sample_rate = 44100


# =====================================================
# 2. CREATE TABLA SOUNDS
# =====================================================

def create_drum_sound(
    frequency,
    duration=0.4
):

    t = np.linspace(
        0,
        duration,
        int(sample_rate * duration),
        False
    )

    # Basic drum sound
    wave = np.sin(
        2 * np.pi * frequency * t
    )

    # Fast decay
    envelope = np.exp(-8 * t)

    wave = wave * envelope

    # Add a little noise
    noise = np.random.uniform(
        -1,
        1,
        len(t)
    )

    wave = wave + 0.15 * noise * envelope

    # Normalize
    wave = wave / np.max(
        np.abs(wave)
    )

    audio = (
        wave * 32767
    ).astype(np.int16)

    stereo_audio = np.column_stack(
        (audio, audio)
    )

    return pygame.sndarray.make_sound(
        stereo_audio
    )


# =====================================================
# TABLA NOTES
# =====================================================

sounds = {

    "DHA": create_drum_sound(
        120,
        0.5
    ),

    "DHI": create_drum_sound(
        180,
        0.35
    ),

    "NA": create_drum_sound(
        400,
        0.3
    ),

    "TIN": create_drum_sound(
        600,
        0.25
    )
}


# =====================================================
# 3. MEDIAPIPE HAND LANDMARKER
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


detector = (
    vision.HandLandmarker
    .create_from_options(options)
)


# =====================================================
# 4. START WEBCAM
# =====================================================

cap = cv2.VideoCapture(0)


if not cap.isOpened():

    print("Cannot open webcam")

    exit()


previous_zone = None

start_time = time.time()


# =====================================================
# 5. MAIN LOOP
# =====================================================

while True:

    ret, frame = cap.read()


    if not ret:

        break


    # Mirror webcam
    frame = cv2.flip(
        frame,
        1
    )


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
        (time.time() - start_time)
        * 1000
    )


    results = detector.detect_for_video(
        mp_image,
        timestamp_ms
    )


    # =================================================
    # TABLA POSITION
    # =================================================

    center_x = width // 2

    center_y = height // 2

    radius = 170


    # =================================================
    # DRAW TABLA
    # =================================================

    # Tabla body
    cv2.ellipse(
        frame,

        (center_x, center_y),

        (250, 170),

        0,

        0,

        360,

        (180, 180, 180),

        -1
    )


    # Tabla border
    cv2.ellipse(
        frame,

        (center_x, center_y),

        (250, 170),

        0,

        0,

        360,

        (0, 0, 0),

        5
    )


    # Tabla center
    cv2.circle(
        frame,

        (center_x, center_y),

        radius,

        (100, 100, 100),

        3
    )


    # Black syahi
    cv2.circle(
        frame,

        (center_x, center_y),

        60,

        (40, 40, 40),

        -1
    )


    # =================================================
    # PLAYING ZONES
    # =================================================

    current_zone = None


    if results.hand_landmarks:

        hand = results.hand_landmarks[0]


        # Index fingertip
        fingertip = hand[8]


        x = int(
            fingertip.x * width
        )

        y = int(
            fingertip.y * height
        )


        # ---------------------------------------------
        # DRAW HAND LANDMARKS
        # ---------------------------------------------

        for landmark in hand:

            lx = int(
                landmark.x * width
            )

            ly = int(
                landmark.y * height
            )

            cv2.circle(
                frame,
                (lx, ly),
                4,
                (0, 255, 0),
                -1
            )


        # Finger tip
        cv2.circle(
            frame,
            (x, y),
            12,
            (0, 0, 255),
            -1
        )


        # =================================================
        # DISTANCE FROM TABLA CENTER
        # =================================================

        distance = np.sqrt(
            (x - center_x) ** 2
            +
            (y - center_y) ** 2
        )


        # Only detect inside tabla
        if distance < 250:


            # ---------------------------------------------
            # CENTER → DHA
            # ---------------------------------------------

            if distance < 60:

                current_zone = "DHA"


            # ---------------------------------------------
            # UPPER AREA → TIN
            # ---------------------------------------------

            elif y < center_y - 60:

                current_zone = "TIN"


            # ---------------------------------------------
            # LEFT AREA → DHI
            # ---------------------------------------------

            elif x < center_x:

                current_zone = "DHI"


            # ---------------------------------------------
            # RIGHT AREA → NA
            # ---------------------------------------------

            else:

                current_zone = "NA"


    # =================================================
    # PLAY SOUND
    # =================================================

    if current_zone is not None:

        if current_zone != previous_zone:

            sounds[
                current_zone
            ].play()

            previous_zone = current_zone


    else:

        previous_zone = None


    # =================================================
    # DISPLAY TITLE
    # =================================================

    cv2.putText(
        frame,

        "AIR TABLA",

        (20, 50),

        cv2.FONT_HERSHEY_SIMPLEX,

        1.5,

        (0, 0, 255),

        3
    )


    # =================================================
    # DISPLAY SOUND
    # =================================================

    if current_zone:

        cv2.putText(
            frame,

            "Beat: " + current_zone,

            (20, 100),

            cv2.FONT_HERSHEY_SIMPLEX,

            1,

            (0, 0, 255),

            2
        )


    # =================================================
    # INSTRUCTIONS
    # =================================================

    cv2.putText(
        frame,

        "Move your index finger on the tabla",

        (20, height - 40),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.7,

        (255, 255, 255),

        2
    )


    # =================================================
    # SHOW
    # =================================================

    cv2.imshow(
        "Air Tabla",
        frame
    )


    # Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# =====================================================
# CLEANUP
# =====================================================

cap.release()

cv2.destroyAllWindows()

detector.close()

pygame.mixer.quit()