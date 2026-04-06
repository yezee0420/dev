# 파서 버전 비교

## v1 (아까 버전) — 현재 적용됨
- `parser_v1_before.py` — git HEAD 기준 (복수 부고 본문 우선 로직 없음)
- `config_v1_before.py` — 상대 경로 `./bugo.db`

## v2 (지금 버전)
- `parser_v2_current.py` — 추가된 패턴: ◇A씨 별세·B 관계상, ■이름 씨(소속) 별세, 장례예식장/문화원, 병원만 등
- `config_v2_current.py` — 절대 경로 DB

## 버전 전환

```bash
# v1 사용 (아까 버전) — 현재 상태
cp versions/parser_v1_before.py ../app/crawler/parser.py
cp versions/config_v1_before.py ../app/config.py

# v2 사용 (지금 버전)
cp versions/parser_v2_current.py ../app/crawler/parser.py
cp versions/config_v2_current.py ../app/config.py
```

전환 후 `python reparse_all.py` 실행 권장.
