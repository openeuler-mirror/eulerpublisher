#!/bin/bash
set -e

# install packages
if [[ ! -z "${INSTALL_PACKAGES}" ]]; then
    yum -y update
    yum -y install ${INSTALL_PACKAGES}
fi

# disable PasswordAuth
sed -i '/PasswordAuthentication/s/^/# /'        /etc/ssh/sshd_config
sed -i '$a\PasswordAuthentication no'           /etc/ssh/sshd_config
sed -i '/KbdInteractiveAuthentication/s/^/# /'  /etc/ssh/sshd_config
sed -i '$a\KbdInteractiveAuthentication no'     /etc/ssh/sshd_config

# enable RSAAuthentication
sed -i '/RSAAuthentication/s/^/# /'      /etc/ssh/sshd_config
sed -i '$a\RSAAuthentication yes'        /etc/ssh/sshd_config

# disable RhostsRSAAuthentication
sed -i '/RhostsRSAAuthentication/s/^/# /' /etc/ssh/sshd_config
sed -i '$a\RhostsRSAAuthentication no'    /etc/ssh/sshd_config

# disable set_hostname
sed -i "/set_hostname/d"     /etc/cloud/cloud.cfg
sed -i "/update_hostname/d"  /etc/cloud/cloud.cfg
sed -i "/update_etc_hosts/d" /etc/cloud/cloud.cfg
sed -i "/set_passwords/d"    /etc/cloud/cloud.cfg

#delete root
sudo passwd -d root
sudo sed -i 's/root:/&*/'  /etc/shadow

# disable root and pwauth, enable `sudo` for user-openeuler
sed -i -E "/groups:/s/^([[:blank:]]*).*/\1groups: [sudo, wheel, adm, systemd-journal]/" /etc/cloud/cloud.cfg
sed -i -E '/groups:/s/^([[:blank:]]*).*/&\n\1sudo: ["ALL=(ALL) NOPASSWD:ALL"]/' /etc/cloud/cloud.cfg

# disable Apparmor
echo "GRUB_CMDLINE_LINUX_DEFAULT=\"apparmor=0\"" >> /etc/default/grub
# Update grub config
if [[ "$(uname -m)" == "x86_64" ]]; then
    grub2-mkconfig -o /boot/grub2/grub.cfg
elif [[ "$(uname -m)" == "aarch64" ]]; then
    grub2-mkconfig -o /boot/efi/EFI/openEuler/grub.cfg
fi