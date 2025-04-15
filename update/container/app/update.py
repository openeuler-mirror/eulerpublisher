# coding=utf-8
import argparse
import click
import json
import requests
import subprocess
import shutil
import sys
import os
import re
import yaml

from packaging.version import Version
from prettytable import PrettyTable
from eulerpublisher.publisher import logger

DEFAULT_WORKDIR = "/tmp/eulerpublisher/ci/container/"
REPOSITORY_REQUEST_URL = (
    "https://gitee.com/api/v5/repos/openeuler/openeuler-docker-images/pulls/"
)
DOCKERFILE_PATH_DEPTH = 3
MAX_REQUEST_COUNT = 20
SUCCESS_CODE = 200
TEST_NAMESPACE = "openeulertest"
OFFICIAL_NAMESPACE = "openeuler"
IMAGE_DOC_FILES = ["logo", "image-info"]

CHECK_PATH_HEADER = [
    "Image Name",
    "File Path",
    "Path Check Result"
]
IMAGE_SPECIFICATION_HEADER = [
    "Image Name",
    "Check Item",
    "Check Result"
]
IMAGE_INFO_HEADER = [
    "Image Name",
    "Image-info Item",
    "Format Check Result"
]
IMAGE_INFO_ATTR = [
    "name",
    "category",
    "description",
    "license",
    "similar_packages",
    "dependency",
    "environment: |",
    "tags: |",
    "download: |",
    "usage: |",
]
IMAGE_EXTENSIONS = [
    ".jpeg",
    ".jpg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
    ".svg",
    ".heif",
    ".heic",
]
# {0} indicates the image path prefix.
FILE_PATH_FORMAT = {
    "README": "{0}/README.md",
    "picture": "{0}/doc/picture",
    "logo": "{0}/doc/picture/{1}",
    "meta": "{0}/meta.yml",
    "doc": "{0}/doc",
    "image-info": "{0}/doc/image-info.yml",
    "Dockerfile": "{0}/{1}/{2}/Dockerfile",
    "Distrofile": "{0}/{1}/{2}/Distrofile"
}


def _request(url: str):
    cnt = 0
    response = None
    while (not response) and (cnt < MAX_REQUEST_COUNT):
        response = requests.get(url=url)
        cnt += 1
    return response


# transform openEuler version into specifical format
# e.g., 22.03-lts-sp3 -> oe2203sp3
def _transform_version_format(os_version: str):
    # check if os_version has substring "-sp"
    if "-sp" in os_version:
        # delete "lts" in os_version
        os_version = os_version.replace("lts", "")
    # delete all "." and "-"
    ret = os_version.replace(".", "").replace("-", "")

    return ret


"""
 # Single image scenario does not require an image-list.yml file. Example directory structure:
/openeuler-docker-images/
└── nginx(Application)
    ├── x.x.x(application version)
    │   └── xx.xx-xxx(os version)
    │       └── Dockerfile
    ├── doc
    │   ├── image-info.yml
    │   └── picture
    │       └── logo.png
    ├── meta.yml
    └── README.md

# Scenario/solution image categorization, example directory structure:
/openeuler-docker-images/
└── ai(Scenario)
    ├── image-list.yml
    ├── opea(solution)
    │   ├── chatqna(application)
    │   │   ├── x.x.x(application version)
    │   │   │   └── xx.xx-xxx(os version)
    │   │   │       └── Dockerfile
    │   │   ├── doc
    │   │   │   ├── image-info.yml
    │   │   │   └── picture
    │   │   │       └── logo.png
    │   │   ├── meta.yml
    │   │   └── README.md
    │   └── chatqna-ui
    │       ├── x.x.x(application version)
    │       │   └── xx.xx-xxx(os version)
    │       │       └── Dockerfile
    │       ├── doc
    │       │   ├── image-info.yml
    │       │   └── picture
    │       │       └── logo.png
    │       ├── meta.yml
    │       └── README.md
    └── pytorch
        ├── x.x.x(application version)
        │   └── xx.xx-xxx(os version)
        │       └── Dockerfile
        ├── doc
        │   ├── image-info.yml
        │   └── picture
        │       └── logo.png
        ├── meta.yml
        └── README.md
        
# AI scenario/solution image-list.yml file path:
/openeuler-docker-images/ai/image-list.yml

# AI scenario/solution image-list.yml configuration example:
images:
  chatqna: opea/chatqna
  chatqna-ai: opea/chatqna-ui
  pytorch: pytorch
"""
def parse_image_directory(file: str):
    """
    Parse and return the image directory based on the given file path.
    """
    if len(file.split("/")) == 1:
        return ""

    # Default application directory is the first segment in the file path.
    image_dir = file.split("/")[0]
    image_list_yaml = os.path.join(image_dir, "image-list.yml")
    if not os.path.exists(image_list_yaml):
        return image_dir

    # Load the image-list.yml file
    with open(image_list_yaml, "r", encoding="utf-8") as f:
        image_list = yaml.safe_load(f)
    if not image_list:
        return image_dir
    # Validate that each image path ends with it's corresponding name
    images = image_list.get("images", [])
    for key, value in images.items():
        if value.endswith(key):
            continue
        raise ValueError(f"Image path does not end with {key}.")

    # Other files do not need to be checked, return empty.
    file_type = os.path.basename(file).split(".")[0]
    if file_type not in FILE_PATH_FORMAT:
        return ""

    # Check if the file path matches any of the image paths in the YAML file
    for key, value in images.items():
        prefix_path = image_dir + "/" + value.rstrip("/") + "/"
        if not file.startswith(prefix_path):
            continue
        suffix_path = file.replace(prefix_path, "")
        suffix_len = len(suffix_path.split("/"))
        format_path = FILE_PATH_FORMAT[file_type]
        format_len = len(format_path.split("/"))
        if suffix_len != format_len - 1:
            continue
        return prefix_path.rstrip("/")
    return image_dir


def _parse_info_default(file: str, image_dir: str):
    """
    Parse application information from the `Dockerfile` or `Distrofile` path.

    `{app-version}/{os-version}/Dockerfile`
    `{app-version}/{os-version}/Distrofile`
    """
    # Validate the `Dockerfile` or `Distrofile` path structure.
    image_dir = image_dir.rstrip("/") + "/"
    context_path = file.replace(image_dir, "")
    if len(context_path.split("/")) != DOCKERFILE_PATH_DEPTH:
        raise Exception(
            f"Failed to check file path: {file}, "
            "the correct `Dockerfile` or `Distrofile` path should be "
            "{image-version}/{os-version}/Dockerfile or "
            "{image-version}/{os-version}/Distrofile"
        )

    # Extract base OS version, app version, and app name.
    os_version_path = os.path.dirname(file)
    os_version = os.path.basename(os_version_path)

    image_version_path = os.path.dirname(os_version_path)
    image_version = os.path.basename(image_version_path)

    image_path = os.path.dirname(image_version_path)
    image_name = os.path.basename(image_path)
    return os_version, image_version, image_name


# parse meta.yml and get the tags && building platforms
def _parse_meta_yml(file: str, image_dir: str):
    tag = {
        'tag': "",
        'latest': "False"
    }
    arch = ""
    tags = []
    meta = os.path.join(image_dir, "meta.yml")
    # meta = image_dir + "/meta.yml"
    if os.path.exists(meta):
        with open(meta, "r") as f:
            tags = yaml.safe_load(f)
        try:
            if not isinstance(tags, dict):
                raise Exception(f"Format error: {meta}")
            for key in tags:
                dockerfile = image_dir + "/" + tags[key]['path']
                if dockerfile != file:
                    continue
                tag['tag'] = key
                if 'arch' in tags[key]:
                    arch = tags[key]['arch']
                break
        except yaml.YAMLError as e:
            raise logger.error(f"Error in YAML file : {file} : {e}")

    # generate the default tag
    os_version, image_version, image_name = (
        _parse_info_default(file=file, image_dir=image_dir)
    )
    if not tag['tag']:
        tag['tag'] = re.sub(r'\D', '.', image_version) + \
                     "-oe" + _transform_version_format(os_version)
    # check if the tag is the latest
    if not tags:
        tag['latest'] = "True"
    elif Version(tag['tag'].split('-')[0]) >= max([Version(s.split('-')[0]) for s in tags]):
        tag['latest'] = "True"
    return image_name, tag, arch


def _push_readme(file: str, namespace: str, image: str):
    current = os.path.dirname(os.path.abspath(__file__))
    script = os.path.abspath(os.path.join(current, '../pushrm/pushrm.sh'))
    os.chmod(script, 0o755)
    try:
        subprocess.run(
            [script, file, namespace, image],
            env={**os.environ, 'APIKEY__QUAY_IO': os.environ["DOCKER_QUAY_APIKEY"]}
        )
    except subprocess.CalledProcessError as err:
        logger.error(f"{err}")


def _check_document(self):
    result, table = 0, PrettyTable(field_names=IMAGE_SPECIFICATION_HEADER)

    image_dirs = []
    for change_file in self.change_files:
        if not os.path.exists(change_file):
            continue
        image_dir = parse_image_directory(change_file)
        image_dirs.append(image_dir)

    image_dirs = list(filter(
        _filter_doc_images,
        image_dirs
    ))

    for image_dir in set(image_dirs):
        if _check_image_info(image_dir, table):
            result = 1
    print(table)
    return result


def _filter_doc_images(image_dir: str):
    doc_path = FILE_PATH_FORMAT["doc"].format(image_dir)
    if not os.path.exists(doc_path):
        return False
    info_path = FILE_PATH_FORMAT["image-info"].format(image_dir)
    if not os.path.exists(info_path):
        return False
    with open(info_path, "r") as f:
        image_info = yaml.safe_load(f)
    if "show-on-appstore" not in image_info:
        return True
    return image_info["show-on-appstore"]


def _check_image_info(image_dir, table):
    # check the image-info.yml file
    image_path = FILE_PATH_FORMAT["image-info"].format(image_dir)
    info_exists = os.path.exists(image_path)
    table.add_row(
        [
            image_dir,
            image_path,
            click.style(
                "pass" if info_exists else "The image information file does not exist!",
                fg="green" if info_exists else "red",
            ),
        ]
    )
    # check the image logo
    logo_list, logo_exists = [], False
    logo_path = FILE_PATH_FORMAT["picture"].format(image_dir)
    if os.path.exists(logo_path):
        logo_list = os.listdir(logo_path)
    for key in IMAGE_EXTENSIONS:
        for picture in logo_list:
            if not picture.endswith(key):
                logo_exists = True
                break
    table.add_row(
        [
            image_dir,
            f"{image_dir}/doc/picture/*",
            click.style(
                "pass" if logo_exists else "The image logo does not exist!",
                "green" if logo_exists else "red"
            ),
        ]
    )
    return 0 if logo_exists and info_exists else 1


# Check if the required files exist, contains these files in the FILE_PATH_FORMAT
def _check_file_path(self):
    result, table = 0, PrettyTable(field_names=CHECK_PATH_HEADER)
    for file in self.change_files:
        if not os.path.exists(file):
            continue

        contents = file.split("/")
        name = contents[-1].split(".")[0]
        if name not in FILE_PATH_FORMAT:
            continue
        # Dockerfile or Distrofile does not need to be checked.
        if name == "Dockerfile" or name == "Distrofile":
            continue

        # check file under image directory
        image_dir = parse_image_directory(file)
        if not file.startswith(image_dir):
            continue
        # check all files exclude Dockerfile and Distrofile
        file_path = FILE_PATH_FORMAT[name].format(
            image_dir, contents[-1]
        )
        path_error = (
                os.path.exists(image_dir)
                and not os.path.exists(file_path)
        )
        if path_error:
            result = 1
        table.add_row(
            [
                image_dir,
                file,
                click.style(
                    "failed" if path_error else "pass",
                    fg="red" if path_error else "green",
                ),
            ]
        )
    print(table)
    return result


# Check that the format of each attribute in the image-info.yml is correct
def _check_image_content(self):
    result, table = 0, PrettyTable(field_names=IMAGE_INFO_HEADER)
    image_files = filter(
        lambda f: f.endswith("image-info.yml"),
        self.change_files
    )

    for file in image_files:
        if not os.path.exists(file):
            continue
        image_dir = parse_image_directory(file)
        if not file.startswith(image_dir):
            continue
        try:
            with open(file, "r") as f:
                yaml.safe_load(f)
                f.seek(0)
                lines = f.readlines()
            image = image_dir.split("/")[-1]
            if not _check_key_exist(table, lines, image):
                continue
            result = 1
        except yaml.YAMLError as e:
            raise e
    print(table)
    return result


# Check if the required attributes exist, contains these attributes in the IMAGE_INFO_ATTR
def _check_key_exist(table, lines, image):
    result, attr_names = 0, list(
        map(
            lambda line: line if line.endswith(": |") else line.split(":")[0],
            list(map(lambda line: line.rstrip(), lines)),
        )
    )
    for key in IMAGE_INFO_ATTR:
        if key not in attr_names:
            result = 1
        msg = "pass" if key in attr_names else "failed"
        color = "green" if key in attr_names else "red"
        table.add_row([
            image,
            re.sub(r"[ :|]", "", key),
            click.style(msg, fg=color)
        ])
    return result

def _check_app_image(file: str):
    # build and push multi-platform image to `openeulertest`
    image_dir = parse_image_directory(file)
    name, tag, arch = _parse_meta_yml(file=file, image_dir=image_dir)
    if subprocess.call([
        "eulerpublisher",
        "container",
        "app",
        "publish",
        "-a", arch,
        "-p", f"{TEST_NAMESPACE}/{name}",
        "-t", tag['tag'],
        "-l", tag['latest'],
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
        "-t", tag['tag']
    ]) != 0:
        return 1
    return 0
    
def _check_distroless_image(file: str):
    # build and push distroless image to `openeulertest`
    image_dir = parse_image_directory(file)
    name, tag, arch = _parse_meta_yml(file=file, image_dir=image_dir)
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
    name, tag, arch = _parse_meta_yml(file=file, image_dir=image_dir)
    if subprocess.call([
        "eulerpublisher",
        "container",
        "app",
        "publish",
        "-a", arch,
        "-p", f"{OFFICIAL_NAMESPACE}/{name}",
        "-t", tag['tag'],
        "-l", tag['latest'],
        "-f", file,
        "-m"
    ]) != 0:
        return tag['tag']
    return ""

def _publish_distroless_image(file: str, image_dir: str):
    # build and push distroless image to `openeuler`
    name, tag, arch = _parse_meta_yml(file=file, image_dir=image_dir)
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
        return tag['tag']
    return ""

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
        response = _request(url=url)
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
        os.chdir(self.workdir)
        # Check the file list in the image directory
        path_check_result = _check_file_path(self)

        # list total check results items
        check_result = 0
        if path_check_result:
            logger.error("There are some wrong file paths in this PR."
                " The file path check results of the related images are as above.")
            check_result = 1
        else:
            logger.info("The file paths check in this PR has passed.")

        # Check the content format for image-info.yml
        content_check_result = _check_image_content(self)
        if content_check_result:
            logger.error(
                "There are some format errors in `image-info.yml`, "
                "please check as above."
            )
            check_result = 1
        else:
            logger.info("The image-info.yml file content format check has passed.")

        # Check image specifications for releasing on appstore
        document_check_result = _check_document(self)
        if document_check_result:
            logger.error(
                "There are some specification errors for "
                "releasing on appstore in this PR, please check as above."
            )
            check_result = 1
        else:
            logger.info("The image specification check for releasing on appstore has passed.")
        return check_result

    def publish_updates(self):
        os.chdir(self.workdir)
        failed_tags = []
        for file in self.change_files:
            if not os.path.exists(file):
                logger.info(f"The file: {file} is deleted, no need to publish.")
                continue
            # update readme while changed file is README.md
            image_dir = parse_image_directory(file)
            image = image_dir.split("/")[-1]
            if os.path.basename(file) == "README.md":
                _push_readme(file=file, namespace="openeuler", image=image)
                continue
            if os.path.basename(file) == "Dockerfile":
                failed = _publish_app_image(file=file, image_dir=image_dir)
                if failed:
                    failed_tags.append(failed)
            elif os.path.basename(file) == "Distrofile":
                failed = _publish_distroless_image(file=file, image_dir=image_dir)
                if failed:
                    failed_tags.append(failed)
            else:
                continue
        if len(failed_tags) == 0:
            return 0
        else:
            logger.error(f"Failed to publish image:{failed_tags}")
            return 1


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
