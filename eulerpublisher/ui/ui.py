import gradio as gr
import os
import json
from datetime import datetime
import pika
from multiprocessing import Process
from eulerpublisher.utils.constants import ASSET_DIR

PACKAGES_DEP_PYTHON = ["cann", "pytorch"]
SUPPORTED_VERSIONS = {
    "cann": ["8.0.0.alpha001", "8.0.RC2.alpha003", "8.1.RC1.alpha001 "],
    "python": ["3.9.1", "3.10.1", "3.11.1"],
    "pytorch": ["2.4.1", "2.5.0", "2.6.0"]
}


def software_exist(entry: str, existing_list):
    found = any(entry in item[0] for item in existing_list)
    if not found:
        return False
    return True

def python_valiable(software: str, existing_list):
    if software in PACKAGES_DEP_PYTHON:
        return software_exist(entry="python", existing_list=existing_list)
    return True

class UI(Process):
    def __init__(self, logger, config, db):
        super().__init__()
        self.logger = logger
        self.config = config
        self.db = db
        self.logger.info("UI initialized")

    def run(self):
        def add_software(current_software, current_version, existing_list):
            if current_software and current_version:
                new_entry = (current_software, current_version)
                if not software_exist(current_software, existing_list):
                    if python_valiable(current_software, existing_list):
                        return "", existing_list + [new_entry]
                    else:
                        return "<span style='color: red;'>错误！请先添加依赖的python。</span>", existing_list
            return "", existing_list

        def update_software_list(software_list):
            return [[software, version] for software, version in software_list]

        def update_dropdowns(software_dropdown, version_dropdown):   
            versions = SUPPORTED_VERSIONS[software_dropdown]
            version_dropdown = gr.Dropdown(choices=versions,value=versions[0],interactive=True)
            return version_dropdown

        def request_build(added_software, archs, registries, repository="zhihang161013"):
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
                            {"name": software, "version": version} for software, version in added_software
                        ]
                    }
                }
            }
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host='localhost'))
            channel = connection.channel()

            channel.exchange_declare(exchange='eulerpublisher', exchange_type='topic')
            channel.basic_publish(exchange='eulerpublisher', routing_key='orchestrator', body=json.dumps(build_request, indent=4))
            connection.close()
            return json.dumps(build_request, indent=4)

        with gr.Blocks(title="EulerPublisher", theme=gr.themes.Soft()) as demo:
            gr.Markdown("<h1 style='font-size: 36px;'>🚀 EulerPublisher - openEuler 软件制品构建分发工具 demo</h1>")
            with gr.Row():
                with gr.Column(scale=7):
                    gr.Markdown(
                        """
                        <p style='font-size: 18px;'>
                        EulerPublisher 是一个“一站式”自动构建、测试和分发 openEuler 软件制品的工具。它支持以 openEuler 为底座构建多样化基础和应用容器镜像，并根随 openEuler 的发布计划，构建针对主流公有云的云镜像，同时还支持二进制软件包的处理。EulerPublisher 使用 python 语言编写， 以 Web 交互界面形式向用户提供 openEuler 软件制品构建分发能力，面向 AWS、华为云、腾讯云、阿里云等主流公有云平台，Docker Hub、Quay.io 等主流容器镜像仓库，以及 PyPI、Conda 等软件包仓库，极大地提升 openEuler 软件制品构建分发效率，降低用户获取和体验 openEuler 的门槛。
                        </p >
                        """
                    )
                with gr.Column(scale=3):
                    gr.Image(
                        value=os.path.join(ASSET_DIR, "EulerPublisher.png"),
                        show_label=False, 
                        interactive=False
                    )
                        
            # select openEuler
            gr.Markdown("<hr>")
            gr.Markdown("<h2 style='font-size: 24px;'>Step 1: openEuler版本</h2>")
            versions = ["25.03", "24.03-LTS-SP1", "24.03-LTS", "22.03-LTS-SP4", "22.03-LTS"]
            oe_version = gr.Dropdown(
                label="openEuler 版本",
                choices=versions,
                value=versions[0],
                interactive=True
            )

            # select softwares
            gr.Markdown("<hr>")
            gr.Markdown("<h2 style='font-size: 24px;'>Step 2: 内置软件</h2>")
            added_software = gr.State([])
            with gr.Row():
                softwares = ["cann", "python", "pytorch"]
                software_dropdown = gr.Dropdown(
                    label="软件名称",
                    choices=softwares,
                    value="python",
                    interactive=True
                )
                version_dropdown = gr.Dropdown(
                    label="软件版本",
                    choices=[],
                    interactive=True
                )
                add_btn = gr.Button("➕ 添加", variant="secondary")
                clean_btn = gr.Button("❌ 清空", variant="secondary")
            error_message = gr.Markdown("")  # 用于显示错误信息

            # show selected woftwares
            with gr.Row():
                software_list = gr.DataFrame(
                    headers=["已添加软件", "软件版本"],
                    datatype=["str", "str"], 
                    interactive=False,
                    col_count=(2, "fixed")
                )
                
            add_btn.click(
                fn=add_software,
                inputs=[software_dropdown, version_dropdown, added_software],
                outputs=[error_message, added_software]
            )

            clean_btn.click(
                fn=lambda: [],
                inputs=None,
                outputs=added_software
            )

            software_dropdown.change(
                fn=update_dropdowns,
                inputs=[software_dropdown, version_dropdown],
                outputs=[version_dropdown]
            )

            added_software.change(
                fn=update_software_list,
                inputs=added_software,
                outputs=software_list
            )

            gr.Markdown("<hr>")
            gr.Markdown("<h2 style='font-size: 24px;'>Step 3: 目标架构</h2>")
            with gr.Row():
                archs = gr.CheckboxGroup(
                    label="目标架构",
                    choices=["x86_64", "aarch64"],
                    value=["x86_64"],
                    interactive=True
                )

            gr.Markdown("<hr>")
            gr.Markdown("<h2 style='font-size: 24px;'>Step 4: 推送仓库</h2>")
            with gr.Row():
                registries = gr.CheckboxGroup(
                    label="推送仓库",
                    choices=["docker.io", "quay.io"],
                    value=["docker.io"],
                    interactive=True
                )

            gr.Markdown("<hr>")

            gr.Markdown("<h2 style='font-size: 24px;'>Step 5: 触发构建</h2>")

            with gr.Column(scale=2):
                submit = gr.Button("触发构建", variant="primary")
                output = gr.Textbox(label="操作结果", interactive=False)

            submit.click(
                fn=lambda oe_version, added_software, archs, registries: request_build(
                    [("openeuler", oe_version)] + added_software, archs, registries
                ),
                inputs=[oe_version, added_software, archs, registries],
                outputs=output
            )
            
        demo.launch(server_port=7860, share=True, allowed_paths=[ASSET_DIR])