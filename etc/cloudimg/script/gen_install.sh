#!/bin/bash
set -e

# mount disk
DEV_NUM="/dev/nbd0"
OPENEULER_IMG="$1"
OUTPUT_IMG_NAME="$2"
TMP_DATA_PATH="$3"
INSTALL_PACKAGES="$4"
SECURITY_CONFIG="$5"
MOUNT_DIR="/mnt/nbd0"
OUTPUT_DIR="/etc/eulerpublisher/cloudimg/gen/output/"
sudo mkdir -p $OUTPUT_DIR

if [[ $(uname) == "Darwin" ]]; then
    echo "MacOS is not supported"
    exit 1
fi

sudo modprobe nbd max_part=3
nbd_mount=$(mount | grep nbd0 || echo -n "")
if [[ ! -z "${nbd_mount}" ]]; then
    sudo umount "${MOUNT_DIR}"
fi

nbd_loaded=$(lsblk | grep nbd0 || echo -n "")
if [[ ! -z "${nbd_loaded}" ]]; then
    sudo qemu-nbd -d "${DEV_NUM}"
fi
sudo qemu-nbd -c "${DEV_NUM}" "${TMP_DATA_PATH}${OPENEULER_IMG}"
sleep 3

# change configuration
sudo mkdir -p ${MOUNT_DIR}
sudo mount ${DEV_NUM}p2 ${MOUNT_DIR}
sleep 3

# the packages must be installed
yum -y --installroot=${MOUNT_DIR} install cloud-init cloud-utils-growpart
# other packages need to be installed
yum -y --installroot=${MOUNT_DIR} install $(cat ${INSTALL_PACKAGES})

# for security
if [[ ! -z ${SECURITY_CONFIG} ]]; then
    echo "copy secruity.cfg ..."
    cp -f ${SECURITY_CONFIG} ${MOUNT_DIR}/etc/cloud/cloud.cfg.d/
fi

sudo sync
sleep 3
sudo umount ${MOUNT_DIR}
sudo qemu-nbd -d $DEV_NUM
qemu-img convert -O ${OUTPUT_IMG_NAME##*.} ${TMP_DATA_PATH}${OPENEULER_IMG} ${OUTPUT_DIR}${OUTPUT_IMG_NAME}
