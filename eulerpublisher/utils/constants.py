import os
import sys

paths = [
    os.path.join(sys.prefix, "etc/eulerpublisher/"),
    "/usr/local/etc/eulerpublisher/",
    "/usr/etc/eulerpublisher/",
    "/etc/eulerpublisher/",
]

ROOT_DIR = None

for path in paths:
    if os.path.exists(path):
        ROOT_DIR = path
        break

CONFIG_DIR = os.path.join(ROOT_DIR, "configs")
TEST_DIR = os.path.join(ROOT_DIR, "tests")
TEMPLATE_DIR = os.path.join(ROOT_DIR, "templates")
ASSET_DIR = os.path.join(ROOT_DIR, "assets")
DOCKERFILE_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, "recipes", "container")
SHELL_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, "recipes", "shell")
SPECFILE_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, "recipes", "rpm")

GITHUB_ACTIONS_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, "workflows", "github_actions")
CODEARTS_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, "workflows", "codearts")
JENKINS_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, "workflows", "jenkins")

LOG_DIR = ROOT_DIR
DATABASE_DIR = ROOT_DIR

WORK_DIR = "/tmp/eulerpublisher"

WORKFLOW_TYPES = {
    0: "Github Actions",
    1: "CodeArts",
    2: "Jenkins",
}

ARTIFACT_TYPES = {
    0: "container",
    1: "rpm",
    2: "cloudimg"
}

ARCHS = ["x86_64", "aarch64"]
REGISTRIES = ["docker.io", "quay.io"]
REPOSITORY = "openeuler"
FILTER_CONFIG_ = os.path.join(CONFIG_DIR, "version_rules.yaml")

UPSTREAM_MONITOR_URL = "https://easysoftware-monitoring.test.osinfra.cn/api/v2/projects/"

GITHUB_ACTIONS_HEADER = """
name: EulerPublisher 🚀
on: [push]
jobs:
"""

GITHUB_ACTIONS_SUCCESS = "success"