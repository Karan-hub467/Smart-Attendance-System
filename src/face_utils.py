import os
import cv2
import numpy as np
from pathlib import Path
from src.config import KNOWN_FACES_DIR, RECOGNITION_THRESHOLD
from src.logger import logger


class FaceProcessor:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load Haar cascade classifier")

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.labels = {}
        self._trained = False

    def detect_faces(self, image, scale_factor=1.1, min_neighbors=5):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=scale_factor, minNeighbors=min_neighbors
        )
        return gray, faces

    def extract_face(self, gray, face_rect, size=(200, 200)):
        x, y, w, h = face_rect
        face = gray[y : y + h, x : x + w]
        return cv2.resize(face, size)

    def train_from_directory(self):
        faces, labels = [], []
        self.labels = {}
        current_label = 0

        for person_dir in sorted(KNOWN_FACES_DIR.iterdir()):
            if not person_dir.is_dir():
                continue
            label_name = person_dir.name
            self.labels[current_label] = label_name

            for img_path in person_dir.glob("*"):
                if img_path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                    continue
                img = cv2.imread(str(img_path))
                if img is None:
                    logger.warning(f"Could not read image: {img_path}")
                    continue
                gray, faces_rects = self.detect_faces(img)
                if len(faces_rects) == 0:
                    logger.warning(f"No face found in {img_path}")
                    continue
                face = self.extract_face(gray, faces_rects[0])
                faces.append(face)
                labels.append(current_label)

            current_label += 1

        if not faces:
            logger.error("No faces found for training")
            return False

        self.recognizer.train(faces, np.array(labels))
        self._trained = True
        logger.info(
            f"Model trained on {len(faces)} faces across {len(self.labels)} person(s)"
        )
        return True

    def recognize(self, image):
        if not self._trained:
            logger.warning("Recognizer not trained yet")
            return None, None, None

        gray, faces_rects = self.detect_faces(image)
        results = []

        for face_rect in faces_rects:
            face = self.extract_face(gray, face_rect)
            label_id, confidence = self.recognizer.predict(face)
            name = self.labels.get(int(label_id), self.labels.get(label_id, "Unknown"))

            confidence_pct = round(100.0 - confidence, 2)
            if confidence_pct >= RECOGNITION_THRESHOLD:
                results.append(
                    {
                        "name": name,
                        "confidence": confidence_pct,
                        "bbox": face_rect.tolist(),
                    }
                )
            else:
                results.append(
                    {
                        "name": "Unknown",
                        "confidence": confidence_pct,
                        "bbox": face_rect.tolist(),
                        "matched": name,
                    }
                )

        return results

    def save_model(self, path):
        if self._trained:
            self.recognizer.save(str(path))
            logger.info(f"Model saved to {path}")

    def load_model(self, path, labels):
        if not Path(path).exists():
            logger.error(f"Model file not found: {path}")
            return False
        self.recognizer.read(str(path))
        self.labels = {int(k) if isinstance(k, str) else k: v for k, v in labels.items()}
        self._trained = True
        logger.info(f"Model loaded from {path}")
        return True

    def capture_photos(self, name, count=20, camera_id=0):
        person_dir = KNOWN_FACES_DIR / name
        person_dir.mkdir(exist_ok=True)

        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            logger.error("Could not open camera")
            return False

        logger.info(f"Capturing {count} photos for '{name}'. Press SPACE to capture, ESC to quit.")
        captured = 0

        while captured < count:
            ret, frame = cap.read()
            if not ret:
                break

            display = frame.copy()
            gray, faces = self.detect_faces(frame)

            for (x, y, w, h) in faces:
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

            cv2.putText(
                display,
                f"Captured: {captured}/{count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            cv2.imshow("Capture - Press SPACE", display)

            key = cv2.waitKey(1) & 0xFF
            if key == 32:
                if len(faces) > 0:
                    face_img = self.extract_face(gray, faces[0])
                    img_path = person_dir / f"{name}_{captured:03d}.jpg"
                    cv2.imwrite(str(img_path), face_img)
                    captured += 1
                    logger.info(f"Captured {img_path}")
            elif key == 27:
                break

        cap.release()
        cv2.destroyAllWindows()
        logger.info(f"Captured {captured} photos for '{name}'")
        return captured > 0

    def recognize_from_camera(self, db_manager=None, camera_id=0):
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            logger.error("Could not open camera")
            return

        logger.info("Starting recognition. Press ESC to quit.")
        recognized_today = set()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            display = frame.copy()
            results = self.recognize(frame)

            for result in results:
                x, y, w, h = result["bbox"]
                name = result["name"]
                conf = result["confidence"]

                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)
                label = f"{name} ({conf:.1f}%)"
                cv2.putText(display, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                if db_manager and name != "Unknown" and name not in recognized_today:
                    user = db_manager.get_user_by_id(
                        next((k for k, v in self.labels.items() if v == name), None)
                    )
                    if user:
                        db_manager.record_attendance(
                            user["id"], status="present", confidence=conf
                        )
                        db_manager.record_log(
                            user["id"], "check_in", confidence=conf
                        )
                        recognized_today.add(name)
                        logger.info(f"Marked attendance for {name}")

            cv2.putText(display, "ESC to exit", (10, display.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.imshow("Smart Attendance System", display)

            if cv2.waitKey(1) & 0xFF == 27:
                break

        cap.release()
        cv2.destroyAllWindows()
        logger.info("Recognition session ended")
