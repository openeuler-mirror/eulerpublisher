#!/bin/bash
set -e

DEV_NUM="/dev/nbd0"
OPENEULER_IMG="openEuler-""$1-$2"
TMP_DATA_PATH="$3"
MOUNT_DIR="/mnt/nbd0"

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
sudo qemu-nbd -c "${DEV_NUM}" "${TMP_DATA_PATH}${OPENEULER_IMG}.qcow2"
sudo e2fsck -fy ${DEV_NUM}p2 
sudo resize2fs ${DEV_NUM}p2 6G
sudo sync

# Add some timeout to avoid device busy error
sleep 3

# Reset fdisk error status
sed -e 's/\s*\([\+0-9a-zA-Z]*\).*/\1/' << EOF | sudo fdisk ${DEV_NUM}
  p # print current partition
  d # delete partition
  2 # partition number 2
  n # create new partition
  p # partition type primary
  2 # partition number 2
    # default start position
  +6G # 6G for root partition
  w # sync changes to disk
  p # print partition
  q # done
EOF

sudo sync
sleep 3

# Insert ena.ko when boots
if [[ "$2" == "aarch64" ]]; then
    mkdir -p ${MOUNT_DIR}
    sudo mount ${DEV_NUM}p2 ${MOUNT_DIR}
    sudo rm -f ${TMP_DATA_PATH}ena.txt
    sudo find ${MOUNT_DIR}/usr/lib/modules/ -name ena.ko.xz > ${TMP_DATA_PATH}ena.txt
    # if ena.ko is not found within current image, copy from external
    if [ -z "${TMP_DATA_PATH}ena.txt" ]; then  
        sudo cp -f ${TMP_DATA_PATH}ena.ko ${MOUNT_DIR}/root/
    else  
        sudo cp -f $(cat ${TMP_DATA_PATH}ena.txt | head -n 1) ${MOUNT_DIR}/root/
        sudo unxz -f ${MOUNT_DIR}/root/ena.ko.xz
    fi
    sudo bash -c ' echo "install ena insmod /root/ena.ko" >> ${MOUNT_DIR}/etc/modprobe.d/ena.conf '
    sudo bash -c ' echo "ena" >> ${MOUNT_DIR}/etc/modules-load.d/ena.conf '
    sudo sync
    sudo umount ${MOUNT_DIR}
fi

sudo qemu-nbd -d ${DEV_NUM}
qemu-img resize ${TMP_DATA_PATH}${OPENEULER_IMG}.qcow2 --shrink 8G
qemu-img convert ${TMP_DATA_PATH}${OPENEULER_IMG}.qcow2 ${OPENEULER_IMG}.raw
