import logging
import sqlite3

from eulerpublisher.utils.constants import DB_NAME

class DBInitializer:
    """
    A DataBase Initializing class for DataBase image_matrix.db.
    """
    
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
                    version VARCHAR(30) NOT NULL,
                    FOREIGN KEY (software_id) REFERENCES software_data(id),
                    UNIQUE (software_id, version)
                )
                ''')

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

                cursor.execute('''
                CREATE TABLE IF NOT EXISTS dependency_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER NOT NULL,
                    depend_software_id INTEGER NOT NULL,
                    FOREIGN KEY (software_id) REFERENCES software_data(id),
                    FOREIGN KEY (depend_software_id) REFERENCES software_data(id),
                    UNIQUE (software_id, depend_software_id)
                )
                ''')
                
                 # Insert initial data into software_data table
                initial_software_data = [
                    ('openeuler',),
                    ('python',),
                    ('cann',),
                    ('mindspore',),
                    ('pytorch',)
                ]
                cursor.executemany('''
                INSERT OR IGNORE INTO software_data (software_name) VALUES (?)
                ''', initial_software_data)
                cursor.execute('SELECT * FROM software_data')
                print(f"Current software_data: {cursor.fetchall()}")
                cursor.execute('SELECT id, software_name FROM software_data')
                software_id_map = {row[1]: row[0] for row in cursor.fetchall()}
                
                initial_dependency_data = [
                    (software_id_map['python'], software_id_map['openeuler']),
                    (software_id_map['cann'], software_id_map['python']),
                    (software_id_map['mindspore'], software_id_map['cann']),
                    (software_id_map['pytorch'], software_id_map['cann'])
                ]
                
                cursor.executemany('''
                INSERT OR IGNORE INTO dependency_data (software_id, depend_software_id) VALUES (?, ?)
                ''', initial_dependency_data)
                
                cursor.execute('SELECT COUNT(*) FROM dependency_data')
                dep_count = cursor.fetchone()[0]
                logging.info("111")
                if dep_count < 4:
                    logging.warning(f"Only {dep_count} dependencies inserted - some may already exist")
                
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"image_matrix database initial error: {e}")
            raise
