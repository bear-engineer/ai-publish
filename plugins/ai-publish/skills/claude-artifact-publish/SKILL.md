---
name: claude-artifact-publish
description: 로컬 HTML·Markdown·CSV·JSON·YAML 파일을 claude.ai Claude Code artifact(claude.ai/code/artifact/<id>)로 발행·갱신·조회·삭제할 때 사용. "artifact로 올려줘", "claude 링크로 공유" 요청. Markdown 문서는 읽기용 페이지로 변환해 올리고, 그림은 diagram-design으로 그려 넣는다.
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

## 문서 발행 (Markdown → 읽기용 페이지)

`.md`를 CLI에 바로 넘기지 않는다. CLI 기본 렌더는 본문 14px에 제목 크기 차이가 작고, 한글 줄바꿈과 다크 모드가 없으며, 모바일에서는 넓은 표가 글자 단위로 쪼개진다. `**60%**가`, `**"용어"**는`처럼 문장부호로 끝난 강조 뒤에 한글이 붙으면 `**`가 그대로 보인다.

CLI는 `<!doctype html>`로 시작하는 파일을 바꾸지 않고 올린다. 그래서 본문을 HTML로 변환해 이 스킬의 `assets/page.html` 뒤에 붙여 올린다. `page.html`은 읽기용 글꼴 크기·줄 간격·폭, 다크 모드, 표만 가로로 스크롤, 소제목 3개 이상이면 목차를 맡는다. 경로는 이 스킬 디렉터리 기준이다.

```sh
S=<이 스킬 디렉터리>
cd <Markdown이 있는 폴더>   # ![…](그림.svg) 경로의 기준
npx -y -p marked@18.1.1 -p marked-cjk-friendly@0.1.2 marked -c "$S/assets/marked.config.mjs" -i report.md -o /tmp/report.body.html
cat "$S/assets/page.html" /tmp/report.body.html > /tmp/report.html
$A create /tmp/report.html --title "<문서의 H1>" --label "<YYYY-MM-DD>"
```

- 문서는 `# 제목` 하나로 시작한다. `--title`을 빼면 파일 이름이 갤러리 제목이 된다.
- 갱신은 같은 변환 뒤 `$A update <id|url> /tmp/report.html --label …`.
- HTML을 직접 쓸 때도 `page.html` 뒤에 본문을 이어 쓴다. 대시보드처럼 레이아웃이 다른 페이지만 예외다.
- 코드 블록은 문법 강조 없이 단색으로 나온다.

## 그림 (diagram-design)

구조·흐름·관계를 보여 줄 그림은 diagram-design 스킬로 그린다. 스킨은 diagram-design 기본값을 쓴다(2026-10-13 사용자 결정). 아티팩트용 그림에서는 첫 다이어그램 스킨 질문을 다시 하지 않는다.

1. diagram-design으로 `<slug>.html`을 만든다. 크기는 기본 `doc-inline`(viewBox 960)이다.
2. SVG를 뽑는다: `python3 <diagram-design 디렉터리>/scripts/export_svg.py <slug>.html <slug>.svg`
3. Markdown에 그림만 있는 한 줄을 넣는다: `![그림 설명](<slug>.svg)`. 변환할 때 SVG가 인라인된 `<figure>`가 되고, 설명은 캡션이 된다.

- 넓은 화면에서는 그림이 본문 폭 밖으로 viewBox 너비까지 넓어지고, 좁은 화면에서는 그림만 가로로 스크롤한다. 글자가 작아지지 않게 SVG는 viewBox 너비 아래로 줄이지 않는다.
- Mermaid 코드 블록은 뷰어에서 그려지지 않는다. 남아 있으면 변환이 멈춘다. diagram-design의 Mermaid 가져오기로 다시 그려 위 2·3단계로 바꾼다.
- 그림 글꼴(Geist 등)은 Google Fonts에서 받는다. 뷰어 CSP가 막으면 시스템 글꼴로 바뀐다.
- 기본 스킨은 종이색이 본문과 달라 테두리 있는 카드로 보이고, 다크 모드에서도 밝은 카드로 남는다.

## 페이지 제약

- 한 파일, 자체 완결 HTML(인라인 CSS/JS). 백엔드·다중 라우트 불가.
- CSV·JSON·YAML·소스 파일은 CLI가 코드 블록으로 보여 준다. 표로 읽어야 하는 데이터는 Markdown 표로 옮겨 문서 발행을 쓴다.
- 외부 CDN 스크립트는 claude.ai 뷰어 CSP에 막힐 수 있다 → 인라인 우선.

## 공유

- 새 artifact는 **본인만** 볼 수 있다. 조직/공개 공유는 브라우저에서 페이지 헤더 **Share**로만 한다(CLI 미지원).
- 갤러리: https://claude.ai/code/artifacts

## 발행 전 필수 점검

- 발행은 사외 서비스로의 반출이다. 개인정보(연락처·이메일·계좌·주민번호·건강정보 등), 비밀값, 내부 전용 데이터가 페이지에 없는지 확인한다.
- 공개 링크 공유는 사용자가 명시적으로 요청한 경우에만 안내한다.
- 변환한 `/tmp/report.html`을 브라우저로 열어 표·그림·목차가 깨지지 않았는지 본 뒤 올린다.
