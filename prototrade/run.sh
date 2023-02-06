#!/bin/bash
pkill python3; pip uninstall prototrade; python3 -m setup install --user 

if [ "$#" -eq 1 ]
then
  python3 $1
fi
