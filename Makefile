PREFIX=/usr/local
BINDIR=$(DESTDIR)$(PREFIX)/bin

SCRIPT_SRC_FILENAME=yubikey-oath-dmenu.py
SCRIPT_INSTALL_FILENAME=yubikey-oath-dmenu
SCRIPT_INSTALL_FULL_PATH=$(BINDIR)/$(SCRIPT_INSTALL_FILENAME)


default:
	@echo "Nothing to do!"
	@echo 'Use "make install" to install the program to $(BINDIR)'

install:
	install -D -m755 "$(SCRIPT_SRC_FILENAME)" "$(SCRIPT_INSTALL_FULL_PATH)"

uninstall:
	rm "$(SCRIPT_INSTALL_FULL_PATH)"
