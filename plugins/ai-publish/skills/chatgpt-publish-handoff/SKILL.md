---
name: chatgpt-publish-handoff
description: omp에서 만든 결과물을 ChatGPT Sites(호스팅 웹앱) 또는 ChatGPT Pages(Space 문서)로 발행하려 할 때 사용. 프로그램 발행 API가 없으므로 로컬 준비 + ChatGPT 앱 핸드오프 절차를 안내한다.
---

# ChatGPT Sites / Pages 발행 (omp)

2026-10 기준 둘 다 **공개 API·CLI 없음**. omp가 직접 배포할 수 없다. omp의 몫은 "발행 가능한 상태로 만들고 넘기기"다.
근거: https://learn.chatgpt.com/docs/sites ("Sites doesn't have a standalone Codex CLI management view"), https://learn.chatgpt.com/docs/space/pages

## Sites (웹사이트·웹앱·게임 호스팅)

1. omp에서 로컬 프로젝트를 만들고 빌드·테스트한다. Git 커밋까지 해 둔다(Sites 버전이 커밋에 묶임).
2. 영속 데이터가 필요하면 D1(관계형)·R2(파일) 바인딩 이름을 정해 둔다. 링크 정보는 Sites가 `.openai/hosting.json`에 쓴다:
   ```json
   { "project_id": "<Sites가 채움>", "d1": "DB", "r2": null }
   ```
   비밀값은 이 파일·프롬프트에 넣지 않는다. Site 설정의 환경변수로만.
3. **ChatGPT 데스크톱 앱(Codex)** 에서 그 폴더를 열고:
   `Deploy this project with Sites. Check whether it is compatible, make any required changes, and give me the deployment URL.`
4. 2단계 발행: *Save a version*(후보) → *Deploy*(프로덕션 URL). 새 Site는 소유자·워크스페이스 관리자만 접근 가능, 공유 범위는 Share에서 조정.
5. 지원: HTTP/HTTPS/WebSocket. 미지원: raw TCP, PHI·카드데이터 처리.

## Pages (Space 문서)

1. omp에서 Markdown으로 작성한다.
2. ChatGPT Space → **New page** 에 붙여넣거나, 대화에서 "이 내용을 page로 만들어줘". 표·코드·이미지 블록은 붙여넣기로 변환된다.
3. 공유는 Space/부모 페이지 권한을 상속한다. Share에서 확인.

## 발행 전 필수 점검

- 사외 서비스로의 반출이다. 개인정보·비밀값·내부 전용 데이터 제거 후 넘긴다.
- 브라우저 자동화로 chatgpt.com UI를 조작해 발행하지 않는다(로그인 세션·약관 리스크). 사용자가 앱에서 직접 실행한다.
