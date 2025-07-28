# coding=utf-8
import argparse
import json
import requests
import subprocess
import shutil
import sys
import os
import platform

from eulerpublisher.publisher import logger, DEFAULT_APP_ARCHES, AVAILABLE_ARCHES
import format

REPOSITORY_REQUEST_URL = (
    "https://gitee.com/api/v5/repos/openeuler/openeuler-docker-images/pulls/"
)
MAX_REQUEST_COUNT = 20
SUCCESS_CODE = 200
TEST_NAMESPACE = "openeulertest"
OFFICIAL_NAMESPACE = "openeuler"
DEFAULT_WORKDIR = "/tmp/eulerpublisher/ci/container/"


def _request(method: str, url: str, body=None, timeout=MAX_REQUEST_COUNT):
    # support only `get` and `post`
    if method.lower() not in ["get", "post"]:
        return 1
    # set timeout
    cnt = 0
    response = None
    try:
        while (not response) and (cnt < timeout):
            if method.lower() == "get":
                response = requests.get(url=url)
            else:
                json = {
                    "access_token": os.environ["GITEE_API_TOKEN"],
                    "body": body
                }
                response = requests.post(url=url, json=json)
            cnt += 1
    except requests.exceptions.Timeout as e:
        logger.warning("requests timeout")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning("requests exception, %s", e)
        return None
    return response


def _push_readme(file: str, namespace: str, image_dir: str):
    current = os.path.dirname(os.path.abspath(__file__))
    script = os.path.abspath(os.path.join(current, '../pushrm/pushrm.sh'))
    os.chmod(script, 0o755)
    try:
        subprocess.run(
            [script, file, namespace, image_dir.split("/")[-1]],
            env={**os.environ, 'APIKEY__QUAY_IO': os.environ.get("DOCKER_QUAY_APIKEY", "")}
        )
        return True
    except subprocess.CalledProcessError as err:
        logger.error(f"{err}")
    return False


def _check_app_image(file: str):
    # build and push multi-platform image to `openeulertest`
    image_dir = format.parse_image_directory(file)
    name, tag, arch = format.parse_meta_yml(file=file, image_dir=image_dir)

    # To denote different arches
    local_arch = platform.machine()
    test_tag = tag['tag'] + f"-{local_arch}"
    
    # each CI node only build the same-arch image
    if not arch or local_arch in arch:
        if subprocess.call([
            "eulerpublisher",
            "container",
            "app",
            "publish",
            "-a", local_arch,
            "-p", f"{TEST_NAMESPACE}/{name}",
            "-t", test_tag,   
            "-l", "False",
            "-f", file
        ]) != 0:
            return 1
        # check image pulled from hub
        if subprocess.call([
            "eulerpublisher",
            "container",
            "app",
            "check",
            "-h", TEST_NAMESPACE,
            "-n", name,
            "-t", test_tag
        ]) != 0:
            return 1
    return 0


def _check_distroless_image(file: str):
    # build and push distroless image to `openeulertest`
    image_dir = format.parse_image_directory(file)
    name, tag, arch = format.parse_meta_yml(file=file, image_dir=image_dir)
    if subprocess.call([
        "eulerpublisher",
        "container",
        "distroless",
        "publish",
        "-p", f"{TEST_NAMESPACE}/{name}",
        "-t", tag['tag'],
        "-f", file
    ]) != 0:
        return 1
    return 0


def _publish_app_image(file: str, image_dir: str):
    # build and push multi-platform image to `openeuler`
    name, tag, arch = format.parse_meta_yml(file=file, image_dir=image_dir)
    # multiple single-arch images are denoted by different arch suffixs
    verified_tags = []
    registry_tag = f"docker.io/{TEST_NAMESPACE}/{name}:{tag['tag']}"

    if arch:
        arches = arch.replace(" ", "").split(",")
    else:
        arches = DEFAULT_APP_ARCHES.keys()

    for specify_arch in arches:
        verified_tags.append(f"{registry_tag}-{specify_arch}")

    full_tag = f"{name}:{tag['tag']}"
    success = True
    if subprocess.call([
        "eulerpublisher",
        "container",
        "app",
        "publish",
        "-a", arch,
        "-p", f"{OFFICIAL_NAMESPACE}/{name}",
        "-t", tag['tag'],
        "-l", tag['latest'],
        "-s", " ".join([f"{tag}" for tag in verified_tags]),
        "-f", file,
        "-m"
    ]) != 0:
        success = False
    return full_tag, success


def _publish_distroless_image(file: str, image_dir: str):
    # build and push distroless image to `openeuler`
    name, tag, arch = format.parse_meta_yml(file=file, image_dir=image_dir)
    full_tag = f"{name}:{tag['tag']}"
    success = True
    if subprocess.call([
        "eulerpublisher",
        "container",
        "distroless",
        "publish",
        "-p", f"{OFFICIAL_NAMESPACE}/{name}",
        "-t", tag['tag'],
        "-f", file,
        "-m"
    ]) != 0:
        success = False
    return full_tag, success


class ContainerVerification:
    '''
    Check whether the upstream application supports openEuler
    1. Build container image with Dockerfile
    2. Test the container image
    3. Comment the PR with test result
    '''

    def __init__(self,
                 prid,
                 operation,
                 source_repo,
                 source_code_url,
                 source_branch,
                 ):
        self.prid = prid
        self.source_repo = source_repo
        self.source_code_url = source_code_url
        self.source_branch = source_branch
        self.workdir = DEFAULT_WORKDIR + f"{operation}/{self.source_repo}"
        self.change_files = []
        if os.path.exists(self.workdir):
            shutil.rmtree(self.workdir)

    def get_change_files(self):
        url = REPOSITORY_REQUEST_URL + f"{self.prid}/files?access_token=" + \
              os.environ["GITEE_API_TOKEN"]
        response = _request(method="get", url=url)
        # check status code
        if response.status_code == SUCCESS_CODE:
            files = response.json()
            for file in files:
                self.change_files.append(file['filename'])
        else:
            logger.error(f"Failed to fetch files: {response.status_code}")
            return 1
        return 0

    def pull_source_code(self):
        # create workdir
        if not os.path.exists(DEFAULT_WORKDIR):
            os.makedirs(DEFAULT_WORKDIR)
        # git clone
        s_repourl = self.source_code_url
        s_branch = self.source_branch
        if subprocess.call(
            ['git', 'clone', '-b', s_branch, s_repourl, self.workdir]
        ) != 0:
            logger.error(f"Failed to clone {s_repourl}")
            return 1
        logger.info(f"Clone {s_repourl} successfully.")
        return 0

    def comment_publish_result(self, columns, status):
        head = "<tr>" + " ".join(f"<th>{column}</th>" for column in columns) + "</tr>"
        body = ""
        for tag, success in status.items():
            result = ":white_check_mark:SUCCESS"
            if not success:
                result = ":x:FAILED"
            body += f"<tr><th colspan=2>{tag}</th> <th>{result}</th></tr>"
        return self.post_comment_to_pr(head, body)

    def post_comment_to_pr(self, head, body):
        # all publish results
        comment = "<table>" + head + body + "</table>"
        # post comment
        url = f"{REPOSITORY_REQUEST_URL}{self.prid}/comments"
        rs = _request(method="post", url=url, body=comment)
        if not rs:
            logger.warning("comment pull request failed")
            return 1
        return 0

    def check_updates(self):
        os.chdir(self.workdir)
        # build update images by Dockerfiles
        for file in self.change_files:
            if not os.path.exists(file):
                logger.info(f"The file: {file} is deleted, no need to check.")
                continue
            if os.path.basename(file) == "Dockerfile":
                if _check_app_image(file=file) != 0:
                    return 1
            elif os.path.basename(file) == "Distrofile":
                if _check_distroless_image(file=file) != 0:
                    return 1
            else:
                continue
        return 0

    def check_code(self):
        """
        Image release compliance check, see README.md for details.
        """
        os.chdir(self.workdir)
        head, body, fail_count = format.check_report(self.change_files)

        if fail_count:
            logger.error("There are some specification errors for releasing "
                         "on appstore in this PR, please check as above.")
            self.post_comment_to_pr(head, body)
            return 1
        logger.info("The image specification check for releasing on appstore has passed.")
        return 0


    def publish_updates(self):
        os.chdir(self.workdir)
        status = {}
        columns = []
        for file in self.change_files:
            if not os.path.exists(file):
                logger.info(f"The file: {file} is deleted, no need to publish.")
                continue
            # update readme while changed file is README.md
            image_dir = format.parse_image_directory(file)
            columns = ["Image Tag", "Publish Result"]
            if os.path.basename(file) == "README.md":
                columns = ["Image Readme", "Publish Result"]
                success = _push_readme(file=file, namespace="openeuler", image_dir=image_dir)
                status[file] = success
            elif os.path.basename(file) == "Dockerfile":
                full_tag, success = _publish_app_image(file=file, image_dir=image_dir)
                status[full_tag] = success
            elif os.path.basename(file) == "Distrofile":
                full_tag, success = _publish_distroless_image(file=file, image_dir=image_dir)
                status[full_tag] = success
            else:
                continue
        self.comment_publish_result(columns, status)
        if False in status.values():
            return 1
        return 0


def init_parser():
    new_parser = argparse.ArgumentParser(
        prog="update.py",
        description="update application container images",
    )

    new_parser.add_argument("-pr", "--prid", help="Pull Request ID")
    new_parser.add_argument(
        "-sr", "--source_repo", help="source repo of the PR"
    )
    new_parser.add_argument(
        "-su", "--source_code_url", help="source code url of the PR"
    )
    new_parser.add_argument(
        "-br", "--source_branch", help="source branch of the PR"
    )
    new_parser.add_argument(
        "-op", "--operation", choices=['check', 'push'],
        help="specify the operation within `check` and `push`"
    )
    return new_parser


if __name__ == "__main__":
    parser = init_parser()
    args = parser.parse_args()

    if (
            not args.prid
            or not args.source_repo
            or not args.source_code_url
            or not args.source_branch
            or not args.operation
    ):
        parser.print_help()
        sys.exit(1)

    obj = ContainerVerification(
        prid=args.prid,
        operation=args.operation,
        source_repo=args.source_repo,
        source_code_url=args.source_code_url,
        source_branch=args.source_branch
    )
 
    if obj.get_change_files():
        sys.exit(1)
    logger.info(f"Difference: {json.dumps(obj.change_files, indent=4)}")
    if obj.pull_source_code():
        sys.exit(1)
            
    # whether to push to `openeuler`
    if args.operation == "push":
        if obj.publish_updates():
            sys.exit(1)
    elif args.operation == "check":
        if obj.check_code():
            sys.exit(1)
        if obj.check_updates():
            sys.exit(1)
    else:
        logger.error(f"Unsupported operation: {args.operation}")
    sys.exit(0)
