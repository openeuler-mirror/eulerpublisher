# -*- coding:utf-8 -*-
import boto3
import os
import click
import json
import subprocess
import time

from eulerpublisher.publisher import EP_PATH
DATA_PATH = "/tmp/eulerpublisher/cloudimg/data/"
RESOURCE_PATH = EP_PATH + "config/cloudimg/resource/"
AWS_ROLE_POLICY = RESOURCE_PATH + "role-policy.json"
AWS_TRUST_POLICY = RESOURCE_PATH + "trust-policy.json"

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

def push_aws(arch, version, bucket, region, image):
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
