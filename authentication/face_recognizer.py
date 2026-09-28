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

        self.face_size = (200, 200)

    def preprocess_face(self, face):

        if face is None or face.size == 0:
            return None

        if len(face.shape) == 3:
            gray = cv2.cvtColor(
                face,
                cv2.COLOR_BGR2GRAY
            )
        else:
            gray = face

        gray = cv2.resize(
            gray,
            self.face_size
        )

        gray = cv2.equalizeHist(gray)

        return gray

    def prepare_training_data(self):

        faces = []
        labels = []

        label_id = 0

        if not os.path.exists(self.faces_path):
            os.makedirs(self.faces_path)

        # IMPORTANT:
        # Always use the same sorted order.
        person_names = sorted(
            name for name in os.listdir(self.faces_path)
            if os.path.isdir(
                os.path.join(self.faces_path, name)
            )
        )

        for person_name in person_names:

            person_path = os.path.join(
                self.faces_path,
                person_name
            )

            self.names[label_id] = person_name

            for image_name in sorted(
                os.listdir(person_path)
            ):

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

                image = self.preprocess_face(image)

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

        if len(self.names) == 0:

            print("No registered users found.")
            return False

        self.recognizer.train(
            faces,
            labels
        )

        os.makedirs(
            os.path.dirname(self.model_path),
            exist_ok=True
        )

        self.recognizer.write(
            self.model_path
        )

        self.is_trained = True

        print("Face recognition model trained.")
        print(f"Registered users: {list(self.names.values())}")
        print(f"Model saved to: {self.model_path}")

        return True

    def load(self):

        if not os.path.exists(self.model_path):

            print("No trained face model found.")
            return False

        if not os.path.exists(self.faces_path):

            print("Face data directory not found.")
            return False

        self.names = {}

        # MUST match the training order exactly.
        person_names = sorted(
            name for name in os.listdir(self.faces_path)
            if os.path.isdir(
                os.path.join(self.faces_path, name)
            )
        )

        for label_id, person_name in enumerate(person_names):

            self.names[label_id] = person_name

        if not self.names:

            print("No registered users found.")
            return False

        self.recognizer.read(
            self.model_path
        )

        self.is_trained = True

        print("Face recognition model loaded.")
        print(f"Registered users: {list(self.names.values())}")

        return True

    def predict(self, face):

        if not self.is_trained:

            return None, None

        processed_face = self.preprocess_face(face)

        if processed_face is None:

            return "Unknown", 999.0

        label, confidence = self.recognizer.predict(
            processed_face
        )

        name = self.names.get(
            label,
            "Unknown"
        )

        return name, confidence