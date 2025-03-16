import requests
import logging

from .version_combinator import VersionCombinator
from eulerpublisher.composer.db_manager.db_handler import DBHandler
from eulerpublisher.utils.constants import BASE_URL

class APIMonitor:

    def fetch_software_data(self, project_name):
        url = f"{BASE_URL}?name={project_name}"
        try:
            response = requests.get(url).json()
            versions_data = None
            for item in response["items"]:
                if item["tag"] == "app_up":
                    versions_data = item["versions"]
                    break
            return versions_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch data for project '{project_name}': {e}")
            return None

    def schedule_task(self):
        software_names = DBHandler.get_all_software_names()
        # euler，python，cann，mindspore，pytorch
        for software_name in software_names:
            old_versions = DBHandler.get_versions_by_software_name(software_name)
            cur_versions = self.fetch_software_data(software_name)
            if cur_versions:
                logging.info(f"Data for project fetched successfully.")
                
            if not old_versions:
                latest_two_versions = cur_versions
                for version in latest_two_versions:
                    VersionCombinator.combine_version(software_name, version)
