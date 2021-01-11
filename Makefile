include mk/subdir_pre.mk
include mk/recipes.mk

base_dir := $(d)
base_reached := y

CFLAGS += -Wall -Wextra -Wno-unused-parameter -O3 -fPIC
CXXFLAGS += -Wall -Wextra -Wno-unused-parameter -O3 -fPIC

VERILATOR = verilator
VFLAGS = +1364-2005ext+v \
    -Wno-WIDTH -Wno-PINMISSING -Wno-LITENDIAN -Wno-IMPLICIT -Wno-SELRANGE \
    -Wno-CASEINCOMPLETE -Wno-UNSIGNED

lib_proto_inc := $(d)proto/
QEMU_IMG := $(d)qemu/build/qemu-img
QEMU := $(d)qemu/build/qemu-system-x86_64

$(eval $(call subdir,netsim_common))
$(eval $(call subdir,nicsim_common))
$(eval $(call subdir,libnicbm))

$(eval $(call subdir,i40e_bm))
$(eval $(call subdir,corundum))
$(eval $(call subdir,corundum_bm))

$(eval $(call subdir,net_wire))
$(eval $(call subdir,net_tap))
$(eval $(call subdir,net_switch))

$(eval $(call subdir,images))

###############################################################################

help:
	@echo "Targets:"
	@echo "  all: builds all the tools directly in this repo"
	@echo "  clean: cleans all the tool folders in this repo"
	@echo "  build-images: prepare prereqs for VMs (images directory)"
	@echo "  external: clone and build our tools in external repos "
	@echo "            (qemu, gem5, ns-3)"

external: $(d)gem5/ready $(d)qemu/ready $(d)ns-3/ready

$(d)gem5:
	git clone git@github.com:FreakyPenguin/gem5-cosim.git $@

$(d)gem5/ready: $(d)gem5
	+cd $< && scons build/X86/gem5.opt -j`nproc`
	touch $@


$(d)qemu:
	git clone git@github.com:FreakyPenguin/qemu-cosim.git $@

$(d)qemu/ready: $(d)qemu
	+cd $< && ./configure \
	    --target-list=x86_64-softmmu \
	    --disable-werror \
	    --extra-cflags="-I$(abspath $(lib_proto_inc))" \
	    --enable-cosim-pci && \
	  $(MAKE)
	touch $@

$(QEMUG_IMG): $(d)qemu/ready
	touch $@

$(QEMU): $(d)qemu/ready
	touch $@


$(d)ns-3:
	git clone git@github.com:FreakyPenguin/ns-3-cosim.git $@

$(d)ns-3/ready: $(d)ns-3 $(lib_netsim)
	+cd $< && COSIM_PATH=$(abspath $(base_dir)) ./cosim-build.sh configure
	touch $@

###############################################################################

DISTCLEAN := $(base_dir)gem5 $(base_dir)qemu $(base_dir)ns-3
include mk/subdir_post.mk
