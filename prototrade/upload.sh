#!/bin/bash
python3 setup.py bdist_wheel && python3 -m twine upload --verbose dist/* -u__token__