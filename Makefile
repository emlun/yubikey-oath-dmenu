PREFIX=/usr/local
BINDIR=$(DESTDIR)$(PREFIX)/bin

PROJECT_NAME=yubikey-oath-dmenu
SCRIPT_SRC_FILENAME=$(PROJECT_NAME).py

SCRIPT_INSTALL_FILENAME=$(PROJECT_NAME)
SCRIPT_INSTALL_FULL_PATH=$(BINDIR)/$(SCRIPT_INSTALL_FILENAME)

VERSION?=$(shell ./compute-version.sh)
VERSION_TAG=v$(VERSION)
SCRIPT_VERSIONED_FILENAME=$(PROJECT_NAME)-$(VERSION).py
TAR_FILENAME=$(PROJECT_NAME)-$(VERSION).tar.gz
ARCHIVE_PREFIX=$(PROJECT_NAME)-$(VERSION)/


.PHONY: default
default:
	@echo "Nothing to do!"
	@echo 'Use "make install" to install the program to $(BINDIR) .'
	@echo 'Use "make archive" to build a source release archive.'

.PHONY: install
install:
	install -D -m755 "$(SCRIPT_SRC_FILENAME)" "$(SCRIPT_INSTALL_FULL_PATH)"

.PHONY: uninstall
uninstall:
	rm "$(SCRIPT_INSTALL_FULL_PATH)"



.PHONY: archive
archive: $(TAR_FILENAME)

.PHONY: set-version
set-version: $(SCRIPT_SRC_FILENAME)
	sed -i "s/^VERSION\s*=\s*'.*'/VERSION = '$(VERSION)'/" "$(SCRIPT_SRC_FILENAME)"
	git diff --exit-code

.PHONY: release
release: set-version $(TAR_FILENAME) $(TAR_FILENAME).sig $(SCRIPT_VERSIONED_FILENAME).sig
	@echo "Successfully built version $(VERSION) release"

$(TAR_FILENAME):
	git archive --prefix "$(ARCHIVE_PREFIX)" -o "$@" "$(VERSION_TAG)"

$(SCRIPT_VERSIONED_FILENAME): set-version $(SCRIPT_SRC_FILENAME)
	install -m 644 "$(SCRIPT_SRC_FILENAME)" "$(SCRIPT_VERSIONED_FILENAME)"

%.sig: %
	gpg --detach-sign "$<"
	gpg --verify "$@"
