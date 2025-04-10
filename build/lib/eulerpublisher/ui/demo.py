import gradio as gr
import pika
import json

def add_software(current_software, current_version, existing_list):
    if current_software and current_version:
        new_entry = (current_software, current_version)
        if new_entry not in existing_list:
            return existing_list + [new_entry]
    return existing_list

def update_software_list(software_list):
    return [[software, version] for software, version in software_list]

def update_dropdowns(software_dropdown, version_dropdown):   
    if software_dropdown == "python":  
        options = ["3.9.1", "3.10.1", "3.11.1", "3.12.1", "3.13.1"]  
    elif software_dropdown == "cann": 
        options = ["7.0.0", "7.0.1", "8.0.RC1.beta1", "8.0.RC2.beta1", "8.0.RC3.beta1", "8.0.0"]   
    elif software_dropdown == "pytorch":
        options = ["2.5.0", "2.5.1"]
    elif software_dropdown == "nginx":
        options = ["1.21.0", "1.21.1", "1.22.0", "1.23.0"]
    version_dropdown = gr.Dropdown(choices=options,value=options[0],interactive=True)
    return version_dropdown

with gr.Blocks(title="EulerPublisher") as demo:
    gr.Markdown("<h1 style='font-size: 36px;'>🚀 EulerPublisher - openEuler 软件制品构建平台</h1>")
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
                    <img src='/file=assets/EulerPublisher.jpg' alt='openEuler-logo' style='width: 300px; height: auto;'>
                    """,
                    label="openEuler",
                )

    gr.Markdown("<hr>")

    gr.Markdown("<h2 style='font-size: 30px;'>STEP 1: 选择 openEuler 版本</h2>")

    gr.Dropdown(
        label="openEuler 版本",
        choices=[
            "openEuler-20.03-LTS",
            "openEuler-20.09",
            "openEuler-22.03-LTS",
            "openEuler-22.09",
            "openEuler-24.03-LTS",
            "openEuler-24.09",
            "openEuler-25.03",
        ],
        value="openEuler-25.03",
        interactive=True
    )

    gr.Markdown("<hr>")

    gr.Markdown("<h2 style='font-size: 30px;'>STEP 2: 添加自定义软件</h2>")

    added_software = gr.State([])

    with gr.Row():
        software_dropdown = gr.Dropdown(
            label="软件名称",
            choices=[
                "python",
                "cann",
                "pytorch",
                "nginx"
            ],
            value="python",
            interactive=True
        )

        version_dropdown = gr.Dropdown(
            label="软件版本",
            choices=[],
            interactive=True
        )
        add_btn = gr.Button("➕ 添加", variant="secondary")


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

if __name__ == "__main__":
    demo.launch(server_port=7860, share=True, allowed_paths=["assets"])