#!/bin/bash
pkill python3; pip uninstall prototrade; sudo pip uninstall prototrade; python3 -m setup install --user && python3 $1