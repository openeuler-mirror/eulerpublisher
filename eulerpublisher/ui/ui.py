import gradio as gr
import os
import json
from datetime import datetime
import pika
import time
from multiprocessing import Process
from eulerpublisher.utils.constants import ASSET_DIR, INDEX_DIR
from eulerpublisher.engine.engine import Engine

PACKAGES_DEP_PYTHON = [
    "pytorch",
    "cann",
    "tensorflow",
    "keras",
    "opencv-python",
    "scikit-learn",
    "matplotlib",
    "transformers",
    "huggingface_hub",
    "langchain",
    "openai"
]

# SUPPORTED_VERSIONS = {
#     "cann": ["8.1.RC1", "8.0.0", "8.0.RC3", "8.0.RC2", "8.0.RC1"],
#     "python": ["3.8.1", "3.9.1", "3.10.1", "3.11.1", "3.13.3"],
#     "pytorch": ["2.4.1", "2.5.0", "2.6.0"]
# }
SUPPORTED_MODELS = ["不使用模型分析", "Qwen3-Coder-30B-A3B-Instruct",
                    "Qwen3-Next-80B-A3B-Instruct", "DeepSeek-V3.1"]


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
        self.engine = Engine(config=config, logger=logger)
        self.software_list = db.list_software()
        self.software_versions = {software['name']:[item['name'] for item in db.list_version(software['name'])] for software in self.software_list}
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
            versions = self.software_versions[software_dropdown]
            version_dropdown = gr.Dropdown(choices=versions,value=versions[0],interactive=True)
            return version_dropdown

        def on_model_change(model_name):
            show = model_name != "不使用模型分析"
            return gr.Row.update(visible=show), gr.Row.update(visible=show)

        def get_lastest_pdf_modified_time():
            file_path = f"{INDEX_DIR}/customized_faiss_index/index.faiss"
            if os.path.exists(file_path):
                mtime = os.path.getmtime(file_path)
                last_modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                return last_modified
            else:
                return "当前不存在自定义索引"

        def handle_pdf(file):
            updated_time = f"上传PDF文件以构建自定义索引(当前自定义索引最后更新时间：{get_lastest_pdf_modified_time()})"
            if file is None:
                return "上传文件为空", updated_time
            try:
                self.engine.parse_pdf(file)
                return f"已成功上传并处理文件: {os.path.basename(file.name)}", updated_time
            except Exception as e:
                return f"处理文件时出错: {str(e)}", updated_time

        def model_analyse(added_software, archs, registries, model_name, repository=self.config.get("docker", "repository")):
            # start = time.time()
            if(len(added_software)==0):
                return "请至少添加一个软件", gr.update(visible=False)
            if(model_name=="不使用模型分析"):
                return request_build(added_software, archs, registries, model_name, repository), gr.update(visible=False)
            layers = [{"name": software, "version": version} for software, version in added_software]
            if model_name in ["Qwen3-Coder-30B-A3B-Instruct", "Qwen3-Next-80B-A3B-Instruct"]:
                model_name = "Qwen/" + model_name
            elif model_name in ["DeepSeek-V3.1"]:
                model_name = "deepseek-ai/" + model_name
            response = self.engine.analyze_layers(layers, model_name)
            try:
                json_result = json.loads(response)
                # print(f"模型响应时间: {time.time() - start} 秒")
                if json_result["conflict"] is True:
                    return "存在版本冲突，无法触发构建：" + ", ".join(json_result["requires"]) + \
                           "\n详细信息："+json_result["detail"], gr.update(visible=True)
                elif json_result["change"] is True:
                    self.new_layers = json_result["new_layers"]
                    return "优化建议：" + json_result["detail"] + \
                    "\n优化后的构建顺序：" + ",".join(json_result["new_layers"]), gr.update(visible=True)
                else:
                    request_build(added_software, archs, registries, model_name, repository)
                    return "无版本冲突，且无优化建议，已触发构建。", gr.update(visible=False)
            except json.JSONDecodeError:
                return "模型输出异常：" + response, gr.update(visible=False)

        def on_click_accept(archs, registries, model_name, repository=self.config.get("docker", "repository")):
            try:
                added_software = [(layer.split('=')[0], layer.split('=')[1]) for layer in self.new_layers]
            except:
                return f"解析优化后的构建顺序时出错"
            return request_build(added_software, archs, registries, model_name, repository)

        def on_click_skip(added_software, archs, registries, model_name, repository=self.config.get("docker", "repository")):
            return request_build(added_software, archs, registries, model_name, repository)

        def request_build(added_software, archs, registries, model_name, repository):
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            layers = [{"name": software, "version": version} for software, version in added_software]

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
                        "layers": layers
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
            versions = ["25.03", "24.03.LTS.SP1", "24.03.LTS", "22.03.LTS.SP1", "22.03.LTS"]
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
                default_software = "python"
                software_dropdown = gr.Dropdown(
                    label="软件名称",
                    choices=self.software_versions.keys(),
                    value=default_software,
                    interactive=True
                )
                version_dropdown = gr.Dropdown(
                    label="软件版本",
                    choices=self.software_versions[default_software],
                    interactive=True
                )
                add_btn = gr.Button("➕ 添加", variant="secondary")
                clean_btn = gr.Button("❌ 清空", variant="secondary")
            error_message = gr.Markdown("")  # 用于显示错误信息

            # show selected softwares
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
            gr.Markdown("<h2 style='font-size: 24px;'>Step 5：依赖分析引擎</h2>")
            with gr.Row():
                model_name = gr.Dropdown(
                    label="分析模型",
                    choices=SUPPORTED_MODELS,
                    value="Qwen3-Coder-30B-A3B-Instruct",
                    interactive=True
                )

            pdf_tip = gr.Markdown(f"上传PDF文件以构建自定义索引(当前自定义索引最后更新时间：{get_lastest_pdf_modified_time()})",
            visible=True)

            pdf_row = gr.Row(visible=True)
            with pdf_row:
                pdf_file = gr.File(label="上传PDF文件", file_types=[".pdf"], interactive=True)
                pdf_output = gr.Textbox(label="PDF处理结果，处理过程需要等待约2～5分钟，与模型、文本字数相关。", interactive=False)

            model_name.change(
                fn=on_model_change,
                inputs=[model_name],
                outputs=[pdf_tip, pdf_row]
            )

            pdf_file.change(
                fn=handle_pdf,
                inputs=[pdf_file],
                outputs=[pdf_output, pdf_tip]
            )

            gr.Markdown("<hr>")

            gr.Markdown("<h2 style='font-size: 24px;'>Step 6: 触发构建</h2>")

            with gr.Column(scale=2):
                submit = gr.Button("触发构建", variant="primary")
                output = gr.Textbox(label="操作结果(若使用模型需要等待约2～5分钟）", interactive=False)

                with gr.Row(visible=False) as btn_row:
                        btn_accept = gr.Button("采纳优化建议并继续构建",variant="primary")
                        btn_skip = gr.Button("忽略优化建议", variant="primary")

            submit.click(
                fn=lambda oe_version, added_software, archs, registries, model_name: model_analyse(
                    [("openeuler", oe_version)] + added_software, archs, registries, model_name
                ),
                inputs=[oe_version, added_software, archs, registries, model_name],
                outputs=[output, btn_row]
            )

            btn_accept.click(
                fn=lambda oe_version, added_software, archs, registries, model_name: on_click_accept(
                    archs, registries, model_name
                ),
                inputs=[oe_version, added_software, archs, registries, model_name],
                outputs=output
            )

            btn_skip.click(
                fn=lambda oe_version, added_software, archs, registries, model_name: on_click_skip(
                    [("openeuler", oe_version)] + added_software, archs, registries, model_name
                ),
                inputs=[oe_version, added_software, archs, registries, model_name],
                outputs=output
            )
            
        demo.launch(server_port=7860, share=True, allowed_paths=[ASSET_DIR])