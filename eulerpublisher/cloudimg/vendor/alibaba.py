# -*- coding:utf-8 -*-
import os
import subprocess
import click

from alibabacloud_ecs20140526.client import Client as Ecs20140526Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_20140526_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

DATA_PATH = "/tmp/eulerpublisher/cloudimg/data/"

def push_alibaba(arch, version, bucket, region, image):
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
            image_name = "openEuler-" + version + "-" + arch,
            architecture = arch if arch == 'x86_64' else 'arm64'
        )
        runtime = util_models.RuntimeOptions()
        client.import_image_with_options(import_image_request, runtime)
    except Exception as err:
        raise click.ClickException(
            "\n[Push] (Alibaba cloud) " + str(err)
        )