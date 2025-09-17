from eulerpublisher.rpm.eur import EurOperation
from eulerpublisher.utils.constants import SUCCESS, FAILED, RPM_REPO_TYPES
from eulerpublisher.utils.exceptions import UnsupportedRpmRepoType


class RpmHandler():
    def __init__(self, config, logger, db) -> None:
        self.config = config
        self.logger = logger
        self.db = db
        self.eur = EurOperation()


    def prepare(self, ownername, projectname, chroots: list, desc: str):
        proj = self.eur.get_project(ownername=ownername, projectname=projectname)
        if proj: # `project` has been created
            self.logger.warning(
                f'Project<{ownername}/{projectname}> '
                'has been created already, no need to create it again!')
            return SUCCESS
        proj = self.eur.create_project(
            ownername=ownername,
            projectname=projectname,
            chroots=chroots,
            description=desc)
        return SUCCESS if proj else FAILED


    def build_scm_repo(self, ownername, projectname, packages):
        buildlist = []
        for url, subdirectory, spec, branch in packages:
            self.logger.info(f'Building {url}, {subdirectory}, {spec}, {branch}')
            buildlist.append(self.eur.create_build_from_scm(
                ownername=ownername,
                projectname=projectname,
                clone_url=url,
                subdirectory=subdirectory,
                spec=spec,
                committish=branch))
        return buildlist

    def build_pypi_repo(self, ownername, projectname, packages):
        buildlist = []
        for pypi_package_name, pypi_package_version in packages:
            pypi_package_version = None if pypi_package_version == '' else pypi_package_version
            buildlist.append(self.eur.create_build_from_pypi(
                ownername=ownername,
                projectname=projectname,
                pypi_package_name=pypi_package_name,
                pypi_package_version=pypi_package_version))
        return buildlist

    def build_rubygems_repo(self, ownername, projectname, packages):
        buildlist = []
        for gem_name in packages:
            buildlist.append(self.eur.create_build_from_rubygems(
                ownername=ownername,
                projectname=projectname,
                gem_name=gem_name))
        return buildlist
    
    
    def query_build_state(self, buildids: list):
        states = []
        for id in buildids:
            state = self.eur.get_build_state_by_id(id)
            if state:
                states.append((id, state))
        return states

    def handle_rpm(self, artifact_type, artifact_info):
        self.logger.info("Building rpm using EUR API...")
        repo_type =artifact_info["repo_type"]
        owner = artifact_info["owner"]
        project = artifact_info["project"]
        chroots = artifact_info["chroots"]
        desc = artifact_info.get("desc", "")
        packages = artifact_info["packages"]

        ret = FAILED
        while ret != SUCCESS:
            ret = self.prepare(owner, project, chroots=chroots.split(','), desc=desc)

        build_functions = {
            RPM_REPO_TYPES[0]: self.build_scm_repo,
            RPM_REPO_TYPES[1]: self.build_pypi_repo,
            RPM_REPO_TYPES[2]: self.build_rubygems_repo,
        }
        if repo_type not in build_functions:
            self.logger.error(f"Unsupported repo type: {repo_type}")
            raise UnsupportedRpmRepoType(repo_type)

        build_list = build_functions[repo_type](owner, project, packages)
        states = self.query_build_state(build_list)
        self.logger.info(f"build states:{states}")
