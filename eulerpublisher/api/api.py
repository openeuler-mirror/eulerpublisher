from datetime import datetime

from flask import Flask, request, jsonify
import pika
import json
from threading import Thread
from flask_cors import CORS


class ApiServer:
    def __init__(self, config, logger, db):
        self.config = config
        self.logger = logger
        self.db = db
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

    def _setup_routes(self):

        @self.app.route('/api/rpm/build', methods=['POST', 'OPTIONS'])
        def send_rpm_message():
            if request.method == 'OPTIONS':
                return jsonify({'status': 'success', 'message': 'Preflight allowed'}), 200
            try:
                jsondata = request.get_json()

                if not jsondata or 'data' not in jsondata:
                    return jsonify({
                        'status': 'error',
                        'message': '缺少消息内容'
                    }), 400

                data = jsondata.get('data')

                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                version = data.get("version")
                arch = data.get("arch")
                chroot_list = []
                for v in version:
                    for a in arch:
                        chroot_list.append(f"openeuler-{v}-{a}")
                chroots = ",".join(chroot_list)
                repo_type = data.get("type")
                if repo_type == "scm":
                    packages = [
                        [data.get("gitUrl"), data.get("subDir"), data.get("specPath"), data.get("branch")]
                    ]
                elif repo_type == "pypi":
                    packages = [
                        [data.get("pypiName"), data.get("pypiVersion")]
                    ]
                elif repo_type == "rubygems":
                    packages = [
                        [data.get("gemName")]
                    ]
                else:
                    raise UnsupportedRpmRepoType(repo_type)

                processed_data = {
                    "trigger": {
                        "type": "mannual",
                        "timestamp": timestamp
                    },
                    "artifact": {
                        "type": "rpm",
                        "info": {
                            "repo_type": data.get("type"),
                            "owner": "Kylin2000",
                            "project": data.get("project"),
                            "chroots": chroots,
                            "packages": packages
                        }
                    }
                }

                self.logger.info(f"processed_data,{str(processed_data)}")

                # 发送到RabbitMQ
                self._build_request(processed_data)

                self.logger.info(f"消息已处理并发送到RabbitMQ: {str(processed_data)}")

                return jsonify({
                    'status': 'success',
                    'message': '消息已接收并发送',
                }), 200

            except Exception as e:
                self.logger.error(f"处理消息时出错: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'处理消息失败: {str(e)}'
                }), 500

        @self.app.route('/api/container/build', methods=['POST', 'OPTIONS'])
        def send_container_message():
            if request.method == 'OPTIONS':
                return jsonify({'status': 'success', 'message': 'Preflight allowed'}), 200
            try:
                jsondata = request.get_json()

                if not jsondata or 'data' not in jsondata:
                    return jsonify({
                        'status': 'error',
                        'message': '缺少消息内容'
                    }), 400

                data = jsondata.get('data')

                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                archs = data.get("archs")
                registries = data.get("registries")
                repository = "qitong8899"
                layers = data.get("layers")

                processed_data = {
                    "trigger": {
                        "type": "mannual",
                        "timestamp": timestamp
                    },
                    "artifact": {
                        "type": "container",
                        "info": {
                            "archs": archs,
                            "registries": registries,
                            "repository": repository,
                            "layers": layers,
                        }
                    }
                }

                self._build_request(processed_data)

                self.logger.info(f"消息已处理并发送到RabbitMQ: {str(processed_data)}")

                return jsonify({
                    'status': 'success',
                    'message': '消息已接收并发送',
                }), 200

            except Exception as e:
                self.logger.error(f"处理消息时出错: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'处理消息失败: {str(e)}'
                }), 500

    def _build_request(self, request):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        channel.exchange_declare(exchange='eulerpublisher', exchange_type='topic')
        channel.basic_publish(exchange='eulerpublisher', routing_key='orchestrator',
                              body=json.dumps(request, indent=4))
        connection.close()


    def _setup_rabbitmq(self):
        """初始化RabbitMQ连接配置"""
        self.rabbitmq_config = {
            'host': self.config.get('rabbitmq', 'host', fallback='localhost'),
            'port': self.config.getint('rabbitmq', 'port', fallback=5672),
            'username': self.config.get('rabbitmq', 'username', fallback='guest'),
            'password': self.config.get('rabbitmq', 'password', fallback='guest'),
            'queue': self.config.get('rabbitmq', 'queue', fallback='frontend_messages')
        }

    def _get_rabbitmq_connection(self):
        """创建RabbitMQ连接"""
        credentials = pika.PlainCredentials(
            self.rabbitmq_config['username'],
            self.rabbitmq_config['password']
        )
        parameters = pika.ConnectionParameters(
            host=self.rabbitmq_config['host'],
            port=self.rabbitmq_config['port'],
            credentials=credentials
        )
        return pika.BlockingConnection(parameters)

    def _send_to_rabbitmq(self, data):
        """发送消息到RabbitMQ队列"""
        connection = None
        try:
            connection = self._get_rabbitmq_connection()
            channel = connection.channel()

            # 声明队列（如果不存在则创建）
            channel.queue_declare(
                queue=self.rabbitmq_config['queue'],
                durable=True  # 队列持久化
            )

            # 发送消息
            channel.basic_publish(
                exchange='',
                routing_key=self.rabbitmq_config['queue'],
                body=json.dumps(data),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 消息持久化
                    content_type='application/json'
                )
            )
        except Exception as e:
            self.logger.error(f"发送消息到RabbitMQ失败: {str(e)}")
            raise
        finally:
            if connection:
                connection.close()



    def start(self):
        """启动API服务器"""
        # 打印所有已注册的路由（关键调试步骤）
        print("当前已注册的路由：")
        for rule in self.app.url_map.iter_rules():
            print(f"路径: {rule.rule}, 方法: {rule.methods}")

        self.running = True
        # 在单独的线程中运行Flask应用，避免阻塞主程序
        self.thread = Thread(target=self._run_server, daemon=True)
        self.thread.start()
        self.logger.info(f"API服务器已启动，监听端口: 5001")

    def _run_server(self):
        """实际运行Flask服务器的方法"""
        try:
            self.app.run(
                host='0.0.0.0',
                port=5001,
                debug=True,
                use_reloader=False  # 禁用自动重载，避免多线程问题
            )
        except Exception as e:
            self.logger.error(f"API服务器运行出错: {str(e)}")
            self.running = False

    def terminate(self):
        """停止API服务器"""
        self.running = False
        if self.thread and self.thread.is_alive():
            # Flask没有直接的停止方法，这里我们通过设置running标志并让线程自然退出
            self.logger.info("API服务器正在停止...")
