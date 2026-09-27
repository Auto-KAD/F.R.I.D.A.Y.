from authentication.face_recognizer import FaceRecognizer


def main():

    print("=" * 50)
    print("          FRIDAY FACE TRAINING")
    print("=" * 50)

    recognizer = FaceRecognizer()

    print()
    print("Preparing face data...")

    success = recognizer.train()

    if success:
        print()
        print("Training completed successfully!")
        print("FRIDAY now knows the registered faces.")
    else:
        print()
        print("Training failed.")
        print("Make sure registered face images exist.")


if __name__ == "__main__":
    main()