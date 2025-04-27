import sqlite3
import os
from eulerpublisher.utils.exceptions import DatabaseError
from eulerpublisher.utils.constants import DATABASE_DIR

DATABASE_PATH = os.path.join(DATABASE_DIR, "eulerpublisher.db")

class Database:
    def __init__(self, config, logger, db_path=DATABASE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.config = config
        self.logger = logger
        self._create_table()
        self.logger.info(f"Database initialized")

    def _create_table(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('BEGIN TRANSACTION')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS software_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_name VARCHAR(30) NOT NULL UNIQUE
                )
                ''')

                cursor.execute('''
                CREATE TABLE IF NOT EXISTS version_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER,
                    version VARCHAR(100) NOT NULL,
                    FOREIGN KEY (software_id) REFERENCES software_data(id),
                    UNIQUE (software_id, version)
                )
                ''')

                cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER NOT NULL,
                    version_id INTEGER NOT NULL,
                    arch VARCHAR(10) NOT NULL,
                    registry VARCHAR(100) NOT NULL,
                    repository VARCHAR(100) NOT NULL,
                    tag VARCHAR(100) NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (software_id) REFERENCES software_data(id),
                    FOREIGN KEY (version_id) REFERENCES version_data(id),
                    UNIQUE (software_id, version_id, arch, registry, repository, tag)
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS dependency_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER NOT NULL,
                    dependency_id INTEGER NOT NULL,
                    UNIQUE (software_id, dependency_id)
                )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error creating tables: {e}")
            raise DatabaseError(f"Error creating tables: {e}")

    def insert_software(self, software_name):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                INSERT INTO software_data (software_name)
                VALUES (?)
                ''', (software_name,))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            self.logger.warning(f"Software {software_name} already exists")
            return self.query_software(software_name)
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting software: {e}")
            raise DatabaseError(f"Error inserting software: {e}")

    def delete_software(self, software_name):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA FOREIGN_KEYS=ON")
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                DELETE FROM software_data WHERE software_name = ?
                ''', (software_name,))
                conn.commit()
        except sqlite3.IntegrityError as e:
            self.logger.warning(f"Software {software_name} has dependent records and cannot be deleted")
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting software: {e}")
            raise DatabaseError(f"Error deleting software: {e}")

    def query_software(self, software_name):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id FROM software_data WHERE software_name = ?
                ''', (software_name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            self.logger.error(f"Error querying software: {e}")
            raise DatabaseError(f"Error querying software: {e}")

    def query_softwares(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT software_name FROM software_data')
                results = cursor.fetchall()
                return [result[0] for result in results]
        except sqlite3.Error as e:
            self.logger.error(f"Error querying all software: {e}")
            raise DatabaseError(f"Error querying all software: {e}")

    def insert_version(self, software_name, version):
        try:
            software_id = self.query_software(software_name)
            if software_id is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                INSERT INTO version_data (software_id, version)
                VALUES (?, ?)
                ''', (software_id, version))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            self.logger.warning(f"Version {version} for software {software_name} already exists")
            return self.query_version(software_name, version)
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting version: {e}")
            raise DatabaseError(f"Error inserting version: {e}")

    def delete_version(self, software_name, version):
        try:
            software_id = self.query_software(software_name)
            if software_id is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA FOREIGN_KEYS=ON")
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                DELETE FROM version_data WHERE software_id = ? AND version = ?
                ''', (software_id, version))
                conn.commit()
        except sqlite3.IntegrityError:
            self.logger.warning(f"Version {version} for software {software_name} has dependent records and cannot be deleted")
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting version: {e}")
            raise DatabaseError(f"Error deleting version: {e}")

    def query_version(self, software_name, version):
        try:
            software_id = self.query_software(software_name)
            if software_id is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id FROM version_data WHERE software_id = ? AND version = ?
                ''', (software_id, version))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            self.logger.error(f"Error querying version: {e}")
            raise DatabaseError(f"Error querying version: {e}")

    def query_versions(self, software_name):
        try:
            software_id = self.query_software(software_name)
            if software_id is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT version FROM version_data WHERE software_id = ?
                ''', (software_id,))
                results = cursor.fetchall()
                return [result[0] for result in results]
        except sqlite3.Error as e:
            self.logger.error(f"Error querying versions: {e}")
            raise DatabaseError(f"Error querying versions: {e}")

    def insert_image(self, software_name, version, arch, registry, repository, tag):
        try:
            software_id = self.query_software(software_name)
            version_id = self.query_version(software_name, version)
            if version_id is None:
                version_id = self.insert_version(software_name, version)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA FOREIGN_KEYS=ON")
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                INSERT INTO image_data (software_id, version_id, arch, registry, repository, tag)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (software_id, version_id, arch, registry, repository, tag))
                conn.commit()
        except sqlite3.IntegrityError:
            self.logger.warning(f"Image {registry}/{repository}/{software_name}:{tag} already exists")
            return self.query_images(software_name, version, arch, registry, repository, tag)

    def query_images(self, software_name, version, arch, repository, tag, registry="docker.io"):
        try:
            software_id = self.query_software(software_name)
            if software_id is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT * FROM image_data WHERE software_id = ? AND arch = ? AND registry = ? AND repository = ? AND tag = ?
                ''', (software_id, arch, registry, repository, tag))
                result = cursor.fetchall()
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Error querying images: {e}")
            raise DatabaseError(f"Error querying images: {e}")
    
    def delete_image(self, software_name, version, arch, registry, repository, tag):
        try:
            software_id = self.query_software(software_name)
            version_id = self.query_version(software_name, version)
            if software_id is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            if version_id is None:
                self.logger.error(f"Version {version} for software {software_name} not found")
                raise DatabaseError(f"Version {version} for software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA FOREIGN_KEYS=ON")
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                DELETE FROM image_data WHERE software_id = ? AND version_id = ? AND arch = ? AND registry = ? AND repository = ? AND tag = ?
                ''', (software_id, version_id, arch, registry, repository, tag))
                conn.commit()
        except sqlite3.IntegrityError:
            self.logger.warning(f"Image {registry}/{repository}{software_name}:{tag} has dependent records and cannot be deleted")
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting image: {e}")
            raise DatabaseError(f"Error deleting image: {e}")
        
    def query_dependency(self, software_name):
        try:
            software_id = self.query_software(software_name)
            if software_id is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT s.software_name FROM dependency_data d
                JOIN software_data s ON d.dependency_id = s.id
                WHERE d.software_id = ?
                ''', (software_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            self.logger.error(f"Error querying dependency: {e}")
            raise DatabaseError(f"Error querying dependency: {e}")