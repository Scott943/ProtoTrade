#!/bin/bash
for p in `pgrep python3`; do kill -9 $p; done;