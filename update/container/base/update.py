# coding=utf-8
import click
import sys
import subprocess
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from eulerpublisher.publisher import logger


UPDATE_VERSIONS = sys.argv[1:]
MAX_REQUEST_COUNT = 20
INIT_DATE = "2000-Jan-01 00:01"
SECONDS_PER_DAY = 24 * 60 * 60
UPDATE_PATTERN = re.compile(r'^\d+')
VERSION_PATTERN = re.compile(r'^openEuler-\d+')
HOME_URL = "http://repo.openeuler.org/"
DEFAULT_HUB = "http://hub.docker.com/v2/repositories/" + \
    "openeuler/openeuler/"


def request(url):
    cnt = 0
    response = None
    while (not response) and (cnt < MAX_REQUEST_COUNT):
        response = requests.get(url=url)
        cnt += 1
    return response


def search_repo(table=None, pattern=UPDATE_PATTERN):
    if not table:
        return None, INIT_DATE
    # find the latest
    update = ""
    latestdate = INIT_DATE
    for row in table.find_all('tr'):
        link = row.find('td', class_='link')
        if link and pattern.match(link.get_text()):
            strlatest = \
                datetime.strptime(latestdate, "%Y-%b-%d %H:%M")
            date = (row.find('td', class_='date')).get_text()
            strptime = datetime.strptime(date, "%Y-%b-%d %H:%M")
            if strptime > strlatest:
                update = link.get_text()
                latestdate = date
    return update, latestdate


def get_table(url):
    # request
    response = request(url=url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # find table
    table = soup.find('tbody')
    return table


def search_hub(url=DEFAULT_HUB):
    # get all tags from url
    tags_url = url + "tags/?page_size=100"
    response = request(url=tags_url)
    data = response.json()
    # parse tags and update date
    tags = []
    for result in data["results"]:
        tag = result["name"]
        last_updated = result["last_updated"]
        tags.append((tag, last_updated))
    if not tags:
        logger.error(f"{url} has no tag!")
    return tags


def get_date(tag="", tag_list=[]):
    for item in tag_list:
        if tag.lower() == item[0].lower():
            return item[1]


def publish_updates(hubtags=[]):
    # search latest update on dockerhub
    for version in UPDATE_VERSIONS:
        url = "http://repo.openeuler.org/openEuler-" \
              + version.upper() \
              + "/docker_img/update/"
        repo_latest, repo_date = search_repo(
            table=get_table(url),
            pattern=UPDATE_PATTERN
        )
        if not repo_latest:
            logger.info(f"{version} has no update.")
            continue
        hub_last_updated = get_date(tag=version.lower(), tag_list=hubtags)
        hub_dts = datetime.strptime(hub_last_updated, "%Y-%m-%dT%H:%M:%S.%fZ")
        repo_dts = datetime.strptime(repo_date, "%Y-%b-%d %H:%M")
        days_diff = (repo_dts - hub_dts).total_seconds() / SECONDS_PER_DAY
        if days_diff > 1:
            logger.info(f"{version} is updating ...")
            # run eulerpublisher to update
            if subprocess.call([
                "eulerpublisher", "container", "base", "publish",
                "-v", version.lower(),
                "-i", "docker_img/update/" + repo_latest,
                "-m"
            ]) != 0:
                return 1
        else:
            logger.info(f"{version} has no update.")
    return 0


def publish_new(hubtags=[]):
    repo_latest, repo_date = search_repo(
        table=get_table(HOME_URL),
        pattern=VERSION_PATTERN
    )
    if not repo_latest:
        logger.error("Result is null, please check searching pattern!")
        return 1
    if repo_latest.endswith('/'):
        repo_latest = repo_latest.rstrip('/')
    new_version = repo_latest.lstrip('openEuler-')
    # if this new version doesn't exist on dockerhub
    if not get_date(tag=new_version.lower(), tag_list=hubtags):
        logger.info(f"Publishing new version {new_version} ...")
        # run eulerpublisher to publish new version
        if subprocess.call([
            "eulerpublisher", "container", "base", "publish",
            "-v", new_version.lower(),
            "-m"
        ]) != 0:
            return 1
    else:
        logger.info(f"No new version.")
    return 0


if __name__ == '__main__':
    # 1. Get the tags which have been published on hub
    hubtags = search_hub()
    if not hubtags:
        sys.exit(1)
    # 2. Publish the updates which are newer than those on hub
    if publish_updates(hubtags) != 0:
        sys.exit(1)
    # 3. Publish new release version
    if publish_new(hubtags) != 0:
        sys.exit(1)
    sys.exit(0)
