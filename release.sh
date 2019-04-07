#!/bin/bash

set -x # Echo commands
set -e # Exit on error

version="${1:-$(./compute-version.sh)}"

SCRIPT_SRC_FILENAME=yubikey-oath-dmenu.py
SCRIPT_VERSIONED_FILENAME="${SCRIPT_SRC_FILENAME}-${version}.py"
SCRIPT_SIG_FILENAME="${SCRIPT_VERSIONED_FILENAME}.sig"
PROJECT_NAME=yubikey-oath-dmenu
TAR_FILE="${PROJECT_NAME}"-"${version}".tar.gz
SIG_FILE="${TAR_FILE}".sig
PREFIX="${PROJECT_NAME}"-"${version}"/
TAG=v"${version}"

git archive --prefix "${PREFIX}" -o "${TAR_FILE}" "${TAG}"
gpg --detach-sign "${TAR_FILE}"
gpg --verify "${SIG_FILE}"


install -m 644 "${SCRIPT_SRC_FILENAME}" "${SCRIPT_VERSIONED_FILENAME}"
gpg --detach-sign "${SCRIPT_VERSIONED_FILENAME}"
gpg --verify "${SIG_FILE}"

echo "Successfully released version ${version}"
