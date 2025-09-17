import sys
import logging
from eulerpublisher.rpm.rpm import RpmHandler
from eulerpublisher.utils.constants import PUBLISH_FAILED, PUBLISH_SUCCESS

def prepare(owner, project, chroots, configfile, desc):
    obj = RpmHandler(
        ownername=owner,
        projectname=project,
        configfile=configfile
    )
    ret = obj.prepare(chroots=chroots.split(','), desc=desc)
    if ret != PUBLISH_SUCCESS:
        sys.exit(1)
    logging.info(f"The project<{owner}/{project}> has been created successfully.")
    sys.exit(0)

def build(owner, project, configfile, url, branch):
    packages = [(url, branch)]
    obj = RpmHandler(
        ownername=owner,
        projectname=project,
        configfile=configfile
    )
    builds = obj.build(packages=packages)
    if builds == []:
        sys.exit(1)
    logging.info("The build ID is: ")
    logging.info(builds)
    sys.exit(0)

