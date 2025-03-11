import logging
import sqlite3

class DBHandler:
    def __init__(self, db_name='image_matrix.db'):
        self.db_name = db_name

    def get_db_connection(self):
        return sqlite3.connect(self.db_name)

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
            logging.error(f"Failed to add software '{software_name}': {e}")
            raise

    def add_version(self, software_name, version):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM software_data WHERE software_name = ?', (software_name,))
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"Software '{software_name}' does not exist in the database.")
                software_id = result[0]
                self.execute_query('INSERT INTO version_data (software_id, version) VALUES (?, ?)', (software_id, version))
        except sqlite3.Error as e:
            logging.error(f"Failed to add version '{version}' for software '{software_name}': {e}")
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
