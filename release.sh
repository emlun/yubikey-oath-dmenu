#!/bin/bash

set -x # Echo commands
set -e # Exit on error

version="${1:-$(./compute-version.sh)}"

PROJECT_NAME=yubikey-oath-dmenu
TAR_FILE="${PROJECT_NAME}"-"${version}".tar.gz
SIG_FILE="${TAR_FILE}".sig
PREFIX="${PROJECT_NAME}"-"${version}"/
TAG=v"${version}"

git archive --prefix "${PREFIX}" -o "${TAR_FILE}" "${TAG}"
gpg --detach-sign "${SIG_FILE}"
gpg --verify "${SIG_FILE}"

echo "Successfully released version ${version}"
