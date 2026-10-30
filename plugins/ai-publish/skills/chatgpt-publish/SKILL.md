---
name: chatgpt-publish
description: 로컬 Markdown 문서나 웹 프로젝트를 ChatGPT Pages(Space 문서)나 ChatGPT Sites(호스팅 웹사이트)로 발행·수정할 때 사용. "ChatGPT Page로 올려줘", "Pages랑 artifact 둘 다", "Site로 배포해줘" 요청. Codex는 자기 Pages·Sites 도구로 직접 발행하고, Claude Code·omp·Pi는 Herdr의 ho나 `codex exec`로 Codex에 맡긴다. 긴 문서는 콜아웃과 diagram-design 그림(Visualize 임베드)으로 시각화한다.
---

# ChatGPT Pages / Sites 발행

공개 REST API는 없다. ChatGPT 계정으로 로그인한 Codex의 플러그인 도구로 발행한다.
- Pages(`pages@openai-curated-remote`, 공식 스킬 `write-page`): create_page, edit_page, patch_page, read_page, list_pages, create_page_visualization, update_page_sharing, trash_page …
- Sites(`sites@openai-curated-remote`, Sites 스킬): create_site, save_site_version, deploy_site_version, save_version_and_deploy_private, get_deployment_status, update_site_access …

정본 리비전, 영수증, 재시도·재조회, ho 위임, 문서 작성 흐름은 `../claude-artifact-publish/references/publish-flow.md`(이하 "공통 절차")를 따른다.

## 경로 고르기

위에서부터 처음 맞는 줄을 쓴다.

| 상황 | 경로 |
|---|---|
| ho 워커로 `publisher_pages`를 배정받았다 | 내 도구로 직접 한다. 도구가 없으면 blocked로 보고한다. ho·`codex exec`로 다시 넘기지 않는다 |
| 내 도구 목록에 Pages(Sites면 Sites) 도구가 있다 | "Codex에서 직접". `codex exec`를 띄우지 않는다 |
| Codex인데 그 도구가 없다 | 아래 전제 명령으로 플러그인 상태를 본다. 설치·활성 전이면 사용자에게 알리고 멈춘다. 활성인데 이 세션에 없으면(세션 시작 뒤 설치) 새 세션을 권하거나 "`codex exec` 대안"을 쓴다 |
| Pages이고, Claude Code·omp·Pi이고 Herdr 안(공통 절차 2절의 표시), `ho` 있음 | ho에 맡긴다(공통 절차 2절). coordinator가 `publisher_pages`로 배정한다 |
| 그 밖(Sites 포함) | "`codex exec` 대안" |

Sites는 ho로 맡기지 않는다. ho의 발행 대상은 Pages와 artifact뿐이며(`publisher_pages`는 Sites용이 아니다), ho가 Sites를 명시적으로 지원하기 전까지 Sites는 자기 도구나 단독 `codex exec`로만 발행한다.

## 전제

- `codex login`(ChatGPT 계정).
- Pages는 `pages@openai-curated-remote`, Sites는 `sites@openai-curated-remote`가 installed, enabled.

```sh
codex --version
codex plugin list --marketplace openai-curated-remote | grep -E '^(pages|sites)@openai-curated-remote '
```

예전 문서는 `codex features list`의 `apps=true`를 전제로 했다(codex-cli 0.161.0 기준). 기능 플래그 이름과 기본값은 버전마다 바뀔 수 있으므로 판단 근거로 쓰지 않는다. 플러그인 상태와 실제 도구 목록으로 판단한다.

## Codex에서 직접

Pages:
1. 공식 `write-page` 스킬을 읽는다. 새 페이지는 그 스킬의 `references/page-content.md`를, 기존 페이지 수정은 `references/edit-requests.md`를 먼저 읽는다.
2. `../claude-artifact-publish/scripts/receipt.mjs freeze`로 정본과 참조 그림을 실행별 디렉터리에 고정하고 sha256·input을 영수증과 비교한다(공통 절차 4절). 이후 그 사본만 읽는다. plain이면 영수증에 `pending`을 남긴다.
3. 새 페이지는 `space_id`·`parent_page_id` 없이 비공개로 만든다. 사용자가 Space나 상위 페이지를 지정했을 때만 넣는다. Space는 `list_spaces`로 `space_id`를 얻는다.
4. `read_page`로 다시 읽어 제목·소제목·표·콜아웃이 정본과 맞는지 본다. 맞으면 `verified`다. 쓰기 결과가 불확실하면 새로 쓰기 전에 같은 페이지를 다시 읽어 맞춘다.
5. page_id, 도구가 돌려준 URL, 응답에 sequence가 있으면 version, 상태, 근거를 영수증(ho 워커면 ho 보고)에 남긴다. URL은 지어내지 않는다. 도구가 URL을 주지 않았을 때만 2026-10-13에 확인한 형식 `https://chatgpt.com/space/<page_id>`를 쓰고 evidence에 "형식으로 만든 URL"이라고 적는다.

갱신은 기록된 page_id에 `edit_page`·`patch_page`를 쓴다. 새 페이지를 만들지 않는다.

Sites: 배포 전에 `receipt.mjs tree <프로젝트>`로 input을 계산해 프로젝트 옆 영수증(`<프로젝트 폴더 이름>.publish.json`)과 비교한다. Sites 스킬을 읽고 프로젝트 폴더에서 비공개로 배포한다. `get_deployment_status`로 저장한 버전이 배포됐는지 확인한 뒤 url과 version(saved_version_id)을 남긴다. 배포 없이 저장만 하려면 `save_site_version`을 쓴다.

## `codex exec` 대안

Codex 실행 기본값은 `--yolo`다(2026-10-30 사용자 결정). codex-cli 0.165.0에서 `--yolo`는 `--dangerously-bypass-approvals-and-sandbox`의 별칭이라 승인과 셸 샌드박스가 모두 꺼진다. 그래서 `-s`를 함께 쓰지 않고, 할 일은 프롬프트로 좁힌다. 지정 파일만 읽고 로컬 파일은 고치지 않으며(Sites의 빌드와 `.openai/hosting.json`만 예외), 삭제·휴지통·공유 변경 도구는 부르지 않는다.

결과는 마지막 줄을 grep하지 않고 JSON 파일로 받는다. `--output-schema`가 최종 응답 형식을 정하고 `-o`가 그 응답을 파일에 쓴다. 형식은 이 스킬의 `assets/result.schema.json`이다: `state`(공통 절차 4절의 `verified`·`saved`·`partial`·`unknown`·`failed`), `target`(`pages`·`sites`. 영수증·ho 보고의 대상 키와 같다), `id`, `url`, `version`, `evidence`(readback 근거), `note`. 종료 코드와 결과 파일을 함께 확인한다.

```sh
S=<이 스킬 디렉터리의 절대 경로>
R=$(mktemp -d "${TMPDIR:-/tmp}/chatgpt-publish.XXXXXX")   # 실행마다 새 디렉터리
codex exec --yolo --skip-git-repo-check \
  --output-schema "$S/assets/result.schema.json" -o "$R/result.json" \
  "<지시>" > "$R/codex.log" 2>&1
rc=$?
if [ "$rc" -ne 0 ] || [ ! -s "$R/result.json" ]; then
  echo "codex exec 실패: exit=$rc. 상태는 unknown이다. 재조회 전에 다시 만들지 않는다"
  tail -n 20 "$R/codex.log"
else
  cat "$R/result.json"
fi
```

모든 지시는 같은 문장으로 끝낸다: `Answer with the JSON schema. Use state=verified only if you read the result back and it matched. If a write's outcome is unknown, do not retry it; answer state=unknown.` 아래 예시의 `…`가 이 문장이다.

### Pages

정본을 `$R`에 고정하고 그 사본에서 실행한다. 고정 사본만 읽으므로 원본 폴더가 그 사이에 바뀌어도 발행물은 기록한 sha256·input과 같다.

```sh
node "$S/../claude-artifact-publish/scripts/receipt.mjs" freeze <정본 폴더>/report.md "$R"   # sha256·input
cd "$R"
```

```sh
codex exec --yolo --skip-git-repo-check \
  --output-schema "$S/assets/result.schema.json" -o "$R/result.json" \
  "Use the Pages write-page skill. Read ./report.md and do not modify local files. Create a PRIVATE page (omit space_id and parent_page_id). Use its H1 as the page title, not as body text. Then read_page it and check the title and section headings against the file. Never call trash, delete, or sharing tools. Set target=pages, id=<page_id>, url=<the page URL the tool returned, or null if none>. …" \
  > "$R/codex.log" 2>&1
```

- 갱신: `Update page <page_id> to match ./report.md with edit_page or patch_page, following the write-page edit-requests reference. Do not create a new page. …`
- 재조회(`pending`·`unknown`, page_id 없음): `Do not create or edit anything. Use list_pages to find private pages titled '<제목>' and read_page each match. …` 찾은 page_id를 영수증에 남긴다.
- 특정 Space에 넣으려면 먼저 `list_spaces`로 space_id를 얻어 create_page에 넘긴다.

#### 긴 문서 시각화

글이 길면 Pages에도 인포그래픽을 넣는다. 무엇을 어떤 diagram-design 타입으로 그릴지는 `claude-artifact-publish` 스킬의 "긴 문서는 인포그래픽으로" 표와 규칙을 따른다(원문 사실만, 캡션은 결론, 섹션당 그림 하나). Pages가 받는 형식은 로컬 Codex의 `pages@openai-curated-remote` 0.1.21 플러그인 지침(`write-page/references/page-content.md`)으로 2026-10-13에 확인했고, 2026-10-30에 0.1.26 지침에서 아래 내용이 그대로인지 다시 확인했다.

- **그림·차트**: diagram-design으로 그리고 `export_svg.py`로 SVG를 뽑아 HTML로 감싼 뒤 `chatgpt_space.create_page_visualization`(`page_id`, `title`, 256 KiB 이하 `html`)으로 넣는다. 도구가 `![제목](visualize:<file-id>)` 임베드를 단독 문단으로 삽입한다. 임베드 안에는 그림만 두고 제목·해설·출처는 페이지 본문 블록에 쓴다. 넓은 그림은 그 블록의 `layout`을 `flexible`로 둔다.
- **대표 수치·결론**: 네이티브 콜아웃을 쓴다. 표시 줄과 본문을 별도 인용 문단으로 나눈다: `> [!CALLOUT] 💡` / `>` / `> **결론** …`. `[!NOTE]`·`[!WARNING]`은 지원하지 않는다.
- **표·체크리스트**: GFM 표와 `- [ ]`를 그대로 쓴다. 페이지 본문의 HTML·CSS는 글자로 보이므로 쓰지 않는다(표 셀의 정해진 태그만 예외).
- **Mermaid**: Pages는 `mermaid` 코드 블록을 다이어그램 미리보기로 그린다. Visualize를 쓸 수 없을 때만 대안으로 쓴다.
- 문서의 H1은 페이지 제목으로 쓰고 본문 첫 제목으로 되풀이하지 않는다.
- 본문 저장 뒤 그림 삽입이 실패하면 상태는 `partial`이다. 같은 page_id에 그림만 다시 넣는다.

```sh
codex exec --yolo --skip-git-repo-check \
  --output-schema "$S/assets/result.schema.json" -o "$R/result.json" \
  "Use the Pages write-page skill. Read ./report.md and do not modify local files. Create a PRIVATE page (omit space_id and parent_page_id). Use its H1 as the page title, not as body text. Put the key takeaways in a callout. Insert ./figs/<slug>.svg right after the section '<섹션 제목>' with create_page_visualization: wrap the SVG in a minimal HTML document that keeps it at its viewBox width and scrolls horizontally when narrower. Use only facts from the file. Then read_page it and check the title, headings and embed. Never call trash, delete, or sharing tools. Set target=pages, id=<page_id>, url=<the page URL the tool returned, or null if none>. …" \
  > "$R/codex.log" 2>&1
```

### Sites

프로젝트 폴더에서 빌드하고 `.openai/hosting.json`을 쓴다. 배포 전후에 `node "$S/../claude-artifact-publish/scripts/receipt.mjs" tree ./my-site`로 input을 계산해 같을 때만 영수증(`./my-site.publish.json`)에 남긴다. Sites의 sha256은 null이다.

```sh
codex exec --yolo -C ./my-site \
  --output-schema "$S/assets/result.schema.json" -o "$R/result.json" \
  "Use the Sites skill. Deploy this project as a private Site. Do not change site access. Then check get_deployment_status for the saved version. Set target=sites, url=<deployed url>, version=<saved_version_id>. …" \
  > "$R/codex.log" 2>&1
```

- 새 Site는 비공개(소유자 + 워크스페이스 관리자)로 시작한다. 공개 범위 변경은 사용자가 명시적으로 요청했을 때 사람이 UI에서 한다.
- 저장만 하려면 `save_site_version`을 쓴다(배포하지 않음).

## 승인 동작 (2026-10-13 실측, codex-cli 0.161.0)

과거 기록이다. `--yolo` 없이 `exec -s read-only` 기본 승인 정책에서 측정했다. 지금 기본인 `--yolo`는 승인 정책을 끄므로 아래의 거부에 기대지 않는다(0.165.0에서 발행 동작은 다시 측정하지 않았다). 그래서 금지할 도구는 프롬프트에 적는다.

| 도구 | `exec -s read-only` 기본 설정 |
|---|---|
| create_page, read_page, list_sites | 승인 없이 실행됨 |
| trash_page (destructive) | 거부됨: `requires approval, but approval policy is never`. `-c apps.*.approval_mode`로도 풀리지 않음 |

- destructive 도구(trash/delete/공유 변경 등)는 사람이 처리한다. 브라우저 UI에서 하거나, 대화형 `codex`에서 직접 한다.
- `--dangerously-bypass-approvals-and-sandbox`(= `--yolo`)를 쓰면 실행됐다. 2026-10-30부터 사용자 결정으로 Codex 기본값이며, 셸 샌드박스도 꺼지므로 프롬프트를 지정 파일·지정 도구로 좁힌다.

## 실행 환경 확인 (2026-10-30, codex-cli 0.165.0)

도움말·플러그인 목록 확인이며 발행 실측이 아니다.

- `codex exec --yolo --help`는 통과하고, `--yolo --dangerously-bypass-approvals-and-sandbox`는 같은 인자 중복으로 거부된다. `--output-schema`, `-o/--output-last-message`가 있다.
- `pages@openai-curated-remote` 0.1.26, `sites@openai-curated-remote` 1.1.2가 installed, enabled. `apps` 기능은 stable, true로 표시된다.

## 발행 전 필수 점검

- 사외 서비스로 반출하는 것이다. 개인정보(연락처·이메일·계좌·주민번호·건강정보 등), 비밀값, 내부 전용 데이터를 제거한 뒤 넘긴다.
- 사용자가 발행을 요청했는지 확인한다. 작성 요청만으로는 발행하지 않는다.
- sha256·input과 영수증(또는 ho journal)을 확인한다. `verified`이고 둘 다 같으면 다시 보내지 않고, ID가 있으면 갱신하고, `pending`·`unknown`이면 재조회부터 한다. Sites는 input만 비교한다.
- 공개/외부 공유는 사용자가 명시한 경우에만 하며 자동 실행에서 바꾸지 않는다.
- 비용: `codex exec` 대안은 호출마다 Codex 모델 턴 1회가 든다(2026-10-13 기본 모델로 약 35k 토큰 실측).
