#!/bin/bash
set -e

# mount disk
DEV_NUM="/dev/nbd0"
OPENEULER_IMG="$1"
TMP_DATA_PATH="$2"
CLOUD_INIT_CONFIG="$3"
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

# makes sure that running yum in the chroot it can get out to download stuff
sudo cp /etc/resolv.conf $MOUNT_DIR/etc/resolv.conf
# install cloud-init 
sudo chroot $MOUNT_DIR yum install -y cloud-init cloud-utils-growpart
# clean cache
sudo chroot $MOUNT_DIR yum clean all

# copy cloud-init configuration file
if [[ ! -z ${CLOUD_INIT_CONFIG} ]]; then
  sudo cp -f ${CLOUD_INIT_CONFIG} ${MOUNT_DIR}/etc/cloud/cloud.cfg.d/
fi

# enable `sudo` for user-openeuler
sudo chroot $MOUNT_DIR sed -i -E "/groups:/s/^([[:blank:]]*).*/\1groups: [sudo, wheel, adm, systemd-journal]/" /etc/cloud/cloud.cfg
sudo chroot $MOUNT_DIR sed -i -E '/groups:/s/^([[:blank:]]*).*/&\n\1sudo: ["ALL=(ALL) NOPASSWD:ALL"]/' /etc/cloud/cloud.cfg

sudo sync
sleep 3

sudo umount -f ${MOUNT_DIR}/dev
sudo umount -f ${MOUNT_DIR}/proc
sudo umount -f ${MOUNT_DIR}/sys
sudo umount -f ${MOUNT_DIR}
sudo rmdir ${MOUNT_DIR}
sudo qemu-nbd -d $DEV_NUM

INPUT_FORMAT="${OPENEULER_IMG##*.}"
OUTPUT_IMG_NAME="${OPENEULER_IMG%.*}-$(date +%Y%m%d_%H%M%S).qcow2"
OUTPUT_FORMAT="${OUTPUT_IMG_NAME##*.}"
qemu-img convert -p -c -f ${INPUT_FORMAT} -O ${OUTPUT_FORMAT} \
  ${TMP_DATA_PATH}${OPENEULER_IMG} ${OUTPUT_DIR}${OUTPUT_IMG_NAME}

# delete temporary data
sudo rm -rf ${TMP_DATA_PATH}${OPENEULER_IMG}
echo "Original image cleaned."