#!/bin/bash

git describe --always --tags --match 'v*.*.*' --dirty=-DIRTY | sed 's/^v//'
