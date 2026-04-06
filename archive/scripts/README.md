# scripts

개발 편의용 스크립트 모음.

## cursor-usage

Cursor API 사용량을 터미널에서 확인.

```bash
# PATH에 추가 (선택)
export PATH="$PATH:/Users/macbookair/Documents/GitHub/dev/scripts"

# 사용량 조회 (공개 API 한도 내)
cursor-usage

# Cursor 설정 페이지 열기 (전체 상세: API 100%, Auto+Composer 등)
cursor-usage --open

# API 원본 JSON
cursor-usage --json
```

**참고**: `cursor.com/api/usage`는 제한된 데이터만 반환. 토큰 기반 상세(Claude, agent_review 등)는 `cursor-usage --open`으로 설정 페이지를 열어 확인.
