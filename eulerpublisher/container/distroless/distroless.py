# coding=utf-8
import click
import subprocess


# coding=utf-8
import eulerpublisher.container.distroless.common as common
import eulerpublisher.publisher.publisher as pb
from eulerpublisher.publisher import EP_PATH


DEFAULT_REGISTRY = EP_PATH + "config/container/app/registry.yaml"
TESTCASE_PATH = EP_PATH + "tests/container/app/"
DOCKERFILE_PATH = EP_PATH + "config/container/distroless/Dockerfile"
TESTCASE_SUFFIX = "_test.sh"

class DistrolessPublisher(pb.Publisher):
    def __init__(
        self, repo="", registry="", name="", version="", packages="", arch="", dockerfile="", multi=False
    ):
        self.repo = repo
        self.name = name
        self.arch = arch
        self.version = version
        self.registry = registry
        self.packages = packages
        self.multi_file = common.init_multi_file(multi)
        self.platform = common.init_platform(arch)
        self.dockerfile = common.init_dockerfile(dockerfile, DOCKERFILE_PATH)
        self.workdir = common.init_workdir(self.dockerfile)
        oe_version = common.transform_version_format(os_version=version)
        if self.arch:
            image_tag = f"{name}-{self.arch}-{oe_version}"
        else:
            image_tag = f"{name}-{oe_version}"
        tag = {
            'tag': image_tag,
            'latest': False
        }
        self.tags_build, self.tags_push = common.init_tags(
            registry=registry, repo=repo, tag=tag, multi=self.multi_file
        )

    def build(self, op="load"):
        build_args = {
            "PACKAGES": ",".join(self.packages),
            "VERSION": self.version
        }
        return common.build(op, self, build_args)

    def push(self):
        return common.push(self)
    
    # this function is only used for publishing multi-platform image
    def build_and_push(self):
        build_args = {
            "PACKAGES": ",".join(self.packages),
            "VERSION": self.version
        }
        return common.build_and_push(self, build_args)