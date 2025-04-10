import sqlite3
import os
from eulerpublisher.utils.exceptions import DatabaseError
from eulerpublisher.utils.constants import DATABASE_DIR
from eulerpublisher.utils.utils import _dict_factory

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
                CREATE TABLE IF NOT EXISTS software (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    description VARCHAR(300)
                )
                ''')

                cursor.execute('''
                CREATE TABLE IF NOT EXISTS version (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER,
                    name VARCHAR(50) NOT NULL,
                    FOREIGN KEY (software_id) REFERENCES software(id),
                    UNIQUE (software_id, name)
                )
                ''')

                cursor.execute('''
                CREATE TABLE IF NOT EXISTS image (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER NOT NULL,
                    version_id INTEGER NOT NULL,
                    arch VARCHAR(50) NOT NULL,
                    registry VARCHAR(100) NOT NULL,
                    repository VARCHAR(100) NOT NULL,
                    tag VARCHAR(100) NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (software_id) REFERENCES software(id),
                    FOREIGN KEY (version_id) REFERENCES version(id),
                    UNIQUE (software_id, version_id, arch, registry, repository, tag)
                )
                ''')
                
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error creating tables: {e}")
            raise DatabaseError(f"Error creating tables: {e}")

    def insert_software(self, name):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                INSERT INTO software (name)
                VALUES (?)
                ''', (name,))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            self.logger.warning(f"Software {name} already exists")
            return self.query_software(name)
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting software: {e}")
            raise DatabaseError(f"Error inserting software: {e}")

    def delete_software(self, name):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA FOREIGN_KEYS=ON")
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                DELETE FROM software WHERE name = ?
                ''', (name,))
                conn.commit()
        except sqlite3.IntegrityError as e:
            self.logger.warning(f"Software {name} has dependent records and cannot be deleted")
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting software: {e}")
            raise DatabaseError(f"Error deleting software: {e}")

    def query_software(self, name):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = _dict_factory
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id FROM software WHERE name = ?
                ''', (name,))
                result = cursor.fetchone()
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Error querying software: {e}")
            raise DatabaseError(f"Error querying software: {e}")

    def list_software(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = _dict_factory
                cursor = conn.cursor()
                cursor.execute('''
                SELECT * FROM software
                ''')
                result = cursor.fetchall()
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Error listing software: {e}")
            raise DatabaseError(f"Error listing software: {e}")

    def insert_version(self, software_name, version_name):
        try:
            software = self.query_software(software_name)
            if software is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                INSERT INTO version (software_id, name)
                VALUES (?, ?)
                ''', (software['id'], version_name))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            self.logger.warning(f"Version {version_name} for software {software_name} already exists")
            return self.query_version(software_name, version_name)
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting version: {e}")
            raise DatabaseError(f"Error inserting version: {e}")

    def delete_version(self, software_name, version_name):
        try:
            software = self.query_software(software_name)
            if software is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = _dict_factory
                conn.execute("PRAGMA FOREIGN_KEYS=ON")
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                DELETE FROM version WHERE software_id = ? AND name = ?
                ''', (software['id'], version_name))
                conn.commit()
        except sqlite3.IntegrityError:
            self.logger.warning(f"Version {version_name} for software {software_name} has dependent records and cannot be deleted")
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting version: {e}")
            raise DatabaseError(f"Error deleting version: {e}")

    def query_version(self, software_name, version_name):
        try:
            software = self.query_software(software_name)
            if software is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = _dict_factory
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id FROM version WHERE software_id = ? AND name = ?
                ''', (software['id'], version_name))
                result = cursor.fetchone()
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Error querying version: {e}")
            raise DatabaseError(f"Error querying version: {e}")

    def list_version(self, software_name):
        try:
            software = self.query_software(software_name)
            if software is None:
                self.logger.error(f"Software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = _dict_factory
                cursor = conn.cursor()
                cursor.execute('''
                SELECT * FROM version WHERE software_id = ?
                ''', (software['id'],))
                result = cursor.fetchall()
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Error listing version: {e}")
            raise DatabaseError(f"Error listing version: {e}")

    def insert_image(self, software_name, version_name, arch, registry, repository, tag):
        try:
            software = self.query_software(software_name)
            if software is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            version = self.query_version(software_name, version_name)
            if version is None:
                self.logger.error(f"Version {version_name} for {software_name} not found")
                raise DatabaseError(f"Version {version_name} for {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = _dict_factory
                conn.execute("PRAGMA FOREIGN_KEYS=ON")
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                INSERT INTO image (software_id, version_id, arch, registry, repository, tag)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (software['id'], version['id'], arch, registry, repository, tag))
                conn.commit()
        except sqlite3.IntegrityError:
            self.logger.warning(f"Image {registry}/{repository}/{software_name}:{tag} already exists")
            return self.query_images(software_name, version_name, arch, registry, repository, tag)

    def query_images(self, software_name, version_name, arch, repository, tag, registry="docker.io"):
        try:
            software = self.query_software(software_name)
            if software is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            version = self.query_version(software_name, version_name)
            if version is None:
                self.logger.error(f"Version {version_name} for {software_name} not found")
                raise DatabaseError(f"Version {version_name} for {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = _dict_factory
                cursor = conn.cursor()
                cursor.execute('''
                SELECT * FROM image WHERE software_id = ? AND version_id = ? AND arch = ? AND registry = ? AND repository = ? AND tag = ?
                ''', (software['id'], version['id'], arch, registry, repository, tag))
                result = cursor.fetchall()
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Error querying images: {e}")
            raise DatabaseError(f"Error querying images: {e}")
    
    def delete_image(self, software_name, version_name, arch, registry, repository, tag):
        try:
            software = self.query_software(software_name)
            if software is None:
                self.logger.error(f"Software {software_name} not found")
                raise DatabaseError(f"Software {software_name} not found")
            version = self.query_version(software_name, version_name)
            if version is None:
                self.logger.error(f"Version {version_name} for software {software_name} not found")
                raise DatabaseError(f"Version {version_name} for software {software_name} not found")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = _dict_factory
                conn.execute("PRAGMA FOREIGN_KEYS=ON")
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                DELETE FROM image WHERE software_id = ? AND version_id = ? AND arch = ? AND registry = ? AND repository = ? AND tag = ?
                ''', (software['id'], version['id'], arch, registry, repository, tag))
                conn.commit()
        except sqlite3.IntegrityError:
            self.logger.warning(f"Image {registry}/{repository}{software_name}:{tag} has dependent records and cannot be deleted")
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting image: {e}")
            raise DatabaseError(f"Error deleting image: {e}")