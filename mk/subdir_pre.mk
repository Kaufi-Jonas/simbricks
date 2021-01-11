ifdef base_reached
else
ifeq "$(abspath $(cur_dir)mk)" "$(realpath $(cur_dir)mk)"
# we're in the base directory (mk/ is a symlink everywhere else)
else
cur_dir := ../$(d)
include $(cur_dir)/Makefile
cur_dir := $(d)
endif
endif

#$(warning entering $(cur_dir))

sp := $(sp).x
dirstack_$(sp) := $(d)
d := $(cur_dir)

ALL :=
CLEAN :=
DISTCLEAN :=
DEPS :=
OBJS :=
