"""
Smart Attendance System
AI-based facial recognition attendance system

Usage:
    python main.py setup          Initialize database schema
    python main.py register       Register a new user (captures face via camera)
    python main.py train          Train the face recognition model
    python main.py run            Start real-time attendance recognition
    python main.py report         View today's attendance records
"""

import sys
import json
from src.config import KNOWN_FACES_DIR
from src.logger import logger
from src.database import DatabaseManager
from src.face_utils import FaceProcessor


def cmd_setup():
    db = DatabaseManager()
    db.initialize_schema()
    db.close()
    print("Database schema initialized successfully.")


def cmd_register():
    name = input("Enter full name: ").strip()
    email = input("Enter email: ").strip()
    department = input("Enter department: ").strip()
    role = input("Enter role (student/employee/admin) [employee]: ").strip() or "employee"

    processor = FaceProcessor()
    ok = processor.capture_photos(name)
    if not ok:
        print("Failed to capture photos. Aborting registration.")
        return

    db = DatabaseManager()
    user_id = db.register_user(
        name=name,
        email=email,
        department=department,
        role=role,
        image_path=str(KNOWN_FACES_DIR / name),
    )
    db.close()
    print(f"User '{name}' registered successfully (ID: {user_id}).")
    print(f"Photos saved to: {KNOWN_FACES_DIR / name}")
    print("Run 'python main.py train' to update the recognition model.")


def cmd_train():
    processor = FaceProcessor()
    ok = processor.train_from_directory()
    if ok:
        print("Model trained successfully.")
    else:
        print("Training failed. Ensure known_faces directory has labeled subdirectories.")


def cmd_run():
    db = DatabaseManager()
    processor = FaceProcessor()
    labels_path = KNOWN_FACES_DIR / "labels.json"

    if labels_path.exists():
        with open(labels_path, "r") as f:
            labels = json.load(f)
        processor.load_model(str(KNOWN_FACES_DIR / "model.yml"), labels)
    else:
        logger.info("No saved model found. Training from directory...")
        ok = processor.train_from_directory()
        if not ok:
            print("No training data available. Register users first.")
            db.close()
            return
        processor.recognizer.save(str(KNOWN_FACES_DIR / "model.yml"))
        with open(labels_path, "w") as f:
            json.dump(processor.labels, f)
        print("Model trained and saved.")

    processor.recognize_from_camera(db_manager=db)
    db.close()


def cmd_report():
    db = DatabaseManager()
    records = db.get_today_attendance()
    db.close()

    if not records:
        print("No attendance records for today.")
        return

    print(f"\n{'Name':<25} {'Department':<20} {'Time':<20} {'Status':<10} {'Confidence':<10}")
    print("-" * 85)
    for r in records:
        print(
            f"{r['name']:<25} {r['department']:<20} {str(r['check_in']):<20} "
            f"{r['status']:<10} {str(r['confidence']):<10}"
        )
    print(f"\nTotal: {len(records)} record(s)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    commands = {
        "setup": cmd_setup,
        "register": cmd_register,
        "train": cmd_train,
        "run": cmd_run,
        "report": cmd_report,
    }

    cmd = sys.argv[1]
    if cmd in commands:
        commands[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
