import os
from jinja2 import Environment, FileSystemLoader
from eulerpublisher.utils.constants import TMP_DOCKERFILE_DIR, TEMPLATE_DIR

class DockerfileGenerate:
    
    def render_template(self, template_file: str, image_tag: str, software: str, version: str, dependence: str):
        """
        Render a template file with the specified software, version, and dependency, and save the output to a file.
        
        Parameters:
        template_file (str): The path to the template file.
        image_tag (str): The tag for the Docker image.
        software (str): The name of the software.
        version (str): The version of the software.
        dependence (str): The base image or dependency for the software.
        
        Returns:
        None
        """
        if not os.path.exists(template_file):
            raise FileNotFoundError(f"Template file {template_file} not found.")
        env = Environment(loader=FileSystemLoader(os.path.dirname(template_file)))
        template = env.get_template(os.path.basename(template_file))
        rendered_content = template.render(software=software, version=version, dependence=dependence)
        output_file = os.path.join(TMP_DOCKERFILE_DIR, image_tag, ".Dockerfile")
        with open(output_file, 'w') as f:
            f.write(rendered_content)

    def build_dockerfile(self, input: list):
        """
        Generate Dockerfiles for a list of software images and save them to a specified directory.
        
        Parameters:
        input_data (list): A list of dictionaries, each containing 'software', 'version', and optionally 'dependence' keys.
            - 'software' (str): The name of the software.
            - 'version' (str): The version of the software.
            - 'dependence' (str, optional): The base image or dependency for the software.
        
        Returns:
        list: A list of dictionaries, each containing the 'dockerfile_path' and 'image_tag' keys.
            - 'dockerfile_path' (str): The path to the generated Dockerfile.
            - 'image_tag' (str): The tag for the Docker image.
        Input:
            input=[
                {
                    'software': 'openeuler',
                    'version': '22.04',
                    'dependence': 'base1'
                },
                {
                    'software': 'openeuler',
                    'version': '23.04',
                    'dependence':  'base2'
                }
            ]
        """
        workflow_build_list = []
        if not os.path.exists(TMP_DOCKERFILE_DIR):
            os.makedirs(TMP_DOCKERFILE_DIR)

        for image in input:
            if not os.path.exists(TMP_DOCKERFILE_DIR + "/" + software):
                os.makedirs(TMP_DOCKERFILE_DIR)
            software = image.get('software')
            version = image.get('version')
            dependence = image.get('dependence')
            template_file = TEMPLATE_DIR + "/" + software + ".dockerfile"
            image_tag = version + "-" + dependence
            output_file = self.render_template(template_file, image_tag, software, version, dependence)
            image_dict = {'dockerfile_path': output_file, 'image_tag':'image_tag'}
            workflow_build_list.append(image_dict)
        return workflow_build_list
