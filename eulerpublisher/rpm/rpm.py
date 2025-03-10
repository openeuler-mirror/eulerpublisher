from eulerpublisher.rpm.eur import EurOperation
import eulerpublisher.publisher.publisher as pb
import logging


BUILD_STATE_SUCCESS = "succeeded"
BUILD_STATE_FAILED = "failed"


class EurBuildRpms(pb.Publisher):
    def __init__(self, ownername, projectname="", configfile="") -> None:
        self.ownername = ownername
        self.projectname = projectname
        self.eur = EurOperation(configfile=configfile)


    def prepare(self, chroots: list, desc: str):
        proj = self.eur.get_project(ownername=self.ownername, projectname=self.projectname)
        if proj: # `project` has been created
            logging.warning(
                f'Project<{self.ownername}/{self.projectname}> '
                'has been created already, no need to create it again!')
            return pb.PUBLISH_SUCCESS
        proj = self.eur.create_project(
            ownername=self.ownername,
            projectname=self.projectname,
            chroots=chroots,
            description=desc)
        return pb.PUBLISH_SUCCESS if proj else pb.PUBLISH_FAILED


    def build(self, packages):
        buildlist = []
        for url, branch in packages:
            buildlist.append(self.eur.create_build_from_scm(
                ownername=self.ownername,
                projectname=self.projectname,
                clone_url=url,
                committish=branch))
        return buildlist
    
    
    def query_build_state(self, buildids: list):
        states = []
        for id in buildids:
            state = self.eur.get_build_state_by_id(id)
            if state:
                states.append((id, state))
        return states

