import requests
import pika
import json
import datetime
import schedule
from multiprocessing import Process
from eulerpublisher.utils.constants import UPSTREAM_MONITOR_URL
from eulerpublisher.database.database import Database
class Monitor(Process):
    def __init__(self, logger, config, db):
        self.logger = logger
        self.config = config
        self.db = db
        self.logger.info("Monitor initialized")

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

    def filter_versions(self, software_name, versions):
        pass
    
    def run(self):
        schedule.every().day.at("00:00").do(self.schedule_task)
        
        def request_build(added_software, archs, registries, repository):
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            build_request = {
                "trigger": {
                    "type": "manual",
                    "timestamp": timestamp
                },
                "artifact": {
                    "type": "container",
                    "info": {
                        "archs": archs,
                        "registries": registries,
                        "repository": repository,
                        "layers": [
                            {"name": software, "version": version, "dependency": dependency} for software, version, dependency in added_software
                        ]
                    }
                }
            }
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            channel = connection.channel()
            channel.exchange_declare(exchange='eulerpublisher', exchange_type='topic')
            channel.basic_publish(exchange='eulerpublisher', routing_key='orchestrator', body=json.dumps(build_request, indent=4))
            connection.close()
            return json.dumps(build_request, indent=4)
        