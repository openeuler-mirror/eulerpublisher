#!/bin/bash
set -e

# mount disk
DEV_NUM="/dev/nbd0"
OPENEULER_IMG="$1"
TMP_DATA_PATH="$2"
CLOUD_INIT_CONFIG="$3"
INSTALL_PACKAGES="$4"
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
sudo chroot $MOUNT_DIR yum install -y $(cat ${INSTALL_PACKAGES})
# clean cache
sudo chroot $MOUNT_DIR yum clean all

# for security needed by cloud provider
sudo cp -f ${CLOUD_INIT_CONFIG} ${MOUNT_DIR}/etc/cloud/cloud.cfg.d/
sudo chroot ${MOUNT_DIR} passwd -d root
sudo chroot ${MOUNT_DIR} sed -i 's/root:/&*/'                                                                /etc/shadow
sudo chroot ${MOUNT_DIR} sed -i '/PermitRootLogin/d'                                                         /etc/ssh/sshd_config
sudo chroot ${MOUNT_DIR} sed -i '$aPermitRootLogin no'                                                       /etc/ssh/sshd_config
sudo chroot ${MOUNT_DIR} sed -i '/PasswordAuthentication/d'                                                  /etc/ssh/sshd_config
sudo chroot ${MOUNT_DIR} sed -i '$aPasswordAuthentication no'                                                /etc/ssh/sshd_config
sudo chroot ${MOUNT_DIR} sed -i "/MACs/d"                                                                    /etc/ssh/sshd_config
sudo chroot ${MOUNT_DIR} sed -i '$aMACs hmac-sha2-512,hmac-sha2-256'                                         /etc/ssh/sshd_config
sudo chroot ${MOUNT_DIR} sed -i "/Ciphers/d"                                                                 /etc/ssh/sshd_config
sudo chroot ${MOUNT_DIR} sed -i '$aCiphers aes256-ctr,aes192-ctr,aes128-ctr'                                 /etc/ssh/sshd_config
sudo chroot ${MOUNT_DIR} sed -i -E 's/^([[:space:]]*)group.*/\1groups: [sudo, wheel, adm, systemd-journal]/' /etc/cloud/cloud.cfg
sudo chroot ${MOUNT_DIR} sed -i -E 's/^([[:space:]]*)group.*/&\n\1sudo: ["ALL=(ALL) NOPASSWD:ALL"]/'         /etc/cloud/cloud.cfg

sudo sync
sleep 3

# Insert ena.ko when boots
ARCH="${OPENEULER_IMG##*-}"
ARCH="${ARCH%.*}"
if [[ "${ARCH}" == "aarch64" ]]; then
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
sudo umount -f ${MOUNT_DIR}/dev
sudo umount -f ${MOUNT_DIR}/proc
sudo umount -f ${MOUNT_DIR}/sys
sudo umount -f ${MOUNT_DIR}
sudo rmdir ${MOUNT_DIR}
sudo qemu-nbd -d $DEV_NUM

INPUT_FORMAT="${OPENEULER_IMG##*.}"
OUTPUT_IMG_NAME="${OPENEULER_IMG%.*}-$(date +%Y%m%d_%H%M%S).raw"
OUTPUT_FORMAT="${OUTPUT_IMG_NAME##*.}"
qemu-img resize ${TMP_DATA_PATH}${OPENEULER_IMG} --shrink 8G
qemu-img convert -p -f ${INPUT_FORMAT} -O ${OUTPUT_FORMAT} \
  ${TMP_DATA_PATH}${OPENEULER_IMG} ${OUTPUT_DIR}${OUTPUT_IMG_NAME}

# Delete temporary data
sudo rm -rf ${TMP_DATA_PATH}${OPENEULER_IMG}
echo "Original image cleaned."
