# coding=utf-8
import shutil
import subprocess
import sys
import os

import yaml

from eulerpublisher.publisher import logger

OFFICIAL_NAMESPACE = "openeuler"
DEFAULT_WORKDIR = "/tmp/eulerpublisher"


def _publish_app_image(file: str, name, tag):
    if subprocess.call([
        "eulerpublisher",
        "container",
        "app",
        "publish",
        "-p", f"{OFFICIAL_NAMESPACE}/{name}",
        "-t", tag,
        "-f", file,
        "-m"
    ]) != 0:
        return False
    return True


def _publish_distroless_image(file: str, name: str, tag: str):
    if subprocess.call([
        "eulerpublisher",
        "container",
        "distroless",
        "publish",
        "-p", f"{OFFICIAL_NAMESPACE}/{name}",
        "-t", tag,
        "-f", file,
        "-m"
    ]) != 0:
        return False
    return True


def get_publish_images(workdir):
    try:
        # Directory for categorized Distroless container images
        distroless_dir = os.path.join(workdir, "Distroless")
        with open(os.path.join(distroless_dir, "image-list.yml"), "r") as f:
            image_data = yaml.safe_load(f)
            images = image_data.get("images", {})
    except (yaml.YAMLError, OSError) as e:
        logger.error(f"Failed to load image list: {e}")
        return []

    publish_images = []
    for image_name, image_path in images.items():
        image_dir = os.path.join(distroless_dir, image_path)
        # Load tags configuration in the meta.yml
        try:
            with open(os.path.join(image_dir, "meta.yml"), "r") as f:
                tags = yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError) as e:
            logger.error(f"Failed to load tags for {image_name}: {e}")
            continue
        # Republish each tagged version
        publish_image = {}
        for tag, tag_info in tags.items():
            build_file = os.path.join(image_dir, tag_info.get("path", ""))
            publish_image["name"] = image_name
            publish_image["file"] = build_file
            publish_image["tag"] = tag
            publish_images.append(publish_image)
    return publish_images


def _publish_updates(publish_image):
    # Publish a specific image file with given name and tag.
    file, name, tag = publish_image["file"], publish_image["name"], publish_image["tag"]
    if file.endswith("Distrofile"):
        success = _publish_distroless_image(file, name, tag)
    elif file.endswith("Dockerfile"):
        success = _publish_app_image(file, name, tag)
    else:
        logger.warning(f"Unsupported file type: {file}")
        return
    if success:
        logger.info(f"Successfully published {name}:{tag}")
    else:
        logger.error(f"Failed to publish {name}:{tag}")


def _pull_source_code():
    # create workdir
    if os.path.exists(DEFAULT_WORKDIR):
        shutil.rmtree(DEFAULT_WORKDIR)

    # git clone
    s_repourl = "https://gitcode.com/openeuler/openeuler-docker-images.git"
    workdir = f"{DEFAULT_WORKDIR}/openeuler-docker-images"
    os.makedirs(workdir)

    if subprocess.call(['git', 'clone', s_repourl, workdir]) != 0:
        logger.error(f"Failed to clone {s_repourl}")
        return None
    logger.info(f"Clone {s_repourl} successfully.")
    return workdir


if __name__ == "__main__":

    workdir = _pull_source_code()
    if not workdir:
        sys.exit(1)

    publish_images = get_publish_images(workdir)
    for publish_image in publish_images:
        _publish_updates(publish_image)

    sys.exit(0)
