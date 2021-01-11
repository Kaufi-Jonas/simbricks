all: $(ALL_LIST)

clean:
	rm -rf $(CLEAN_LIST)

cleanall:
	rm -rf $(CLEAN_ALL)

distclean:
	rm -rf $(CLEAN_LIST) $(DISTCLEAN_LIST)


.PHONY: all clean cleanall
.DEFAULT_GOAL := all
