from datetime import datetime

from flask import Flask, request, jsonify
import pika
import json
from threading import Thread
from flask_cors import CORS

from eulerpublisher.utils.constants import WORKFLOW_STATUS_FAILED
from eulerpublisher.utils.exceptions import UnsupportedRpmRepoType
from eulerpublisher.utils.date import get_current_timestamp


class ApiServer:
    def __init__(self, config, logger, db):
        self.config = config
        self.logger = logger
        self.db = db
        self.rpm_handler = self._get_rpm_handler()
        self.app = Flask(__name__)
        self._setup_routes()
        self.running = False
        self.thread = None

        CORS(self.app, resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type"],
                "supports_credentials": False
            }
        })

    def _get_rpm_handler(self):
        from eulerpublisher.rpm.rpm import RpmHandler
        return RpmHandler(self.config, self.logger, self.db)

    def _setup_routes(self):

        @self.app.route('/api/rpm/build', methods=['POST', ])
        def handle_rpm_build():
            try:
                jsondata = request.get_json()

                if not jsondata or 'data' not in jsondata:
                    return jsonify({
                        'status': 'error',
                        'data': 'Missing required field: data'
                    }), 400

                data = jsondata.get('data')
                version = data.get("version")
                arch = data.get("arch")
                chroot_list = []
                for v in version:
                    for a in arch:
                        chroot_list.append(f"openeuler-{v}-{a}")
                chroots = ",".join(chroot_list)
                repo_type = data.get("repo_type")
                if repo_type == "scm":
                    package = [
                        data.get("gitUrl"), data.get("subDir"), data.get("specPath"), data.get("branch")
                    ]
                elif repo_type == "pypi":
                    package = [
                        data.get("pypiName"), data.get("pypiVersion")
                    ]
                elif repo_type == "rubygems":
                    package = [
                        data.get("gemName")
                    ]
                else:
                    raise UnsupportedRpmRepoType(repo_type)

                processed_data = {
                    "repo_type": data.get("repo_type"),
                    "owner": "Kylin2000",
                    "project": data.get("project"),
                    "chroots": chroots,
                    "package": package
                }

                build = self.rpm_handler.handle_rpm(processed_data)
                data = {"id": build.id}

                return jsonify({
                    'status': 'success',
                    'data': data,
                }), 200

            except Exception as e:
                self.logger.error(f"Error processing RPM build request: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'data': f'Failed to process RPM build request: {str(e)}'
                }), 500

        @self.app.route('/api/rpm/build/<int:id>', methods=['GET'])
        def get_build(id):
            try:
                build = self.rpm_handler.query_build_state(id)
                self.logger.info(f"in get_build(): {str(build)}")
                filtered_data = build.copy()
                filtered_data.pop('__response__', None)
                filtered_data.pop('__proxy__', None)

                return jsonify({
                    'status': 'success',
                    'data': dict(filtered_data),
                }), 200
            except Exception as e:
                self.logger.error(f"Error querying RPM build information: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'data': f'Failed to query RPM build information: {str(e)}'
                }), 500

        @self.app.route('/api/container/build', methods=['POST', ])
        def send_container_message():
            try:
                jsondata = request.get_json()

                if not jsondata or 'data' not in jsondata:
                    return jsonify({
                        'status': 'error',
                        'data': 'Missing required field: data'
                    }), 400

                data = jsondata.get('data')

                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                archs = data.get("archs")
                registries = data.get("registries")
                repository = "qitong8899"
                layers = data.get("layers")

                submitted_on = get_current_timestamp()
                id = self.db.insert_workflow(0, submitted_on)

                processed_data = {
                    "trigger": {
                        "type": "mannual",
                        "timestamp": timestamp
                    },
                    "artifact": {
                        "type": "container",
                        "info": {
                            "id": id,
                            "archs": archs,
                            "registries": registries,
                            "repository": repository,
                            "layers": layers,
                        }
                    }
                }

                self._build_request(processed_data)

                self.logger.info(f"Sent message to RabbitMQ: {str(processed_data)}")

                return jsonify({
                    'status': 'success',
                    'data': {
                        "id": id
                    },
                }), 200

            except Exception as e:
                self.logger.error(f"Error processing container build request: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'data': f'Failed to process container build request: {str(e)}'
                }), 500

        @self.app.route('/api/workflow/status/<int:id>', methods=['GET'])
        def get_workflow_status(id):
            workflow = self.db.query_by_id(id)
            if workflow:
                return jsonify({
                    'status': 'success',
                    'data': workflow
                }), 200
            else:
                return jsonify({
                    'status': 'error',
                    'data': 'Error query workflow status, invalid id'
                }), 404

    def _build_request(self, request):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        channel.exchange_declare(exchange='eulerpublisher', exchange_type='topic')
        channel.basic_publish(exchange='eulerpublisher', routing_key='orchestrator',
                              body=json.dumps(request, indent=4))
        connection.close()


    def start(self):
        self.running = True
        self.thread = Thread(target=self._run_server, daemon=True)
        self.thread.start()
        self.logger.info(f"API server is running on port: 5001")

    def _run_server(self):
        try:
            self.app.run(
                host='0.0.0.0',
                port=5001,
                debug=True,
                use_reloader=False  # Disable auto-reload to avoid multithreading issues
            )
        except Exception as e:
            self.logger.error(f"Error running API server: {str(e)}")
            self.running = False

    def terminate(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.logger.info("Stopping API server...")
