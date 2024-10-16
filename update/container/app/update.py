# coding=utf-8
import argparse
import click
import requests
import subprocess
import shutil
import sys
import os
import re
import yaml

from packaging.version import Version
from prettytable import PrettyTable


DEFAULT_WORKDIR = "/tmp/eulerpublisher/ci/container/"
REPOSITORY_REQUEST_URL = (
    "https://gitee.com/api/v5/repos/openeuler/openeuler-docker-images/pulls/"
)
DOCKERFILE_PATH_DEPTH = 4
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
FILE_PATH_FORMAT = {
    "README": "{0}/README.md",
    "picture": "{0}/doc/picture",
    "logo": "{0}/doc/picture/{1}",
    "meta": "{0}/meta.yml",
    "doc": "{0}/doc",
    "image-info": "{0}/doc/image-info.yml",
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

# parse meta.yml and get the tags && building platforms
def _parse_meta_yml(file: str):
    tag = {
        'tag': "",
        'latest': "False"
    }
    arch = ""
    tags = []
    contents = file.split("/")
    if len(contents) != DOCKERFILE_PATH_DEPTH:
        raise Exception(
            f"Failed to check file path: {file}, "
            "the correct Dockerfile path should be "
            "`{app-name}/{app-version}/{os-version}/Dockerfile`"
        )
    meta = contents[0] + "/meta.yml"
    if os.path.exists(meta):
        with open(meta, "r") as f:
            tags = yaml.safe_load(f)
        try:
            if not isinstance(tags, dict):
                raise Exception(f"Format error: {meta}")
            for key in tags:
                if tags[key]['path'] != file:
                    continue
                tag['tag'] = key
                if 'arch' in tags[key]:
                    arch = tags[key]['arch']
                break
        except yaml.YAMLError as e:
            raise click.echo(click.style(
                f"Error in YAML file : {file} : {e}", fg="red"
            ))
    # generate the default tag
    if not tag['tag']:
        tag['tag'] = re.sub(r'\D', '.', contents[1]) + \
              "-oe" + _transform_version_format(contents[2])
    # check if the tag is the latest
    if Version(tag['tag'].split('-')[0]) >= max([Version(s.split('-')[0]) for s in tags]):
        tag['latest'] = "True"

    return contents[0], tag, arch

def _push_readme(file: str, namespace: str, repo: str):
    current = os.path.dirname(os.path.abspath(__file__))
    script = os.path.abspath(os.path.join(current, '../pushrm/pushrm.sh'))
    os.chmod(script, 0o755)
    try:
        subprocess.run(
            [script, file, namespace, repo],
            env={**os.environ, 'APIKEY__QUAY_IO': os.environ["DOCKER_QUAY_APIKEY"]}
        )
    except subprocess.CalledProcessError as err:
        click.echo(click.style(f"{err}", fg="red"))

def _check_document(self):
    result, table = 0, PrettyTable(field_names=IMAGE_SPECIFICATION_HEADER)
    images = list(filter(
        _filter_doc_images,
        list(map(lambda file: file.split("/")[0], self.change_files))
    ))
    for image in set(images):
        if _check_doc_files(image, table):
            result = 1
    print(table)
    return result

def _filter_doc_images(image):
    doc_path = FILE_PATH_FORMAT["doc"].format(image)
    if not os.path.exists(doc_path):
        return False
    info_path = FILE_PATH_FORMAT["image-info"].format(image)
    if not os.path.exists(info_path):
        return True
    with open(info_path, "r") as f:
        image_info = yaml.safe_load(f)
    if not "show-on-appstore" in image_info:
        return True
    return image_info["show-on-appstore"]

def _check_doc_files(image, table):
    # check the image-info.yml file
    image_path = FILE_PATH_FORMAT["image-info"].format(image)
    info_exists = os.path.exists(image_path)
    table.add_row(
        [
            image,
            image_path,
            click.style(
                "pass" if info_exists else "The image information file does not exist!",
                fg="green" if info_exists else "red",
            ),
        ]
    )
    # check the application logo
    logo_list, logo_exists, logo_path = [], False, FILE_PATH_FORMAT["picture"].format(image)
    if os.path.exists(logo_path):
        logo_list = os.listdir(logo_path)
    for key in IMAGE_EXTENSIONS:
        for picture in logo_list:
            if not picture.endswith(key):
                logo_exists = True
                break
    table.add_row(
        [
            image,
            f"{image}/doc/picture/*",
            click.style(
                "pass" if logo_exists else "The application logo does not exist!",
                "green" if logo_exists else "red"
            ),
        ]
    )
    return 0 if logo_exists and info_exists else 1


# Check if the required files exist, contains these files in the FILE_PATH_FORMAT
def _check_file_path(self):
    result, table = 0, PrettyTable(field_names=CHECK_PATH_HEADER)
    for file in self.change_files:
        contents = file.split("/")
        if len(contents) == 1:
            continue
        name = contents[len(contents) - 1].split(".")[0]
        if not name in FILE_PATH_FORMAT:
            continue
        file_path = FILE_PATH_FORMAT[name].format(
            contents[0], contents[len(contents) - 1]
        )
        path_error = os.path.exists(contents[0]) and not os.path.exists(file_path)
        if path_error:
            result = 1
        table.add_row(
            [
                contents[0],
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
        lambda f: f.split("/")[2] == "image-info.yml",
        filter(lambda f: len(f.split("/")) == 3, self.change_files),
    )
    for file in image_files:
        try:
            with open(file, "r") as f:
                yaml.safe_load(f)
                f.seek(0)
                lines = f.readlines()
            if not _check_key_exist(table, lines, file.split("/")[0]):
                continue
            result = 1
        except yaml.YAMLError as e:
            raise click.echo(
                click.style(f"Error in YAML file : {file} : {e}", fg="red")
            )
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
        if not key in attr_names:
            result = 1
        msg = "pass" if key in attr_names else "failed"
        color = "green" if key in attr_names else "red"
        table.add_row([image, re.sub(r"[ :|]", "", key), click.style(msg, fg=color)])
    return result


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
        self.workdir = DEFAULT_WORKDIR + f"/{operation}/{self.source_repo}"
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
            click.echo(click.style(
                f"Failed to fetch files: {response.status_code}", 
                fg="red"
            ))
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
            click.echo(click.style(f"Failed to clone {s_repourl}", fg="red"))
            return 1
        click.echo(click.style(f"Clone {s_repourl} successfully."))
        return 0
        
    def check_updates(self):
        os.chdir(self.workdir)
        # build update images by Dockerfiles
        for file in self.change_files:
            if os.path.basename(file) != "Dockerfile":
                continue
            # build and push multi-platform image to `openeulertest`
            name, tag, arch = _parse_meta_yml(file=file)
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
    
    def check_code(self):
        check_result = 0
        os.chdir(self.workdir)
        # Check the file list in the image directory
        path_check_result = _check_file_path(self)
        if path_check_result:
            click.echo(click.style(
                "There are some wrong file paths in this PR. The file path check results of the related images are as above.",
                fg="red",
            ))
            check_result = 1
        else:
            click.echo(click.style(
                "The file paths check in this PR has passed.",
                fg="green"
            ))

        # Check the content format for image-info.yml
        content_check_result = _check_image_content(self)
        if content_check_result:
            click.echo(click.style(
                "There are some format errors in `image-info.yml`, please check as above.",
                fg="red",
            ))
            check_result = 1
        else:
            click.echo(click.style(
                "The image-info.yml file content format check has passed.",
                fg="green",
            ))

        # Check image specifications for releasing on appstore
        document_check_result = _check_document(self)
        if document_check_result:
            click.echo(click.style(
                "There are some specification errors for releasing on appstore in this PR, please check as above.",
                fg="red",
            ))
            check_result = 1
        else:
            click.echo(click.style(
                "The image specification check for releasing on appstore has passed.",
                fg="green",
            ))
        return check_result

    def publish_updates(self):
        os.chdir(self.workdir)
        failed_tags = []
        for file in self.change_files:
            # update readme while changed file is README.md
            if os.path.basename(file) == "README.md":
                name = file.split("/")[0]
                _push_readme(file=file, namespace="openeuler", repo=name)
                continue
            if os.path.basename(file) != "Dockerfile":
                continue
            # build and push multi-platform image to `openeuler`
            name, tag, arch = _parse_meta_yml(file=file)
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
                failed_tags.append(tag['tag'])
        if len(failed_tags) == 0:
            return 0
        else:
            click.echo(click.style(f"Failed to publish image:{failed_tags}", fg="red"))
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
    click.echo(click.style(f"Difference: {obj.change_files}"))

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
        click.echo(click.style(
            f"Unsupported operation: {args.operation}",
            fg="red"
        ))
    sys.exit(0)
