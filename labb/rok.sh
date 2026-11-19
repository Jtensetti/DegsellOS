#!/usr/bin/env bash
# Röktest: körs inne i labb-avbildningen i CI.
set -euo pipefail
R -q -e 'suppressMessages({library(tidyverse); library(lme4); library(psych); library(renv)}); cat("R ok\n")'
python -c 'import pandas, scipy, statsmodels, pingouin, matplotlib; print("Python ok")'
pandoc --version | head -1
test -s /opt/degsellos/python-las.txt
test -s /opt/degsellos/r-session.txt
echo "OK: labbet"
