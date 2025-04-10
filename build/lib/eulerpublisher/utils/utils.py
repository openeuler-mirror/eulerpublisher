import os
import shutil
from datetime import datetime
from git import Repo, GitCommandError
from jinja2 import Environment, FileSystemLoader
from eulerpublisher.utils.exceptions import (
    NoSuchFile,
    GitCloneFailed,
    GitPullFailed,
    GitPushFailed,
)

def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def _copy_template(src_dir, dest_dir):
    shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)

def _render_template(template_path, output_path, context, mode):
        template_dir = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        rendered_content = template.render(context)
        
        with open(output_path, mode) as f:
            f.write(rendered_content)

def _init_repository(repo_dir, repo_url):
    os.makedirs(repo_dir, exist_ok=True)
    try:
        Repo.clone_from(repo_url, repo_dir)
    except GitCommandError as e:
        raise GitCloneFailed(f"Failed to clone {repo_url}")

def _git_pull(repo):
    try:
        repo.remotes.origin.pull()
    except GitCommandError as e:
        raise GitPullFailed("Pull operation failed")

def _git_commit(repo):
    repo.git.add(A=True)
    repo.index.commit(f"Update workflow - {datetime.now().isoformat()}")

def _git_push(repo):
    try:
        repo.remotes.origin.push()
    except GitCommandError as e:
        raise GitPushFailed("Push operation failed")