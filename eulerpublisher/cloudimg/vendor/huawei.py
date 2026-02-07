# -*- coding:utf-8 -*-
import os
import click
import subprocess

from eulerpublisher.publisher import get_temp_dir

from huaweicloudsdkcore.auth.credentials import BasicCredentials as HuaweiCredential
from huaweicloudsdkims.v2.region.ims_region import ImsRegion
from huaweicloudsdkims.v2 import *

DATA_PATH = get_temp_dir("cloudimg", "data") + os.sep

def push_huawei(arch, version, ak, sk, bucket, region, image):
    from eulerpublisher.publisher import logger

    # 凭证信息
    ims_cred = HuaweiCredential(ak, sk)

    # 上传镜像到OBS存储
    endpoint = "obs." + region + ".myhuaweicloud.com"
    logger.info("[Push] (Huawei cloud) Uploading image to OBS bucket: %s" % bucket)
    try:
        ret = subprocess.call(
            [
                "obsutil",
                "cp",
                DATA_PATH + "output/" + image,
                "obs://" + bucket + "/" + image,
                "-i", ak,
                "-k", sk,
                "-e", endpoint,
            ]
        )
        if ret != 0:
            raise click.ClickException(
                "\n[Push] (Huawei cloud) Failed to upload image to "
                "bucket: %s" % bucket
            )
    except Exception as err:
        raise click.ClickException(
            "\n[Push] (Huawei cloud) Failed to upload image to "
            "bucket: %s" % bucket
        )
    logger.info("[Push] (Huawei cloud) Upload completed successfully")

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
            "\n[Push] (Huawei cloud)" + str(err)
        )