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


DEFAULT_WORKDIR="/tmp/eulerpublisher/ci/container/"
REPOSITORY_REQUEST_URL="https://gitee.com/api/v5/repos/openeuler/openeuler-docker-images/pulls/"
DOCKERFILE_PATH_DEPTH=4
MAX_REQUEST_COUNT=20
SUCCESS_CODE=200
TEST_NAMESPACE="openeulertest"


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
    tag = ""
    arch = ""
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
            try:
                tags = yaml.safe_load(f)
                if isinstance(tags, dict):
                    for key in tags:
                        if tags[key]['path'] == file:
                            tag = key
                            if 'arch' in tags[key]:
                                arch = tags[key]['arch']
                            break
            except yaml.YAMLError as e:
                click.echo(click.style(
                    f"Error in YAML file : {file} : {e}", fg="red"
                ))
    if not tag:
        tag = re.sub(r'\D', '.', contents[1]) + \
              "-oe" + _transform_version_format(contents[2])
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
                "-t", tag,
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
                "-t", tag
            ]) != 0:
                return 1
        return 0
    
    def publish_updates(self):
        os.chdir(self.workdir)
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
                "-p", f"openeuler/{name}",
                "-t", tag,
                "-f", file,
                "-m"
            ]) != 0:
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
    click.echo(click.style(f"Difference: {obj.change_files}"))

    if obj.pull_source_code():
        sys.exit(1)
            
    # whether to push to `openeuler`
    if args.operation == "push":
        if obj.publish_updates():
            sys.exit(1)
    elif args.operation == "check":
        if obj.check_updates():
            sys.exit(1)
    else:
        click.echo(click.style(
            f"Unsupported operation: {args.operation}",
            fg="red"
        ))
    sys.exit(0)
