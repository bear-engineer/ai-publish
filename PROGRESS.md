# PROGRESS — ai-publish 0.4.0 (multi-host + Herdr/ho)

- worktree: `/Users/teddy/omp-ai-publish-worktrees/herdr-ho-publish`, 브랜치 `feat/herdr-ho-publish-wt` (기준 `feat/herdr-ho-publish` @ `e2c993d`)
- 메인 checkout `/Users/teddy/omp-ai-publish`은 건드리지 않음. Claude·omp `ai-publish` 마켓플레이스는 부모가 이 worktree로 돌려 둠(2026-10-30 확인).
- 커밋·푸시·원격 발행 없음.

## 사용자 결정 (작업 중 추가)

1. Codex 실행 기본 `--yolo` (standalone `codex exec` 대안, ho 문서). Claude는 별도.
2. Claude 실행은 `--permission-mode auto`, 사용자가 고른 작업 cwd를 신뢰. `bypassPermissions`·전역 trust-all 금지.
3. 기본 git worktree. 문서 산출물은 실행별 디렉터리, 발행자는 고정된 정본 리비전만 읽고 원본을 동시에 고치지 않음.

## 조사 결과 (2026-10-30)

- codex-cli 0.165.0. `--yolo`는 `--dangerously-bypass-approvals-and-sandbox`의 숨은 별칭(같이 주면 중복 인자 오류). `--output-schema`, `-o/--output-last-message` 있음.
- `pages@openai-curated-remote` 0.1.26, `sites@openai-curated-remote` 1.1.2 installed/enabled. `apps` 기능 플래그는 stable/true지만 판단 근거로 쓰지 않음.
- 공식 `write-page` 스킬: readback 후에만 성공, unknown commit은 재조회 후 쓰기, `create_page_visualization` 인자 동일.
- claude-artifacts 0.1.14: `create/update --output json` → `artifact_id`·`artifact_url`·`version`(로컬 캡처 서버로 확인). `read --content --output json` → `version`·`share_mode`·`content_html`(+`author_email`). `list --output json` → `title`·`label`(+`owner_email`).
- Claude Code 2.1.314: `--permission-mode auto`, `--effort xhigh`, `--model` 있음. `-p`는 신뢰 대화상자를 건너뜀.
- ho(`/Users/teddy/ho`)는 아직 커밋 없음·`ho` 미설치. 인터페이스는 설치될 ho 스킬/`ho --help`를 따르도록 문서화(플래그 창작 금지).

## 진행

- [x] worktree 생성
- [x] 매니페스트 0.4.0
- [x] 공통 절차 `claude-artifact-publish/references/publish-flow.md`
- [x] chatgpt-publish SKILL.md + `assets/result.schema.json`
- [x] claude-artifact-publish SKILL.md
- [x] `scripts/install.py` + `scripts/test_install.py`
- [x] README.md, AGENTS.md
- [x] 검증(아래)
- [x] 검토 의견 반영: Terra 예시 `--skip-git-repo-check`, 대상 키 `pages`·`sites`·`artifact` 통일, Pages URL은 도구 반환값, Sites는 ho로 보내지 않음, 리비전은 sha256 64자 전체
- [x] `ONBOARDING.review.md` 작성(초안은 수정하지 않음)

## 검증 결과 (모두 로컬, 원격 발행·삭제 없음)

| 검사 | 결과 |
|---|---|
| `claude plugin validate .` / `plugins/ai-publish` | 통과. 경고는 main 기준선과 동일(author, icon) |
| AGENTS.md 정합성 검사(`node -e`) | `manifest/skill invariants OK`, 두 매니페스트 0.4.0 |
| `python3 -m unittest discover -s scripts -v` | 7개 통과. 돌연변이(링크 대상 검사·버전 비교 무력화)에서 3개 실패 확인 |
| `install.py codex claude omp --dry-run`(실제 환경) | exit 0, 변경 없음. codex 링크 ok, claude·omp는 0.3.2→0.4.0 갱신 계획 |
| `install.py codex`(임시 `CODEX_HOME`) | 링크 생성, 재실행 시 ok만(멱등), 링크 경유 `../claude-artifact-publish/references/` 해석 확인 |
| 문서 변환 → artifact CLI(로컬 캡처 서버) | 한국어 강조 `**` 0, SVG `<figure>` 인라인, 소제목 3, 올린 바이트 = `report.html`, 라벨에 sha 앞 12자 |
| 영수증 병합·readback 비교 node 스니펫 | 병합 후 기존 id 유지·다른 대상 보존, 같음 exit 0·다름 exit 1, 이메일 미출력 |
| `codex exec` 종료 코드 검사(가짜 codex, bash·zsh) | 실패·빈 결과는 unknown 경로, 성공은 JSON 출력 |
| 결과 스키마 | strict 형태(모든 필드 required, additionalProperties false) |
| `page.html`·`marked.config.mjs` | 변경 없음 |

## 확인하지 못한 것

- `--output-schema`를 실제 모델 호출로 받아 보지 않음(브리프상 도움말 확인만). 스키마는 strict 규칙 형태만 점검.
- 네이티브 `Artifact` 도구 경로와 실제 `read --content`의 `content_html` 바이트 일치는 원격 호출이 필요해 미확인.
- `claude plugin update`가 디렉터리 원본 마켓플레이스에서 0.4.0을 읽는지는 실행하지 않아 미확인(부모 설치 단계).
- ho는 아직 미설치·미완(`/Users/teddy/ho`), ho 경로는 문서 규칙과 ho 코드 대조까지만.

## 0.4.1 — Sol 검토(`publish-review.md`) 반영 (2026-10-30)

| 검토 항목 | 처리 |
|---|---|
| null `id`·`url`·`version`이 알던 값을 지움 | 고침. 병합을 `claude-artifact-publish/scripts/receipt.mjs merge`로 옮기고 null은 "모름"(기존 값 유지)으로 정의 |
| 리비전이 SVG 자산·Site 입력을 반영 못함 | 최소로 고침. `sha256`(정본 Markdown)은 그대로 두고 `input` digest를 추가. 문서는 `freeze`가 정본+참조 자산(다크 짝 포함)을 `$R`에 복사하고 `input.json`을 쓰며 변환·발행은 사본만 읽음. Site는 `tree`(git 추적·미무시 파일, `.git`·`.openai`·`node_modules` 제외), 영수증은 프로젝트 폴더 옆. 재발행 생략은 `verified`이고 둘 다 같을 때만 |
| `A="npx …"; $A`가 zsh에서 실패 | 고침. `A() { npx -y claude-artifacts@0.1.14 "$@"; }` |
| 초안 뒤 대상 선택 생략 | 반려(사용자 결정: 대상이 정해지지 않았을 때만 묻고, 먼저 명시한 발행 요청은 승인이다) |
| ho 전체 SHA | 런타임 쪽에서 이미 고침 |

- 회귀: `scripts/test_publish.py` 6개(null 병합, 자산만 바뀐 경우, 폴더 밖 자산 거부, Site 입력 제외 규칙, gitignore 빌드 제외, 문서의 `A()` 줄을 `zsh -f`로 실행). zsh 테스트는 문서 수정 전 RED, null 병합 테스트는 보존 줄을 뺀 사본에서 RED 확인.
- 문서대로 `freeze` → `$R` 변환 → 그림 인라인 확인, zsh에서 `A --help`로 실제 CLI 실행 확인.
- 0.4.1로 올림. 전체 13개 테스트 통과, validate 경고 기준선과 동일, dry-run은 claude·omp 0.4.0→0.4.1 갱신 계획.

## 0.4.2 — ho 백엔드 감지 (2026-10-30)

- ho 위임 조건을 "Herdr TUI 패널(`HERDR_ENV=1`+`HERDR_PANE_ID`) 또는 Herdr 앱 터미널(`HC_TERMINAL_ID`), 그리고 `ho`"로 넓혔다. 백엔드는 ho가 자동으로 고르고, 두 표시가 함께 있을 때만 `HO_BACKEND=tui|hc`를 정한다(계약: `/Users/teddy/ho-hc-adapter/INTEGRATION.md`). 공통 절차·두 경로표·README·AGENTS를 함께 고쳤다.
- 캐시 갱신을 위해 0.4.2로 올렸다.
- Codex `quick_validate.py`가 `claude-artifact-publish` 설명의 꺾쇠괄호(`artifact/<id>`)를 거부해 `artifact/ID`로 바꿨다. `scripts/test_publish.py`에 두 스킬의 Codex 검증 테스트를 더해 14개 통과.
