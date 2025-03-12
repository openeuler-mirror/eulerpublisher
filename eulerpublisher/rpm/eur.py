import logging
import os
import yaml
from copr.v3 import Client
from eulerpublisher.publisher import EP_PATH


RESPONSE_SUCCESS = 0
RESPONSE_FAILED = 1
DEFAULT_CONFIG_PATH = f'{EP_PATH}/config/rpm/init.yaml'
EUR_HOMEPAGE = 'https://eur.openeuler.openatom.cn'


def init_client_by_default(config_path: str):
    try:
        with open(config_path, "r") as f:
            file = yaml.safe_load(f)
        # 若init.yaml中指明了config-file的路径，则优先使用其初始化client
        if file.get("config-file") and os.path.exists(file["config-file"]):
            logging.debug('Initilizing EUR client from ', file["config-file"])
            return Client.create_from_config_file(file["config-file"])
        else: # 否则，按照约定的环境变量获取初始化参数值
            logging.debug('Initilizing EUR client with environment vars')
            copr = file.get("copr-cli", {})
            return Client(
                config = {
                    'copr_url': EUR_HOMEPAGE,
                    'login': os.environ.get(copr.get("login")),
                    'token': os.environ.get(copr.get("token")),
                    'username': os.environ.get(copr.get("username"))}
            )
    except FileNotFoundError as e:
        logging.error(f"Not found {config_path}: {e}")
    except yaml.YAMLError as e:
        logging.error(f"YAML parsing error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    return None


class EurOperation():
    def __init__(self, configfile="") -> None:
        obs_path = os.path.abspath(configfile)
        if os.path.exists(obs_path):
            logging.debug(f'Initilizing EUR client from input configfile<{obs_path}>')
            try:
                self.client = Client.create_from_config_file(obs_path)
            except Exception as e:
                logging.error(f'Failed to init client with<{obs_path}>: {e}')
            return
        logging.debug("Initilizing EUR client by default configuration")
        self.client = init_client_by_default(DEFAULT_CONFIG_PATH)


    def create_project(self, ownername, projectname, chroots: list, description=None):
        try:
            return self.client.project_proxy.add(ownername,
                                          projectname,
                                          chroots,
                                          description)
        except Exception as e:
            logging.error(f'Failed to create project<{projectname}>: {e}')
            return None


    def get_project(self, ownername, projectname):
        try:
            return self.client.project_proxy.get(ownername, projectname)
        except Exception:
            return None


    def delete_project(self, owner, projectname):
        try:
            self.client.project_proxy.delete(owner, projectname)
            return RESPONSE_SUCCESS
        except Exception as e:
            logging.error(f'Failed to delete project<{projectname}>: {e}')
            return RESPONSE_FAILED


    def create_package_with_scm(self, ownername, projectname, packagename, source_dict : dict):
        """
        Args:
            source_dict = {
                'clone_url': 'url',
                'committish': '',
                'subdirectory': 'path',
                'spec': 'package.spec',
                'scm_type': 'git'
            }
        """
        try:
            return self.client.package_proxy.add(ownername,
                                                 projectname,
                                                 packagename,
                                                 source_type='scm',
                                                 source_dict=source_dict)
        except Exception as e:
            logging.error(f'Failed to create package<{ownername}/{projectname}/{packagename}> with scm: {e}')
            return None


    def delete_package(self, ownername, projectname, packagename):
        try:
            self.client.package_proxy.delete(ownername, projectname, packagename)
            return RESPONSE_SUCCESS
        except Exception as e:
            logging.error(f'Failed to delete package<{ownername}/{projectname}/{packagename}>: {e}')
            return RESPONSE_FAILED


    def get_package(self,
                    ownername,
                    projectname,
                    packagename,
                    with_latest_build=False,
                    with_latest_succeeded_build=False):
        try:
            return self.client.package_proxy.get(
                ownername,
                projectname,
                packagename,
                with_latest_build,
                with_latest_succeeded_build
            )
        except Exception as e:
            logging.error(f'Failed to get package<{ownername}/{projectname}/{packagename}: {e}')
            return None


    def get_package_list(self, ownername, projectname):
        try:
            return self.client.package_proxy.get_list(
                ownername,
                projectname
            )
        except Exception as e:
            logging.error(f'Failed to get all packages from project<{ownername}/{projectname}>: {e}')
            return None


    def get_build_state_by_id(self, id: int):
        try:
            res = self.client.build_proxy.get(id)
            return res.state
        except Exception as e:
            logging.error(f'Failed to get build<{id}>: {e}')
            return None


    def get_project_builds(self, ownername, projectname, packagename=None, status=None):
        try:
            return self.client.build_proxy.get_list(ownername,
                                                    projectname,
                                                    packagename,
                                                    status)
        except Exception as e:
            logging.error(f'Failed to get for project<{projectname}>, package<{packagename}>: {e}')
            return None


    def cancel_build(self, buildid: int):
        try:
            self.client.build_proxy.cancel(buildid)
        except Exception as e:
            logging.error(f'Failed to cancel build<{buildid}>: {e}')


    def create_build_from_scm(self,
                              ownername,
                              projectname,
                              clone_url,
                              subdirectory='',
                              spec='',
                              committish=''):
        try:
            return self.client.build_proxy.create_from_scm(
                ownername,
                projectname,
                clone_url,
                committish,
                subdirectory,
                spec
            ).id
        except Exception as e:
            logging.error(f'Failed to create build from scm for <{clone_url}>: {e}')
            return None


    def create_build_from_package(self,
                                  ownername,
                                  projectname,
                                  packagename):
        try:
            return self.client.package_proxy.build(ownername, projectname, packagename)
        except Exception as e:
            logging.error(f'Failed to create build from package<{ownername}/{projectname}/{packagename}>: {e}')
            return None
