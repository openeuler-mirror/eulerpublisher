from collections import deque
from typing import List, Dict, Optional


class JobConfig:
    """
    A configuration class for jobs involving software building and/or deploying.

    Attributes:
        job_type (str): Specifies the type of job, such as 'buildpush','build','test','cve','sign' and 'push'.
        dockerfile_path (str): The filepath pointing to the Dockerfile.
        image_tag (str): The tag assigned to the Docker image.
        job_name (str): The name of the job, generated based on job_type and image_tag.
    """

    def __init__(self, job_type: str, dockerfile_path: str, image_tag: str):
        """
        Initializes a new JobConfig instance.

        Parameters:
            job_type (str): The type of job (e.g., 'build', 'deploy').
            dockerfile_path (str): The absolute or relative path to the Dockerfile.
            image_tag (str): The unique identifier for the Docker image.
        """
        self.job_type = job_type
        self.dockerfile_path = dockerfile_path
        self.image_tag = image_tag
        self.job_name = self._generate_job_name(self.job_type, self.image_tag)

    def __repr__(self):
        """
        Returns a string representation of the JobConfig object.

        Returns:
            str: A formatted string containing the job type, job name, Dockerfile path, and image tag.
        """
        return (f"JobConfig(job_type='{self.job_type}', "
                f"job_name='{self.job_name}', "
                f"dockerfile_path='{self.dockerfile_path}', "
                f"image_tag='{self.image_tag}')")
   
    def _generate_job_name(self, job_type: str, image_tag: str) -> str:
        """
        Generates a job name by combining the job type and a sanitized version of the image tag.

        Parameters:
            job_type (str): The type of job.
            image_tag (str): The tag of the Docker image, which will be sanitized.

        Returns:
            str: The generated job name.
        """
        sanitized_tag = ''.join(char for char in image_tag if char.isalnum() or char == '-' or char == '_')

        return f"{job_type}_{sanitized_tag}"


def task_queue_generate( 
    job_configs_list: List[Dict[str, Optional[str]]],
    buildpush: bool = True,
    build: bool = False,
    test: bool = False,
    cve: bool = False,
    sign: bool = False,
    push: bool = False
 ) -> deque:
    """
    Generate a task queue based on job configurations and task flags.

    Parameters:
    - job_configs_list: A list of dictionaries containing 'dockerfile_path' and 'image_tag'.
    - buildpush: Include a combined build and push task if True.
    - build: Include a build task if True.
    - test: Include a test task if True.
    - cve: Include a CVE scan task if True.
    - sign: Include a signing task if True.
    - push: Include a push task if True.

    Raises:
    - ValueError: If invalid task combinations are specified.

    Returns:
    - A deque containing JobConfig objects.
    """
    if buildpush and any([build, test, cve, sign, push]):
        raise ValueError("buildpush cannot be True when any other task is specified.")

    if not build and any([test, cve, sign, push]):
        raise ValueError("build must be True when any other task (test, cve, sign, push) is specified.")

    job_types_map = {
        'buildpush': ('buildpush', buildpush),
        'build': ('imagebuild', build),
        'test': ('imagetest', test),
        'cve': ('cvescan', cve),
        'sign': ('signature', sign),
        'push': ('imagepush', push)
    }

    job_queue = deque()
    for job_config_dict in job_configs_list:
        dockerfile_path = job_config_dict.get('dockerfile_path')
        image_tag = job_config_dict.get('image_tag')

        if dockerfile_path is None or image_tag is None:
            raise ValueError("Both dockerfile_path and image_tag can not be None.")

        for _, (job_type, should_add) in job_types_map.items():
            if should_add:
                job_config = JobConfig(job_type, dockerfile_path, image_tag)
                job_queue.append(job_config)
                if job_type == 'buildpush':
                    break

    return job_queue


def main():
    input=[
        {
            'dockerfile_path': '${{ github.workspace }}/img1.dockerfile',
            'image_tag': 'openeuler-python3.10-cann8.0.0',
        },
        {
            'dockerfile_path': '${{ github.workspace }}/img2.dockerfile',
            'image_tag': 'openeuler-python3.10-cann8.0.0.beta1',
        }
    ]
    queue = task_queue_generate(input)
    for q in queue:
        print(f"pop task: {q}")


if __name__ == '__main__':
    main()
