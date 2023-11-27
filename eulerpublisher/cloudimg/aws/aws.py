# -*- coding:utf-8 -*-
import boto3
import click
import datetime
import json
import shutil
import subprocess
import os
import platform
import time
import wget


from botocore.exceptions import ClientError
import eulerpublisher.publisher.publisher as pb
from eulerpublisher.publisher import EP_PATH
from eulerpublisher.publisher import OPENEULER_REPO


ROLE_NAME = "vmimport"
SCRIPT_PATH = EP_PATH + "cloudimg/script/"
PACKER_FILE_PATH = EP_PATH + "cloudimg/aws/"
ROLE_POLICY = PACKER_FILE_PATH + "role-policy.json"
TRUST_POLICY = PACKER_FILE_PATH + "trust-policy.json"
DEFAULT_RPMLIST = PACKER_FILE_PATH + "install_packages.txt"
AWS_DATA_PATH = "/home/tmp/eulerpublisher/cloudimg/data/aws/"


def _check_credentials():
    config = os.path.join(os.environ["HOME"], ".aws", "config")
    credentials = os.path.join(os.environ["HOME"], ".aws", "credentials")
    if not os.path.exists(config) or not os.path.exists(credentials):
        raise TypeError(
            "AWS credentials are not configured,"
            " please run `aws configure` to configure first."
        )


def _check_role(client):
    resp = client.list_roles()
    for role in resp["Roles"]:
        if role["RoleName"] == ROLE_NAME:
            return True
    return False


def _find_object(client, name, bucket):
    resp = client.list_objects(Bucket=bucket)
    for obj in resp["Contents"]:
        if obj["Key"] == name:
            return True
    return False


def _create_policy(bucket=""):
    with open(ROLE_POLICY, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    data["Statement"][0]["Resource"] = [
        "arn:aws:s3:::" + bucket,
        "arn:aws:s3:::" + bucket + "/*",
    ]
    data["Statement"][1]["Resource"] = [
        "arn:aws:s3:::" + bucket,
        "arn:aws:s3:::" + bucket + "/*",
    ]
    with open(ROLE_POLICY, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _resize_cloudimg(arch, version):
    script = SCRIPT_PATH + "aws_resize.sh"
    args = [version, arch, AWS_DATA_PATH]
    subprocess.call(["sudo", "sh", script] + args)


def _make_base_image(arch, version):
    if not os.path.exists(AWS_DATA_PATH):
        os.makedirs(AWS_DATA_PATH, exist_ok=True)
    os.chdir(AWS_DATA_PATH)
    raw_file = "openEuler-" + version + "-" + arch + ".raw"
    qcow2_file = "openEuler-" + version + "-" + arch + ".qcow2"
    xz_file = "openEuler-" + version + "-" + arch + ".qcow2.xz"
    if not os.path.exists(raw_file):
        if not os.path.exists(qcow2_file):
            if not os.path.exists(xz_file):
                url = (
                    OPENEULER_REPO
                    + "openEuler-"
                    + version + "/"
                    + "virtual_machine_img"
                    + "/"
                    + arch
                    + "/"
                    + xz_file
                )
                try:
                    click.echo("\nDownloading " + xz_file + "...")
                    wget.download(url)
                except Exception as err:
                    raise click.ClickException("[Prepare] " + str(err))
            subprocess.call(["unxz", "-f", xz_file])
        _resize_cloudimg(arch=arch, version=version)


def _create_packer(arch, region, img_name, source, rpmlist):
    file = PACKER_FILE_PATH + "aws_" + arch + ".json"
    with open(rpmlist, "r") as rpms:
        packages = rpms.read()
    with open(file, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    data["builders"][0]["region"] = region
    data["builders"][0]["ami_regions"] = [region]
    data["builders"][0]["source_ami"] = source
    data["builders"][0]["ami_name"] = img_name + "-hvm"
    data["provisioners"][0]["environment_vars"] = [
        "INSTALL_PACKAGES=" + packages
    ]
    data["provisioners"][0]["script"] = SCRIPT_PATH + "aws_install.sh"
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


class AwsPublisher(pb.Publisher):
    def __init__(self,
                 version="",
                 arch="",
                 bucket="", 
                 region="",
                 rpmlist=""):
        # 关键参数
        self.img_name = "openEuler-" + version + "-" + arch
        self.version = version
        self.bucket = bucket
        self.region = region
        # 获取支持的架构类型
        if arch != str(platform.machine()):
            raise TypeError(
                "Unsupported architecture " + arch + \
                ", while current host architecture is " + \
                str(platform.machine())
            )
        self.arch = arch
        # 获取要预安装的软件包列表，不显示指定时安装默认包
        if not rpmlist:
            self.rpmlist = DEFAULT_RPMLIST
        else:
            self.rpmlist = os.path.abspath(rpmlist)
        # check aws configure
        _check_credentials()
        # 创建S3客户端
        self.s3_client = boto3.client("s3")
        # 创建IAM客户端
        self.iam_client = boto3.client("iam")
        # 创建EC2客户端
        self.ec2_client = boto3.client("ec2")

    def prepare(self):
        # 获取基础镜像
        _make_base_image(arch=self.arch,
                         version=self.version
        )
        # 上传镜像到S3存储
        key = self.img_name + ".raw"
        if not _find_object(self.s3_client, key, self.bucket):
            click.echo("[Prepare] Uploading raw image to s3 bucket: %s..."
                % self.bucket)
            # 直接使用awscli可以方便实时显示上传进度
            try:
                subprocess.call([
                    "aws",
                    "s3",
                    "cp",
                    AWS_DATA_PATH + key,
                    "s3://" + self.bucket + "/" + key
                ])
            except Exception:
                raise click.ClickException(
                    "[Prepare] Failed to upload raw image to "
                    "s3 bucket: %s" % self.bucket
                )
        else:
            click.echo(
                "[Prepare] %s is already existed on S3://%s, "
                "please delete and re-upload it if you want."
                % (key, self.bucket)
            )
        # 根据实际信息修改role_policy
        _create_policy(self.bucket)
        # 创建vmimport role
        if not _check_role(self.iam_client):
            trust_policy = open(TRUST_POLICY)
            self.iam_client.create_role(
                RoleName=ROLE_NAME,
                AssumeRolePolicyDocument=trust_policy.read()
            )
        # 写入role policy
        role_policy = open(ROLE_POLICY)
        try:
            self.iam_client.put_role_policy(
                RoleName=ROLE_NAME,
                PolicyName=ROLE_NAME,
                PolicyDocument=role_policy.read(),
            )
        except ClientError as e:
            raise click.ClickException(str(e))

        click.echo("[Prepare] finished.\n")

    def build(self):
        # step-1. 导入镜像snapshot
        try:
            resp = self.ec2_client.import_snapshot(
                Description="Import snapshot for " + self.img_name,
                DiskContainer={
                    "Description": self.img_name,
                    "Format": "RAW",
                    "UserBucket": {
                        "S3Bucket": self.bucket,
                        "S3Key": self.img_name + ".raw",
                    },
                },
                RoleName=ROLE_NAME,
            )
        except ClientError as e:
            raise click.ClickException("\n[Build] " + str(e))

        # 循环查询snapshot导入是否完成，完成后获取其ID
        import_taskid = resp["ImportTaskId"]
        status = resp["SnapshotTaskDetail"]["Status"]
        while status != "completed":
            resp = self.ec2_client.describe_import_snapshot_tasks(
                ImportTaskIds=[import_taskid]
            )
            status = \
                resp["ImportSnapshotTasks"][0]["SnapshotTaskDetail"]["Status"]
            time.sleep(2)
        snapshot_id = \
            resp["ImportSnapshotTasks"][0]["SnapshotTaskDetail"]["SnapshotId"]

        # step-2. 根据snapshot_id制作基础AMI镜像
        time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.arch == "aarch64":
            arch = "arm64"
        else:
            arch = self.arch
        resp = self.ec2_client.register_image(
            Name=self.img_name + "-" + time_str + "-BASE",
            Architecture=arch,
            BlockDeviceMappings=[{
                "DeviceName": "/dev/xvda",
                "Ebs": {"SnapshotId": snapshot_id}
            }],
            Description="This is an middleware used to build final image.",
            EnaSupport=True,
            RootDeviceName="/dev/xvda",
            VirtualizationType="hvm",
        )
        image_id = resp["ImageId"]

        # 3. packer build最终镜像，可通过aws_install.sh定制
        _create_packer(
            arch=self.arch,
            region=self.region,
            img_name=self.img_name + "-" +
                datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
            source=image_id,
            rpmlist=self.rpmlist
        )
        try:
            subprocess.call([
                "packer",
                "build",
                PACKER_FILE_PATH + "aws_" + self.arch + ".json"
            ])
        except Exception:
            raise click.ClickException("[Build] Failed to build final image.")

        click.echo("[Build] finished\n")
