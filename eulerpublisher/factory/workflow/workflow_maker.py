from taskqueue import JobConfig
from collections import deque
import yaml, os


def task_generate(jobs_queue: deque, workflow_name: str) -> str:
    """
    Generate YAML content for a workflow based on a jobs queue and workflow name.

    Parameters:
    - jobs_queue: A deque of job configurations.
    - workflow_name: The name of the workflow.

    Returns:
    - A string containing the complete YAML content for the workflow.

    Raises:
    - ValueError: If an invalid job_type is encountered in the jobs queue.
    """
    jobs_content = []
    job_factory = {
        'buildpush': buildpush_job_factory,
        'imagebuild': imagebuild_job_factory,
        'cvescan': cvescan_job_factory,
        'imagetest': imagetest_job_factory,
        'signature': signature_job_factory,
        'imagepush': imagepush_job_factory,
    }

    #todo: mark and set 'need' between different job_task among jobs_queue
    for jobcfg in jobs_queue:
        factory = job_factory.get(jobcfg.job_type)
        if factory is None:
            raise ValueError(f"Invalid job_type: {jobcfg.job_type}")
        content = factory(jobcfg)
        jobs_content.append(content)

    yaml_content = "\n".join(jobs_content)
    res = add_head(workflow_name, yaml_content)

    return res

# todo: only a case currently
def add_head(workflow_name: str, content: str) -> str:
    """
    Add a header with workflow name and a trigger condition to the YAML content.
    This function need to be improve.
 
    Parameters:
    - workflow_name: The name of the workflow to be added to the YAML header.
    - content: The original YAML content containing the jobs.
 
    Returns:
    - A complete YAML string with header, trigger condition, and jobs.
    """
    content_dict = yaml.safe_load(content)
    jobs={'jobs': content_dict}
    body = yaml.safe_dump(jobs, default_flow_style=False, allow_unicode=True)
    head_data = {}
    head_data["name"] = workflow_name
    head = yaml.safe_dump(head_data, default_flow_style=False, allow_unicode=True)

    return head+"on:\n  push:\n\n"+body


def buildpush_job_factory(jobcfg: JobConfig, need = None) -> str:
    """
    Generate a YAML string for a build and push job based on a JobConfig object.
 
    Parameters:
    - jobcfg: A JobConfig object containing job configuration.
    - need: Optional dictionary to pass additional configuration (not used in this version).
 
    Returns:
    - A YAML formatted string representing the job configuration.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_file_path = os.path.join(script_dir, 'etc', 'buildpush.yaml')
    
    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as file:
            yaml_data = yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {yaml_file_path} was not found.")
    except Exception as e:
        raise Exception(f"An error occurred while reading the YAML file: {e}")

    steps = yaml_data.setdefault('steps', [])

    for step in steps:
        if step.get('name') == 'Build and push':
            step['with']['file'] = jobcfg.dockerfile_path
            step['with']['tags'] = jobcfg.image_tag
            break

    final_yaml_data = {jobcfg.job_name: yaml_data}

    yaml_res = yaml.safe_dump(final_yaml_data, default_flow_style=False, allow_unicode=True)

    return yaml_res


# todo
def imagebuild_job_factory(jobcfg: JobConfig, need=None):
    pass

# todo
def cvescan_job_factory(jobcfg: JobConfig, need=None):
    pass

# todo
def imagetest_job_factory(jobcfg: JobConfig, need=None):
    pass

# todo
def signature_job_factory(jobcfg: JobConfig, need=None):
    pass

# todo
def imagepush_job_factory(jobcfg: JobConfig, need=None):
    pass


def main():
    queue = deque()
    j1=JobConfig(job_type='buildpush', dockerfile_path='${{ github.workspace }}/img.dockerfile', image_tag='openeuler-python3.10-cann8.0.0')
    j2=JobConfig(job_type='buildpush', dockerfile_path='${{ github.workspace }}/img.dockerfile', image_tag='openeuler-python3.10-cann8.0.0.beta1')
    queue.append(j1)
    queue.append(j2)
    res_str = task_generate(queue, "my test")
    print(res_str)


if __name__ == '__main__':
    main()
