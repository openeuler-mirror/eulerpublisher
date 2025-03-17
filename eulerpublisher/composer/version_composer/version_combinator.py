import logging
from collections import defaultdict
from eulerpublisher.composer.db_manager.db_handler import DBHandler
from version_monitor import APIMonitor

class VersionCombinator:
    
    def build_image(self, software_name, version, dep_software_info):
        pass
    
    def incremental_build_image(self, software_name, version):
        dep_software_ids = DBHandler.get_depend_software_id_by_software_name(software_name)
        if dep_software_ids:
            dep_software_info = defaultdict(dict)
            for dep_software_id in dep_software_ids:
                dep_software_name = DBHandler.get_software_name_by_software_id(dep_software_id)
                dep_versions = DBHandler.get_versions_by_software_name(dep_software_name)
                for dep_version in dep_versions:
                    release_url = DBHandler.get_release_url_by_software_id_and_version(dep_software_id, dep_version)
                    dep_software_info[dep_software_name][dep_version] = release_url
            self.build_image(software_name, version, dep_software_info)
        else:
            self.build_image(software_name, version, None, None)
        
    #情况一： cann8.0.0, 无python, 无euler 
    #情况二： cann8.0.0, python3.8,python3.9, euler22.03 LTS euler22.03 LTS SP1 对
    #情况三： euler22.03 LTS 无依赖 对
    #情况四： python3.8 无euler
    #情况五： python3.8 euler22.03 LTS euler22.03 LTS SP1 对
    #注意情况一和情况四
    def recursive_incremental_build(self, software_name, version):
        dep_software_ids = DBHandler.get_depend_software_id_by_software_name(software_name)
        if dep_software_ids:
            for dep_software_id in dep_software_ids:
                dep_software_name = DBHandler.get_software_name_by_software_id(dep_software_id)
                dep_versions = DBHandler.get_versions_by_software_name(dep_software_name)
                if not dep_versions:
                    dep_all_versions = APIMonitor.fetch_software_data(software_name)
                    dep_versions = APIMonitor.get_api_latest_versions(software_name, dep_all_versions)
                    for dep_version in dep_versions:
                        self.recursive_incremental_build(dep_software_name, dep_version)
                else:
                    dep_software_info = defaultdict(dict)
                    for dep_version in dep_versions:
                        release_url = DBHandler.get_release_url_by_software_id_and_version(dep_software_id, dep_version)
                        dep_software_info[dep_software_name][dep_version] = release_url
                    self.build_image(software_name, version, dep_software_info)
        self.incremental_build_image(software_name, version)

    def schedule_task(self):
        software_names = DBHandler.get_all_software_names()
        for software_name in software_names:
            old_versions = DBHandler.get_versions_by_software_name(software_name)
            cur_versions = APIMonitor.fetch_software_data(software_name)
            if not cur_versions:
                logging.warning(f"No versions found for software: {software_name}")
                continue
            latest_two_versions = APIMonitor.get_api_latest_versions(software_name, cur_versions)
                
            if not old_versions:
                for version in latest_two_versions:
                    VersionCombinator.recursive_incremental_build(software_name, version)
            else:
                api_first_version = APIMonitor.get_api_first_version(software_name, cur_versions)
                if api_first_version and api_first_version not in old_versions:
                    VersionCombinator.recursive_incremental_build(software_name, api_first_version)