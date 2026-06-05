import mysql.connector
from mysql.connector import Error
from src.config import DB_CONFIG, DB_SETUP_PATH
from src.logger import logger


class DatabaseManager:
    def __init__(self, db_name=None):
        self.connection = None
        self._db_name = db_name or DB_CONFIG["database"]
        self._connect()

    def _connect(self):
        config = DB_CONFIG.copy()
        config["database"] = self._db_name
        try:
            self.connection = mysql.connector.connect(**config)
            logger.info(f"Database connection established to {self._db_name}")
        except mysql.connector.Error as e:
            if e.errno == 1049:
                logger.info(f"Database '{self._db_name}' does not exist, creating...")
                self._create_database()
                self.connection = mysql.connector.connect(**config)
                logger.info(f"Database connection established to {self._db_name}")
            else:
                logger.error(f"Database connection failed: {e}")
                raise

    def _create_database(self):
        config = DB_CONFIG.copy()
        config.pop("database", None)
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
                       f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        conn.close()
        logger.info(f"Database '{DB_CONFIG['database']}' created")

    def initialize_schema(self):
        try:
            with open(DB_SETUP_PATH, "r", encoding="utf-8") as f:
                sql_script = f.read()
            cursor = self.connection.cursor()
            for statement in sql_script.split(";"):
                stmt = statement.strip()
                if stmt:
                    cursor.execute(stmt)
            self.connection.commit()
            cursor.close()
            logger.info("Database schema initialized successfully")
        except Error as e:
            logger.error(f"Schema initialization failed: {e}")
            raise

    def register_user(self, name, email, department, role, image_path=None):
        query = """
            INSERT INTO users (name, email, department, role, image_path)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (name, email, department, role, image_path))
            self.connection.commit()
            user_id = cursor.lastrowid
            cursor.close()
            logger.info(f"User registered: {name} (ID: {user_id})")
            return user_id
        except Error as e:
            logger.error(f"User registration failed: {e}")
            raise

    def get_all_users(self):
        query = "SELECT id, name, email, department, role, image_path FROM users"
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            users = cursor.fetchall()
            cursor.close()
            return users
        except Error as e:
            logger.error(f"Failed to fetch users: {e}")
            return []

    def get_user_by_id(self, user_id):
        query = "SELECT * FROM users WHERE id = %s"
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            cursor.close()
            return user
        except Error as e:
            logger.error(f"Failed to fetch user {user_id}: {e}")
            return None

    def record_attendance(self, user_id, status="present", confidence=None, image_path=None):
        query = """
            INSERT INTO attendance (user_id, check_in, status, confidence, image_path)
            VALUES (%s, NOW(), %s, %s, %s)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (user_id, status, confidence, image_path))
            self.connection.commit()
            cursor.close()
            logger.info(f"Attendance recorded: user_id={user_id}, status={status}, confidence={confidence}")
            return True
        except Error as e:
            logger.error(f"Attendance recording failed: {e}")
            return False

    def record_log(self, user_id, event_type, confidence=None, details=None):
        query = """
            INSERT INTO attendance_logs (user_id, event_type, confidence, details)
            VALUES (%s, %s, %s, %s)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (user_id, event_type, confidence, details))
            self.connection.commit()
            cursor.close()
        except Error as e:
            logger.error(f"Log recording failed: {e}")

    def get_today_attendance(self):
        query = """
            SELECT u.name, u.department, a.check_in, a.status, a.confidence
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE DATE(a.check_in) = CURDATE()
            ORDER BY a.check_in DESC
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            records = cursor.fetchall()
            cursor.close()
            return records
        except Error as e:
            logger.error(f"Failed to fetch today's attendance: {e}")
            return []

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
