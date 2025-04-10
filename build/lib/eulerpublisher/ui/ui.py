import gradio as gr
import pika
import json
from multiprocessing import Process
from eulerpublisher.utils.constants import ASSET_DIR

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
                if new_entry not in existing_list:
                    return existing_list + [new_entry]
            return existing_list

        def update_software_list(software_list):
            return [[software, version] for software, version in software_list]

        def update_dropdowns(software_dropdown, version_dropdown):   

            version_data = self.db.list_version(software_dropdown)
            versions = []
            for data in version_data:
                versions = [ data['name'] ] + versions
            version_dropdown = gr.Dropdown(choices=versions,value=versions[0],interactive=True)
            return version_dropdown

        with gr.Blocks(title="EulerPublisher") as demo:
            gr.Markdown("<h1 style='font-size: 36px;'>🚀 EulerPublisher - openEuler 软件制品构建工具 demo</h1>")
            with gr.Row():
                with gr.Column(scale=7):
                    gr.Markdown(
                        """
                        <p style='font-size: 24px;'>
                        EulerPublisher 是一个“一站式”自动构建、测试和分发 openEuler 软件制品的平台。它支持以 openEuler 为底座构建多样化基础和应用容器镜像，并根随 openEuler 的发布计划，构建针对主流公有云的云镜像，同时还支持二进制软件包的处理。EulerPublisher 使用 python 语言编写， 以 Web 交互界面形式向用户提供 openEuler 软件制品构建分发能力，面向 AWS、华为云、腾讯云、阿里云等主流公有云平台，Docker Hub、Quay.io 等主流容器镜像仓库，以及 PyPI、Conda 等软件包仓库，极大地提升 openEuler 软件制品构建分发效率，降低用户获取和体验 openEuler 的门槛。
                        </p>
                        """
                    )
                with gr.Column(scale=3):
                    with gr.Row():
                        gr.Markdown(
                            """
                            <img src='file/assets/EulerPublisher.jpg' alt='openEuler-logo' style='width: 400px; height: auto;'>
                            """,
                            label="openEuler",
                        )

            gr.Markdown("<hr>")

            gr.Markdown("<h2 style='font-size: 30px;'>STEP 1: 选择 openEuler 版本</h2>")

            version_data = self.db.list_version("openeuler")
            versions = []
            for data in version_data:
                versions = [ data['name'] ] + versions
            gr.Dropdown(
                label="openEuler 版本",
                choices=versions,
                value=versions[0],
                interactive=True
            )

            gr.Markdown("<hr>")

            gr.Markdown("<h2 style='font-size: 30px;'>STEP 2: 添加自定义软件</h2>")

            added_software = gr.State([])

            with gr.Row():
                software_data = self.db.list_software()
                softwares = []
                for data in software_data:
                    if data['name'] != 'openeuler':
                        softwares = [data['name']] + softwares
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


            with gr.Row():
                software_list = gr.DataFrame(
                    headers=["软件名称", "软件版本"],
                    datatype=["str", "str"], 
                    interactive=False,
                    col_count=(2, "fixed")
                )
                
            add_btn.click(
                fn=add_software,
                inputs=[software_dropdown, version_dropdown, added_software],
                outputs=added_software
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

            gr.Markdown("<h2 style='font-size: 30px;'>STEP 3: 选择目标架构</h2>")

            with gr.Row():
                archs = gr.CheckboxGroup(
                    label="目标架构",
                    choices=["x86_64", "aarch64"],
                    value=["x86_64"],
                    interactive=True
                )

            gr.Markdown("<hr>")

            gr.Markdown("<h2 style='font-size: 30px;'>STEP 4: 选择推送仓库</h2>")
            
            with gr.Row():
                registries = gr.CheckboxGroup(
                    label="推送仓库",
                    choices=["docker.io", "quay.io", "hub.oepkgs.net"],
                    value=["docker.io"],
                    interactive=True
                )

            gr.Markdown("<hr>")

            gr.Markdown("<h2 style='font-size: 30px;'>STEP 5: 触发构建请求</h2>")

            with gr.Column(scale=2):
                submit = gr.Button("触发构建", variant="primary")
                output = gr.Textbox(label="操作结果", interactive=False)
        demo.launch(server_port=7860, share=True, allowed_paths=[ASSET_DIR])

