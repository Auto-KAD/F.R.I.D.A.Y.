# F.R.I.D.A.Y.

F.R.I.D.A.Y. is a Python desktop assistant with face-authenticated sign-in, a PyQt6 dashboard, hand-gesture controls, computer-vision tools, and an AI chat panel. The repository also contains **Mark LV**, a separate voice-first assistant that can be launched from FRIDAY.

## Features

- Face-recognition lock screen and local face enrollment.
- Dashboard with system monitoring, calendar, notes, media controls, and utility panels.
- Hand tracking for cursor movement, selection, and dashboard actions.
- Vision Studio and Gesture Lab for camera-based features and gesture feedback.
- Air piano, guitar, and tabla experiences using hand tracking.
- FRIDAY chat with text and voice input, Gemini responses, and spoken narration.
- Optional Mark LV assistant, launched separately from FRIDAY.

## Requirements

- Python 3.12 is the recommended version for the root FRIDAY application.
- A webcam is required for face sign-in and hand tracking. A microphone and speakers are needed for voice features.
- An internet connection and a Google Gemini API key are needed for AI responses.
- Windows is the documented setup below. Some dependencies and operating-system features may differ on other platforms.

## Install

From the repository root, create and activate a virtual environment in PowerShell, then install the FRIDAY dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell prevents virtual-environment activation, run this for the current terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Enroll A Face

The lock screen needs a trained face model. From the repository root, capture face images and train the model:

```powershell
python -m authentication.register_face
python -m authentication.train_faces
```

Follow the registration prompt and keep one face visible to the camera. Images and the trained model are stored under `data/` on your machine.

## Configure FRIDAY Chat

Create a `.env` file in the repository root and add your Gemini API key:

```text
GEMINI_API_KEY=your_api_key_here
```

Keep the key private. The `.env` file is excluded from Git. FRIDAY's chatbot sends prompts to the Gemini API; other dashboard features can be used without opening the chatbot.

## Run

From the repository root, with the virtual environment active:

```powershell
python main.py
```

FRIDAY starts with its camera-based lock screen and opens the dashboard after recognizing an enrolled user. Allow camera and microphone access when prompted by Windows.

## Gestures

The desktop gesture worker uses the webcam while available. Camera-based panels may take control of the camera while open.

| Gesture | Action |
| --- | --- |
| Point | Move the pointer |
| Pinch | Click/select |
| Two fingers | Toggle FRIDAY's question-and-answer chat panel |
| Open palm | Click |
| Fist | Close the active application |
| Two thumbs up | Save a screenshot under `data/screenshots/` |

## Mark LV (Optional)

The **JARVIS** sidebar button launches Mark LV as a separate fullscreen application and closes the FRIDAY window. To install its additional dependencies, activate the same virtual environment and run its setup script:

```powershell
cd Mark-LV-main
python setup.py
cd ..
```

On first launch, Mark LV asks for its Gemini API key and operating system in its setup screen. Its settings are stored separately under `Mark-LV-main/config/`.

## Local Data And Privacy

FRIDAY stores face images, the trained face model, screenshots, notes, and calendar data under `data/`. This directory is ignored by Git and is not included in the repository. Back up any local data you want to keep. API keys and personal face data should not be committed.

Camera frames are used by the local face and gesture features. Chat prompts are sent to Google Gemini when you use FRIDAY chat; Mark LV has its own Gemini integration and configuration.

## Project Layout

```text
authentication/   Face registration, recognition, and training
dashboard/        FRIDAY desktop interface and feature panels
vision/           Camera, hand tracking, gestures, and vision logic
instruments/      Air instrument implementations and model assets
models/           Hand-landmarker model
data/             Local face data, model, notes, calendar, and screenshots
Mark-LV-main/     Separate Mark LV assistant application
main.py           FRIDAY application entry point
requirements.txt  FRIDAY Python dependencies
```
