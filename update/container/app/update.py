# coding=utf-8
import click
import sys


DEFAULT_WORKDIR="/tmp/eulerpublisher/container/app/"


def create_comment(
    armRet: str, armDetails: str, 
    amdRet: str, amdDetails: str
):
    return \
        "| Check Name | Build Result | Build Details | \n" \
        "|------------|--------------|---------------| \n" \
        f"| aarch64   | {armRet}     | {armDetails}  | \n" \
        f"| x86_64    | {amdRet}     | {amdDetails}  |"

def post_comment():
    pass

def parser(url: str):
    pass


class ContainerVerification:
    '''
    Check whether the upstream application supports openEuler
    1. Build container image with Dockerfile
    2. Test the container image
    3. Comment the PR with test result 
    '''

    def __init__(self, url: str):
        pass

    def verify(self):
        # TODO build and test image according to the submitted PR
        pass

    def publish(self):
        # TODO publish while the PR is merged
        pass


if __name__ == "__main__":
    comment = create_comment(
        armRet=":white_check_mark: SUCCESS",
        armDetails="#8926",
        amdRet=":white_check_mark: SUCCESS",
        amdDetails="#8929"
    )
