# Repository Guidelines

## Project Overview

`ai-publish`는 omp의 로컬 결과물을 Claude artifacts와 ChatGPT Pages/Sites로 발행·관리하는 Claude Code 플러그인 마켓플레이스다. 저장소에는 JSON 매니페스트 2개, 스킬 지시문(`SKILL.md`) 2개, Claude artifact용 정적 자산 2개(`page.html`, `marked.config.mjs`)가 있으며, 애플리케이션 서버·패키지·자동 테스트는 없다. 그림은 외부 스킬 diagram-design이 그리며, 저장소에 넣지 않고 마켓플레이스 의존성으로 설치한다. 변경 대상은 거의 항상 스킬의 외부 CLI 절차, 발행 페이지 자산, 플러그인 메타데이터다.

## Architecture & Data Flow

- **로딩:** `.claude-plugin/marketplace.json`의 `plugins[0].source`(`./plugins/ai-publish`) → `plugins/ai-publish/.claude-plugin/plugin.json` → 기본 `skills/` 스캔으로 `skills/<name>/SKILL.md`를 읽는다. `plugin.json`에 `skills` 키가 없으므로 새 스킬은 디렉터리 추가만으로 포함된다.
- **의존성:** 같은 마켓플레이스의 두 번째 항목이 upstream `cathrynlavery/diagram-design`을 GitHub 소스(`sha` 고정)로 등록하고, `ai-publish`의 `plugin.json`이 `"dependencies": ["diagram-design"]`을 선언한다. Claude Code는 `ai-publish@ai-publish` 설치 때 `diagram-design@ai-publish`를 함께 설치하고, 의존성이 없거나 꺼져 있으면 `ai-publish`를 불러오지 않는다. 다른 마켓플레이스를 가리키는 의존성(`marketplace` 필드)은 그 마켓플레이스를 사용자가 먼저 추가해야 설치되므로 쓰지 않는다. 사용자가 upstream 마켓플레이스판(`diagram-design@diagram-design`)도 설치했다면 같은 스킬이 두 벌 생긴다.
- **트리거:** frontmatter `description`이 스킬 선택 조건이고, 본문은 에이전트가 셸에서 실행할 외부 CLI 절차다. 저장소 코드는 `marked` CLI가 읽는 `marked.config.mjs`와 발행 페이지의 인라인 스크립트뿐이다.
- **ChatGPT (`chatgpt-publish`):** 로컬 파일/사이트 프로젝트 → `codex exec`(Codex 모델 턴 1회) → `chatgpt_space.*` 또는 `sites.*` 앱 도구 → 마지막 `RESULT` 줄(`page_id`·`url` 또는 `url`·`version`). Pages는 `-s read-only`, Sites는 `-C <project>`와 `-s workspace-write`로 실행하며 Sites가 대상 프로젝트에 `.openai/hosting.json`을 쓴다.
- **Claude (`claude-artifact-publish`):** 로컬 파일 → `npx -y claude-artifacts@0.1.14` → 로그인 토큰으로 비공식 `api.anthropic.com/api/frame` 직접 호출(LLM 턴 없음) → URL 또는 `--output json`. CLI는 `<!doctype html>`/`<html>`이 있는 파일을 그대로 올리고, 그 밖의 `.md`·HTML 조각은 자체 CSS로 감싼다.
- **문서 경로:** Markdown → `marked@18.1.1` + `marked-cjk-friendly@0.1.2`(`-c assets/marked.config.mjs`) → `assets/page.html` 뒤에 본문을 붙인 단일 HTML → CLI. 설정이 한국어 강조를 고치고, `![캡션](x.svg)`만 있는 문단을 인라인 SVG `<figure class="diagram">`로 바꾸고, `mermaid` 블록이 있으면 변환을 실패시킨다. 페이지 스크립트는 표를 스크롤 영역으로 감싸고(넘치는 쪽 가장자리는 흐리게), 소제목 3개 이상이면 목차를 만든다. 목차는 75rem 이상에서 왼쪽 고정 목록, 그보다 좁으면 오른쪽 아래 버튼과 `<dialog>` 바텀시트이며, 두 목록 모두 읽는 위치에 `aria-current="location"`을 단다.
- **그림:** diagram-design HTML → 그 스킬의 `scripts/export_svg.py` → `.svg` → 위 문서 경로로 인라인.
- 호출은 모두 단발 동기 CLI 실행이다. 재시도·큐·DI·상태 저장 코드는 없으며, 후속 갱신은 서비스가 돌려준 ID/URL(Claude는 선택적 `--base-version`)을 다시 넘긴다. 브라우저는 사람이 하는 공유 설정·파괴적 작업에만 쓴다.

## Key Directories

| 경로 | 용도 |
|---|---|
| `.claude-plugin/` | 마켓플레이스 매니페스트(플러그인 등록·`source` 경로) |
| `plugins/ai-publish/.claude-plugin/` | 플러그인 매니페스트 전용. 스킬 등 나머지 파일은 플러그인 루트에 둔다 |
| `plugins/ai-publish/skills/<name>/` | 스킬 하나당 `SKILL.md` 하나 |
| `plugins/ai-publish/skills/claude-artifact-publish/assets/` | 발행 페이지 셸(`page.html`)과 Markdown 변환 설정(`marked.config.mjs`) |

## Development Commands

빌드·린트·테스트·실행 스크립트와 개발 서버는 없다. 변경 후 저장소 루트에서 다음을 실행한다.

```sh
# 공식 검증(Claude Code 2.1.292 확인). 현재 `author` 누락 경고 1건이 기준선이며 --strict는 이 경고로 실패한다.
claude plugin validate .
claude plugin validate plugins/ai-publish
```

공식 검증이 잡지 못하거나 경고로만 넘기는 항목(매니페스트 `name`·`version` 불일치, 없는 `source`, frontmatter `name`≠디렉터리명, `description` 누락)은 아래 검사로 막는다.

```sh
node -e '
const fs = require("node:fs");
for (const e of JSON.parse(fs.readFileSync(".claude-plugin/marketplace.json", "utf8")).plugins) {
  if (typeof e.source !== "string") continue; // 외부 GitHub 소스(diagram-design)는 저장소 밖
  const p = JSON.parse(fs.readFileSync(`${e.source}/.claude-plugin/plugin.json`, "utf8"));
  if (p.name !== e.name || p.version !== e.version) throw new Error(`name/version mismatch: ${e.source}`);
  for (const d of fs.readdirSync(`${e.source}/skills`, { withFileTypes: true }).filter((d) => d.isDirectory())) {
    const fm = fs.readFileSync(`${e.source}/skills/${d.name}/SKILL.md`, "utf8").match(/^---\n([\s\S]*?)\n---\n/)?.[1] ?? "";
    if (!fm.split("\n").includes(`name: ${d.name}`) || !/^description: \S/m.test(fm)) throw new Error(`bad frontmatter: ${d.name}`);
  }
}
console.log("manifest/skill invariants OK");
'
```

ChatGPT 발행 전제 확인(읽기 전용). 전체 `codex plugin list` 출력은 수천 줄이므로 마켓플레이스로 거른다.

```sh
codex --version                       # 승인 동작 실측 기준: codex-cli 0.161.0
codex features list | grep '^apps '   # 세 번째 열이 true
codex plugin list --marketplace openai-curated-remote | grep '^sites@openai-curated-remote '   # Sites용: installed, enabled
```

발행 페이지 자산을 바꿨을 때는 외부 게시 없이 확인한다. 아래는 CLI의 API 주소를 로컬 캡처 서버로 돌려, 실제로 올라갈 바이트를 `/tmp/uploaded.html`에 받는다(토큰도 더미라 Anthropic 호출이 없다).

```sh
node -e 'require("node:http").createServer((q,s)=>{let b="";q.on("data",c=>b+=c).on("end",()=>{require("node:fs").writeFileSync("/tmp/uploaded.html",JSON.parse(b).content);s.setHeader("content-type","application/json");s.end(JSON.stringify({slug:"00000000-0000-0000-0000-000000000000",version:1}),()=>process.exit())})}).listen(8787)' &
CLAUDE_CODE_ARTIFACTS_API_BASE_URL=http://127.0.0.1:8787 CLAUDE_CODE_OAUTH_TOKEN=offline npx -y claude-artifacts@0.1.14 create /tmp/report.html --output json
cmp /tmp/report.html /tmp/uploaded.html   # doctype 있는 HTML은 그대로 올라가야 한다
```

diagram-design 의존성을 확인하거나 고정 커밋을 올릴 때는 임시 설정 디렉터리로 설치해 본다(사용자 설정을 건드리지 않는다). `ai-publish`와 함께 `diagram-design@ai-publish`가 설치되고 그 안에 `skills/diagram-design/scripts/export_svg.py`가 있어야 한다. upstream에는 릴리스 태그가 없어 버전 범위 대신 `sha`로 고정한다. 올릴 때는 `git ls-remote https://github.com/cathrynlavery/diagram-design HEAD`의 커밋으로 바꾸고 `ai-publish` 버전을 함께 올린다.

```sh
( # 하위 셸이라 CLAUDE_CONFIG_DIR가 현재 셸에 남지 않는다
  export CLAUDE_CONFIG_DIR=$(mktemp -d)
  claude plugin marketplace add "$PWD" && claude plugin install ai-publish@ai-publish   # "(+ 1 dependency: diagram-design)"
  claude plugin list --json
)
```

발행 명령의 단일 출처는 각 `SKILL.md`다. 실행하면 실제로 외부에 게시되므로 사용자 요청과 발행 전 점검 없이 실행하지 않는다.

- Claude: `plugins/ai-publish/skills/claude-artifact-publish/SKILL.md`의 `## 명령 (버전 고정)` — `npx -y claude-artifacts@0.1.14 create|update|list|read|delete`
- ChatGPT: `plugins/ai-publish/skills/chatgpt-publish/SKILL.md`의 `## 호출 패턴` — `codex exec … 2>&1 | grep '^RESULT' | tail -1`

## Code Conventions & Common Patterns

- Markdown 본문은 한국어로 쓰고 명령·식별자·Codex 프롬프트 예시는 원문을 유지한다. JSON은 2칸 들여쓰기. 린터·포매터 설정은 없다.
- **스킬:** `kebab-case` 디렉터리명 = frontmatter `name`. `description`에 적용 대상과 요청 트리거(예: "artifact로 올려줘")를 쓴다. 본문 순서는 전제조건 → 호출/명령 → 제약·승인·공유 → `## 발행 전 필수 점검`.
- **매니페스트:** `name`·`version`을 두 파일에서 같게 유지한다. 설치 시 `plugin.json`의 `version`이 우선하고 마켓플레이스 항목의 버전은 조용히 무시된다. 이름이 다르면 활성화 키(항목 이름)와 스킬 네임스페이스(`plugin.json` 이름)가 갈린다. 기능을 바꾸면 두 `description`도 함께 고친다.
- **결과 계약:** ChatGPT 프롬프트는 마지막 한 줄 `RESULT key=value`로 끝내고 `grep '^RESULT' | tail -1`로 읽는다. Claude 결과 파싱은 `--output json`. 버전 고정(`claude-artifacts@0.1.14`, `marked@18.1.1`, `marked-cjk-friendly@0.1.2`)을 유지하고, 올릴 때는 해당 명령 블록 전체를 새 버전 도움말·출력으로 재확인한다.
- **발행 페이지:** 색·글꼴 토큰은 `page.html`의 `:root` 한곳에 있고 외부 폰트·CDN을 쓰지 않는다. 본문을 뒤에 이어 붙이므로 `page.html`은 `<body>`로 끝나며 `</body></html>`을 넣지 않는다. Markdown 변환 규칙은 `marked.config.mjs`에만 둔다.
- **그림:** diagram-design 프로필 `ai-publish`(`page.html`과 같은 색·글꼴, 2026-10-13 사용자 결정)를 쓴다. 프로필은 사용자 홈(`~/.diagram-design/profiles/ai-publish.md`)에 있으므로 `page.html` 토큰을 바꾸면 diagram-design의 `update ai-publish`로 프로필도 맞춘다. SVG는 viewBox 너비(`--w`) 아래로 줄이지 않고, 넓은 화면에서는 본문 밖으로 넓히고(왼쪽 목차가 있으면 오른쪽으로만) 좁은 화면에서는 그림만 스크롤한다. 다크 모드 교체는 `<slug>-dark.svg` 짝이 있을 때만 한다.
- **인포그래픽:** 긴 문서는 diagram-design의 여러 타입을 내용에 맞게 쓴다. 내용→타입 표, 배치·캡션·사실 규칙은 `claude-artifact-publish/SKILL.md`의 "긴 문서는 인포그래픽으로" 한곳에 두고 Pages 쪽은 그것을 가리킨다. 대표 수치는 `page.html`의 `.stats` 카드(첫 카드만 넓고 강조색)로 쓴다.
- **실측 기록:** `## 승인 동작 (2026-10-13 실측, codex-cli 0.161.0)`처럼 날짜·CLI 버전을 붙인다. 기존 측정은 소급 수정하지 말고 새 측정을 추가한다.
- **오류 처리:** artifact CLI가 깨지면 스킬의 `claude -p` 대안을 쓴다. `codex exec`에서 `trash_page`가 승인 정책으로 거부되는 것은 실측된 정상 동작이다. destructive 도구(trash/delete/공유 변경)는 사람이 브라우저 UI나 대화형 `codex`에서 처리한다. `--dangerously-bypass-approvals-and-sandbox`는 사용자가 명시적으로 요청한 경우에만 쓰고, 프롬프트를 "셸 금지 + 도구 1개"로 좁힌다.
- **안전:** 발행은 사외 반출이다. 개인정보·비밀값·내부 전용 데이터를 제거하고, 비공개 생성을 기본으로 하며, 공개/외부 공유는 명시적 요청이 있을 때만 한다. `-s read-only`는 원격 페이지 생성을 막지 않는다.

## Important Files

- `.claude-plugin/marketplace.json`: 마켓플레이스 이름·소유자, 플러그인 항목(`version`, `category`, `source`). 두 번째 항목은 upstream diagram-design(GitHub `sha` 고정)이다.
- `plugins/ai-publish/.claude-plugin/plugin.json`: 플러그인 `name`·`version`(설치 시 이 `version`이 우선)·설명·라이선스(MIT)·`dependencies`.
- `plugins/ai-publish/skills/chatgpt-publish/SKILL.md`: Pages/Sites 호출, 샌드박스 선택, `RESULT` 형식, 승인 동작 실측표, 비용(호출당 약 35k 토큰).
- `plugins/ai-publish/skills/claude-artifact-publish/SKILL.md`: CLI 명령, 문서 발행(Markdown 변환), 그림(diagram-design), 인증 경로, 페이지 제약, 실패 대안, 공유 방식.
- `plugins/ai-publish/skills/claude-artifact-publish/assets/page.html`: 발행 페이지 셸. 토큰·타이포그래피·다크 모드·표/그림 스크롤·목차 스크립트.
- `plugins/ai-publish/skills/claude-artifact-publish/assets/marked.config.mjs`: `marked -c` 설정. 한국어 강조, SVG 인라인, mermaid 차단, frontmatter 처리.

## Runtime/Tooling Preferences

- 패키지 매니저·lockfile·런타임 버전 고정이 없다. Node.js(`npx`, 정합성 검사), `claude`, `codex` CLI를 쓴다. Python은 그림을 넣을 때 diagram-design의 `export_svg.py`에만 필요하고 Bun은 쓰지 않는다.
- **diagram-design:** Claude Code는 플러그인 의존성으로 자동 설치한다. omp 마켓플레이스는 `dependencies`를 처리하지 않으므로(omp v18.10.3에서 `ai-publish`만 설치됨을 확인) `omp plugin install diagram-design@ai-publish`를 따로 실행하고, Pi는 `pi install https://github.com/cathrynlavery/diagram-design`로 설치한다.
- **Claude 발행:** `claude /login`(Pro/Max/Team/Enterprise)이 필수다. 토큰은 macOS Keychain `Claude Code-credentials` 또는 `CLAUDE_CODE_OAUTH_TOKEN`에서 읽는다. 토큰 값을 출력·커밋하지 않는다.
- **ChatGPT 발행:** `codex login`(ChatGPT 계정)과 `apps=true`가 필요하고, Sites는 `sites@openai-curated-remote` 활성화도 필요하다. 승인 동작은 `codex-cli 0.161.0` 기준이므로 다른 버전에서는 다시 실측한다.
- **artifact 콘텐츠:** 자체 완결 단일 HTML(인라인 CSS/JS)을 우선한다. 백엔드·다중 라우트는 불가하고 외부 CDN은 뷰어 CSP에 막힐 수 있다. Markdown은 `page.html`+`marked`로 변환해 올리고, CSV/JSON/YAML은 CLI가 코드 블록으로 렌더한다. 조직/공개 공유는 브라우저 **Share**로만 한다.

## Testing & QA

- 자동 테스트·CI·커버리지 목표는 없다. `npm test` 같은 명령을 가정하지 않는다.
- 저장소 변경 검증: `claude plugin validate` 2개가 기준선 외 경고 없이 통과하고 `node -e` 정합성 검사가 `manifest/skill invariants OK`를 출력해야 한다.
- CLI 예시를 바꾸면 해당 버전 도움말(`codex exec --help` 등)로 옵션을 확인한다. 도움말 확인은 인증·원격 도구·발행 성공의 증거가 아니다.
- `page.html`·`marked.config.mjs`를 바꾸면 한국어 강조(`**60%**가`)·넓은 표·코드·SVG 그림·수치 카드와 소제목 3개 이상이 든 샘플을 변환해 390px·1280px, 라이트·다크에서 연다. 문서 가로 넘침이 없고(`scrollWidth` = 뷰포트) 표·그림만 스크롤되는지, 본문에 `**`가 남지 않는지 본다. 1280px에서는 왼쪽 목차가 본문·그림과 겹치지 않고 읽는 위치가 표시되는지, 390px에서는 목차 버튼 → 바텀시트 → 항목 이동·Esc·배경 누름으로 닫히는지 본다. 올라갈 바이트는 위 캡처로 확인한다.
- 실제 발행 QA는 사용자가 요청한 작업에서 비민감 입력으로만 한다. 기대한 `RESULT`/URL/JSON을 확인하고 `read_page`·`get_deployment_status`·`read <id|url> --content`로 내용을 대조한다. 새 결과가 비공개인지 확인한다(Page: PRIVATE 생성, artifact: 본인만, Site: 소유자와 워크스페이스 관리자).
- 생성·삭제·공유 변경을 smoke test로 실행하지 않는다.
