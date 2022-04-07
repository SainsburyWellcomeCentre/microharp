# Compile source files to bytecode.

MPY_DIR ?= ../micropython
MPY_CROSS = $(MPY_DIR)/mpy-cross/mpy-cross

REL = ./rel
SRCS = $(wildcard *.py)
OBJS = $(patsubst %.py,$(REL)/%.mpy,$(SRCS))

.PHONY: all clean

all: $(OBJS)

clean:
	rm -rf $(REL)

$(REL)/%.mpy: %.py | $(REL)
	$(MPY_CROSS) -o $@ $<

$(REL):
	mkdir $@