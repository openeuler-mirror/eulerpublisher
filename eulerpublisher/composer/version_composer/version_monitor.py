import requests
import logging

from eulerpublisher.utils.constants import BASE_URL

class APIMonitor:

    def fetch_software_data(self, software_name):
        url = f"{BASE_URL}?name={software_name}"
        try:
            response = requests.get(url).json()
            versions_data = None
            for item in response["items"]:
                if item["tag"] == "app_up":
                    versions_data = item["versions"]
                    break
            logging.info(f"Data for {software_name} fetched successfully.")
            return versions_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch data for project {software_name}: {e}")
            return None
        
    def filter_python_versions(self, versions):
        return [version for version in versions if version.count('.') == 1]
    
    def get_api_latest_versions(self, software_name, versions):
        if software_name == "python":
            filtered_versions = self.filter_python_versions(versions)
            return filtered_versions[:2]
        else:
            return versions[:2]
        
    def get_api_first_version(self, software_name, versions):
        if software_name == "python":
            filtered_versions = self.filter_python_versions(versions)
            return filtered_versions[0] if filtered_versions else None
        else:
            return versions[0] if versions else None
