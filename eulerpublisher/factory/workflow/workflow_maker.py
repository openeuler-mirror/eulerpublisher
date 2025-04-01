from eulerpublisher.factory.workflow.taskqueue import JobConfig
from collections import deque
import yaml, os

class WorkflowMaker:
    
    def buildpush_job_factory(self, jobcfg: JobConfig, need = None):
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
    
    def build_workflow(self, name_workflow, input_data, save_dir, buildpush=True, build=False, test=False, cve=False, sign=False, push=False):
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
        queue = JobConfig.task_queue_generate(input_data, buildpush, build, test, cve, sign, push)
        
        # Generate the workflow content based on the task queue and workflow name
        workflow_content = self.task_generate(queue, name_workflow)
        
        os.makedirs(save_dir, exist_ok=True)
        output_file = os.path.join(save_dir, 'output.yaml')

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(workflow_content)
    
    def add_head(self, workflow_name: str, content: str):
        """
        Add a header with workflow name and a trigger condition to the YAML content.

        Parameters:
        - workflow_name (str): The name of the workflow to be added to the YAML header.
        - content (str): The original YAML content containing the jobs.

        Returns:
        - str: A complete YAML string with header, trigger condition, and jobs.
        """
        content_dict = yaml.safe_load(content)
        jobs={'jobs': content_dict}
        body = yaml.safe_dump(jobs, default_flow_style=False, allow_unicode=True)
        head_data = {}
        head_data["name"] = workflow_name
        head = yaml.safe_dump(head_data, default_flow_style=False, allow_unicode=True)

        return head+"on:\n  push:\n\n"+body
    
    def task_generate(self, jobs_queue: deque, workflow_name: str):
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
            'buildpush': self.buildpush_job_factory,
            'imagebuild': self.imagebuild_job_factory,
            'cvescan': self.cvescan_job_factory,
            'imagetest': self.imagetest_job_factory,
            'signature': self.signature_job_factory,
            'imagepush': self.imagepush_job_factory,
        }

        #todo: mark and set 'need' between different job_task among jobs_queue
        for jobcfg in jobs_queue:
            factory = job_factory.get(jobcfg.job_type)
            if factory is None:
                raise ValueError(f"Invalid job_type: {jobcfg.job_type}")
            content = factory(jobcfg)
            jobs_content.append(content)

        yaml_content = "\n".join(jobs_content)
        res = self.add_head(workflow_name, yaml_content)

        return res