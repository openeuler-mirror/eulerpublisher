import os
import platform
import re
import yaml

from packaging.version import parse, InvalidVersion

from prettytable import PrettyTable
from eulerpublisher.publisher import logger

DOCKERFILE_PATH_DEPTH = 3

# {0} - image path prefix (e.g., AI/opea).
DOC_FILES_PATH_FORMAT = {
    "README": "{0}/README.md",
    "picture": "{0}/doc/picture",
    # {1} - logo file name (e.g., logo.png)
    "logo": "{0}/doc/picture/{1}",
    "meta": "{0}/meta.yml",
    "doc": "{0}/doc",
    "image-info": "{0}/doc/image-info.yml"
}

# parse meta.yml and get the tags && building platforms
def parse_meta_yml(file: str):
    tag = {
        'tag': "",
        'latest': "False"
    }
    arch = ""
    tags = []
    name, prefix = parse_image_prefix(file)
    meta = os.path.join(prefix, "meta.yml")
    # meta = prefix + "/meta.yml"
    if os.path.exists(meta):
        with open(meta, "r") as f:
            tags = yaml.safe_load(f)
        try:
            if not isinstance(tags, dict):
                raise Exception(f"Format error: {meta}")
            for key in tags:
                dockerfile = prefix + "/" + tags[key]['path']
                if dockerfile != file:
                    continue
                tag['tag'] = key
                if 'arch' in tags[key]:
                    arch = tags[key]['arch'].replace(" ", "")
                break
        except yaml.YAMLError as e:
            raise logger.error(f"Error in YAML file : {file} : {e}")

    # generate the default tag
    os_version, image_version = _parse_image_info(file=file, prefix=prefix)
    if not tag['tag']:
        tag['tag'] = re.sub(r'\D', '.', image_version) + \
                     "-oe" + _transform_version_format(os_version)
    # check if the tag is the latest
    tag['latest'] = _is_latest(tag['tag'], tags)
    return name, tag, arch


def _is_latest(current_tag, published_tags):
    if not published_tags:
        return "True"
    try:
        published_versions = [parse(s.split('-')[0]) for s in published_tags]
        current_version = parse(current_tag.split('-')[0])
        if not published_versions:
            return "True"
        elif current_version >= max(published_versions):
            return "True"
        return "False"
    except InvalidVersion:
        return "True"


# transform openEuler version into specifical format
# e.g., 22.03-lts-sp3 -> oe2203sp3
def _transform_version_format(os_version: str):
    # check if os_version has substring "-sp"
    if "-sp" in os_version:
        # delete "lts" in os_version
        os_version = os_version.replace("lts", "")
    # delete all "." and "-"
    ret = os_version.replace(".", "").replace("-", "")

    return ret


def _parse_image_info(file: str, prefix: str):
    """
    Parse application information from the `Dockerfile` or `Distrofile` path.

    `{app-version}/{os-version}/Dockerfile`
    `{app-version}/{os-version}/Distrofile`
    """
    # Check the `Dockerfile` or `Distrofile` path structure.
    prefix = prefix.rstrip("/") + "/"
    context_path = file.replace(prefix, "")
    if len(context_path.split("/")) != DOCKERFILE_PATH_DEPTH:
        raise Exception(
            f"Failed to check file path: {file}, "
            "the correct `Dockerfile` or `Distrofile` path should be "
            "{image-version}/{os-version}/Dockerfile or "
            "{image-version}/{os-version}/Distrofile"
        )

    # Extract base OS version, app version, and app name.
    os_version_path = os.path.dirname(file)
    os_version = os.path.basename(os_version_path)

    image_version_path = os.path.dirname(os_version_path)
    image_version = os.path.basename(image_version_path)

    return os_version, image_version


# see README for details
def parse_image_prefix(file=""):
    """
    Parse and return the image directory based on the given file path.
    """
    contents = file.split("/")
    if len(contents) == 1:
        return "", ""

    # {0} - image path prefix (e.g., AI/opea).
    # {1} - application version (e.g., 1.0.0)
    # {2} - openEuler version (e.g., 24.03-lts-sp2)
    DOCKER_BUILD_FILE_FORMAT = {
        "Dockerfile": "{0}/{1}/{2}/Dockerfile",
        "Distrofile": "{0}/{1}/{2}/Distrofile"
    }

    # Other files do not need to be checked, return empty.
    basename = contents[-1].split(".")[0]
    if basename not in DOC_FILES_PATH_FORMAT and basename not in DOCKER_BUILD_FILE_FORMAT:
        return "", ""

    # Default application directory is the first segment in the file path.
    prefix = contents[0]
    image_list_yaml = os.path.join(prefix, "image-list.yml")
    if not os.path.exists(image_list_yaml):
        return prefix, prefix

    # Load the image-list.yml file
    with open(image_list_yaml, "r", encoding="utf-8") as f:
        image_list = yaml.safe_load(f)

    # Check if the file path matches any of the image paths in the YAML file
    images = image_list.get("images", [])
    for key, value in images.items():
        if all(part in contents for part in value.split("/")):
            return key, prefix + "/" + value.rstrip("/")

    raise ValueError(
        f"Missing required image root directory for multi-scene processing.\n"
        f"Required action: Specify the image root directory in {prefix}/image-list.yml.\n"
        f"File: {file}"
    )


def check_report(change_files: []):
    """
    Minimum Directory Description:
    https://gitee.com/openeuler/openeuler-docker-images/blob/master/README.en.md#22-minimum-directory
    """
    if (platform.machine() != "x86_64"):
        return [], 0

    prefixes = []
    rows = []
    fail_count = 0

    field_names = ["Check Items", "Description", "Check Result"]
    table = PrettyTable(field_names=field_names)
    head = "<tr>" + " ".join(f"<th>{field_name}</th>" for field_name in field_names) + "</tr>"

    # Step 1: Check path format for each changed file
    # The correct path format is defined in the global variable DOC_FILES_PATH_FORMAT.
    for change_file in change_files:

        # Other files and deleted files do not need to be checked.
        file_type = change_file.split("/")[-1].split(".")[0]
        if not os.path.exists(change_file) or file_type not in DOC_FILES_PATH_FORMAT:
            continue

        _, prefix = parse_image_prefix(change_file)
        prefixes.append(prefix)

        # Validate the file path format
        success, description = _check_all_file_paths(change_file)
        fail_count = _append_result(change_file, success, description, rows, table, fail_count)

    # Step 2: Check required documentation files (logo and image-info)
    prefixes = list(set(filter(_need_to_check_doc, prefixes)))
    for prefix in prefixes:

        # Check that logo file exists and is valid
        logo, success, description = _check_image_logo_exist(prefix)
        fail_count = _append_result(logo, success, description, rows, table, fail_count)

        # Check that image-info.yml file exists and passes format checks
        image_info, success, description = _check_image_info(prefix)
        fail_count = _append_result(image_info, success, description, rows, table, fail_count)

    print(table)
    return head, "".join(rows), fail_count


def _append_result(
    file: str,
    success: bool,
    description: str,
    rows: list,
    table: PrettyTable,
    fail_count: int
) -> int:
    """
    Append a failed check result to HTML body and table.
    """
    if success:
        return fail_count

    rows.append(
        f"<tr><th>{file}</th>"
        f"<th>{description}</th>"
        f"<th>:x:FAILED</th></tr>"
    )
    table.add_row([file, description, "FAILURE"])
    return fail_count + 1


def _check_all_file_paths(change_file):
    """
    Check the necessary files for the image, and the global variable
    DOC_FILES_PATH_FORMAT defines the standard path format for files.
    """
    # status = {}
    # field_names = ["Updated File Path Check", "Check Result"]
    # table = PrettyTable(field_names=field_names)
    #
    # for file in change_files:
    contents = change_file.split("/")
    type = contents[-1].split(".")[0]

    _, prefix = parse_image_prefix(change_file)
    correct_path = DOC_FILES_PATH_FORMAT[type].format(
        prefix, contents[-1]
    )
    if not os.path.exists(correct_path):
        return False, f"[Path Error] The expected path should be {correct_path}"
    return True, ""


def _need_to_check_doc(image_root=""):
    """
    Filter the image doc information that needs to be checked.

    These two conditions do not need to be checked.
    1. The doc directory or image-info.yml does not exist.
    2. show-on-appstore: False
    """
    doc_path = DOC_FILES_PATH_FORMAT["doc"].format(image_root)
    if not os.path.exists(doc_path):
        return False
    info_path = DOC_FILES_PATH_FORMAT["image-info"].format(image_root)
    if not os.path.exists(info_path):
        return False
    with open(info_path, "r") as f:
        image_info = yaml.safe_load(f)
    if "show-on-appstore" not in image_info:
        return True
    return image_info["show-on-appstore"]


def _check_image_logo_exist(prefix):
    """
    The standard path for the image logo is {image-prefix}/picture/logo.*
    """
    PICTURE_EXTENSIONS = [".jpeg", ".jpg", ".png", ".gif",
                          ".bmp", ".tiff", ".tif", ".webp",
                          ".svg", ".heif", ".heic"]
    picture_path = DOC_FILES_PATH_FORMAT["picture"].format(prefix)
    logo_path = f"{prefix}/doc/picture/logo.*"

    if not os.path.exists(picture_path):
        return logo_path, False, f"[Missing] LOGO"

    logo_list = os.listdir(picture_path)
    for key in PICTURE_EXTENSIONS:
        for picture in logo_list:
            if not picture.endswith(key):
                return logo_path, True, ""
    return logo_path, False, f"[Missing] LOGO"


def _check_image_info(prefix):
    """
    Parses and checks the contents of the 'image-info.yml' file.
    """
    try:
        image_info = DOC_FILES_PATH_FORMAT["image-info"].format(prefix)
        with open(image_info, "r") as f:
            yaml.safe_load(f)
            f.seek(0)
            lines = f.readlines()
        error_items = check_image_info_items(lines)
        if error_items:
            description = f"[Format Error]: {' '.join(error_items)}"
            return image_info, False, description
        return image_info, True, ""
    except yaml.YAMLError as e:
        raise e


def check_image_info_items(lines):
    """
    YAML format specification for doc/image-info.yml.

    Items:
    - Single-line string values:
      * name
      * category
      * description
      * license

    - Single-line collections (arrays):
      * similar_packages
      * dependency

    - Multi-line blocks (marked with ': |'):
      * environment
      * tags
      * download
      * usage
    """
    standard_items = ["name", "category", "description", "license",
                      "similar_packages", "dependency",
                      "environment: |", "tags: |", "download: |", "usage: |"]

    # Extract image info items from  doc/image-info.yml
    result, content_items = True, list(
        map(
            lambda line: line if line.endswith(": |") else line.split(":")[0],
            list(map(lambda line: line.rstrip(), lines)),
        )
    )

    # Check each required item exists in the doc/image-info.
    error_items = []
    for standard_item in standard_items:
        if standard_item not in content_items:
            error_items.append(standard_item.replace(": |", ""))
    return error_items
