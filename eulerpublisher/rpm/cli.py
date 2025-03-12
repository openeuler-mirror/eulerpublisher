# coding=utf-8
import click
import logging
import sys
import eulerpublisher.publisher.publisher as pb
from eulerpublisher.rpm.rpm import EurBuildRpms


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

@click.group(
    name="rpm",
    help="Build rpms with EUR."
)
def group():
    pass

@group.command(
    name="prepare",
    help="Create the target project on EUR."
)
@click.option(
    "-o",
    "--owner",
    required=True,
    help="The user space you want to create project."
)
@click.option(
    "-p",
    "--project",
    required=True,
    help="The project to be created."
)
@click.option(
    "-f",
    "--configfile",
    help="The path of config file used to initilize EUR API client."
)
@click.option(
    "-c",
    "--chroots",
    default="openeuler-24.03_LTS_SP1-x86_64,openeuler-24.03_LTS_SP1-aarch64",
    help="The chroots, such as `openeuler-24.03_LTS_SP1-aarch64`, "
         "or you can input multiple items connecting by `,`, i.e., "
         "`openeuler-24.03_LTS_SP1-x86_64,openeuler-24.03_LTS_SP1-aarch64`."
)
@click.option(
    "-d",
    "--desc",
    default="",
    help="The descripition for your project.",
)
def prepare(owner, project, chroots, configfile, desc):
    obj = EurBuildRpms(
        ownername=owner,
        projectname=project,
        configfile=configfile
    )
    ret = obj.prepare(chroots=chroots.split(','), desc=desc)
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    logging.info(f"The project<{owner}/{project}> has been created successfully.")
    sys.exit(0)


@group.command(
    name="build",
    help="Build openEuler rpm packages by EUR."
)
@click.option(
    "-o",
    "--owner",
    required=True,
    help="The user space you want to create build."
)
@click.option(
    "-p",
    "--project",
    required=True,
    help="The project where the build locates."
)
@click.option(
    "-f",
    "--configfile",
    help="The path of config file used to initilize EUR API client."
)
@click.option(
    "-u",
    "--url",
    required=True,
    help="The clone url of package source code."
)
@click.option(
    "-b",
    "--branch",
    default="master",
    help="The branch of the source repo.",
)
def build(owner, project, configfile, url, branch):
    packages = [(url, branch)]
    obj = EurBuildRpms(
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
    

@group.command(
    name="query",
    help="Query the build state."
)
@click.option(
    "-o",
    "--owner",
    required=True,
    help="The user space you want to create build."
)
@click.option(
    "-l",
    "--buildlist",
    required=True,
    help="The buildIDs you want to check, such as `101010`, "
         "or you can input multiple IDs connecting by `,`, i.e., "
         "`101010,101011`."
)
def query(owner, buildlist):
    obj = EurBuildRpms(ownername=owner)
    builds = obj.query_build_state(buildids=buildlist.split(','))
    if builds == []:
        sys.exit(1)
    logging.info("The query results: ")
    logging.info(builds)
    sys.exit(0)