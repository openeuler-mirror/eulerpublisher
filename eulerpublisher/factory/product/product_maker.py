import os

class DockerfileGenerate:
    
    def newdepend(self, image_tag):
        """
        Simplified tag, to be improved

        Parameters:
        image_tag (str): The input string that needs to be sanitized.

        Returns:
        str: A new string with only alphanumeric characters and '-' or '_' retained.
        """
        result = ''.join(char for char in image_tag if char.isalnum() or char in '-_')
        return result
            
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
        
        Raises:
        ValueError: If the Dockerfile template for a software is not found.

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

            file_resource = "/etc/" + software + ".dockerfile"
            file_path = cur_dir + file_resource

            if os.path.isfile(file_path) is not True:
                raise ValueError("The templates of this software is not exist.")

            # todo: need to normalize naming
            if dependence:
                image_tag = dependence + software + "-" + version
                brief_name = self.newdepend(dependence + software + version)
                new_name = brief_name + ".dockerfile"
            else:
                image_tag = software + "-" + version
                brief_name = self.newdepend(image_tag + version)
                new_name = brief_name + ".dockerfile"

            output_file = file_save + new_name

            self.dockerfile_generate(file_path, output_file, dependence, version)

            image_dict = {'dockerfile_path': output_file, 'image_tag':image_tag}
            workflow_build_list.append(image_dict)

        return workflow_build_list
    
    def dockerfile_generate(self, input_path: str, output_path: str, base_image: str = None, new_version: str) -> None:
        """
        Generate a new Dockerfile based on an existing one, optionally updating the base image and version.

        Parameters:
        - input_path: The path to the original Dockerfile.
        - output_path: The path to save the new Dockerfile.
        - base_image: The new base image to use in the Dockerfile (optional).
        - new_version: The new version to set for the BASE_VERSION argument (optional).
        """

        if not input_path:
            raise ValueError("input_path must not be empty")
        
        if not output_path:
            raise ValueError("output_path must not be empty")

        # Ensure new_version is provided
        if new_version is None:
            raise ValueError("new_version must be provided")

        try:
            with open(input_path, 'r') as file:
                dockerfile_lines = file.readlines()

            new_dockerfile_lines = []

            # add the new base image in need
            if base_image:
                new_dockerfile_lines.append(f'FROM {base_image}\n')

            # updating the BASE_VERSION
            for line in dockerfile_lines:
                stripped_line = line.strip()
                if stripped_line.startswith('ARG BASE_VERSION'):
                    new_dockerfile_lines.append(f'ARG BASE_VERSION={new_version}\n')
                else:
                    new_dockerfile_lines.append(line)

            with open(output_path, 'w') as file:
                file.writelines(new_dockerfile_lines)

        except FileNotFoundError as fnf_error:
            print(f"Error: {fnf_error}. Check that the input file path is correct.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


# def main():
#     input1=[
#         {
#             'software': 'openeuler',
#             'version': '22.04',
#             'dependence': 'base22.04'
#         },
#         {
#             'software': 'openeuler',
#             'version': '23.04',
#             'dependence':  'base23.04'
#         }
#     ]
#     save_path = "/data/zjl/eulerpublisher/eulerpublisher/factory/etc/"
#     res = build_dockerfile(input1, save_path)
#     print(res)


# if __name__ == '__main__':
#     main()
