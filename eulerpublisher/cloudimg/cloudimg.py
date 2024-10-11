# -*- coding:utf-8 -*-
import boto3
import click
import datetime
import subprocess
import os
import platform
import wget
import time
import json

from huaweicloudsdkcore.auth.credentials import BasicCredentials as HuaweiCredential
from huaweicloudsdkims.v2.region.ims_region import ImsRegion
from huaweicloudsdkims.v2 import *

from tencentcloud.common.credential import Credential as TencentCredential
from tencentcloud.cvm.v20170312 import cvm_client, models

from alibabacloud_ecs20140526.client import Client as Ecs20140526Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_20140526_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

import eulerpublisher.publisher.publisher as pb
from eulerpublisher.publisher import EP_PATH
from eulerpublisher.publisher import OPENEULER_REPO

DATA_PATH = "/tmp/eulerpublisher/cloudimg/data/"
CONFIG_PATH = EP_PATH + "resource/cloudimg/config/"
SCRIPT_PATH = EP_PATH + "resource/cloudimg/script/"
CLOUD_INIT_CONFIG = CONFIG_PATH + "openeuler.cfg"
DEFAULT_RPMLIST = EP_PATH + "resource/cloudimg/install_packages.txt"
AWS_ROLE_POLICY = CONFIG_PATH + "role-policy.json"
AWS_TRUST_POLICY = CONFIG_PATH + "trust-policy.json"

def _push_huaweicloud(arch, version, bucket, region, image):
    # 获取凭证信息
    ak = os.getenv("HUAWEICLOUD_SDK_AK")
    sk = os.getenv("HUAWEICLOUD_SDK_SK")
    ims_cred = HuaweiCredential(ak, sk)

    # 上传镜像到OBS存储
    try:
        subprocess.call(
            [
                "obsutil",
                "cp",
                DATA_PATH + "output/" + image,
                "obs://" + bucket + "/" + image,
            ]
        )
    except Exception:
        raise click.ClickException(
            "\n[Push] (Huawei cloud) Failed to upload image to "
            "bucket: %s" % bucket
        )
    
    # 创建IMS客户端对象
    ims_client = ImsClient.new_builder() \
                .with_credentials(ims_cred) \
                .with_region(ImsRegion.value_of(region)) \
                .build()

    # 发起创建镜像请求
    try:
        req = CreateImageRequest()
        req.body = CreateImageRequestBody(
            image_url = bucket + ":" + image,
            name = "openEuler-" + version + "-" + arch,
            os_version = "Other Linux(64 bit)",
            min_disk = 40
        )
        resp = ims_client.create_image(req)
    except Exception as err:
        raise click.ClickException(
            "\n[Push] (Huawei cloud) " + str(err)
        )

def _push_tencentcloud(arch, version, bucket, region, image):
    # 获取凭证信息
    ak = os.getenv("TENCENTCLOUD_SDK_AK")
    sk = os.getenv("TENCENTCLOUD_SDK_SK")
    cvm_cred = TencentCredential(ak, sk)

    # 上传镜像到COS存储
    try:
        subprocess.call(
            [
                "coscli",
                "cp",
                DATA_PATH + "output/" + image,
                "cos://" + bucket + "/" + image,
            ]
        )
    except Exception:
        raise click.ClickException(
            "\n[Push] (Tencent cloud) Failed to upload image to "
            "bucket: %s" % bucket
        )

    # 创建CVM客户端对象
    client = cvm_client.CvmClient(cvm_cred, region)

    # 发起创建镜像请求
    try:
        req = models.ImportImageRequest()
        params = {
            "ImageName": "openEuler-" + version + "-" + arch,
            "ImageUrl": "https://" + bucket + ".cos." + region + ".myqcloud.com/" + image,
            "Architecture": arch,
            "OsType": "Other Linux",
            "OsVersion": "-",
            "Force": True
        }
        req.from_json_string(json.dumps(params))
        resp = client.ImportImage(req)
    except Exception as err:
        raise click.ClickException(
            "\n[Push] (Tencent cloud) " + str(err)
        )

def _push_alibabacloud(arch, version, bucket, region, image):
    # 获取凭证信息
    ak = os.getenv("ALIBABACLOUD_SDK_AK")
    sk = os.getenv("ALIBABACLOUD_SDK_SK")
    config = open_api_models.Config(ak, sk)
    config.endpoint = "ecs." + region + ".aliyuncs.com"
    
    # 上传镜像到OSS存储
    try:
        subprocess.call(
            [
                "ossutil",
                "cp",
                DATA_PATH + "output/" + image,
                "oss://" + bucket + "/" + image,
            ]
        )
    except Exception:
        raise click.ClickException(
            "\n[Push] (Alibaba cloud) Failed to upload image to "
            "bucket: %s" % bucket
        )

    # 创建ECS客户端对象
    client = Ecs20140526Client(config)
    
    # 发起创建镜像请求
    try:
        disk_device_mapping_0 = ecs_20140526_models.ImportImageRequestDiskDeviceMapping(
            ossbucket = bucket,
            ossobject = image
        )
        import_image_request = ecs_20140526_models.ImportImageRequest(
            region_id = region,
            disk_device_mapping = [
                disk_device_mapping_0
            ],
            role_name = 'AliyunECSImageImportDefaultRole',
            platform = 'Others Linux',
            image_name = "openEuler-" + version + "-" + arch
        )
        runtime = util_models.RuntimeOptions()
        client.import_image_with_options(import_image_request, runtime)
    except Exception as err:
        raise click.ClickException(
            "\n[Push] (Alibaba cloud) " + str(err)
        )

def _aws_check_role(client):
    resp = client.list_roles()
    for role in resp["Roles"]:
        if role["RoleName"] == "vmimport":
            return True
    return False

def _aws_create_policy(bucket=""):
    with open(AWS_ROLE_POLICY, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    data["Statement"][0]["Resource"] = [
        "arn:aws:s3:::" + bucket,
        "arn:aws:s3:::" + bucket + "/*",
    ]
    data["Statement"][1]["Resource"] = [
        "arn:aws:s3:::" + bucket,
        "arn:aws:s3:::" + bucket + "/*",
    ]
    with open(AWS_ROLE_POLICY, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _push_aws(arch, version, bucket, region, image):
    # 获取凭证信息
    ak = os.getenv("AWS_SDK_AK")
    sk = os.getenv("AWS_SDK_SK")

    # 上传镜像到S3存储
    try:
        subprocess.call(
            [
                "aws",
                "s3",
                "cp",
                DATA_PATH + "output/" + image,
                "s3://" + bucket + "/" + image,
            ]
        )
    except Exception:
        raise click.ClickException(
            "[Push] (Amazon web services) Failed to upload image to "
            "bucket: %s" % bucket
        )

    # 创建EC2和IAM客户端对象
    ec2_client = boto3.client("ec2", aws_access_key_id=ak, aws_secret_access_key=sk)
    iam_client = boto3.client("iam", aws_access_key_id=ak, aws_secret_access_key=sk)

    # 根据实际信息修改role_policy
    _aws_create_policy(bucket)

    # 创建vmimport role
    if not _aws_check_role(iam_client):
        trust_policy = open(AWS_TRUST_POLICY)
        iam_client.create_role(
            RoleName="vmimport", AssumeRolePolicyDocument=trust_policy.read()
        )
        trust_policy.close()
        
    # 写入role policy
    role_policy = open(AWS_ROLE_POLICY)
    try:
        iam_client.put_role_policy(
            RoleName="vmimport",
            PolicyName="vmimport",
            PolicyDocument=role_policy.read(),
        )
    except Exception as err:
        raise click.ClickException("[Push] (Amazon web services) " + str(err))
    role_policy.close()

    # 导入镜像snapshot
    try:
        resp = ec2_client.import_snapshot(
            Description="Import snapshot for " + "openEuler-" + version + "-" + arch,
            DiskContainer={
                "Description": image,
                "Format": "RAW",
                "UserBucket": {
                    "S3Bucket": bucket,
                    "S3Key": image,
                },
            },
            RoleName="vmimport",
        )
    except Exception as err:
        raise click.ClickException(
            "[Push] (Amazon web services) " + str(err)
        )

    # 循环查询snapshot导入是否完成，完成后获取其ID
    import_taskid = resp["ImportTaskId"]
    status = resp["SnapshotTaskDetail"]["Status"]
    while status != "completed":
        resp = ec2_client.describe_import_snapshot_tasks(
            ImportTaskIds=[import_taskid]
        )
        status = resp["ImportSnapshotTasks"][0]["SnapshotTaskDetail"]["Status"]
        time.sleep(2)
    snapshot_id = resp["ImportSnapshotTasks"][0]["SnapshotTaskDetail"]["SnapshotId"]

    # 根据snapshot_id制作AMI镜像
    if arch == "aarch64":
        arch = "arm64"
    resp = ec2_client.register_image(
        Name="openEuler-" + version + "-" + arch,
        Architecture=arch,
        BlockDeviceMappings=[
            {"DeviceName": "/dev/xvda", "Ebs": {"SnapshotId": snapshot_id}}
        ],
        EnaSupport=True,
        RootDeviceName="/dev/xvda",
        VirtualizationType="hvm",
    )
    image_id = resp["ImageId"]

class CloudimgPublisher(pb.Publisher):
    def __init__(self, target="", version="", arch="", rpmlist="", bucket="", region="", image=""):
        # 目标云厂商
        self.target = target
        # 镜像版本号
        self.version = version.upper()
        # 镜像架构类型
        if arch != str(platform.machine()):
            raise TypeError(
                "Unsupported architecture "
                + arch
                + "while current host architecture is "
                + str(platform.machine())
            )
        self.arch = arch
        # 获取要预安装的软件包列表，不显示指定时安装默认包
        if not rpmlist:
                self.rpmlist = DEFAULT_RPMLIST
        else:
                self.rpmlist = os.path.abspath(rpmlist)
        # 存储桶
        self.bucket = bucket
        # 地域
        self.region = region
        # 镜像文件
        self.image = image

    def prepare(self):
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH, exist_ok=True)
        os.chdir(DATA_PATH)
        qcow2_file = "openEuler-" + self.version + "-" + self.arch + ".qcow2"
        xz_file = "openEuler-" + self.version + "-" + self.arch + ".qcow2.xz"
        if not os.path.exists(qcow2_file):
            if not os.path.exists(xz_file):
                url = (
                    OPENEULER_REPO
                    + "openEuler-"
                    + self.version
                    + "/"
                    + "virtual_machine_img"
                    + "/"
                    + self.arch
                    + "/"
                    + xz_file
                )
                try:
                    click.echo("\n[Prepare] Downloading '%s'..." % xz_file)
                    wget.download(url)
                except Exception as err:
                    raise click.ClickException("\n[Prepare] " + str(err))
            if subprocess.call(["unxz", "-f", xz_file]):
                click.echo(click.style("\n[Prepare] Failed to unxz '%s'." % xz_file, fg="red"))
                return pb.PUBLISH_FAILED
        click.echo(click.style("\n[Prepare] Finished.", fg="green"))
        return pb.PUBLISH_SUCCESS

    def build(self):
        qcow2_file = "openEuler-" + self.version + "-" + self.arch + ".qcow2"
        if not os.path.exists(DATA_PATH + qcow2_file):
            click.echo(click.style("\n[Build] Failed to find original image '%s'." % qcow2_file, fg="red"))
            return pb.PUBLISH_FAILED

        if self.target == "aws":
            script = SCRIPT_PATH + "aws_install.sh"
        else:
            script = SCRIPT_PATH + "gen_install.sh"
        args = [qcow2_file, DATA_PATH, CLOUD_INIT_CONFIG, self.rpmlist]
        if subprocess.call(["sudo", "sh", script] + args):
            click.echo(click.style("\n[Build] Failed to build cloud image.", fg="red"))
            return pb.PUBLISH_FAILED
        click.echo(click.style("\n[Build] Finished.", fg="green"))
        return pb.PUBLISH_SUCCESS

    def push(self):
        if not os.path.exists(DATA_PATH + "output/" + self.image):
            click.echo(click.style("\n[Push] Failed to find cloud image '%s'." % self.image, fg="red"))
            return pb.PUBLISH_FAILED
        
        if self.target == "huawei":
            _push_huaweicloud(self.arch, self.version, self.bucket, self.region, self.image)
        elif self.target == "tencent":
            _push_tencentcloud(self.arch, self.version, self.bucket, self.region, self.image)
        elif self.target == "alibaba":
            _push_alibabacloud(self.arch, self.version, self.bucket, self.region, self.image)
        elif self.target == "aws":
            _push_aws(self.arch, self.version, self.bucket, self.region, self.image)
        else:
            click.echo(click.style("\n[Push] Unsupported public cloud.", fg="red"))
            return pb.PUBLISH_FAILED

        click.echo(click.style("\n[Push] Finished.", fg="green"))
        return pb.PUBLISH_SUCCESS
