import os
from jinja2 import Environment, FileSystemLoader

class DockerfileGenerate:
    
    def render_template(self, template_file: str, output_file: str, software: str, version: str, dependence: str):
        """
        Render a template file with the specified software, version, and dependency, and save the output to a file.
        
        Parameters:
        template_file (str): The path to the template file.
        output_file (str): The path to save the rendered output.
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
        rendered_output = template.render(software=software, version=version, dependence=dependence)
        # output_file = os.path.join(template_file, f"{item['tags']['common'][0]}.Dockerfile")
        # with open(output_path, 'w') as f:
        #     f.write(rendered_content)
        # print(f"Generated: {output_path}")


    def build_dockerfile(self, input: list, file_save: str):
        """
        Generate Dockerfiles for a list of software images and save them to a specified directory.
        
        Parameters:
        input_data (list): A list of dictionaries, each containing 'software', 'version', and optionally 'dependence' keys.
            - 'software' (str): The name of the software.
            - 'version' (str): The version of the software.
            - 'dependence' (str, optional): The base image or dependency for the software.
        save_directory (str): The directory where the generated Dockerfiles should be saved.
        
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
        cur_dir = os.path.dirname(os.path.abspath(__file__))

        for image in input:
            software = image.get('software')
            version = image.get('version')
            dependence = image.get('dependence')
            
            file_resource = "/templates/product/" + software + ".dockerfile"
            file_path = cur_dir + file_resource
            output_file = file_save + software + version + ".dockerfile"
            self.render_template(file_path, output_file, software, version, dependence)
            
            
            image_dict = {'dockerfile_path': output_file, 'image_tag':'image_tag'}
            workflow_build_list.append(image_dict)
        return workflow_build_list

# openeuler22.03
# py3.10
# cann8.0.0
# 8.0.0-910b-openeuler22.03-py3.10
