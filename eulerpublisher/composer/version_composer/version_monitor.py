import requests
import logging
from itertools import groupby

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
    
    # 对python进行特殊处理，取大版本中的latest小版本
    def filter_python_versions(self, versions):
        
        def get_major_version(version):
            return int(version.split('.')[1])

        def get_minor_version(version):
            return int(version.split('.')[2])

        major_versions = sorted(set(get_major_version(v) for v in versions), reverse=True)[:2]
        filtered_versions = [v for v in versions if get_major_version(v) in major_versions]
        result = [
            max(group, key=get_minor_version)
            for _, group in groupby(
                sorted(filtered_versions, key=get_major_version),
                key=get_major_version
            )
        ]
        return result
    
    def get_api_latest_versions(self, software_name, versions):
        if software_name == "python":
            return self.filter_python_versions(versions)
        else:
            return versions[:2]
        
    def get_api_first_version(self, software_name, versions):
        if software_name == "python":
            filtered_versions = self.filter_python_versions(versions)
            return filtered_versions[0] if filtered_versions else None
        else:
            return versions[0] if versions else None
