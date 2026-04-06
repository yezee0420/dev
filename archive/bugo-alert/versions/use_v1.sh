#!/bin/bash
# 아까 버전(v1) 적용
cd "$(dirname "$0")/.."
cp versions/parser_v1_before.py app/crawler/parser.py
cp versions/config_v1_before.py app/config.py
echo "v1 (아까 버전) 적용됨"
