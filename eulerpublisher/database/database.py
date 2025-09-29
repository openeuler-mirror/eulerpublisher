import sqlite3
import os
from eulerpublisher.utils.exceptions import DatabaseError
from eulerpublisher.utils.constants import DATABASE_DIR, WORKFLOW_STATUS_UPLOADING
from eulerpublisher.utils.utils import _dict_factory

DATABASE_PATH = os.path.join(DATABASE_DIR, "eulerpublisher.db")

class Database:
    def __init__(self, config, logger, db_path=DATABASE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.config = config
        self.logger = logger
        self._create_table()
        self.logger.info("Database initialized")

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
                    UNIQUE (software_id, version_id, registry, repository, tag)
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS dependency (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER NOT NULL,
                    dependency_id INTEGER NOT NULL,
                    UNIQUE (software_id, dependency_id)
                )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS workflow_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        artifact_type INTEGER NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        submitted_on INTEGER,
                        started_on INTEGER,
                        ended_on INTEGER,
                        owner_name VARCHAR(50),
                        repo_name VARCHAR(50),
                        run_id INTEGER NOT NULL,
                        commit_sha VARCHAR(40)
                    )
                ''')

                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error creating tables: {e}")
            raise DatabaseError(f"Failed to create database tables: {e}")

    def insert_software(self, software_name):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                INSERT INTO software (name)
                VALUES (?)
                ''', (software_name,))
                conn.commit()
        except sqlite3.IntegrityError:
            self.logger.warning(f"Software {software_name} already exists")
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting software: {e}")
            raise DatabaseError(f"Failed to insert software: {e}")

    def delete_software(self, software_name):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA FOREIGN_KEYS=ON")
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                DELETE FROM software WHERE name = ?
                ''', (software_name,))
                conn.commit()
        except sqlite3.IntegrityError as e:
            self.logger.warning(f"Software {software_name} has dependent records and cannot be deleted")
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting software: {e}")
            raise DatabaseError(f"Failed to delete software: {e}")

    def query_software(self, software_name):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = _dict_factory
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id FROM software WHERE name = ?
                ''', (software_name,))
                result = cursor.fetchone()
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Error querying software: {e}")
            raise DatabaseError(f"Failed to query software: {e}")

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
            raise DatabaseError(f"Failed to list software: {e}")

    def insert_version(self, software_name, version_name):
        software = self.query_software(software_name)
        if software is None:
            self.logger.error(f"Software {software_name} not found")
            return None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                INSERT INTO version (software_id, name)
                VALUES (?, ?)
                ''', (software['id'], version_name))
                conn.commit()
        except sqlite3.IntegrityError:
            self.logger.warning(f"Version {version_name} for software {software_name} already exists")
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting version: {e}")
            raise DatabaseError(f"Failed to insert version: {e}")
        
    def delete_version(self, software_name, version_name):
        software = self.query_software(software_name)
        if software is None:
            self.logger.error(f"Software {software_name} not found")
            return
        
        try:
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
            raise DatabaseError(f"Failed to delete version: {e}")

    def query_version(self, software_name, version_name):
        software = self.query_software(software_name)
        if software is None:
            self.logger.error(f"Software {software_name} not found")
            return None
                
        try:
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
            raise DatabaseError(f"Failed to query version: {e}")

    def list_version(self, software_name):
        software = self.query_software(software_name)
        if software is None:
            self.logger.error(f"Software {software_name} not found")
            return None
                
        try:
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
            raise DatabaseError(f"Failed to list version: {e}")

    def insert_image(self, software_name, version_name, arch, registry, repository, tag):
        software = self.query_software(software_name)
        if software is None:
            self.logger.error(f"Software {software_name} not found")
            return
        version = self.query_version(software_name, version_name)
        if version is None:
            self.logger.error(f"Version {version_name} for {software_name} not found")
            return                
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = _dict_factory
                conn.execute("PRAGMA FOREIGN_KEYS=ON")
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('''
                INSERT OR REPLACE INTO image (software_id, version_id, arch, registry, repository, tag)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (software['id'], version['id'], arch, registry, repository, tag))
                conn.commit()

        except sqlite3.IntegrityError:
            self.logger.warning(f"Image {registry}/{repository}/{software_name}:{tag} already exists")
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting image: {e}")
            raise DatabaseError(f"Failed to insert image: {e}")
        
    def query_image(self, software_name, version_name, repository, tag, registry="docker.io"):
        software = self.query_software(software_name)
        if software is None:
            self.logger.error(f"Software {software_name} not found")
            return 
        version = self.query_version(software_name, version_name)
        if version is None:
            self.logger.error(f"Version {version_name} for {software_name} not found")
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = _dict_factory
                cursor = conn.cursor()
                cursor.execute('''
                SELECT * FROM image WHERE software_id = ? AND version_id = ? AND registry = ? AND repository = ? AND tag = ?
                ''', (software['id'], version['id'], registry, repository, tag))
                result = cursor.fetchone()
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Error querying images: {e}")
            raise DatabaseError(f"Failed to query images: {e}")
    
    def delete_image(self, software_name, version_name, arch, registry, repository, tag):
        software = self.query_software(software_name)
        if software is None:
            self.logger.error(f"Software {software_name} not found")
            return
        version = self.query_version(software_name, version_name)
        if version is None:
            self.logger.error(f"Version {version_name} for software {software_name} not found")
            return
        
        try:
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
            raise DatabaseError(f"Failed to delete image: {e}")
        
    def query_dependency(self, software_name):
        software_id = self.query_software(software_name)
        if software_id is None:
            self.logger.error(f"Software {software_name} not found")
            return None
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT s.software_name FROM dependency_data d
                JOIN software_data s ON d.dependency_id = s.id
                WHERE d.software_id = ?
                ''', (software_id,))
                result = cursor.fetchone()
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Error querying dependency: {e}")
            raise DatabaseError(f"Failed to query dependency: {e}")

    def insert_workflow(self, artifact_type, submitted_on):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                            INSERT INTO workflow_status (artifact_type, status, submitted_on, started_on, ended_on, owner_name, repo_name, run_id, commit_sha)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (artifact_type, WORKFLOW_STATUS_UPLOADING, submitted_on, None, None, None, None, -1, None))
                inserted_id = cursor.lastrowid
                return inserted_id
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting workflow status: {e}")
            raise DatabaseError(f"Failed to insert workflow status: {e}")

    def update_workflow(self, id, workflow_data):
        valid_updates = {k: v for k, v in workflow_data.items() if v is not None}

        if not valid_updates:
            return None

        set_clause = ", ".join([f"{key} = ?" for key in valid_updates.keys()])
        sql = f"UPDATE workflow_status SET {set_clause} WHERE id = ?"
        params = list(valid_updates.values()) + [id]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            success = cursor.rowcount > 0

            return success

    def query_by_id(self, record_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = """
                    SELECT * 
                    FROM workflow_status 
                    WHERE id = ?
                """

                cursor.execute(query, (record_id,))
                result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            self.logger.error(f"Error querying workflow status: {e}")
            return None