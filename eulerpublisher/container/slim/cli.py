# coding=utf-8
import click
import sys
import subprocess
import os

import eulerpublisher.publisher.publisher as pb
from eulerpublisher.container.base.base import OePublisher


# @click.group(
#     name="slim",
#     help="Command for analyzing and slimming images"
# )
# def group():
#     pass

@click.command(
    name="analyze",
    help="Show what's in the container image and reverse engineer its Dockerfile"
)
@click.option(
    "-i",
    "--image",
    required=True,
    help="Image ID"
    ,
)

def analyze(image):
    if pb.check_slim() == pb.PUBLISH_FAILED:

        sys.exit(1)
    ret = subprocess.call(
        f"slim xray --target {image}"
        ,
        shell=True
    )

    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    else:
        sys.exit(0)


@click.command(
    name="slim",
    help="Reduce the image size without compromising functionality."
)
@click.option(
    "-i",
    "--image",
    required=True,
    help="Image ID"
        ,
)
@click.option(
    "-t",
    "--tag",
    required=True,
    help=" slimmed image tag, "
        ,
)
@click.option(
    "-p",
    "--http-probe",
    type=bool,
    default=True,
    show_default=True,
    help="Enable HTTP probe to check if services are up in the slimmed image (default: True).",
)

def slim(image, tag, http_probe):
    if pb.check_slim() == pb.PUBLISH_FAILED:
        sys.exit(1)

    ret = subprocess.call(
        f"slim build --target {image} --tag {tag} --http-probe={http_probe}"
        ,
        shell=True
    )

    if ret != pb.PUBLISH_SUCCESS:
        print("构建失败,尝试关闭http-probe")
        ret = subprocess.call(
        f"slim build --target {image} --tag {tag} --http-probe=false"
        ,
        shell=True
        )
        if ret != pb.PUBLISH_SUCCESS:
            print("构建失败")
            sys.exit(1)
        else:
            print("构建成功")
            sys.exit(0)
    else:
        print("构建成功")
        sys.exit(0)


