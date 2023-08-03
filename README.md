# EulerPublisher

`eulerpublisher`是Infra SIG提供的”一键式“自动构建和发布openEuler镜像的工具，主要覆盖以下场景：
1.  container images构建、发布
2.  cloud images构建、发布
3.  WSL images构建、发布

`eulerpublisher`仍处于开发过程中，使用以下方式进行安装

```
python setup.py install
```


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
本部分介绍不同云商的云镜像构建及发布流程：
#### AWS云镜像(AMI)发布
使用`eulerpublisher`构建AMI时，需要预先使用`awscli`进行`aws configure`配置，完成身份认证，配置信息如下：
```
$ aws configure
- AWS Access Key ID: <key_id>
- AWS Secret Access Key: <secret_key>
- Default region name: <region>
```
其中，`key_id`和`secret_key`是一对用于访问认证密钥对，生成方法参见[AWS管理访问密钥](https://docs.aws.amazon.com/zh_cn/IAM/latest/UserGuide/id_credentials_access-keys.html?icmpid=docs_iam_console#Using_CreateAccessKey)，`region`是执行构建AMI任务的域。
-  **步骤1** 、AMI构建准备

```
eulerpublisher cloudimg prepare --version <VERSION> --arch <ARCH> --bucket <BUCKET> --region <REGION>
```
此命令中所有参数均需显式指定，`--version`是构建目标AMI的openEuler版本号，`--arch`指定构建AMI的架构类型，目前仅支持`aarch64`或`x86_86`，
`--bucket`是存储桶名，存储桶用于保存`prepare`上传的原始`raw`镜像，`--region`为执行构建任务的域，`bucket`在该域内，其值与上述`aws configure`配置的`region`一致。

执行此命令后，会在AWS对应`region`的`bucket`中出现一个命名为`openEuler-<VERSION>-<ARCH>.raw`的原始镜像。
-  **步骤2** 、构建AMI

```
eulerpublisher cloudimg build --version <VERSION> --arch <ARCH> --bucket <BUCKET> --region <REGION>
```
此命令中所有参数均需显式指定，用法与`eulerpublisher cloudimg prepare`命令一致。`eulerpublisher`通过[aws_install.sh](/etc/cloudimg/script/aws_install.sh)实现定制AMI镜像的能力，目前默认的[aws_install.sh](/etc/cloudimg/script/aws_install.sh)满足构建得到的AMI符合AWS Marketplace AMI发布的要求。

执行此命令后，会在AWS对应`region`的`EC2 AMI`列表中生成一个命名为`openEuler-<VERSION>-<ARCH>-<TIME>-hvm`的最终镜像（例如：`openEuler-22.03-LTS-SP2-x86_64-20230802_010324-hvm`）。

-  **发布AMI到AWS Marketplace**

**步骤2**生成的AMI满足AWS Marketplace云镜像发布的要求，如有需要可进行镜像产品发布。由于AWS Marketplace存在人工审核环节，无法通过自动化流程一键发布，用户需手动操作申请发布AMI，见[https://aws.amazon.com/marketplace](https://aws.amazon.com/marketplace/partners/management-tour)。

### 3. 发布WSL images
待补充

## 参与贡献

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request