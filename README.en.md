# Eulerpublisher

 `eulerpublisher` It is a "one-click" tool provided by Infra SIG to automatically build  and publish openEuler images, which mainly covers the following  scenarios:

1. Container images are built and published 
2. Cloud Images are built and published 
3. WSL images are built and published 

 `eulerpublisher` Still in the development process, the package has been uploaded to PyPI, please use one of the following two ways to install it

1. Download the source code to the local computer and run the command 

```
python setup.py install
```

2. Use `pip` Install, Execute

```
pip install eulerpublisher
```

## Environmental dependencies

1. `eulerpublisher` The multi-platform container image building function relies on docker and qemu, and the installation method is as follows:

```
yum install qemu-img
yum install docker
```

Multi-platform image is built and used `docker buildx` , and the installed docker version needs to meet the requirements `>= 19.03` of or install the `buildx` plug-in separately, and the `docker buildx` installation method is as follows:

1). Find the right binary for your platform from the Docker buildx `release` project's page.

2). Download the binary file to your local computer and rename `docker-buildx` it to the plugin directory `docker` `~/.docker/cli-plugins` of .

3). Grant executable permissions to the binary `chmod +x ~/.docker/cli-plugins/docker-buildx` .

2. `eulerpublisher` Use python implementation, see requirement.txt for dependencies, and install as follows:

```
pip install -r ./requirement.txt
```
💡Tips: Use the scripts `install.sh` and `uninstall.sh` for one-click installation and uninstallation.

## Directions for use

### 1. Publish the container image

#### Basic container image

This section describes how to use EulerPublisher to publish a multi-platform (AMD64 and ARM64) OpenEuler container image (which is different from  application images, such as AI container images). This function can be  used by EulerPublisher to obtain container images from OpenEuler,  customize them twice, and publish them to third-party repositories, and  the tags of the image products strictly comply with the oEEP-0005  specification.

- **Step 1: Obtain the necessary files to build the base image**  

```
eulerpublisher container base prepare --version {VERSION} --index {INDEX}
```

This command `--version` must be explicitly specified to get the files required for the build for the corresponding version. `--index` Specify the path of the official image, `docker_img` select `docker_img/update/Y-M-D` or select to indicate `docker_img` the `release` version of OpenEuler, select to indicate to obtain the `update` version, `docker_img/update/Y-M-D` and obtain the `release` version by default if not explicitly specified.

- **Step 2: Build and push the image to the target repository** 

Before performing this step, you need to configure the username and password  environment variables of the target repository for push to log in to  ensure that push can be successfully executed 

```
export LOGIN_USERNAME="username"
export LOGIN_PASSWORD="password"
```

 `LOGIN_PASSWORD` After completing step 1 and configuring `LOGIN_USERNAME` , run the following command to build and push:

```
eulerpublisher container base push --repo {REPO} --version {VERSION} --registry {REGISTRY} --dockerfile {DOCKERFILE}
```

In this command, `--repo` and `--version` must be explicitly specified, `--registry` the default points to dockerhub (https://hub.docker.com) when not explicitly specified, specifies `--dockerfile` the path to the custom dockerfile, and uses the default dockerfile when not explicitly specified. Since the `docker buildx build` built multi-platform image cannot be cached locally, it must be pushed  to the corresponding repo (which can be private) when building.  Therefore, if you need to test it, try to push the built container image to a private repository before publishing it to the final target  repository after verification is completed.

- **Step 3: Test the underlying container image** 

```
eulerpublisher container base check --tag {TAG} --script {SCRIPT.sh}
```

The above command will test the base container image tagged with {TAG}.  EulerPublisher uses the shUnit2 framework to test container images, and  the test cases of the basic container images are saved in by default `tests/container/base/openeuler_test.sh` , so you can adjust `--script` the test cases according to your own needs.

- **One-click publishing**

```
# Publish a Container Image to a Single Repository：
eulerpublisher container base publish --repo {REPO} --version {VERSION} --index {INDEX} --registry {REGISTRY} --dockerfile {Dockerfile}
```

This command is a sequential function set of steps 1~2 above, and each  parameter has the same meaning as above. The following is an example

```
Example：
eulerpublisher container base publish --repo openeuler/openeuler --version 22.03-LTS-SP1 --registry registry-1.docker.io --dockerfile Dockerfile
```

The effect of the above execution is to release the OpenEuler basic container image that `Dockerfile` `22.03-LTS-SP1` supports arm64 and AMD64 platforms to the `openeuler/openeuler` repository of Dockerhub (https://hub.docker.com).

To publish an image to multiple repositories at the same time, run the following command: 

```
# Publish Container Images to Multiple Repositories：
eulerpublisher container base publish --version {VERSION} --index {INDEX}  --dockerfile {Dockerfile} --mpublish
```

This command uses `--mpublish` the enable "publish one image to multiple repositories", `--repo` which no longer requires setting and `--registry` parameters. The information of the target repositories is determined by the YAML file, and the user specifies the path to the file by  configuring environment variables `EP_LOGIN_FILE` . The default target repositories information is specified by config/container/base/registry.yaml and is as follows

```
# registry.yaml Content Example
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

Each repository maintains a set of information, {LOGIN_USER_1} and  {LOGIN_PASSWD_1} are the environment variables for logging in to  registry-1 with the username and password respectively (the correct user and password need to `export` be configured via before publishing),  registry-1/{USER_1}/{REPOSITORY-1} is the complete repository path, and  the same is true for the information of other repositories.

#### Apply container images

openEuler application container images include scenario-specific application  software on top of the basic container images to provide users with  out-of-the-box development and usage experiences, such as AI container  images (see oEEP-0014).

```
# Publishing Container Images for Applications
eulerpublisher container app publish --arch aarch64 --repo openeuler/cann --dockerfile Dockerfile --tag cann7.0.0.aplha002-oe2203sp2
# Testing Container Images for Applications
eulerpublisher container app check --name {APP_NAME} --script {SCRIPT.sh} --tag {APP_TAG}
```

By default `tests/container/app/{APP_NAME}_test.sh` , the test cases of the application container image are saved in , and users can adjust `--script` the test cases according to their own needs.

#### Distroless container images

The openEuler Distroless container image is designed to install a specified list of application software, fulfilling the software requirements for programs to run in specific scenarios. It avoids installing unnecessary software and files, such as package managers like yum, command-line tools like bash, and other tools that are not related to program execution.

Here’s how you can publish a Distroless container image. In this command, the list of software to be installed is provided at the end, separated by spaces.
```
eulerpublisher container distroless publish -a aarch64 -p openeuler/distroless -f Dockerfile -n base -version 22.03-LTS glibc filesystem ...
```

#### Test the framework

EulerPublisher uses the shunit2 test framework.

### 2. Build cloud images

#### Build a general-purpose cloud image

Using `eulerpublisher` the general cloud image construction on the local executor, the  customized image meets the requirements of most major cloud vendors for  image release and can be used for publishing.

- **Step 1: Prepare for the foundation construction**

```
eulerpublisher cloudimg gen prepare --version {VERSION} --arch {ARCH}
```

All parameters in this command need to be explicitly specified, `--version` which is the openEuler version number of the target image, specifying the architecture type of the target image, `--arch` which is currently only supported `aarch64` or `x86_64` , the function of this step is to obtain the base image from the openEuler repo for the next customization.

- **Step 2: Build a generic image** 

```
eulerpublisher cloudimg gen build --version {VERSION} --arch {ARCH} --output {NAME} --rpmlist {RPMLIST}
```

This command `{NAME}` specifies the name of the final build image, which `{RPMLIST}` is a list of packages that the user needs to pre-install, and once  specified, it cannot be empty. The other parameters are the same as  those in Step 1.

```
# rpmlist Content Example
tar
make
zip
curl
...
```

After this command is executed, a final image named named `{NAME}` will be generated in the executor directory, `/tmp/eulerpublisher/cloudimg/gen/output/` which meets the technical requirements of most mainstream public cloud  vendors Cloud Marketplace image release, and users can manually publish  the image.

#### AWS cloud image build

When you build `eulerpublisher` an AMI, you need to `aws configure` configure and authenticate the AMI in advance `awscli` , and the configuration information is as follows:

```
$ aws configure
- AWS Access Key ID: <key_id>
- AWS Secret Access Key: <secret_key>
- Default region name: <region>
```

where , `key_id` and `secret_key` is a pair of keys used for access authentication, and the generation method can be found in AWS Managing Access Keys, which `region` is the domain that performs the task of building AMI.

- **Step 1: Prepare for AMI build**  

```
eulerpublisher cloudimg aws prepare --version {VERSION} --arch {ARCH} --bucket {BUCKET}
```

All parameters in this command need to be specified explicitly, `--version` which is the openEuler version number of the target AMI, `--arch` specifying the schema type of the AMI, currently only supported `aarch64` or `x86_64` , `--bucket` is the bucket name, and the bucket is used to save the `prepare` uploaded `raw` original image, `bucket` which is `aws configure` configured in `region` Inside.

When this command is executed, an original image named :openEuler-22.03-LTS-SP2-x86_64.raw `openEuler-{VERSION}-{ARCH}.raw` appears `bucket` in the corresponding in AWS `region` .

- **Step 2: Build an AMI** 

```
eulerpublisher cloudimg aws build --version {VERSION} --arch {ARCH} --bucket {BUCKET} --region {REGION} --rpmlist {RPMLIST}
```

All parameters in `--rpmlist` this command except for must be specified explicitly, and the parameters act the same as the `eulerpublisher cloudimg aws prepare` command. `eulerpublisher` The ability to customize AMI images is implemented through  aws_install.sh, and the current default aws_install.sh meets the  requirements of the built AMI to meet the requirements of the AWS  Marketplace AMI, and the software that needs to be pre-installed in the  image is determined by the `--rpmlist` specified file {RPMLIST}.

```
# rpmlist Example
tar
make
zip
curl
...
```

When this command is executed, a final image named named is generated `region` in the corresponding `EC2 AMI` list `openEuler-{VERSION}-{ARCH}-{TIME}-hvm` of AWS (for example: `openEuler-22.03-LTS-SP2-x86_64-20230802_010324-hvm` ).

- **Publish AMI to the AWS Marketplace**

At the same time, EulerPublisher provides the ability to publish to your  AWS personal account with one click, that is, the preceding steps 1 and 2 are executed in the following order: 

```
eulerpublisher cloudimg aws publish --version {VERSION} --arch {ARCH} --bucket {BUCKET} --region {REGION} --rpmlist {RPMLIST}
```

The generated AMI meets the requirements of AWS Marketplace cloud image  publishing, and can be released if necessary. Due to the manual review  process in AWS Marketplace, it cannot be published with one click  through the automated process, and users need to manually apply for the  release of the AMI, see https://aws.amazon.com/marketplace.

### 3. Build cloud images
This chapter mainly introduces how to publish the new version of AI image to the openEuler official image repository by running the build script after the new version of the upstream AI image is released. At this stage, it mainly focuses on Ascend-AI images.

- Gitee Account Configuration
	```bash
  export GITEE_API_TOKEN={Gitee-Token}
	export GITEE_USER_NAME={Gitee-User}
  export GITEE_USER_EMAIL={Gitee-Email}
	```
 - Install Tool Dependencies
	```bash
	dnf -y install git python3-pip
	```
- Install Python Dependencies
	```bash
	pip3 install click requests gitpython
	```
- Download the Project
	```bash
	git clone https://gitee.com/baigj/eulerpublisher.git
	```
- Execute the Script
	```bash
	python3 {pwd}/eulerpublisher/update/container/auto/update.py -ov 24.03-lts -an cann -sv 8.0.RC1
	```
- Parameter Description
    | Parameter | Required | Example |  Description |
    |--|--|--|--|
    | `-ov` | Yes | 24.03-lts | openEuler version. |
    | `-sv` | Yes | 8.0.RC1 | SDK version. |
    | `-an` | Yes | cann | Application name, currently only supports CANN, MindSpore, and PyTorch. |
    | `-sn` | No | cann | SDK name, default is CANN, currently supports only CANN. |
    | `-fv` | No | 1.0.0 | AI framework version, including PyTorch and MindSpore-related versions. |
    | `-pv` | No | 3.10 | Python version, default is 3.8. |
    | `-cv` | No | 910b | AI chip version, default is 910b. |
    | `-ps` | No | /tmp/cann.sh | Python installation script, used for building CANN images, with the default being the script in the latest CANN image directory. |
    | `-cs` | No | /tmp/python.sh | CCANN installation script, used for building CANN images, with the default being the script in the latest CANN image directory. |
    | `-dp` | No | /tmp/Dockerfile | When updating application images, you can specify the application image Dockerfile, with the default being the Dockerfile of the latest version of the current image. |