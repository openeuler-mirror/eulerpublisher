
import os
import logging
import yaml
import re
from eulerpublisher.composer.db_manager.db_handler import DBHandler
from eulerpublisher.composer.version_composer.version_monitor import APIMonitor
from eulerpublisher.factory.product.product_maker import DockerfileGenerate
from eulerpublisher.factory.workflow.workflow_maker import WorkflowMaker
from eulerpublisher.utils.constants import FILTER_CONFIG_FILE

class BuildFactory:
    
    def build_task(self, software, version, dependencies):
        """
        Builds a task based on the provided input dictionary and generates related Dockerfiles and workflows.
        """
        dockerfile_build_list = []
        if dependencies is not None:
            for dependency in dependencies:
                dict = {'software':software, 'version':version, 'dependence':dependency}
                dockerfile_build_list.append(dict)
        else:
            dict = {'software':software, 'version':version, 'dependence':None}
            dockerfile_build_list.append(dict)

        etc_dir = os.path.dirname(os.path.abspath(__file__)) + 'product/etc/'

        # generate the dockerfile
        workflow_build_list = DockerfileGenerate().build_dockerfile(dockerfile_build_list, etc_dir)

        # generate the workflow
        WorkflowMaker().build_workflow(software+version, workflow_build_list, etc_dir)
        
    def recursive_incremental_build(self, software_name, version):
        """
        Finish recursive incremental build for version of software.

        Parameters:
        - software_name (str): software which need to build image.
        - version (str): software version which need to build image.
        """
        dep_software_list = []
        dep_software_id = DBHandler().get_depend_software_id(software_name)
        if dep_software_id:
            dep_software_name = DBHandler().get_software_name(dep_software_id)
            dep_versions = DBHandler().get_versions(dep_software_name)
            if not dep_versions:
                dep_all_versions = APIMonitor().fetch_software_data(dep_software_name)
                dep_versions = APIMonitor().get_api_latest_versions(dep_software_name, dep_all_versions)
                for dep_version in dep_versions:
                    self.recursive_incremental_build(dep_software_name, dep_version)

            for dep_version in dep_versions:
                dep_release_url = DBHandler().get_release_url(dep_software_id, dep_version)
                dep_software_list.append(dep_release_url)
                
        self.build_task(software_name, version, dep_software_list)
        # DBHandler.add_version(software_name, version)
        # DBHandler.add_image(software_name, version, image_tag, build_date, status, release_url)
        return
    
    def schedule_task(self):
        """
        Determine the software and version to be built based on whether the version is updated.
        """
        software_names = DBHandler().get_all_software_names()
        for software_name in software_names:
            old_versions = DBHandler().get_versions(software_name)
            cur_versions = APIMonitor().fetch_software_data(software_name)
            if not cur_versions:
                logging.warning(f"No versions found for software: {software_name}")
                continue
            regex = yaml.safe_load(FILTER_CONFIG_FILE)[software_name]
            latest_two_versions = [version for version in cur_versions if re.match(regex, version)][:2]
            if not old_versions:
                for version in latest_two_versions:
                    self.recursive_incremental_build(software_name, version)
            else:
                api_first_version = cur_versions[0]
                if api_first_version not in old_versions:
                    self.recursive_incremental_build(software_name, api_first_version)
