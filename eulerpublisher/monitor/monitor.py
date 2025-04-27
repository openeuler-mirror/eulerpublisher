import requests
import time
import pika
import json
import datetime
import schedule
from zoneinfo import ZoneInfo
from multiprocessing import Process
from eulerpublisher.utils.constants import UPSTREAM_MONITOR_URL
from eulerpublisher.utils.constants import ARCHS, REGISTRIES, REPOSITORY

class Monitor(Process):
    def __init__(self, logger, config, db):
        super().__init__()
        self.logger = logger
        self.config = config
        self.db = db
        self.logger.info("Monitor initialized")
        self._init_existing_software()

    def fetch_versions(self, software_name):
        url = f"{UPSTREAM_MONITOR_URL}?name={software_name}"
        try:
            response = requests.get(url).json()
            versions_data = None
            for item in response["items"]:
                if item["tag"] == "app_up":
                    versions_data = item["versions"]
                    break
            self.logger.info(f"Data for {software_name} fetched successfully.")
            return versions_data
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data for project {software_name}: {e}")
            return None
        
    def _init_existing_software(self):
        software_names = self.db.query_softwares()
        for software_name in software_names:
            versions = self.fetch_versions(software_name)[::-1]
            existing_versions = set(self.db.query_versions(software_name))
            new_versions = [version for version in versions if version not in existing_versions]
            for version in new_versions:
                self.db.insert_version(software_name, version)

    def request_build(self, layers):
        timestamp = datetime.datetime.now(ZoneInfo('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
        build_request = {
            "trigger": {
                "type": "auto",
                "timestamp": timestamp
            },
            "artifact": {
                "type": "container",
                "info": {
                    "archs": ARCHS,
                    "registries": REGISTRIES,
                    "repository": REPOSITORY,
                    "layers": layers
                }
            }
        }
        return build_request

    def recursive_build_request(self, software_name, version):
        base_layer = {"name": software_name, "version": version}
        dep_software = self.db.query_dependency(software_name)
        if not dep_software:
            return [[base_layer]]
        
        dep_versions = self.db.query_versions(dep_software)
        if len(dep_versions) > 2:
            dep_versions = dep_versions[-2:]
            
        all_combinations = []
        for dep_version in dep_versions:
            dep_combinations = self.recursive_build_request(dep_software, dep_version)
            for combination in dep_combinations:
                new_combination = combination + [base_layer]
                all_combinations.append(new_combination)
        return all_combinations

    def generate_all_build_requests(self, software_name, version):
        all_combinations = self.recursive_build_request(software_name, version)
        build_requests = []
        for layers in all_combinations:
            build_requests.append(self.request_build(layers))
        return build_requests

    def schedule_task(self):
        software_names = self.db.query_softwares()
        for software_name in software_names:
            versions = self.fetch_versions(software_name)[::-1]
            if not versions:
                self.logger.warning(f"No versions found for software: {software_name}")
                continue
            existing_versions = self.db.query_versions(software_name)
            new_versions = [version for version in versions if version not in existing_versions]
            for version in new_versions:
                self.db.insert_version(software_name, version)
                build_requests = self.generate_all_build_requests(software_name, version)
                for build_request in build_requests:
                    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
                    channel = connection.channel()
                    channel.exchange_declare(exchange='eulerpublisher', exchange_type='topic')
                    channel.basic_publish(exchange='eulerpublisher', routing_key='orchestrator', body=json.dumps(build_request, indent=4))
                    connection.close()
                    self.logger.info(f"Build request sent for software: {software_name}, version: {version}")
    
    def run(self):
        schedule.every().day.at("00:00").do(self.schedule_task)
        while True:
            schedule.run_pending()
            time.sleep(60)