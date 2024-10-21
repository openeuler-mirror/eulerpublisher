import argparse
import click
import glob
import os
import sys
import subprocess
import shutil

LOCAL_REPO = "/tmp/"
EULER_REPO = "https://repo.huaweicloud.com/openeuler/openEuler-{}/everything/{}/Packages/"
EULER_VERSIONS = [
    "20.03-LTS",
    "20.03-LTS-SP1",
    "20.03-LTS-SP2",
    "20.03-LTS-SP3",
    "20.03-LTS-SP4",
    "20.09",
    "21.03",
    "21.09",
    "22.03-LTS",
    "22.03-LTS-SP1",
    "22.03-LTS-SP2",
    "22.03-LTS-SP3",
    "22.09",
    "23.03",
    "23.09",
    "24.03-LTS",
]
USELESS_DIRS = [
    "usr/share/locale/",
    "var/cache/ldconfig/",
    "var/lib/dnf/",
    "var/lib/rpm/"
]
USELESS_DIRS_FILES = [
    "boot",
    "etc/ld.so.cache",
    "etc/pki/ca-trust/extracted/java/cacerts",
    "etc/pki/java/cacerts/",
    "usr/share/doc",
    "usr/share/info",
    "usr/share/man",
    "usr/share/mime"
]

def download_rpms(eulerrepo, packages):
    os.chdir(LOCAL_REPO)
    for package in packages:
        subprocess.call([
            "wget",
            "-q",
            "-r",
            "-l1",
            "-nd",
            "-A",
            f"{package}-[0-9]*.rpm",
            eulerrepo
        ])

def install_rpms(buildroot, packages):
    os.chdir(LOCAL_REPO)
    for package in packages:
        rpms = glob.glob(f"{package}-[0-9]*.rpm")
        subprocess.call([
            "rpm",
            "-ivh",
            "--nodeps",
            "--noscripts",
            "-r",
            buildroot
        ]  + rpms)

def create_user_group(buildroot):
    passwd = os.path.join(buildroot, "etc", "passwd")
    os.makedirs(os.path.dirname(passwd), exist_ok=True)
    with open(passwd, "a") as passwd:
        passwd.write(
            "nonroot:x:65532:65532:nonroot:/home/nonroot:/sbin/nologin\n"
        )
    group = os.path.join(buildroot, "etc", "group")
    with open(group, "a") as group:
        group.write("nonroot:x:65532:\n")

def create_user_home(buildroot):
    nonroot = os.path.join(buildroot, "home", "nonroot")
    os.makedirs(nonroot, exist_ok=True)
    subprocess.call(["groupadd", "-g", "65532", "nonroot"])
    subprocess.call(["useradd", "nonroot", "-u", "65532", "-g", "nonroot"])
    subprocess.call(["chmod", "700", nonroot])
    subprocess.call(["chown", "-R", "nonroot:nonroot", nonroot])
    subprocess.call(["userdel", "-r", "nonroot"])

def create_os_release(buildroot, version, arch):
    os_release_content = "{}\n{}\n{}\n{}\n{}\n{}\n".format(
        'NAME="openEuler"',
        f'VERSION="{version}"',
        'ID="openEuler"',
        f'VERSION_ID="{version[:5]}"',
        f'PRETTY_NAME="openEuler-distroless {version} {arch}"',
        'ANSI_COLOR="0;31"'
    )
    release = os.path.join(buildroot, "etc", "os-release")
    os.makedirs(os.path.dirname(release), exist_ok=True)
    with open(release, "w") as os_release_file:
        os_release_file.write(os_release_content)

def del_file_dir(path):
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

def cleanup_buildroot(buildroot):
    for dir in USELESS_DIRS:
        path = os.path.join(buildroot, dir)
        if not os.path.exists(path):
            continue
        for file in os.listdir(path):
            del_file_dir(os.path.join(path, file))
    for file in USELESS_DIRS_FILES:
        del_file_dir(os.path.join(buildroot, file))
    log_dir = os.path.join(buildroot, "var", "log")
    if os.path.exists(log_dir):
        logs = list(filter(
            lambda f: f.endswith(".log"), os.listdir(log_dir)
        ))
        for log in logs:
            del_file_dir(os.path.join(log_dir, log))
    locale_dir = os.path.join(buildroot, "usr", "lib", "locale")
    if os.path.exists(locale_dir):
        locales = list(filter(
            lambda f: "en_US" not in f and "C.utf8" not in f,
            os.listdir(locale_dir)
        ))
        for locale in locales:
            del_file_dir(os.path.join(locale_dir, locale))

def init_parser():
    new_parser = argparse.ArgumentParser(
        prog="build.py",
        description="build rootfs for distroless container images",
    )
    new_parser.add_argument(
        "-p", "--buildroot", help="the build path of the rootfs"
    )
    new_parser.add_argument(
        "-v", "--version", help="the build version of the openeuler"
    )
    new_parser.add_argument(
        "-a", "--arch", help="build arch"
    )
    new_parser.add_argument(
        "-l", "--packages", help="specify the rpm list to install"
    )
    return new_parser


if __name__ == "__main__":
    parser = init_parser()
    args = parser.parse_args()

    if (
        not args.buildroot
        or not args.version
        or not args.arch
        or not args.packages
    ):
        parser.print_help()
        sys.exit(1)
    # Check if the repo version is valid
    if args.version.upper() not in EULER_VERSIONS:
        click.echo(click.style(f"Invalid repo version in openEuler, {args.version.upper()}.", fg="red"))
        sys.exit(1)
    # Check if the arch is valid
    if args.arch not in ["x86_64", "aarch64"]:
        click.echo(click.style(f"Support arch: x86_64 and aarch64, {args.arch}.", fg="red"))
        sys.exit(1)
    # Set repo here
    eulerrepo = EULER_REPO.format(args.version.upper(), args.arch)
    # Download necessary RPM packages
    packages = args.packages.split(",")
    download_rpms(eulerrepo, packages)
    # Install necessary RPM packages
    install_rpms(args.buildroot, packages)
    # Add nonroot user and group
    create_user_group(args.buildroot)
    # Create os-release file
    create_os_release(args.buildroot, args.version.upper(), args.arch)
    # Cleanup buildroot
    cleanup_buildroot(args.buildroot)

