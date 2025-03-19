import logging
import sqlite3

from eulerpublisher.utils.constants import DB_NAME

class DBInitializer:
    
    def __init__(self):
        self.db_name = DB_NAME
        self.create_database_and_tables()
 
    def get_db_connection(self):
        return sqlite3.connect(self.db_name)

    def create_database_and_tables(self):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('BEGIN TRANSACTION')
                
                # 创建software_data表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS software_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_name VARCHAR(30) NOT NULL UNIQUE
                )
                ''')

                # 创建version_data表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS version_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER,
                    version VARCHAR(30) NOT NULL,
                    FOREIGN KEY (software_id) REFERENCES software_data(id),
                    UNIQUE (software_id, version)
                )
                ''')

                # 创建image_data表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER NOT NULL,
                    version_id INTEGER NOT NULL,
                    image_tag VARCHAR(100) NOT NULL,
                    build_date DATETIME NOT NULL, 
                    status TEXT NOT NULL CHECK(status IN (
                        'pending', 'building', 'testing', 'signing', 'publishing', 'published'
                    )),
                    release_url VARCHAR(100),
                    FOREIGN KEY (software_id) REFERENCES software_data(id),
                    FOREIGN KEY (version_id) REFERENCES version_data(id)
                )
                ''')

                # 创建dependency_data表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS dependency_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER NOT NULL,
                    depend_software_id INTEGER NOT NULL,
                    FOREIGN KEY (software_id) REFERENCES software_data(id),
                    FOREIGN KEY (depend_software_id) REFERENCES software_data(id)
                )
                ''')
                
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"image_matrix database initial error: {e}")
            raise
    
