from product import build_dockerfile
from workflow import build_workflow
import os


def build_task(input_task: dict):
    """
    Builds a task based on the provided input dictionary and generates related Dockerfiles and workflows.

    Parameters:
    input_task (dict): A dictionary containing the task details, such as software name, version, and dependencies.

    Input:
        input1={
                'software': 'openeuler',
                'version': '24.03-lts',
                'dependence': ['base1', 'base2']}
        input2={
                'software': 'openeuler',
                'version': '24.03-lts',
                'dependence': None}
    """
    dependencies = input_task.get('dependence')
    software = input_task.get('software')
    version = input_task.get('version')

    dockerfile_build_list = []
    if dependencies is not None:
        for dependency in dependencies:
            dict = {'software':software, 'version':version, 'dependence':dependency}
            dockerfile_build_list.append(dict)
    else:
        dict = {'software':software, 'version':version, 'dependence':None}
        dockerfile_build_list.append(dict)

    etc_dir = os.path.dirname(os.path.abspath(__file__)) + '/etc/'

    # generate the dockerfile
    workflow_build_list = build_dockerfile(dockerfile_build_list, etc_dir)

    # generate the workflow
    build_workflow(software+version, workflow_build_list, etc_dir)


def main():
    input={
            'software': 'openeuler',
            'version': '24.03-lts',
            'dependence': ['base1','base2']
        }

    build_task(input)


if __name__ == '__main__':
    main()
