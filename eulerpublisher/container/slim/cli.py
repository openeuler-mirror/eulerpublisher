# coding=utf-8
import click
import sys
import subprocess
import os

import eulerpublisher.publisher.publisher as pb
from eulerpublisher.container.base.base import OePublisher




#静态分析Dockerfile
@click.command(
    name="lint",
    help=" Inspect container instructions in Dockerfile."
)
@click.option(
    "-r",
    "--report",
    required=False,
    default="lint.report.json",
    show_default=True,
    help="Target location where to save the executed command results."
    ,
)
@click.option(
    "-t",
    "--target",
    required=True,
    help="Path of Dockerfile"
    ,
)

def lint(report, target):
    if pb.check_slim() == pb.PUBLISH_FAILED:
        sys.exit(1)
    ret = subprocess.call(
        f"slim --report {report} lint --target {target}"
        ,
        shell=True
    )

    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    else:
        sys.exit(0)


#静态分析镜像
@click.command(
    name="analyze",
    help="Show what's in the container image and reverse engineer its Dockerfile."
)
@click.option(
    "-r",
    "--report",
    required=False,
    default="analyze.report.json",
    show_default=True,
    help="Target location where to save the executed command results."
    ,
)
@click.option(
    "-i",
    "--image",
    required=True,
    help="Image ID"
    ,
)

def analyze(report, image):
    if pb.check_slim() == pb.PUBLISH_FAILED:
        sys.exit(1)
    ret = subprocess.call(
        f"slim --report {report} xray --target {image}"
        ,
        shell=True
    )

    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    else:
        sys.exit(0)

#动态分析镜像
@click.command(
    name="profile",
    help="Collect fat image information and generate a fat container report"
)
@click.option(
    "-r",
    "--report",
    required=False,
    default="profile.report.json",
    show_default=True,
    help="Target location where to save the executed command results."
    ,
)
@click.option(
    "-i",
    "--image",
    required=True,
    help="Image ID"
    ,
)

def profile(report, image):
    if pb.check_slim() == pb.PUBLISH_FAILED:
        sys.exit(1)
    ret = subprocess.call(
        f"slim --report {report} profile --target {image}"
        ,
        shell=True
    )

    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    else:
        sys.exit(0)

#镜像瘦身
@click.command(
    name="slim",
    help="Reduce the image size without compromising functionality."
)
@click.option(
    "-r",
    "--report",
    required=False,
    default="slim.report.json",
    show_default=True,
    help="Target location where to save the executed command results."
    ,
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

def slim(report, image, tag, http_probe):
    if pb.check_slim() == pb.PUBLISH_FAILED:
        sys.exit(1)

    ret = subprocess.call(
        f"slim --report {report} build --target {image} --tag {tag} --http-probe={http_probe}"
        ,
        shell=True
    )

    if ret != pb.PUBLISH_SUCCESS:
        click.echo("构建失败,尝试关闭http-probe")
        ret = subprocess.call(
        f"slim --report {report} build --target {image} --tag {tag} --http-probe=false"
        ,
        shell=True
        )
        if ret != pb.PUBLISH_SUCCESS:
            click.echo("构建失败")
            sys.exit(1)
        else:
            click.echo("构建成功")
            sys.exit(0)
    else:
        click.echo("构建成功")
        sys.exit(0)


