import argparse
import click
import git
import json
import os
import requests
import subprocess
import sys

ENV_TOKEN="GITEE_API_TOKEN"
ENV_USER="GITEE_USER_NAME"
ENV_EMAIL="GITEE_USER_EMAIL"

OWNER_NAME="openEuler"
REPO_NAME="openeuler-docker-images"
TMP_REPO=f"/tmp/{REPO_NAME}"

VERSION_FILTER_FILES=["meta.yml", "doc", "README.md"]
SUPPORT_UPDATE_APPS=["cann", "mindspore", "pytorch"]

PR_TITLE_FORMAT="Auto created pull request, app name: {}, app version: {}"
PR_MESSAGE_FORMAT="Automated commit update files for application: {}"

def _check_update_params(args):
    result = 0
    if not ENV_TOKEN in os.environ:
        click.echo(click.style(f"Environment variable {ENV_TOKEN} not set.", fg="red"))
        result=1
    if not ENV_USER in os.environ:
        click.echo(click.style(f"Environment variable {ENV_USER} not set.", fg="red"))
        result=1
    if not ENV_EMAIL in os.environ:
        click.echo(click.style(f"Environment variable {ENV_EMAIL} not set.", fg="red"))
        result=1
    if args.cann_sh and not os.path.exists(args.cann_sh):
        click.echo(click.style(f"CANN install script not found, file path: {args.cann_sh}.", fg="red"))
        result=1
    if args.python_sh and not os.path.exists(args.python_sh):
        click.echo(click.style(f"Python install script not found, file path: {args.python_sh}.", fg="red"))
        result=1
    return result

def _init_giee_repository():
    if _delete_user_repo():
        return 1
    if _fork_owner_repo():
        return 1
    if _clone_user_repo():
        return 1
    return 0

def _auto_update_process(args):
    obj = UpdateObject(
        openeuler_version=args.openeuler_version,
        sdk_version=args.sdk_version,
        framework_version=args.framework_version,
        chip_version=args.chip_version,
        app_name=args.app_name,
        python_version=args.python_version,
        dockerfile_path=args.dockerfile_path,
        cann_sh=args.cann_sh,
        python_sh=args.python_sh,
        sdk_name=args.sdk_name
    )
    if obj.create_update_files():
        return 1
    if obj.submit_update_files():
        return 1
    if obj.create_pull_request():
        return 1
    return 0

def _transform_version_format(os_version: str):
    # check if os_version has substring "-sp"
    if "-sp" in os_version:
        # delete "lts" in os_version
        os_version = os_version.replace("lts", "")
    # delete all "." and "-"
    ret = os_version.replace(".", "").replace("-", "")
    return f"oe{ret}"

# delete user repository for fork
def _delete_user_repo():
    api_url = f'https://gitee.com/api/v5/repos/{os.environ[ENV_USER]}/{REPO_NAME}'
    headers = {
        'Authorization': f'token {os.environ[ENV_TOKEN]}'
    }
    response = requests.delete(api_url, headers=headers)
    if response.status_code != 204 and response.status_code != 404:
        click.echo(click.style(f"Failed to delete the repository: {response.json()}", fg="red"))
        return 1
    click.echo(click.style("Successfully deleted the repository.", fg="green"))
    return 0

# fork owner repository for update
def _fork_owner_repo():
    api_url = f'https://gitee.com/api/v5/repos/{OWNER_NAME}/{REPO_NAME}/forks'
    headers = {
        'Authorization': f'token {os.environ[ENV_TOKEN]}',
        'Content-Type': 'application/json'
    }
    response = requests.post(api_url, headers=headers)
    if response.status_code != 201 and response.status_code != 403:
        click.echo(click.style(f"Failed to fork the repository: {response.json()}", fg="red"))
        return 1
    click.echo(click.style("Successfully forked the repository.", fg="green"))
    return 0

# clone the userspace repository to local
def _clone_user_repo():
    repo_url =f'https://{os.environ[ENV_USER]}:{os.environ[ENV_TOKEN]}@gitee.com/{os.environ[ENV_USER]}/{REPO_NAME}.git'
    subprocess.call(["rm", "-rf", TMP_REPO])
    ret = subprocess.call([
        'git',
        'clone',
        repo_url,
        TMP_REPO
    ])
    if ret != 0:
        click.echo(click.style(f"Failed to clone the repository: {repo_url}.", fg="red"))
        return 1
    click.echo(click.style("Successfully cloned the repository.", fg="green"))
    return 0

class UpdateObject:
    def __init__(self, 
        openeuler_version,
        sdk_version,
        framework_version,
        chip_version,
        app_name,
        python_version,
        dockerfile_path,
        cann_sh,
        python_sh,
        sdk_name
    ):
        self.openeuler_version = openeuler_version.lower()
        self.framework_version = framework_version
        self.sdk_version = sdk_version
        self.chip_version = chip_version
        self.app_name = app_name.lower()
        self.python_version = python_version
        self.dockerfile_path = dockerfile_path
        self.cann_sh = cann_sh
        self.python_sh = python_sh
        self.sdk_name = sdk_name if sdk_name else "cann"
        self.template_path = self.get_template_path()
        self.dockerfile_path = self.dockerfile_path if self.dockerfile_path else f"{self.template_path}/Dockerfile"

    # automatically create files for update
    def create_update_files(self):
        ret = 0
        if not os.path.exists(self.template_path):
            click.echo(click.style("The previous version does not exist.", fg="red"))
            ret=1
        elif not os.path.exists(self.dockerfile_path):
            click.echo(click.style(f"Template of the dockerfile not found, expected path:{self.dockerfile_path}", fg="red"))
            ret=1 
        elif self.app_name == "cann":
            ret = self.create_sdk_files()
        elif self.app_name == "pytorch":
            ret = self.create_framework_files()
        elif self.app_name == "mindspore":
            ret = self.create_framework_files()
        else:
            click.echo(click.style(f"This application does not support update automatically, support application:{SUPPORT_UPDATE_APPS}", fg="red"))
            ret = 1
        return ret
    
    def create_framework_files(self):
        target_dir = f"{TMP_REPO}/{self.app_name}/{self.framework_version}-{self.sdk_name}{self.sdk_version}/{self.openeuler_version}"
        sdk_tag = f"{self.sdk_version}-{_transform_version_format(self.openeuler_version.lower())}"

        print(sdk_tag)
        subprocess.call(["mkdir", "-p", target_dir])
        subprocess.call(["cp", self.dockerfile_path, target_dir])
        docker_file = f"{target_dir}/Dockerfile"

        print(docker_file)
        subprocess.call([
            "sed", 
            "-i",  
            f"s|^ARG VERSION=.*|ARG VERSION={self.framework_version}|",
            docker_file
        ])
        subprocess.call([
            "sed",
            "-i",
            f"s|^ARG BASE=openeuler\/cann:.*|ARG BASE=openeuler\/cann:{sdk_tag}|",
            docker_file
        ])
        return 0
    
    def create_sdk_files(self):
        target_dir = f"{TMP_REPO}/{self.app_name}/{self.sdk_version}/{self.openeuler_version}"
        subprocess.call(["mkdir", "-p", target_dir])

        docker_file = f"{target_dir}/Dockerfile"
        subprocess.call(["cp", self.dockerfile_path, docker_file])
        subprocess.call([
            "sed", 
            "-i",  
            f"s|^ARG VERSION=.*|ARG VERSION={self.sdk_version}|",
            docker_file
        ])
        subprocess.call([
            "sed",
            "-i",
            f"s|^ARG BASE=openeuler\/openeuler:.*|ARG BASE=openeuler\/openeuler:{self.openeuler_version.lower()}|",
            docker_file
        ])
        if self.chip_version:
            subprocess.call([
                "sed",
                "-i",
                f"s|^ARG CANN_CHIP=.*|ARG CANN_CHIP={self.chip_version}|",
                docker_file
            ])
        if self.python_version:
            subprocess.call([
                "sed",
                "-i",
                f"s|^ARG PY_VERSION=.*|ARG PY_VERSION={self.python_version}|",
                docker_file
            ])
        return self.copy_install_script()
    
    def copy_install_script(self):
        template_dir = f"{self.template_path}/scripts"
        cann_sh = self.cann_sh if self.cann_sh else f"{template_dir}/cann.sh"
        python_sh = self.python_sh if self.python_sh else f"{template_dir}/python.sh"

        target_dir = f"{TMP_REPO}/{self.app_name}/{self.sdk_version}/{self.openeuler_version}/scripts/"
        subprocess.call(["mkdir", "-p", target_dir])
        subprocess.call(["cp", cann_sh, f"{target_dir}/cann.sh"])
        subprocess.call(["cp", python_sh, f"{target_dir}/python.sh"])
        return 0
    
    # based on the template of the target application dockerfile to update
    def get_template_path(self):
        app_path = f"{TMP_REPO}/{self.app_name}"
        sdk_path = f"{TMP_REPO}/{self.sdk_name}/{self.sdk_version}/{self.openeuler_version}"
        if self.app_name != "cann" and not os.path.exists(sdk_path):
            return ""
        if not os.path.exists(app_path):
            return ""
        app_versions = list(filter(lambda x: x not in VERSION_FILTER_FILES, os.listdir(app_path))) 
        app_versions.sort(reverse=True) 
        app_version_path = f"{app_path}/{app_versions[0]}"
        if not os.path.exists(app_version_path):
            return ""
        oe_versions = os.listdir(app_version_path)
        oe_versions.sort(reverse=True)
        template_path = f"{app_version_path}/{oe_versions[0]}"
        return template_path if os.path.exists(template_path) else ""
    
    # submit updated files in the repository
    def submit_update_files(self):
        repo = git.Repo(TMP_REPO)
        with repo.config_writer() as config_writer:
            config_writer.set_value('user', 'name', os.environ[ENV_USER])
            config_writer.set_value('user', 'email', os.environ[ENV_EMAIL]) 
        repo.git.add(A=True)
        repo.index.commit(PR_MESSAGE_FORMAT.format(self.app_name))
        origin = repo.remote(name='origin')
        origin.set_url(f'https://{os.environ[ENV_USER]}:{os.environ[ENV_TOKEN]}@gitee.com/{os.environ[ENV_USER]}/{REPO_NAME}.git')
        origin.push()
        click.echo(click.style("Successfully pushed changes to the remote repository.", fg="green"))
        return 0

    # create a pull request to upstream repository
    def create_pull_request(self):
        version = self.sdk_version if self.app_name == "cann" else self.framework_version
        api_url=f"https://gitee.com/api/v5/repos/{OWNER_NAME}/{REPO_NAME}/pulls"
        pr_data = {
            "access_token": os.environ[ENV_TOKEN],
            "title": PR_TITLE_FORMAT.format(self.app_name, version),
            "head": f"{os.environ[ENV_USER]}:master", 
            "base": "master",
            "body": PR_MESSAGE_FORMAT.format(self.app_name)
        }
        json_data=json.dumps(pr_data)
        response = requests.post(
            api_url, data=json_data, headers={"Content-Type": "application/json"}
        )
        if response.status_code != 201:
            click.echo(click.style(f"Failed to create Pull Request: {response.json()}", fg="red"))
            return 1
        click.echo(click.style("Successfully created Pull Request.", fg="green"))
        return 0
    

def init_parser():
    new_parser = argparse.ArgumentParser(
        prog="update.py",
        description="Auto update application container images",
    )
    new_parser.add_argument(
        "-ov", "--openeuler_version", help="openeuler version"
    )
    new_parser.add_argument(
        "-sv", "--sdk_version", help="sdk version"
    )
    new_parser.add_argument(
        "-an", "--app_name", help=f"application name, the applications that support automatic are: {SUPPORT_UPDATE_APPS}"
    )
    new_parser.add_argument(
        "-cs", "--cann_sh", help="cann install script, give the path if you will update"
    )
    new_parser.add_argument(
        "-ps", "--python_sh", help="python install script, give the path if you will update"
    )
    new_parser.add_argument(
        "-dp", "--dockerfile_path", help="dockerfile path of the docker image, give the path if you will update"
    )
    new_parser.add_argument(
        "-sn", "--sdk_name", help="the default sdk is cann,, and other SDKs are not supported yet"
    )
    new_parser.add_argument(
        "-cv", "--chip_version", help="the default cann chip version is 910b, give the version if you will update"
    )
    new_parser.add_argument(
        "-pv", "--python_version", help="the default python version is 3.8, give the version if you will update"
    )
    new_parser.add_argument(
        "-fv", "--framework_version", help="framework version, must give the version if you want to upload the ai-framework image"
    )
    return new_parser

if __name__ == "__main__":
    parser = init_parser()
    args = parser.parse_args()
    if (
        not args.openeuler_version
        or not args.sdk_version
        or not args.app_name
        or args.app_name not in SUPPORT_UPDATE_APPS
    ) or (
        args.app_name != "cann"
        and not args.framework_version
    ):
        parser.print_help()
        sys.exit(1)
    if _check_update_params(args):
        sys.exit(1)
    if _init_giee_repository():
        sys.exit(1)
    if _auto_update_process(args):
        sys.exit(1)    
    sys.exit(0)