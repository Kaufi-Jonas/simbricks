#$(warning leaving $(d))

DEPS := $(DEPS) $(OBJS:.o=.d)
CLEAN := $(CLEAN) $(DEPS)
ifeq "$(word 1,$(subst /, ,$(d)))" ".."
# directory is above run directory
else
# below or in run directory
CLEAN_LIST := $(CLEAN_LIST) $(CLEAN)
DISTCLEAN_LIST := $(DISTCLEAN_LIST) $(DISTCLEAN)
ALL_LIST := $(ALL_LIST) $(ALL)
endif

CLEAN_ALL := $(CLEAN_ALL) $(CLEAN)
DISTCLEAN_ALL := $(DISTCLEAN_ALL) $(DISTCLEAN)
DEPS_ALL := $(DEPS_ALL) $(DEPS)
ALL_ALL := $(ALL_ALL) $(ALL)

ifeq "$(d)" ""
include mk/global.mk
-include $(DEPS_ALL)
else
endif

d := $(dirstack_$(sp))
sp := $(basename $(sp))

ALL :=
CLEAN :=
DISTCLEAN :=
DEPS :=
OBJS :=
