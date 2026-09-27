from gesture_stabilizer import GestureStabilizer


def main():

    stabilizer = GestureStabilizer(
        required_frames=5
    )

    test_sequence = [
        "POINT",
        "POINT",
        "UNKNOWN",
        "POINT",
        "POINT",
        "POINT",
        "POINT",
        "POINT"
    ]

    for gesture in test_sequence:

        confirmed = stabilizer.update(
            gesture
        )

        print(
            f"Input: {gesture:10} "
            f"Confirmed: {confirmed}"
        )


if __name__ == "__main__":
    main()