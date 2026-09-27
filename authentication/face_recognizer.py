import cv2
import os
import numpy as np


class FaceRecognizer:

    def __init__(
        self,
        faces_path="data/faces",
        model_path="data/face_model.yml"
    ):

        self.faces_path = faces_path
        self.model_path = model_path

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()

        self.names = {}

        self.is_trained = False

    def prepare_training_data(self):

        faces = []
        labels = []

        label_id = 0

        if not os.path.exists(self.faces_path):
            os.makedirs(self.faces_path)

        for person_name in os.listdir(self.faces_path):

            person_path = os.path.join(
                self.faces_path,
                person_name
            )

            if not os.path.isdir(person_path):
                continue

            self.names[label_id] = person_name

            for image_name in os.listdir(person_path):

                image_path = os.path.join(
                    person_path,
                    image_name
                )

                image = cv2.imread(
                    image_path,
                    cv2.IMREAD_GRAYSCALE
                )

                if image is None:
                    continue

                faces.append(image)
                labels.append(label_id)

            label_id += 1

        return faces, np.array(labels)

    def train(self):

        faces, labels = self.prepare_training_data()

        if len(faces) == 0:

            print("No training images found.")

            return False

        self.recognizer.train(
            faces,
            labels
        )

        self.recognizer.write(
            self.model_path
        )

        self.is_trained = True

        print("Face recognition model trained.")
        print(f"Model saved to: {self.model_path}")

        return True

    def load(self):

        if not os.path.exists(self.model_path):

            print("No trained face model found.")

            return False

        # Rebuild the name mapping
        self.names = {}

        label_id = 0

        for person_name in sorted(
            os.listdir(self.faces_path)
        ):

            person_path = os.path.join(
                self.faces_path,
                person_name
            )

            if os.path.isdir(person_path):

                self.names[label_id] = person_name

                label_id += 1

        self.recognizer.read(
            self.model_path
        )

        self.is_trained = True

        print("Face recognition model loaded.")

        return True

    def predict(self, face):

        if not self.is_trained:

            return None, None

        label, confidence = self.recognizer.predict(
            face
        )

        name = self.names.get(
            label,
            "Unknown"
        )

        return name, confidence