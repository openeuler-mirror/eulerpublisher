import time
import schedule

from eulerpublisher.composer.db_manager.db_initializer import DBInitializer
from eulerpublisher.composer.version_composer.version_combinator import VersionCombinator

def main():
    DBInitializer()
    print("Database and tables created successfully.")
    
    version_combinator = VersionCombinator()
    schedule.every().day.at("00:00").do(version_combinator.schedule_task)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
    
if __name__ == '__main__':
    main()
