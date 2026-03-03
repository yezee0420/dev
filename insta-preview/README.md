# InstaPreview - 인스타그램 피드 미리보기 앱

실제 인스타그램 계정으로 로그인하여 현재 피드를 가져오고,
새 사진을 올렸을 때 어떻게 보이는지 미리 확인할 수 있는 모바일 앱입니다.

## 기능

- **인스타그램 로그인**: 실제 계정으로 로그인 (2FA 지원)
- **피드 보기**: 내 게시물을 3열 그리드로 확인
- **미리보기**: 새 사진을 선택하면 기존 피드에 삽입되어 어떻게 보일지 확인
- **뷰 모드 전환**: 그리드 뷰 / 포스트 뷰 전환 가능
- **프로필**: 프로필 정보, 팔로워/팔로잉 수 확인

## 프로젝트 구조

```
insta-preview/
  backend/      Node.js + Express + TypeScript 서버
  mobile/       React Native (Expo) 모바일 앱
```

## 실행 방법

### 1. Backend 서버 실행

```bash
cd backend
npm install
npm run dev
```

서버가 `http://localhost:3000`에서 실행됩니다.

### 2. Mobile 앱 실행

```bash
cd mobile
npm install
npx expo start
```

- iOS 시뮬레이터: `i` 키
- Android 에뮬레이터: `a` 키
- Expo Go 앱: QR 코드 스캔

### 서버 URL 설정

실제 기기에서 테스트할 경우, 로그인 화면 하단의 **서버 설정**을 눌러
Backend 서버의 IP 주소를 입력하세요. (예: `http://192.168.0.10:3000`)

## 주의사항

- `instagram-private-api`는 **비공식** 라이브러리로 인스타그램 이용약관에 위배됩니다.
- 계정 **임시 정지** 또는 **영구 정지** 위험이 있습니다.
- **개인 용도**로만 사용하세요.
- 실제 사진 업로드 기능은 **포함되어 있지 않습니다** (미리보기 전용).

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Node.js, Express, TypeScript, instagram-private-api |
| Mobile | React Native, Expo SDK 55, expo-router |
| 상태관리 | Zustand |
| HTTP | Axios |
