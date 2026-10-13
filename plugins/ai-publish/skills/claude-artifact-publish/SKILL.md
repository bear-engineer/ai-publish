---
name: claude-artifact-publish
description: 로컬 HTML·Markdown·CSV·JSON·YAML 파일을 claude.ai Claude Code artifact(claude.ai/code/artifact/<id>)로 발행·갱신·조회·삭제할 때 사용. "artifact로 올려줘", "claude 링크로 공유" 요청.
---

# Claude artifact 발행 (omp)

omp에는 Claude Code의 내장 `Artifact` 도구가 없다. 대신 `claude-artifacts` CLI(비공식, MIT)를 쓴다.
이 CLI는 **로컬 Claude Code 로그인 토큰**(macOS Keychain `Claude Code-credentials`, 또는 `CLAUDE_CODE_OAUTH_TOKEN`)으로
`api.anthropic.com/api/frame` 을 직접 호출한다. LLM 턴을 쓰지 않는다.

- 전제: `claude /login` 완료(Pro/Max/Team/Enterprise).
- 비공식 엔드포인트라 Anthropic 쪽 변경 시 깨질 수 있다. 실패하면 대안: `claude -p "<file> 를 artifact로 발행해줘"`.

## 명령 (버전 고정)

```sh
A="npx -y claude-artifacts@0.1.14"
$A create page.html --title "제목" [--favicon "📊"] [--label v1]   # 새 artifact, URL 출력
$A update <id|url> page.html [--title ...] [--base-version <n>]    # 같은 URL에 새 버전
$A list --limit 20 --output json                                   # 내 artifact 목록
$A read <id|url> --content                                         # 배포된 HTML 받기
$A delete <id|url>
```

출력 기본은 사람용, 파싱할 땐 `--output json`.

## 페이지 제약

- 한 파일, 자체 완결 HTML(인라인 CSS/JS). 백엔드·다중 라우트 불가.
- Markdown·CSV·JSON·YAML·소스 파일도 받으며 CLI가 HTML로 렌더한다.
- 외부 CDN 스크립트는 claude.ai 뷰어 CSP에 막힐 수 있다 → 인라인 우선.

## 공유

- 새 artifact는 **본인만** 볼 수 있다. 조직/공개 공유는 브라우저에서 페이지 헤더 **Share**로만 한다(CLI 미지원).
- 갤러리: https://claude.ai/code/artifacts

## 발행 전 필수 점검

- 발행은 사외 서비스로의 반출이다. 개인정보(연락처·이메일·계좌·주민번호·건강정보 등), 비밀값, 내부 전용 데이터가 페이지에 없는지 확인한다.
- 공개 링크 공유는 사용자가 명시적으로 요청한 경우에만 안내한다.
