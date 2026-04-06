#!/bin/bash
# 지금 버전(v2) 적용
cd "$(dirname "$0")/.."
cp versions/parser_v2_current.py app/crawler/parser.py
cp versions/config_v2_current.py app/config.py
echo "v2 (지금 버전) 적용됨"
