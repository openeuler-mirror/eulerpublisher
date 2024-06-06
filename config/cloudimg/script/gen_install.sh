#!/bin/bash
set -e

# mount disk
DEV_NUM="/dev/nbd0"
OPENEULER_IMG="$1"
OUTPUT_IMG_NAME="$2"
TMP_DATA_PATH="$3"
INSTALL_PACKAGES="$4"
GENERIC_CONFIG="$5"
MOUNT_DIR="/mnt/nbd0"
OUTPUT_DIR="${TMP_DATA_PATH}/output/"
sudo mkdir -p $MOUNT_DIR
sudo mkdir -p $OUTPUT_DIR

if [[ $(uname) == "Darwin" ]]; then
    echo "MacOS is not supported"
    exit 1
fi

sudo modprobe nbd max_part=3
nbd_mount=$(mount | grep nbd0 || echo -n "")
if [[ ! -z "${nbd_mount}" ]]; then
    sudo umount -f ${MOUNT_DIR}/dev
    sudo umount -f ${MOUNT_DIR}/proc
    sudo umount -f ${MOUNT_DIR}/sys
    sudo umount -f ${MOUNT_DIR}
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
sudo mount --bind /dev  ${MOUNT_DIR}/dev
sudo mount --bind /proc ${MOUNT_DIR}/proc
sudo mount --bind /sys  ${MOUNT_DIR}/sys
sleep 3

# install packages
if [[ ! -z "$(cat ${INSTALL_PACKAGES})" ]]; then
    # makes sure that running yum in the chroot it can get out to download stuff
    sudo cp /etc/resolv.conf $MOUNT_DIR/etc/resolv.conf
    # the packages need to be installed are listed in `INSTALL_PACKAGES`
    sudo chroot $MOUNT_DIR yum install -y $(cat ${INSTALL_PACKAGES})
    # clean cache
    sudo chroot $MOUNT_DIR yum clean all
fi

# for security needed by huawei
if [[ ! -z ${GENERIC_CONFIG} ]]; then
    echo "Copying gen.cfg ..."
    sudo cp -f ${GENERIC_CONFIG} ${MOUNT_DIR}/etc/cloud/cloud.cfg.d/
fi

sudo sync
sleep 3

sudo umount -f ${MOUNT_DIR}/dev
sudo umount -f ${MOUNT_DIR}/proc
sudo umount -f ${MOUNT_DIR}/sys
sudo umount -f ${MOUNT_DIR}
sudo rmdir ${MOUNT_DIR}
sudo qemu-nbd -d $DEV_NUM

INPUT_FORMAT="${OPENEULER_IMG##*.}"
OUTPUT_FORMAT="${OUTPUT_IMG_NAME##*.}"
qemu-img convert -c -f ${INPUT_FORMAT} -O ${OUTPUT_FORMAT} \
    ${TMP_DATA_PATH}${OPENEULER_IMG} ${OUTPUT_DIR}${OUTPUT_IMG_NAME}

# delete temporary data
sudo rm -rf ${TMP_DATA_PATH}${OPENEULER_IMG}
echo "Original image cleaned."
