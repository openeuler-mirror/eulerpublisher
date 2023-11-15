# EulerPublisher

`eulerpublisher`是Infra SIG提供的”一键式“自动构建和发布openEuler镜像的工具，主要覆盖以下场景：
1.  container images构建、发布
2.  cloud images构建、发布
3.  WSL images构建、发布

`eulerpublisher`仍处于开发过程中，目前已向PyPI上传v0.0.2版本软件包，请使用以下两种方式之一进行安装
1. 下载源码到本地，执行
```
python setup.py install
```
2. 使用`pip`安装，执行
```
pip install eulerpublisher
```

## 环境依赖
1.`eulerpublisher`实现多平台容器镜像构建功能依赖于docker和qemu，安装方式如下：

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
本部分介绍如何使用eulerpublisher发布多平台（支持amd64和arm64）openeuler容器镜像。eulerpublisher以[openeuler](https://repo.openeuler.org)官方发布的容器镜像为基础，进行二次定制后发布至第三方仓库。
-  **步骤1** 、获取container image构建的必要文件

```
eulerpublisher container prepare --version {VERSION} --index {INDEX}
```
  这个命令中`--version`必须显式指定，用于获取对应版本的构建所需文件。 `--index`指定基础镜像的路径，可选`docker_img`或`docker_img/update/Y-M-D`, 选择`docker_img`表明取openeuler的`release`版本作为基础镜像、选择`docker_img/update/Y-M-D`表明取`update`版本作为基础镜像，不显式指定时默认取`release`版本作为基础镜像。

-  **步骤2** 、构建container image并push到目标仓库

执行本步之前，需要先配置push的目标仓库username和password的环境变量用以登陆，确保push可以成功，执行
```
export LOGIN_USERNAME="username"
export LOGIN_PASSWORD="password"
```
完成上述**步骤1**并配置`LOGIN_USERNAME`、`LOGIN_PASSWORD`之后，可执行如下命令进行build和push
```
eulerpublisher container push --repo {REPO} --version {VERSION} --registry {REGISTRY} --dockerfile {DOCKERFILE}
```
  此命令中，`--repo`和`--version`必须显式指定，`--registry`不显式指定时默认指向dockerhub ([https://hub.docker.com](https://hub.docker.com))，`--dockerfile`指定自定义dockerfile的绝对路径，不显式指定时使用默认[Dockerfile](/etc/container/Dockerfile)。由于`docker builds build`构建的多平台image无法在本地缓存，build的时候必须同步push到对应repo（可以是私有的）。因此，有测试需求的情况下，尽量先将构建的container image push到私有仓库验证完成后再publish到最终目标仓库。

-  **步骤3** 、测试container image

```
eulerpublisher container check --repo {REPO} --version {VERSION} --registry {REGISTRY}
```

  此命令中，所有参数必须和上述`container push`操作的参数一致，目前仅适用于测试使用默认[Dockerfile](/etc/container/Dockerfile)构建的镜像。

- **一键发布**

```
# 向单个仓库发布容器镜像：
eulerpublisher container publish --repo {REPO} --version {VERSION} --index {INDEX} --registry {REGISTRY} --dockerfile {Dockerfile}
```
  此命令是上述**步骤**1～2的顺序功能集合，每个参数的含义与上述相同。使用示例如下
```
示例：
eulerpublisher container publish --repo openeuler/openeuler --version 22.03-LTS-SP1 --registry registry-1.docker.io --dockerfile Dockerfile
```
上述执行的效果是向dockerhub([https://hub.docker.com](https://hub.docker.com))的`openeuler/openeuler`仓库发布由`Dockerfile`定制的tag为`22.03-LTS-SP1`的支持arm64、amd64多平台的openeuler容器镜像, 基础镜像来自于`22.03-LTS-SP1`的`release`版本。

为了方便将一个镜像同时发布到多个仓库，可使用如下命令：
```
# 向多个仓库发布容器镜像：
eulerpublisher container publish --version {VERSION} --index {INDEX}  --dockerfile {Dockerfile} --mpublish
```
  此命令使用`--mpublish`使能"publish one image to multiple repositories", 不再需要设置`--repo`和`--registry`参数。目标repositories的信息由[etc/container/registry.yaml](etc/container/registry.yaml)指定，内容如下
```
registry-1:
  - LOGIN_USER_1
  - LOGIN_PASSWD_1
  - registry-1/{USER_1}/{REPOSITORY-1}

registry-2:
  - LOGIN_USER_2
  - LOGIN_PASSWD_2
  - registry-2/{USER_2}/{REPOSITORY-2}

  ...
```
  其中每个仓库都维护一组信息，{LOGIN_USER_1}和{LOGIN_PASSWD_1}分别是登录registry-1的用户名和密码的环境变量，registry-1/{USER_1}/{REPOSITORY-1}是完整的仓库路径，其他仓库的信息也是如此。
### 2. 构建cloud images
#### 通用云镜像构建
使用`eulerpublisher`在本地执行机上进行通用云镜像构建，定制的镜像符合大多数主流云厂商镜像发布的要求，可用于发布。
-  **步骤1** 、基础构建准备
```
eulerpublisher cloudimg gen prepare --version {VERSION} --arch {ARCH}
```
此命令中所有参数均需显式指定，`--version`是构建目标镜像的openEuler版本号，`--arch`指定构建目标镜像的架构类型，目前仅支持`aarch64`或`x86_86`，
该步骤实现的功能是从openEuler Repo获取基础镜像，用于下一步定制。
-  **步骤2** 、构建镜像
```
eulerpublisher cloudimg gen build --version {VERSION} --arch {ARCH} --output {NAME} --rpmlist {RPMLIST}
```
此命令中`{NAME}`指定最终构建镜像的名称，`{RPMLIST}`是用户需要预安装的软件包列表文件，一旦指定不能为空。其余参数作用与步骤1命令中参数作用一致。
```
# rpmlist内容示例
tar
make
zip
curl
...
```
执行此命令后，会在执行机`/etc/eulerpublisher/cloudimg/gen/output/`目录下生成一个命名为`{NAME}`的最终镜像，该镜像满足目前大多数主流公有云厂商云市场镜像发布的技术要求，用户可手动进行镜像发布。

#### AWS云镜像构建
使用`eulerpublisher`构建AMI时，需要预先使用`awscli`进行`aws configure`配置，完成身份认证，配置信息如下：
```
$ aws configure
- AWS Access Key ID: <key_id>
- AWS Secret Access Key: <secret_key>
- Default region name: <region>
```
其中，`key_id`和`secret_key`是一对用于访问认证的密钥对，生成方法参见[AWS管理访问密钥](https://docs.aws.amazon.com/zh_cn/IAM/latest/UserGuide/id_credentials_access-keys.html?icmpid=docs_iam_console#Using_CreateAccessKey)，`region`是执行构建AMI任务的域。
-  **步骤1** 、AMI构建准备

```
eulerpublisher cloudimg aws prepare --version {VERSION} --arch {ARCH} --bucket {BUCKET}
```
此命令中所有参数均需显式指定，`--version`是构建目标AMI的openEuler版本号，`--arch`指定构建AMI的架构类型，目前仅支持`aarch64`或`x86_86`，
`--bucket`是存储桶名，存储桶用于保存`prepare`上传的原始`raw`镜像，`bucket`在`aws configure`配置的`region`内。

执行此命令后，会在AWS对应`region`的`bucket`中出现一个命名为`openEuler-{VERSION}-{ARCH}.raw`的原始镜像（例如：openEuler-22.03-LTS-SP2-x86_64.raw）。
-  **步骤2** 、构建AMI

```
eulerpublisher cloudimg aws build --version {VERSION} --arch {ARCH} --bucket {BUCKET} --region {REGION} --rpmlist {RPMLIST}
```
此命令中除`--rpmlist`以外的所有参数均需显式指定，参数作用与`eulerpublisher cloudimg aws prepare`命令一致。`eulerpublisher`通过[aws_install.sh](/etc/cloudimg/script/aws_install.sh)实现定制AMI镜像的能力，目前默认的[aws_install.sh](/etc/cloudimg/script/aws_install.sh)满足构建得到的AMI符合AWS Marketplace AMI发布的要求，需要预安装到镜像中的软件由`--rpmlist`指定的文件{RPMLIST}确定。
```
# rpmlist示例
tar
make
zip
curl
...
```

执行此命令后，会在AWS对应`region`的`EC2 AMI`列表中生成一个命名为`openEuler-{VERSION}-{ARCH}-{TIME}-hvm`的最终镜像（例如：`openEuler-22.03-LTS-SP2-x86_64-20230802_010324-hvm`）。

-  **发布AMI到AWS Marketplace**

同时，eulerpublisher提供“一键发布”到AWS个人账户的能力，即上述步骤1、2的顺序执行，命令如下：
```
eulerpublisher cloudimg aws publish --version {VERSION} --arch {ARCH} --bucket {BUCKET} --region {REGION} --rpmlist {RPMLIST}
```
生成的AMI满足AWS Marketplace云镜像发布的要求，如有需要可进行镜像产品发布。由于AWS Marketplace存在人工审核环节，无法通过自动化流程一键发布，用户需手动操作申请发布AMI，见[https://aws.amazon.com/marketplace](https://aws.amazon.com/marketplace/partners/management-tour)。


### 3. 发布WSL images
待补充

## 参与贡献

1.  Fork 本仓库
2.  新建分支
3.  提交代码
4.  新建 Pull Request