# coding=utf-8
import os
import shutil
import subprocess
import yaml
import eulerpublisher.publisher.publisher as pb
from eulerpublisher.publisher import EP_PATH
from eulerpublisher.publisher import logger


DISTROLESS_CACHE_PATH = "/tmp/eulerpublisher/container/distroless"
DEFAULT_REGISTRY = EP_PATH + "config/container/distroless/registry.yaml"
DOCKERFILE_PATH = EP_PATH + "config/container/distroless/Dockerfile"
TESTCASE_PATH = EP_PATH + "tests/container/app/"
TESTCASE_SUFFIX = "_test.sh"


def parse_build_yaml(configfile: str):
    try:
        with open(configfile, "r") as f:
            params = yaml.safe_load(f)
        base = params.get("base", "")
        parts = ' '.join(params.get("parts", ""))
        release = params.get("release", "")
        # "linux/amd64,linux/arm64"
        arches = params.get("platforms", "")
    except FileNotFoundError:
            logger.error(f"The file '{configfile}' was not found.")
    except yaml.YAMLError as e:
        logger.error(f"Failed to read '{configfile}' as yaml: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    
    return base, parts, arches, release

# tag image for all registries
def init_tags(registry, repo, tag: str, multi):
    full_repos = []
    if not multi:
        full_repos.append(registry + '/' + repo)
    else:
        with open(multi, "r") as f:
            env = yaml.safe_load(f)
        for key in env:
            full_repos.append(str(key) + '/' + repo)
    tags_bulid = ""
    for item in full_repos:
        tags_bulid += "-t " + item + ":" + tag
        tags_bulid += " "
    return tags_bulid

def get_multi_file(multi):
    if multi:
        # if EP_LOGIN_FILE exists or valuable
        if (not "EP_LOGIN_FILE" in os.environ) or (not os.environ["EP_LOGIN_FILE"]):
            return DEFAULT_REGISTRY
        else:
            return os.path.abspath(os.environ["EP_LOGIN_FILE"])
    else:
        return ""

def run_build_command(command, workdir=DISTROLESS_CACHE_PATH, dockerfile=DOCKERFILE_PATH):
    try:
        if not os.path.exists(workdir):
            os.makedirs(workdir)
        os.chdir(workdir)
        if workdir != os.path.dirname(dockerfile):
            shutil.copy2(dockerfile, "./")
        # ensure qemu is installed
        if pb.check_qemu() != pb.PUBLISH_SUCCESS:
            return pb.PUBLISH_FAILED
        # ensure the docker is starting
        if pb.start_docker() != pb.PUBLISH_SUCCESS:
            return pb.PUBLISH_FAILED
        # build images with 'buildx'
        builder = pb.create_builder()
        ret = subprocess.call(command, shell=True)
        subprocess.call(["docker", "buildx", "stop", builder])
        subprocess.call(["docker", "buildx", "rm", builder])
        if ret != 0:
            return pb.PUBLISH_FAILED
    except (OSError, subprocess.CalledProcessError) as err:
        raise err
    logger.info("[Build] finished")
    return pb.PUBLISH_SUCCESS


class DistrolessPublisher(pb.Publisher):
    def __init__(self,
                 repo="",
                 registry="",
                 configfile="",
                 tag="",
                 multi=False
        ):
        self.repo = repo
        self.registry = registry
        self.multi_file = get_multi_file(multi)
        self.workdir = DISTROLESS_CACHE_PATH
        self.tags_build = init_tags(
            registry=registry, repo=repo, tag=tag, multi=self.multi_file
        )
        self.base, self.parts, self.arches, self.release = parse_build_yaml(os.path.abspath(configfile))


    def prepare(self):
        for arch in self.arches:
            """
            rootfs: 
            1. The directory of rootfs, such as, `openEuler-distroless-rootfs.amd64`
            2. `rootfs` is ADDed by `config/container/distroless/Dockerfile` to generate final image
            """
            rootfs = "openEuler-distroless-rootfs." + arch.split('/')[-1]
            logger.info(f"|+++++++ output-path{self.workdir}/{rootfs}/ ++++++++|")
            command = "splitter cut -a {} -r {} -o {} {}".format(
                arch, self.release, f"{self.workdir}/{rootfs}/", self.parts
            )
            ret = subprocess.call(command, shell=True)
            if ret != pb.PUBLISH_SUCCESS:
                logger.error(f"Failed to generate required slices for {arch}")
                return pb.PUBLISH_FAILED
        return pb.PUBLISH_SUCCESS
    
    def build(self, op="load"):
        if (op == "load") and (len(self.arches) > 1):
            logger.warning(
                "Multi-platform image can not be loaded on local host, "
                "please use `publish` command to build and push the image to hubs."
            )
            return pb.PUBLISH_FAILED
        # generate required slices
        if self.prepare() != pb.PUBLISH_SUCCESS:
            return pb.PUBLISH_FAILED
        # build image from slices
        build_args = f"--build-arg BASE={self.base}"
        command = "docker buildx build --platform {} {} {} --{} .".format(
            ','.join(self.arches), self.tags_build, build_args, op
        )
        return run_build_command(command, workdir=self.workdir)


    def build_and_push(self):
        try:
            if pb.login_registry(registry=self.registry, multi=self.multi_file) != pb.PUBLISH_SUCCESS:
                return pb.PUBLISH_FAILED
            if self.build(op="push") != pb.PUBLISH_SUCCESS:
                return pb.PUBLISH_FAILED
        except (OSError, subprocess.CalledProcessError) as err:
            logger.error(f"[Push] {err}")
        logger.info("[Push] finished")
        return pb.PUBLISH_SUCCESS