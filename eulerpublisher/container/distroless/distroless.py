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
        self.version = version
        self.registry = registry
        self.packages = packages
        self.multi_file = common.init_multi_file(multi)
        self.platform = common.init_platform(arch)
        self.dockerfile = common.init_dockerfile(dockerfile, DOCKERFILE_PATH)
        self.workdir = common.init_workdir(self.dockerfile)
        tag = {
            'tag': f"{name}-{common.transform_version_format(os_version=version)}",
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
        return common.build(
            op,
            self.workdir,
            self.dockerfile,
            self.platform,
            self.tags_build,
            build_args
        )

    def push(self):
        return common.push(
            self.registry, self.tags_push, self.multi_file
        )
    
    # this function is only used for publishing multi-platform image
    def build_and_push(self):
        try:
            # login registry
            if (
                pb.login_registry(registry=self.registry, multi=self.multi_file)
                != pb.PUBLISH_SUCCESS
            ):
                return pb.PUBLISH_FAILED
            if self.build(op="push") != pb.PUBLISH_SUCCESS:
                return pb.PUBLISH_FAILED
        except (OSError, subprocess.CalledProcessError) as err:
            click.echo(click.style(f"[Push] {err}", fg="red"))
        click.echo("[Push] finished")
        return pb.PUBLISH_SUCCESS