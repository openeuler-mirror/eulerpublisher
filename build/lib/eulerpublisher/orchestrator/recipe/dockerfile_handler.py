import json
import os
import re
import shutil
from eulerpublisher.utils.utils import _copy_template, _render_template
from eulerpublisher.orchestrator.recipe.base import RecipeHandler
from eulerpublisher.utils.exceptions import NoSuchFile
from eulerpublisher.utils.constants import DOCKERFILE_TEMPLATE_DIR

class DockerfileHandler(RecipeHandler):
    def __init__(self, config, logger, work_dir):
        self.config = config
        self.logger = logger
        self.work_dir = work_dir
        self.logger.info("Dockerfile Handler initialized")
        
    def handle_recipe(self, name, version, base):
        self.logger.info(f"Generating Dockerfile for {name}:{version}...")
        template_dir = os.path.join(DOCKERFILE_TEMPLATE_DIR, name)
        if not os.path.exists(template_dir):
            self.logger.error(f"Template {template_dir} not found")
            raise NoSuchFile(template_dir)
        template_path = os.path.join(template_dir, "Dockerfile.j2")
        
        output_dir = os.path.join(self.work_dir, name)
        _copy_template(template_dir, output_dir)
        output_path = os.path.join(output_dir, "Dockerfile")

        _render_template(
            template_path=template_path,
            output_path=output_path,
            context={
                "name": name,
                "version": version,
                "base": base,
            },
            mode="w",
        )
        
        self.logger.info(f"Dockerfile for {name}:{version} generated successfully")