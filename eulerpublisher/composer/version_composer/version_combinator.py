import logging
from collections import defaultdict
from eulerpublisher.composer.db_manager.db_handler import DBHandler
from eulerpublisher.composer.version_composer.version_monitor import APIMonitor

class VersionCombinator:

    def recursive_incremental_build(self, software_name, version):
        dep_software_info = defaultdict(dict)
        dep_software_ids = DBHandler().get_depend_software_id(software_name)
        if dep_software_ids:
            for dep_software_id in dep_software_ids:
                dep_software_name = DBHandler().get_software_name(dep_software_id)
                dep_versions = DBHandler().get_versions(dep_software_name)
                if not dep_versions:
                    dep_all_versions = APIMonitor().fetch_software_data(dep_software_name)
                    dep_versions = APIMonitor().get_api_latest_versions(dep_software_name, dep_all_versions)
                    for dep_version in dep_versions:
                        self.recursive_incremental_build(dep_software_name, dep_version)

                for dep_version in dep_versions:
                    release_url = DBHandler().get_release_url(dep_software_id, dep_version)
                    dep_software_info[dep_software_name][dep_version] = release_url
                    
        # 完成镜像构建，并获取回调信息，完成数据库的更新
        # xxx.build_image(software_name, version, dep_software_info)
        # DBHandler.add_version(software_name, version)
        # DBHandler.add_image(software_name, version, image_tag, build_date, status, release_url)
        return
    
    def schedule_task(self):
        software_names = DBHandler().get_all_software_names()
        for software_name in software_names:
            old_versions = DBHandler().get_versions(software_name)
            cur_versions = APIMonitor().fetch_software_data(software_name)
            if not cur_versions:
                logging.warning(f"No versions found for software: {software_name}")
                continue
            latest_two_versions = APIMonitor().get_api_latest_versions(software_name, cur_versions)
                
            if not old_versions:
                for version in latest_two_versions:
                    self.recursive_incremental_build(software_name, version)
            else:
                api_first_version = APIMonitor().get_api_first_version(software_name, cur_versions)
                if api_first_version and api_first_version not in old_versions:
                    self.recursive_incremental_build(software_name, api_first_version)