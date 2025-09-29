import os
import shutil
import re
from git import Repo
from github import Github, GithubException
from eulerpublisher.utils.constants import WORKFLOW_STATUS_RUNNING, WORKFLOW_STATUS_FAILED, WORKFLOW_STATUS_SUCCEEDED, WORKFLOW_STATUS_WAITING_RUNNING
from eulerpublisher.utils.date import get_current_timestamp
import time

from eulerpublisher.orchestrator.workflow.base import WorkflowHandler
from eulerpublisher.utils.exceptions import (
    UnsupportedArtifactType,
    NoSuchFile
)
    
from eulerpublisher.utils.constants import (
    WORK_DIR, 
    WORKFLOW_TYPES, 
    ARTIFACT_TYPES, 
    GITHUB_ACTIONS_TEMPLATE_DIR, 
    GITHUB_ACTIONS_HEADER
)
from eulerpublisher.utils.utils import (
    _render_template,
    _init_repository,
    _git_pull,
    _git_commit,
    _git_push
)

class GithubActionsHandler(WorkflowHandler):
    """GitHub Actions 工作流处理器
    
    功能：
    - 自动化生成 GitHub Actions 工作流文件
    - 管理代码仓库的克隆、提交和推送
    - 支持容器镜像、RPM包和云镜像的构建流程
    
    典型工作流程：
    1. 初始化时克隆目标仓库
    2. 根据制品类型生成对应工作流
    3. 渲染模板并生成最终配置文件
    4. 提交变更并推送到远程仓库
    """
    def __init__(self, config, logger, db):
        self.config = config
        self.logger = logger
        self.db = db
        self.owner_name = self.config.get(WORKFLOW_TYPES[0], "owner_name")
        self.repo_name = self.config.get(WORKFLOW_TYPES[0], "repo_name")
        self.repo_url = self.config.get(WORKFLOW_TYPES[0], "repo_url")
        self.repo_dir = os.path.join(WORK_DIR, self.repo_name)
        _init_repository(repo_dir=self.repo_dir, repo_url=self.repo_url)
        self.logger.info("Github Actions Handler initialized")

    def handle_workflow(self, artifact_type, artifact_info):
        handle_functions = {
            ARTIFACT_TYPES[0]: self._handle_container_workflow,
            ARTIFACT_TYPES[1]: self._handle_rpm_workflow,
            ARTIFACT_TYPES[2]: self._handle_cloudimg_workflow
        }

        if artifact_type not in handle_functions:
            self.logger.error(f"Unsupported artifact type: {artifact_type}")
            raise UnsupportedArtifactType(artifact_type)

        handle_functions[artifact_type](artifact_info)

    def _handle_rpm_workflow(self, artifact_info):
        pass

    def _handle_cloudimg_workflow(self, artifact_info):
        pass

    def _handle_container_workflow(self, artifact_info):
        self.logger.info("Generating container workflow...")
        from eulerpublisher.orchestrator.recipe.dockerfile_handler import DockerfileHandler
        try:
            archs = artifact_info["archs"]
            registries = artifact_info["registries"]
            repository = artifact_info["repository"]
            layers = artifact_info["layers"]

            workflow_path = os.path.join(self.repo_dir, ".github", "workflows", "workflow.yml")
            os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
            with open(workflow_path, "w") as f:
                f.write(GITHUB_ACTIONS_HEADER)

            recipe_handler = DockerfileHandler(self.config, self.logger, self.repo_dir)

            tag = None
            needs = None
            base = "scratch"
            for layer in layers:
                name = layer.get("name")
                version = layer.get("version")

                # special handling for openeuler
                if name == "openeuler":
                    tag = re.sub(r'\.(?=LTS)|\.(?=SP\d)', '-', version).lower()
                else:
                    tag = f"{version}-{tag}"

                image = self.db.query_image(
                                software_name=name,
                                version_name=version,
                                repository=repository,
                                tag=tag)
                if not image or not set(archs).issubset(set(image["arch"].split(","))):
                    recipe_handler.handle_recipe(name, version, base)
                    self._handle_container_job(registries, repository, name, version, tag, needs, archs)
                    needs = name
                base = f"{registries[0]}/{repository}/{name}:{tag}"

                # special handling for openeuler
                if name == "openeuler":
                    tag = re.sub(r'LTS(?=\.)', '', version)
                    tag = "oe" + re.sub(r'\.', '', tag).lower()
                else:
                    tag = f"{name}{tag}"
            self.logger.info("Container workflow generated successfully")
        except Exception as e:
            id = artifact_info["id"]
            update_data = {
                "status": WORKFLOW_STATUS_FAILED
            }
            self.db.update_workflow(id, update_data)
            self.logger.error(f"Failed to generate container workflow: {e}")


    def _handle_container_job(self, registries, repository, name, version, tag, needs, archs):
        self.logger.info(f"Generating job for {name}:{version}...")
        template_path = os.path.join(GITHUB_ACTIONS_TEMPLATE_DIR, ARTIFACT_TYPES[0] + ".yml.j2")
        if not os.path.exists(template_path):
            self.logger.error(f"Template {template_path} not found")
            raise NoSuchFile(template_path)

        runner = self.config.get("Github Actions", "runner")

        workflow_path = os.path.join(self.repo_dir, ".github", "workflows", "workflow.yml")

        _render_template(
            template_path=template_path,
            output_path=workflow_path,
            context={
                "runner": runner,
                "name": name,
                "archs": archs,
                "needs": needs,
                "tag": tag,
                "registries": registries,
                "repository": repository,
                "version": version
            },
            mode="a",
        )
        self.logger.info(f"Job for {name}:{version} generated successfully")

    def upload_workflow(self, id):
        self.logger.info("Uploading Github Actions workflow...")
        try:
            repo = Repo(self.repo_dir)
            _git_pull(repo)
            _git_commit(repo)
            _git_push(repo)

            commit_sha = repo.head.commit.hexsha

            started_on = get_current_timestamp()
            run_id = self.get_run_id_by_commit(
                commit_sha,
                max_attempts=15,
                interval=2
            )
            if not run_id:
                self.logger.warning(f"Could not find run_id for commit {commit_sha}")
                update_data = {
                    "status": WORKFLOW_STATUS_WAITING_RUNNING,
                    "started_on": started_on,
                    "owner_name": self.owner_name,
                    "repo_name": self.repo_name,
                    "commit_sha": commit_sha
                }
            else:
                update_data = {
                    "status": WORKFLOW_STATUS_RUNNING,
                    "started_on": started_on,
                    "owner_name": self.owner_name,
                    "repo_name": self.repo_name,
                    "run_id": run_id,
                    "commit_sha": commit_sha
                }
            self.db.update_workflow(id, update_data)
            self.logger.info("Github Actions workflow uploaded successfully")
        except Exception as e:
            update_data = {
                "status": WORKFLOW_STATUS_FAILED
            }
            self.db.update_workflow(id, update_data)
            self.logger.error(f"Failed to upload Github Actions workflow{e}")

    def get_run_id_by_commit(self, commit_sha, max_attempts=15, interval=2):
        try:
            token = os.environ.get("GITHUB_TOKEN")
            g = Github(token)
            repo = g.get_repo(f"{self.owner_name}/{self.repo_name}")

            for attempt in range(max_attempts):
                try:
                    runs = repo.get_workflow_runs(head_sha=commit_sha)
                    if runs.totalCount > 0:
                        self.logger.info(f"Found run_id {runs[0].id} for commit {commit_sha}")
                        return runs[0].id
                except GithubException as e:
                    self.logger.warning(f"GitHub API request failed (attempt {attempt + 1}/{max_attempts}): {str(e)}")

                if attempt < max_attempts - 1:
                    time.sleep(interval)

            self.logger.warning(f"Timeout after {max_attempts * interval} seconds waiting for workflow run")
            return None
        except Exception as e:
            self.logger.error(f"Error while getting run_id by commit: {str(e)}")
            return None
        
    def __del__(self):
        if os.path.exists(self.repo_dir):
            shutil.rmtree(self.repo_dir)
            self.logger.info(f"Cleaned up working directory: {self.repo_dir}")