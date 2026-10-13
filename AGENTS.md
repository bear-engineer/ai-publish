# Repository Guidelines

## Project Overview

`ai-publish`는 omp의 로컬 결과물을 Claude artifacts와 ChatGPT Pages/Sites로 발행·관리하는 Claude Code 플러그인 마켓플레이스다. 저장소에는 JSON 매니페스트 2개와 스킬 지시문(`SKILL.md`) 2개만 있으며, 애플리케이션 소스·서버·패키지·자동 테스트는 없다. 변경 대상은 거의 항상 스킬의 외부 CLI 절차나 플러그인 메타데이터다.

## Architecture & Data Flow

- **로딩:** `.claude-plugin/marketplace.json`의 `plugins[0].source`(`./plugins/ai-publish`) → `plugins/ai-publish/.claude-plugin/plugin.json` → 기본 `skills/` 스캔으로 `skills/<name>/SKILL.md`를 읽는다. `plugin.json`에 `skills` 키가 없으므로 새 스킬은 디렉터리 추가만으로 포함된다.
- **트리거:** frontmatter `description`이 스킬 선택 조건이고, 본문은 에이전트가 셸에서 실행할 외부 CLI 절차다. 저장소 안에서 실행되는 코드는 없다.
- **ChatGPT (`chatgpt-publish`):** 로컬 파일/사이트 프로젝트 → `codex exec`(Codex 모델 턴 1회) → `chatgpt_space.*` 또는 `sites.*` 앱 도구 → 마지막 `RESULT` 줄(`page_id`·`url` 또는 `url`·`version`). Pages는 `-s read-only`, Sites는 `-C <project>`와 `-s workspace-write`로 실행하며 Sites가 대상 프로젝트에 `.openai/hosting.json`을 쓴다.
- **Claude (`claude-artifact-publish`):** 로컬 파일 → `npx -y claude-artifacts@0.1.14` → 로그인 토큰으로 비공식 `api.anthropic.com/api/frame` 직접 호출(LLM 턴 없음) → URL 또는 `--output json`.
- 호출은 모두 단발 동기 CLI 실행이다. 재시도·큐·DI·상태 저장 코드는 없으며, 후속 갱신은 서비스가 돌려준 ID/URL(Claude는 선택적 `--base-version`)을 다시 넘긴다. 브라우저는 사람이 하는 공유 설정·파괴적 작업에만 쓴다.

## Key Directories

| 경로 | 용도 |
|---|---|
| `.claude-plugin/` | 마켓플레이스 매니페스트(플러그인 등록·`source` 경로) |
| `plugins/ai-publish/.claude-plugin/` | 플러그인 매니페스트 전용. 스킬 등 나머지 파일은 플러그인 루트에 둔다 |
| `plugins/ai-publish/skills/<name>/` | 스킬 하나당 `SKILL.md` 하나 |

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

발행 명령의 단일 출처는 각 `SKILL.md`다. 실행하면 실제로 외부에 게시되므로 사용자 요청과 발행 전 점검 없이 실행하지 않는다.

- Claude: `plugins/ai-publish/skills/claude-artifact-publish/SKILL.md`의 `## 명령 (버전 고정)` — `npx -y claude-artifacts@0.1.14 create|update|list|read|delete`
- ChatGPT: `plugins/ai-publish/skills/chatgpt-publish/SKILL.md`의 `## 호출 패턴` — `codex exec … 2>&1 | grep '^RESULT' | tail -1`

## Code Conventions & Common Patterns

- Markdown 본문은 한국어로 쓰고 명령·식별자·Codex 프롬프트 예시는 원문을 유지한다. JSON은 2칸 들여쓰기. 린터·포매터 설정은 없다.
- **스킬:** `kebab-case` 디렉터리명 = frontmatter `name`. `description`에 적용 대상과 요청 트리거(예: "artifact로 올려줘")를 쓴다. 본문 순서는 전제조건 → 호출/명령 → 제약·승인·공유 → `## 발행 전 필수 점검`.
- **매니페스트:** `name`·`version`을 두 파일에서 같게 유지한다. 설치 시 `plugin.json`의 `version`이 우선하고 마켓플레이스 항목의 버전은 조용히 무시된다. 이름이 다르면 활성화 키(항목 이름)와 스킬 네임스페이스(`plugin.json` 이름)가 갈린다. 기능을 바꾸면 두 `description`도 함께 고친다.
- **결과 계약:** ChatGPT 프롬프트는 마지막 한 줄 `RESULT key=value`로 끝내고 `grep '^RESULT' | tail -1`로 읽는다. Claude 결과 파싱은 `--output json`. `claude-artifacts@0.1.14` 버전 고정을 유지하고, 올릴 때는 명령 블록 전체를 새 버전 도움말로 재확인한다.
- **실측 기록:** `## 승인 동작 (2026-10-13 실측, codex-cli 0.161.0)`처럼 날짜·CLI 버전을 붙인다. 기존 측정은 소급 수정하지 말고 새 측정을 추가한다.
- **오류 처리:** artifact CLI가 깨지면 스킬의 `claude -p` 대안을 쓴다. `codex exec`에서 `trash_page`가 승인 정책으로 거부되는 것은 실측된 정상 동작이다. destructive 도구(trash/delete/공유 변경)는 사람이 브라우저 UI나 대화형 `codex`에서 처리한다. `--dangerously-bypass-approvals-and-sandbox`는 사용자가 명시적으로 요청한 경우에만 쓰고, 프롬프트를 "셸 금지 + 도구 1개"로 좁힌다.
- **안전:** 발행은 사외 반출이다. 개인정보·비밀값·내부 전용 데이터를 제거하고, 비공개 생성을 기본으로 하며, 공개/외부 공유는 명시적 요청이 있을 때만 한다. `-s read-only`는 원격 페이지 생성을 막지 않는다.

## Important Files

- `.claude-plugin/marketplace.json`: 마켓플레이스 이름·소유자, 플러그인 항목(`version`, `category`, `source`).
- `plugins/ai-publish/.claude-plugin/plugin.json`: 플러그인 `name`·`version`(설치 시 이 `version`이 우선)·설명·라이선스(MIT).
- `plugins/ai-publish/skills/chatgpt-publish/SKILL.md`: Pages/Sites 호출, 샌드박스 선택, `RESULT` 형식, 승인 동작 실측표, 비용(호출당 약 35k 토큰).
- `plugins/ai-publish/skills/claude-artifact-publish/SKILL.md`: CLI 명령, 인증 경로, 페이지 제약, 실패 대안, 공유 방식.

## Runtime/Tooling Preferences

- 패키지 매니저·lockfile·런타임 버전 고정이 없다. Node.js(`npx`, 정합성 검사), `claude`, `codex` CLI만 쓴다. Bun·Python은 필요 없다.
- **Claude 발행:** `claude /login`(Pro/Max/Team/Enterprise)이 필수다. 토큰은 macOS Keychain `Claude Code-credentials` 또는 `CLAUDE_CODE_OAUTH_TOKEN`에서 읽는다. 토큰 값을 출력·커밋하지 않는다.
- **ChatGPT 발행:** `codex login`(ChatGPT 계정)과 `apps=true`가 필요하고, Sites는 `sites@openai-curated-remote` 활성화도 필요하다. 승인 동작은 `codex-cli 0.161.0` 기준이므로 다른 버전에서는 다시 실측한다.
- **artifact 콘텐츠:** 자체 완결 단일 HTML(인라인 CSS/JS)을 우선한다. 백엔드·다중 라우트는 불가하고 외부 CDN은 뷰어 CSP에 막힐 수 있다. Markdown/CSV/JSON/YAML은 CLI가 HTML로 렌더한다. 조직/공개 공유는 브라우저 **Share**로만 한다.

## Testing & QA

- 자동 테스트·CI·커버리지 목표는 없다. `npm test` 같은 명령을 가정하지 않는다.
- 저장소 변경 검증: `claude plugin validate` 2개가 기준선 외 경고 없이 통과하고 `node -e` 정합성 검사가 `manifest/skill invariants OK`를 출력해야 한다.
- CLI 예시를 바꾸면 해당 버전 도움말(`codex exec --help` 등)로 옵션을 확인한다. 도움말 확인은 인증·원격 도구·발행 성공의 증거가 아니다.
- 실제 발행 QA는 사용자가 요청한 작업에서 비민감 입력으로만 한다. 기대한 `RESULT`/URL/JSON을 확인하고 `read_page`·`get_deployment_status`·`read <id|url> --content`로 내용을 대조한다. 새 결과가 비공개인지 확인한다(Page: PRIVATE 생성, artifact: 본인만, Site: 소유자와 워크스페이스 관리자).
- 생성·삭제·공유 변경을 smoke test로 실행하지 않는다.
