import sys, os

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, ".")))

from taskqueue import task_queue_generate
from workflow_maker import task_generate


def build_workflow(name_workflow, input_data, save_dir, buildpush=True, build=False, test=False, cve=False, sign=False, push=False):
    """
    This function generates a workflow based on the provided parameters and saves it to a YAML file.
    
    Parameters:
    name_workflow (str): The name of the workflow to be generated.
    input_data: The input data or parameters required for generating the workflow tasks.
    save_dir (str): The directory where the output YAML file should be saved.
    buildpush (bool): Whether to include build and push tasks in the workflow (default is True).
    build (bool): Whether to include a build task in the workflow.
    test (bool): Whether to include a test task in the workflow.
    cve (bool): Whether to include a CVE scanning task in the workflow.
    sign (bool): Whether to include a signing task in the workflow.
    push (bool): Whether to include a push task in the workflow.

    Returns:
    None: The function saves the workflow to a file and does not return any value.

    Input:
        input=[
            {
                'dockerfile_path': '${{ github.workspace }}/img1.dockerfile',
                'image_tag': 'ascendai/cann:openeuler-python3.10-cann8.0.0'
            },
            {
                'dockerfile_path': '${{ github.workspace }}/img2.dockerfile',
                'image_tag': 'ascendai/cann:openeuler-python3.10-cann8.0.0.beta1'
            }
        ]
    """
    # Generate the task queue based on the provided parameters
    queue = task_queue_generate(input_data, buildpush, build, test, cve, sign, push)
    
    # Generate the workflow content based on the task queue and workflow name
    workflow_content = task_generate(queue, name_workflow)
    
    os.makedirs(save_dir, exist_ok=True)
    output_file = os.path.join(save_dir, 'output.yaml')

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(workflow_content)


def main():
    input=[
        {
            'dockerfile_path': '${{ github.workspace }}/img1.dockerfile',
            'image_tag': 'ascendai/cann:openeuler-python3.10-cann8.0.0'
        },
        {
            'dockerfile_path': '${{ github.workspace }}/img2.dockerfile',
            'image_tag': 'ascendai/cann:openeuler-python3.10-cann8.0.0.beta1'
        }
    ]
    build_workflow("my task1433", input)


if __name__ == '__main__':
    main()
