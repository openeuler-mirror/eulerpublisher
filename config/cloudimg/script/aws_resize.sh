#!/bin/bash
set -e

DEV_NUM="/dev/nbd0"
OPENEULER_IMG="openEuler-""$1-$2"
TMP_DATA_PATH="$3"
OUTPUT_DIR="${TMP_DATA_PATH}/output/"
MOUNT_DIR="/mnt/nbd0"
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
sudo qemu-nbd -c "${DEV_NUM}" "${TMP_DATA_PATH}${OPENEULER_IMG}.qcow2"
sudo e2fsck -fy ${DEV_NUM}p2 || true
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

# mount disk
mkdir -p ${MOUNT_DIR}
sudo mount ${DEV_NUM}p2 ${MOUNT_DIR}

# enable PasswordAuth for temporary ssh
sed -i '/PasswordAuthentication/s/^/# /'        ${MOUNT_DIR}/etc/ssh/sshd_config
sed -i '$a\PasswordAuthentication yes'          ${MOUNT_DIR}/etc/ssh/sshd_config
sed -i '/KbdInteractiveAuthentication/s/^/# /'  ${MOUNT_DIR}/etc/ssh/sshd_config
sed -i '$a\KbdInteractiveAuthentication yes'    ${MOUNT_DIR}/etc/ssh/sshd_config

# Insert ena.ko when boots
if [[ "$2" == "aarch64" ]]; then
    sudo rm -f ${TMP_DATA_PATH}ena.txt
    sudo find ${MOUNT_DIR}/usr/lib/modules/ -name ena.ko.xz > ${TMP_DATA_PATH}ena.txt
    # if ena.ko is not found throw error
    if [ -z "${TMP_DATA_PATH}ena.txt" ]; then  
        echo "ena.ko is needed!"
    else  
        sudo cp -f $(cat ${TMP_DATA_PATH}ena.txt | head -n 1) ${MOUNT_DIR}/root/
        sudo unxz -f ${MOUNT_DIR}/root/ena.ko.xz
    fi
    sudo bash -c ' echo "install ena insmod /root/ena.ko" >> ${MOUNT_DIR}/etc/modprobe.d/ena.conf '
    sudo bash -c ' echo "ena" >> ${MOUNT_DIR}/etc/modules-load.d/ena.conf '
    sudo sync
fi

# umount
sudo umount ${MOUNT_DIR}
sudo rmdir ${MOUNT_DIR}

sudo qemu-nbd -d ${DEV_NUM}
qemu-img resize ${TMP_DATA_PATH}${OPENEULER_IMG}.qcow2 --shrink 8G
qemu-img convert ${TMP_DATA_PATH}${OPENEULER_IMG}.qcow2 ${OUTPUT_DIR}${OPENEULER_IMG}.raw


# Delete temporary data
sudo rm -rf ${TMP_DATA_PATH}${OPENEULER_IMG}.qcow2
echo "Original image cleaned."
