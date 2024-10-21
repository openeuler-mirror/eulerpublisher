# -*- coding:utf-8 -*-
import os
import click
import subprocess

from huaweicloudsdkcore.auth.credentials import BasicCredentials as HuaweiCredential
from huaweicloudsdkims.v2.region.ims_region import ImsRegion
from huaweicloudsdkims.v2 import *

DATA_PATH = "/tmp/eulerpublisher/cloudimg/data/"

def push_huawei(arch, version, bucket, region, image):
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
    except Exception as err:
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