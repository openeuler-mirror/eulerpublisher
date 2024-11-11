# -*- coding:utf-8 -*-
import os
import click
import subprocess
import json

from tencentcloud.common.credential import Credential as TencentCredential
from tencentcloud.cvm.v20170312 import cvm_client, models

DATA_PATH = "/tmp/eulerpublisher/cloudimg/data/"

def push_tencent(arch, version, bucket, region, image):
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