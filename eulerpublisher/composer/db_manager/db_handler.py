import logging
import sqlite3

from eulerpublisher.utils.constants import DB_NAME

class DBHandler:
        
    def get_db_connection(self):
        return sqlite3.connect(DB_NAME)

    def execute_query(self, query, params=None):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database error during query execution: {e}")
            raise

    def add_software(self, software_name):
        try:
            self.execute_query('INSERT INTO software_data (software_name) VALUES (?)', (software_name,))
        except sqlite3.Error as e:
            logging.error(f"Failed to add software {software_name}: {e}")
            raise
        
    def add_version(self, software_name, version):
        try:
            software_id = self.get_software_id(software_name)
            self.execute_query('INSERT INTO version_data (software_id, version) VALUES (?, ?)', 
                                (software_id, version))
        except sqlite3.Error as e:
            logging.error(f"Failed to add version {version} for software {software_name}: {e}")
            raise

    def add_image(self, software_name, version, image_tag, build_date, status, release_url):
        try:
            software_id = self.get_software_id(software_name)
            version_id = self.get_version_id(software_id, version)
            self.execute_query(
                'INSERT INTO image (software_id, version_id, image_tag, build_date, status, release_url) VALUES (?, ?)', 
                (software_id, version_id, image_tag, build_date, status, release_url))
        except sqlite3.Error as e:
            logging.error(f"Failed to add image for software {software_name}, version {version}, image_tag {image_tag}: {e}")
            raise
    
    def get_software_name(self, software_id):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT software_name FROM software_data WHERE software_id = ?', (software_id,))
                software_name_result = cursor.fetchone()
                if not software_name_result:
                    raise ValueError(f"Software {software_id} does not exist in the database.")
                return software_name_result[0]
        except sqlite3.Error as e:
            logging.error(f"Failed to get software name for software {software_id}: {e}")
            raise
        
    def get_software_id(self, software_name):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM software_data WHERE software_name = ?', (software_name,))
                software_id_result = cursor.fetchone()
                if not software_id_result:
                    raise ValueError(f"Software {software_name} does not exist in the database.")
                return software_id_result[0]
        except sqlite3.Error as e:
            logging.error(f"Failed to get software id for software {software_name}: {e}")
            raise
        
    def get_version_id(self, software_id, version):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM version_data WHERE software_id = ? AND version = ?', 
                               (software_id, version))
                version_id_result = cursor.fetchone()
                if not version_id_result:
                    raise ValueError(f"Version {version} does not exist in the database.")
                return version_id_result[0]
        except sqlite3.Error as e:
            logging.error(f"Failed to get version id for version {version}: {e}")
            raise
        
    def get_all_software_names(self):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT software_name FROM software_data')
                results = cursor.fetchall()
            return [result[0] for result in results]
        except sqlite3.Error as e:
            logging.error(f"Failed to fetch software names: {e}")
            raise
            
    def get_versions(self, software_name):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                software_id = self.get_software_id(software_name)
                cursor.execute('SELECT version FROM version_data WHERE software_id = ?', (software_id,))
                results = cursor.fetchall()
                return [result[0] for result in results]
        except sqlite3.Error as e:
            logging.error(f"Failed to fetch versions for software {software_name}: {e}")
            raise
        
    def get_depend_software_id(self, software_name):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                software_id = self.get_software_id(software_name)
                cursor.execute('SELECT depend_software_id FROM dependency_data WHERE software_id = ?', (software_id,))
                results = cursor.fetchall()
                return [result[0] for result in results]
        except sqlite3.Error as e:
            logging.error(f"Failed to fetch versions for software {software_name}: {e}")
            raise
        
    def get_release_url(self, software_id, version):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                version_id = self.get_version_id(software_id, version)
                cursor.execute('SELECT release_url FROM dependency_data WHERE software_id = ? AND version_id = ?', 
                               (software_id, version_id))
                release_result = cursor.fetchone()
                if not release_result:
                    raise ValueError(f"No release_url found for software_id={software_id} and version_id={version_id}")
                return release_result[0]
        except sqlite3.Error as e:
            logging.error(f"Failed to fetch release_url for software_id={software_id}, version_id={version_id}: {e}")
            raise
        
    


