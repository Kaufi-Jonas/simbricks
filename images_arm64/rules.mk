# Copyright 2021 Max Planck Institute for Software Systems, and
# National University of Singapore
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

include mk/subdir_pre.mk

PACKER_VERSION := 1.7.0
KERNEL_VERSION := 5.15.93

BASE_IMAGE := $(d)output-base/base
VTA_DEP_IMAGE := $(d)output-vta_dep/vta_dep
VTA_IMAGE := $(d)output-vta/vta
GEMSTONE_IMAGE := $(d)output-gemstone/gemstone
COMPRESSED_IMAGES ?= false

IMAGES := $(BASE_IMAGE) $(NOPAXOS_IMAGE) $(MEMCACHED_IMAGE) $(VTA_IMAGE)
RAW_IMAGES := $(addsuffix .raw,$(IMAGES))

IMAGES_MIN := $(BASE_IMAGE)
RAW_IMAGES_MIN := $(addsuffix .raw,$(IMAGES_MIN))

img_dir := $(d)
packer := $(d)packer

bz_image := $(d)bzImage
vmlinux := $(d)vmlinux
kernel_pardir := $(d)kernel
kernel_dir := $(kernel_pardir)/linux-$(KERNEL_VERSION)
kernel_config := $(kernel_pardir)/config-$(KERNEL_VERSION)
kernel_options := ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
kheader_dir := $(d)kernel/kheaders
kheader_tar := $(d)kheaders.tar.bz2
m5_bin := $(d)m5
guest_init := $(d)/scripts/guestinit.sh

build-images: $(IMAGES) $(RAW_IMAGES) $(vmlinux) $(bz_image)

build-images-min: $(IMAGES_MIN) $(RAW_IMAGES_MIN) $(vmlinux) $(bz_image)

# only converts existing images to raw
convert-images-raw:
	for i in $(IMAGES); do \
	    [ -f $$i ] || continue; \
	    $(QEMU_IMG) convert -f qcow2 -O raw $$i $${i}.raw ; done

################################################
# Disk image

%.raw: %
	$(QEMU_IMG) convert -f qcow2 -O raw $< $@

$(BASE_IMAGE): $(packer) $(QEMU) $(bz_image) $(m5_bin) $(kheader_tar) \
    $(guest_init) $(kernel_config) \
    $(addprefix $(d), extended-image.pkr.hcl scripts/install-base.sh \
      scripts/cleanup.sh)
	rm -rf $(dir $@)
	mkdir -p $(img_dir)input-base
	cp $(m5_bin) $(kheader_tar) $(guest_init) $(bz_image) $(kernel_config) \
	    $(img_dir)input-base/
	truncate -s 64m $(img_dir)varstore.img
	truncate -s 64m $(img_dir)efi.img
	dd if=/usr/share/qemu-efi-aarch64/QEMU_EFI.fd of=$(img_dir)efi.img conv=notrunc
	cd $(img_dir) && ./packer-wrap.sh base base base.pkr.hcl \
	    $(COMPRESSED_IMAGES)
	rm -rf $(img_dir)input-base
	touch $@

TVM_DIR := $(img_dir)tvm

$(VTA_DEP_IMAGE): $(packer) $(QEMU) $(BASE_IMAGE) \
    $(addprefix $(d), extended-image.pkr.hcl scripts/install-vta_dep.sh \
      scripts/cleanup.sh)
	rm -rf $(dir $@)
	cd $(img_dir) && ./packer-wrap.sh base vta_dep extended-image.pkr.hcl \
	    $(COMPRESSED_IMAGES)
	touch $@

$(VTA_IMAGE): $(packer) $(QEMU) $(VTA_DEP_IMAGE) \
    $(addprefix $(d), extended-image.pkr.hcl scripts/install-vta.sh \
      scripts/cleanup.sh)
	rm -rf $(dir $@)
	cd $(img_dir) && ./packer-wrap.sh vta_dep vta extended-image.pkr.hcl \
	    $(COMPRESSED_IMAGES)
	touch $@

$(GEMSTONE_IMAGE): $(packer) $(QEMU) $(BASE_IMAGE) \
    $(addprefix $(d), extended-image.pkr.hcl scripts/install-gemstone.sh \
      scripts/cleanup.sh)
	rm -rf $(dir $@)
	rm -rf $(img_dir)input-gemstone
	mkdir -p $(img_dir)input-gemstone
	ln -s /home/jonask/Repos/cpu_micro_benchmarks $(img_dir)input-gemstone/cpu_micro_benchmarks
	cd $(img_dir) && ./packer-wrap.sh base gemstone extended-image.pkr.hcl \
	    $(COMPRESSED_IMAGES)
	touch $@


$(packer):
	wget -O $(img_dir)packer_$(PACKER_VERSION)_linux_amd64.zip \
	    https://releases.hashicorp.com/packer/$(PACKER_VERSION)/packer_$(PACKER_VERSION)_linux_amd64.zip
	cd $(img_dir) && unzip packer_$(PACKER_VERSION)_linux_amd64.zip
	rm -f $(img_dir)packer_$(PACKER_VERSION)_linux_amd64.zip


################################################
# Kernel

$(kernel_dir)/vmlinux: $(kernel_dir)/.config
	$(MAKE) $(kernel_options) -C $(kernel_dir)
	touch $@

$(vmlinux): $(kernel_dir)/vmlinux
	cp $< $@
	touch $@

# this dependency is a bit stupid, but not sure how to better do this
$(bz_image): $(kernel_dir)/vmlinux
	cp $(kernel_dir)/arch/arm64/boot/Image.gz $@
	touch $@

$(kheader_tar): $(kernel_dir)/vmlinux
	rm -rf $(kheader_dir)
	mkdir -p $(kheader_dir)
	$(MAKE) $(kernel_options) -C $(kernel_dir) headers_install INSTALL_HDR_PATH=$(abspath $(kheader_dir)/usr)
	$(MAKE) $(kernel_options) -C $(kernel_dir) modules_install INSTALL_MOD_PATH=$(abspath $(kheader_dir))
	rm -f $(kheader_dir)/lib/modules/$(KERNEL_VERSION)/build
	ln -s /usr/src/linux-headers-$(KERNEL_VERSION) \
	    $(kheader_dir)/lib/modules/$(KERNEL_VERSION)/build
	rm -f $(kheader_dir)/lib/modules/$(KERNEL_VERSION)/source
	mkdir -p $(kheader_dir)/usr/src/linux-headers-$(KERNEL_VERSION)
	cp -r $(kernel_dir)/.config $(kernel_dir)/Makefile \
	    $(kernel_dir)/Module.symvers $(kernel_dir)/scripts \
	    $(kernel_dir)/include \
	    $(kheader_dir)/usr/src/linux-headers-$(KERNEL_VERSION)/
	mkdir -p $(kheader_dir)/usr/src/linux-headers-$(KERNEL_VERSION)/tools/objtool/
	mkdir -p $(kheader_dir)/usr/src/linux-headers-$(KERNEL_VERSION)/arch/arm64/
	cp -r $(kernel_dir)/arch/arm64/Makefile \
	    $(kernel_dir)/arch/arm64/include \
	    $(kheader_dir)/usr/src/linux-headers-$(KERNEL_VERSION)/arch/arm64
	cd $(kheader_dir) && tar cjf $(abspath $@) .

$(kernel_dir)/.config: $(kernel_pardir)/config-$(KERNEL_VERSION)
	rm -rf $(kernel_dir)
	wget -O - https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-$(KERNEL_VERSION).tar.xz | \
	    tar xJf - -C $(kernel_pardir)
	cd $(kernel_dir) && patch -p1 < ../linux-$(KERNEL_VERSION)-timers-gem5.patch
	cp $< $@


CLEAN := 
DISTCLEAN := $(kernel_dir) $(packer) $(bz_image) $(vmlinux) $(kheader_dir) \
    $(foreach i,$(IMAGES),$(dir $(i)) $(subst output-,input-,$(dir $(i)))) \
    $(d)packer_cache $(d)kheaders.tar.bz2

include mk/subdir_post.mk
