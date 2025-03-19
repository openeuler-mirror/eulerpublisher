import os, sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, ".")))

from product_maker import dockerfile_generate


def build_dockerfile(input: list, file_save: str):
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
            brief_name = newdepend(dependence + software + version)
            new_name = brief_name + ".dockerfile"
        else:
            image_tag = software + "-" + version
            brief_name = newdepend(image_tag + version)
            new_name = brief_name + ".dockerfile"

        output_file = file_save + new_name

        dockerfile_generate(file_path, output_file, dependence, version)

        image_dict = {'dockerfile_path': output_file, 'image_tag':image_tag}
        workflow_build_list.append(image_dict)

    return workflow_build_list


def newdepend(image_tag):
    """
    Simplified tag, to be improved

    Parameters:
    image_tag (str): The input string that needs to be sanitized.

    Returns:
    str: A new string with only alphanumeric characters and '-' or '_' retained.
    """
    result = ''.join(char for char in image_tag if char.isalnum() or char in '-_')
    return result


def main():
    input1=[
        {
            'software': 'openeuler',
            'version': '22.04',
            'dependence': 'base22.04'
        },
        {
            'software': 'openeuler',
            'version': '23.04',
            'dependence':  'base23.04'
        }
    ]
    save_path = "/data/zjl/eulerpublisher/eulerpublisher/factory/etc/"
    res = build_dockerfile(input1, save_path)
    print(res)


if __name__ == '__main__':
    main()
