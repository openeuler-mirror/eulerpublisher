# EulerPublisher

`eulerpublisher`是Infra SIG提供的”一键式“自动构建和发布openEuler镜像的工具，主要覆盖以下场景：
1.  container images构建、发布
2.  cloud images构建、发布
3.  WSL images构建、发布

## 环境依赖
1.`eulerpublisher`实现多平台docker镜像构建功能依赖于docker和qemu，安装方式如下：

```
yum install qemu-img
yum install docker
```
多平台镜像构建使用`docker buildx`，安装的docker版本需满足`>= 19.03`或单独安装`buildx`插件，单独安装`docker buildx`方法如下：

1). 从[Docker buildx](https://github.com/docker/buildx/releases/tag/v0.11.1)项目的`release`页面找到适合自己平台的二进制文件。

2). 下载二进制文件到本地并重命名为`docker-buildx`，移动到`docker`的插件目录`~/.docker/cli-plugins`。

3). 向二进制文件授予可执行权限`chmod +x ~/.docker/cli-plugins/docker-buildx`。

2.`eulerpublisher`使用python实现，依赖见[requirement.txt](/requirement.txt)，安装如下：
```
pip install -r ./requirement.txt
```


## 使用说明

### 1. 发布container images
本部分介绍如何使用eulerpublisher发布多平台（支持amd64和arm64）openeuler容器镜像。
-  **步骤1** 、获取container image构建的必要文件

```
eulerpublisher container prepare --version <VERSION>
```
  这个命令中`--version`是必需的，用于获取对应版本的构建所需文件。

-  **步骤2** 、构建container image并push到目标仓库

执行本步之前，需要先配置push的目标仓库username和password的环境变量用以登陆，确保push可以成功，执行
```
export LOGIN_USERNAME="username"
export LOGIN_PASSWORD="password"
```
完成上述**步骤1**并配置`LOGIN_USERNAME`、`LOGIN_PASSWORD`之后，可执行如下命令进行build和push
```
eulerpublisher container push --repo <REPO> --version <VERSION> --registry <REGISTRY> --dockerfile <Dockerfile>
```
  此命令中，`--repo`和`--version`必须显式指定，`--registry`不显式指定时默认指向dockerhub ([https://hub.docker.com](https://hub.docker.com))，`--dockerfile`指定自定义dockerfile的绝对路径，不显式指定时使用默认[Dockerfile](/etc/container/Dockerfile)。由于`container builds build`构建的多平台image无法在本地缓存，build的时候必须同步push到对应repo（可以是私有的）。因此，有测试需求的情况下，尽量先将构建的container image push到私有仓库验证完成后再publish到最终目标仓库。

-  **步骤3** 、测试container image

```
eulerpublisher container check --repo <REPO> --version <VERSION> --registry <REGISTRY>
```

  此命令中，所有参数必须和上述`container push`操作的参数一致，目前仅适用于测试使用默认[Dockerfile](/etc/container/Dockerfile)构建的镜像。

- **一键发布**

```
eulerpublisher container publish --repo <REPO> --version <VERSION> --registry <REGISTRY> --dockerfile <Dockerfile>
```
  此命令是上述**步骤**1～2的顺序功能集合，每个参数的含义与上述相同。使用示例如下
```
示例：
eulerpublisher container publish --repo openeuler/openeuler --version 22.03-LTS-SP1 --registry registry-1.docker.io --dockerfile Dockerfile
```
上述执行的效果是向dockerhub([https://hub.docker.com](https://hub.docker.com))的`openeuler/openeuler`仓库发布由`Dockerfile`定制的tag为`22.03-LTS-SP1`的支持arm64、amd64多平台的openeuler容器镜像。

### 2. 发布cloud images
待补充

### 3. 发布WSL images
待补充

### 4. 发布container images（Dev-V1）（建议使用该种方式）

**Dev-V1分支提供了UI版本的Eulerpublisher，无需输入### 1中的指令**

-  **步骤1** 、配置必要参数(`configs/eulerpublisher.conf`)
[global] llm_token 如需使用engine模块，需配置模型在线api的token
[Github Actions] repo_name repo_url 配置个人的git仓库名和git地址，Eulerpublisher会将渲染后的模板上传到目标仓库，并自动执行CI/CD构建容器镜像
[docker] repository 容器仓库地址，构建成功后，Github Actions会将容器镜像发布到对应的仓库

-  **步骤2** 、（环境搭建略，但是需要注意eulerpublisher还需要rabbitmq支持）安装eulerpublisher
```
python setup.py install
```

-  **步骤3** 、启动eulerpublisher
```
eulerpublisher
```

-  **注意事项**
1.Engine模块说明：
  -Engine模块为依赖分析引擎，能够基于模型判断用户选择的软件是否存在版本冲突、构建顺序不合理、依赖层可合并等。
  -如果不需要使用该模块，在前端可直接选择“不使用模型分析”。
  -Engine模块直接集成至UI模块(`eulerpublisher/ui/ui.py`)，需要提前配置可用的模型至`ui.py`中的SUPPORTED_MODELS列表，并在`engine.py`中配置
  调用模型的API，配置所有`OpenAI`调用时的`base_url`。
  -模型的分析效果与模型的选型相关，根据测试结果，70B的模型即可达到较好的分析效果，不建议选择小于30B的模型，具体模型请根据具体任务结合专业知识选择。
2.其他说明：
  -Eulerpublisher目前有多种使用方式（UI或命令行），都可以实现完整功能，可自行选择。

## 参与贡献

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request