# 발행 공통 절차

`chatgpt-publish`와 `claude-artifact-publish`가 함께 따르는 규칙이다. 대상별 명령과 경로표는 각 `SKILL.md`에 있다. 두 스킬은 같은 부모 디렉터리에 설치되므로 `chatgpt-publish`에서는 `../claude-artifact-publish/references/publish-flow.md`로 이 파일을 연다.

## 1. 도구는 실제로 있는 것만 쓴다

- 지금 세션의 도구 목록에 있는 도구만 부른다. 이 문서나 다른 호스트 문서에 이름이 나온다고 내 도구로 가정하지 않는다. 목록에 없는 도구는 이 세션에서 지원되지 않는 것이며, 이름을 맞춰 호출해 보지 않는다.
- 내 도구로 할 수 있으면 직접 한다. 같은 일을 하려고 `codex exec`, `claude -p`, ho로 다른 에이전트를 띄우지 않는다.
- 다른 에이전트에 맡기는 것은 내 도구로 못 하는 대상일 때뿐이며, 맡긴 쪽이 다시 맡기지 않는다(아래 ho 워커 규칙).

## 2. Herdr의 ho로 맡기기

다음이 모두 참일 때 대상 `SKILL.md`의 경로표에 따라 ho로 맡긴다.

```sh
{ [ "${HERDR_ENV:-}" = 1 ] || [ -n "${HC_TERMINAL_ID:-}" ]; } && command -v ho   # Herdr 안이고 ho가 설치됨
```

Herdr TUI 패널은 `HERDR_ENV=1`과 `HERDR_PANE_ID`, Herdr 앱 터미널은 `HC_TERMINAL_ID`가 표시다. 백엔드는 ho가 이 표시로 고르므로 따로 정하지 않는다. 두 표시가 함께 있을 때만 사용자가 지금 쓰는 쪽을 `HO_BACKEND=tui` 또는 `HO_BACKEND=hc`로 붙여 제출하고, 어느 쪽인지 모르면 묻는다. 어느 백엔드가 동작하는지는 `ho doctor`가 정본이다.

- 나는 ho 워커가 아니다.
- 대상을 내 도구로 발행할 수 없다(Claude·omp·Pi의 Pages, Codex·omp·Pi의 artifact). ChatGPT Sites는 ho 대상이 아니다. ho가 Sites를 명시적으로 지원하기 전까지 자기 도구나 단독 `codex exec`로만 발행한다.

ho의 사용자 진입점은 명시 호출뿐이다(Codex `$ho`, Claude `/ho`). 이 스킬은 발행 구간만 ho에 넘긴다. ho coordinator가 이 요청을 `publisher_pages`(Codex, Pages·Sites 도구) 또는 `publisher_artifact`(Claude, 네이티브 Artifact 또는 이 스킬의 CLI) 역할로 배정(dispatch)한다.

- 제출·상태 조회·보고 명령과 옵션은 설치된 ho 스킬의 `SKILL.md`와 `ho --help`를 따른다. 거기에 없는 플래그나 하위 명령을 만들어 쓰지 않는다.
- 제출 내용: 정본 파일의 절대 경로와 sha256, 대상(`pages`·`artifact`·둘 다), 사용자의 발행 요청 원문(발행 승인 근거), 비공개 생성, 갱신이면 기존 ID·URL.
- 제출 명령은 바로 돌아온다. 작업 ID를 사용자에게 알리고 대화에서 기다리지 않는다. ho 상태가 그 대상을 readback 확인 완료로 보여 주기 전에는 "발행 완료"라고 말하지 않는다.
- 띄우는 에이전트의 실행 옵션은 ho가 정한다. 사용자 결정(2026-10-30)에 따른 기본값은 Codex `--yolo`, Claude `--permission-mode auto`다. 작업 cwd는 사용자가 고른 디렉터리이며 그 디렉터리를 신뢰한다. Claude에 `bypassPermissions`·`--dangerously-skip-permissions`나 전역 신뢰 설정은 쓰지 않는다.

### ho 워커일 때

작업 지시서(brief)에 ho 배정과 `publisher_pages`·`publisher_artifact` 역할이 있으면 나는 워커다.

- 배정받은 발행을 직접 한다. ho에 다시 제출하지 않고, `codex exec`·`claude -p` 대안으로 다른 에이전트를 띄우지 않는다.
- 지시서의 정본 경로에서 sha256을 다시 계산한다. 지시서 값과 64자 전체가 같지 않으면 발행하지 않고 blocked로 보고한다.
- 필요한 도구가 없으면 blocked로 보고한다.
- 결과는 ho 스킬이 정한 보고 명령으로 ho journal에 남긴다. 보고에 붙이는 결과 파일에는 4절 항목(상태, sha256, input, ID, URL, 버전, 근거)을 JSON으로 쓴다. `verified`일 때만 완료로 보고하고, 다른 상태는 그 상태와 근거를 보고한다. 영수증 파일은 쓰지 않는다.

## 3. 문서 작성과 발행 결정

- "써 줘", "정리해 줘"처럼 작성만 요청하면 로컬 Markdown까지만 만든다. 발행하지 않는다.
- 정본은 한국어 Markdown 한 파일이다. 실행마다 새 출력 디렉터리를 만들고 기존 문서를 덮어쓰지 않는다. 예: `<작업 폴더>/out/<YYYYMMDD-HHMM>-<slug>/<slug>.md`. 그림(`<slug>.svg`, `<slug>-dark.svg`)도 같은 디렉터리에 둔다.
- 작성은 Terra(`gpt-6.1-terra`, xhigh)가 하고, Claude Opus 5.5(`claude-opus-5-5`, xhigh)가 구조·논리·근거를 비평하고, Terra가 반영해 확정한다. 상호 비평은 같은 원본 리비전(sha256)을 두고 최대 3라운드다. 3라운드 안에 합의하지 못하면 남은 쟁점을 사람에게 묻는다.
  - Herdr와 ho가 있으면 ho에 문서 작업으로 제출한다. 역할 배정과 라운드 제한은 ho가 맡는다.
  - ho가 없으면 내가 그 역할의 모델일 때 직접 하고, 상대 역할만 한 번짜리 실행으로 부른다. `OUT`은 이번 실행의 출력 디렉터리다.

```sh
codex exec --yolo --skip-git-repo-check -m gpt-6.1-terra -c model_reasoning_effort=xhigh -C "$OUT" "<작성 또는 비평 반영 지시>"
(cd "$OUT" && claude -p --model claude-opus-5-5 --effort xhigh --permission-mode auto "<비평 지시. 파일은 고치지 말고 비평만 출력한다>")
```

- 초안이 나오면 경로와 요약을 보여 주고 발행 대상(ChatGPT Pages, Claude artifact, 둘 다)을 고르게 한다. 처음 요청에 발행과 대상이 이미 명시돼 있으면 다시 묻지 않는다.
- 확정한 정본은 발행이 끝날 때까지 고치지 않는다. 발행자는 정본을 읽기만 하고, 변환물은 실행별 임시 디렉터리에 만든다. 고칠 일이 생기면 새 리비전(새 sha256)을 만들어 다시 발행한다. 그림 같은 자산도 발행 중에는 바꾸지 않는다.
- 새 결과는 비공개로 만든다. 조직·공개·링크 공유로 넓히는 일은 사용자가 명시적으로 요청한 경우에만 하고, 사람이 서비스 UI에서 처리한다. `codex exec --yolo`나 ho 워커 같은 자동 실행에서는 공유 범위를 바꾸지 않는다.

## 4. 리비전·입력과 대상 상태 기록

두 값을 함께 기록한다.

- `sha256`: 정본 Markdown의 64자 전체 hex(`shasum -a 256 <정본>.md`). 원고 내용의 리비전이며 ho journal의 리비전과 같은 값이다. 앞 12자는 artifact 라벨처럼 사람이 보는 표시에만 쓰고 비교에 쓰지 않는다. Sites는 정본 Markdown이 없으므로 null이다.
- `input`: 실제로 발행되는 입력 전체의 digest. 문서는 정본과 정본이 참조하는 로컬 자산(그림 SVG, 옆의 `-dark.svg` 짝, 그 밖의 로컬 이미지), Sites는 프로젝트 파일(git이면 추적·미무시 파일, `.git`·`.openai`·`node_modules` 제외)이다. 그림만 바뀌어도 `input`은 달라진다.

두 값은 이 스킬의 `scripts/receipt.mjs`가 만든다. `chatgpt-publish`에서는 `../claude-artifact-publish/scripts/receipt.mjs`다.

```sh
P=<claude-artifact-publish 디렉터리의 절대 경로>/scripts/receipt.mjs
R=$(mktemp -d "${TMPDIR:-/tmp}/ai-publish.XXXXXX")
node "$P" freeze <정본 폴더>/report.md "$R"   # {"sha256","input","files"}. $R에 정본·자산 사본과 input.json(파일별 sha256)
node "$P" tree ./my-site                        # Sites: {"sha256":null,"input","files"}. 복사하지 않는다
```

- 문서는 `freeze` 뒤 `$R`의 사본만 읽어 변환·발행한다. 원본 폴더의 파일이 그 사이에 바뀌어도 발행물은 고정한 입력과 같다. 정본 폴더 밖(`../`, 절대 경로)을 가리키는 그림은 고정하지 못하므로 `freeze`가 실패한다. 그림을 정본 폴더 안으로 옮긴다.
- Sites는 배포 직전에 `tree`를 계산하고 배포 뒤 다시 계산해 같을 때만 그 값을 기록한다.

| 상태 | 뜻 | 다음 행동 |
|---|---|---|
| `pending` | 생성·갱신 호출 직전에 남긴 기록 | 응답 없이 끝났으면 `unknown`과 같이 다룬다 |
| `saved` | 서비스가 ID·URL을 돌려줬으나 readback 전 | 다시 읽어 확인한다 |
| `verified` | 다시 읽은 내용이 기록한 `sha256`·`input`과 맞음 | 둘 다 같으면 다시 보내지 않는다 |
| `partial` | 일부만 반영됨(예: 본문은 저장, 그림 삽입 실패) | 같은 ID를 갱신한다 |
| `unknown` | 시간 초과·중단·결과 없음. 원격에 생겼을 수 있음 | 5절 재조회부터 한다 |
| `failed` | 반영되지 않은 것이 확실함(인증 실패, 요청 거부) | 원인을 고친 뒤 다시 한다 |

`verified`일 때만 "발행 완료"라고 알린다. 나머지는 상태 이름과 근거를 그대로 알린다.

ho 안에서는 ho journal에 남긴다. ho journal의 리비전은 `sha256`이므로 `input`은 보고 결과 파일과 근거에 적는다. ho 밖(plain)에서는 영수증 파일에 남긴다.

- 문서: 정본 옆 `<정본 이름>.publish.json`. 예: `report.md` → `report.publish.json`.
- Sites: 프로젝트 폴더 **옆** `<프로젝트 폴더 이름>.publish.json`. 예: `./my-site` → `./my-site.publish.json`. 프로젝트 안에 두면 함께 배포되고 `input`도 바뀐다.

대상 키는 `pages`, `sites`, `artifact`다(ho 역할 `publisher_pages`·`publisher_artifact`, 플러그인 `pages@`·`sites@`와 같은 이름). `codex exec` 결과의 `target`도 같은 값을 쓴다.

```json
{
  "source": "report.md",
  "targets": {
    "artifact": { "state": "verified", "sha256": "<64자 hex>", "input": "<64자 hex>", "id": "…", "url": "https://claude.ai/code/artifact/…", "version": 3, "title": "배포 개선 보고서", "evidence": "read --content 바이트 일치", "at": "2026-10-30T03:00:00.000Z" },
    "pages": { "state": "unknown", "sha256": "<64자 hex>", "input": "<64자 hex>", "title": "배포 개선 보고서", "evidence": "create_page 응답 없음", "at": "2026-10-30T03:01:00.000Z" }
  }
}
```

항목은 `merge`로 하나씩 합친다. 다른 대상 항목은 그대로 남는다. `id`·`url`·`version`의 null은 "모름"이라는 뜻이며, 이미 아는 값을 지우지 않는다. 그래서 결과를 모르는 갱신 뒤에도 갱신할 대상 ID가 남는다.

```sh
node "$P" merge report.publish.json report.md artifact '{"state":"pending","sha256":"<64자 hex>","input":"<64자 hex>","title":"<제목>"}'
```

- 둘 다 발행할 때 plain에서는 한 대상씩 차례로 하고, 한 번에 한 대상 항목만 고친다.
- 영수증과 ho 보고에는 토큰·비밀값·이메일을 넣지 않는다.

## 5. 재시도와 재조회

- `verified`이고 `sha256`과 `input`이 모두 같은 대상은 다시 보내지 않는다. 하나라도 다르면 갱신한다. 둘 중 한쪽만 실패했으면 실패한 쪽만 다시 한다.
- ID가 있으면 새로 만들지 않고 그 ID를 갱신한다. 새 리비전 발행도 갱신이다.
- `pending`·`unknown`이고 ID가 없으면 만들기 전에 찾는다. artifact는 `list`의 제목·라벨, Pages는 `list_pages`의 제목, Sites는 프로젝트의 `.openai/hosting.json`과 배포 상태로 찾는다. 찾으면 그 ID를 기록하고 다시 읽는다. 못 찾으면 사용자에게 알리고 다시 만들지 확인받는다.
- 시간 초과는 실패가 아니다. 같은 생성 요청을 바로 되풀이하지 않는다.
- 중복을 발견해도 지우지 않는다. 사용자에게 알리고 삭제는 사람이 한다. 자동 정리(삭제·휴지통)는 하지 않는다.
