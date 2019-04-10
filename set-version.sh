#!/bin/bash

version=$(./compute-version.sh)

sed -i "s/^VERSION\s*=\s*'.*'/VERSION = '$version'/" yubikey-oath-dmenu.py
