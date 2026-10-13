---
name: chatgpt-publish
description: omp 결과물을 ChatGPT Pages(Space 문서)나 ChatGPT Sites(호스팅 웹사이트)로 발행·수정할 때 사용. Codex CLI(`codex exec`)의 ChatGPT apps 도구(chatgpt_space.*, sites.*)를 대리 호출한다. 긴 문서는 콜아웃과 diagram-design 그림(Visualize 임베드)으로 시각화한다.
---

# ChatGPT Pages / Sites 발행 (omp → Codex CLI)

공개 REST API는 없다. 대신 Codex CLI에 ChatGPT 로그인으로 붙는 앱 도구가 있다:
- `chatgpt_space.*`: create_page, edit_page, patch_page, read_page, list_pages, update_page_sharing, trash_page …
- `sites.*` (Codex 플러그인 `sites@openai-curated-remote`): create_site, save_site_version, deploy_site_version, save_version_and_deploy_private, get_deployment_status, update_site_access …

전제: `codex login`(ChatGPT 계정), `codex features list`에서 `apps`가 true, Sites는 `codex plugin list`에서 `sites@openai-curated-remote`가 enabled.

## 호출 패턴

모델 턴 하나로 도구를 부른다. 마지막 줄만 파싱한다.

```sh
codex exec --skip-git-repo-check -s read-only "<지시>. 마지막에 정확히 한 줄: RESULT ..." 2>&1 | grep '^RESULT' | tail -1
```

### Pages

```sh
codex exec --skip-git-repo-check -s read-only \
  "Read ./report.md. Using chatgpt_space tools only, create a PRIVATE page (omit space_id and parent_page_id) titled '<제목>' whose blocks reproduce the markdown. Print: RESULT page_id=<id> url=<url>"
```
- 갱신: `... edit_page/patch_page page_id=<id> ...`
- 특정 Space에 넣으려면: 먼저 `list_spaces`로 space_id를 얻고 create_page에 넘긴다.
- URL 형식: `https://chatgpt.com/space/<page_id>`

#### 긴 문서 시각화

글이 길면 Pages에도 인포그래픽을 넣는다. 무엇을 어떤 diagram-design 타입으로 그릴지는 `claude-artifact-publish` 스킬의 "긴 문서는 인포그래픽으로" 표와 규칙을 따른다(원문 사실만, 캡션은 결론, 섹션당 그림 하나). Pages가 받는 형식은 로컬 Codex의 `pages@openai-curated-remote` 0.1.21 플러그인 지침(`write-page/references/page-content.md`)으로 2026-10-13에 확인했다.

- **그림·차트**: diagram-design으로 그리고 `export_svg.py`로 SVG를 뽑아 HTML로 감싼 뒤 `chatgpt_space.create_page_visualization`(`page_id`, `title`, 256 KiB 이하 `html`)으로 넣는다. 도구가 `![제목](visualize:<file-id>)` 임베드를 단독 문단으로 삽입한다. 임베드 안에는 그림만 두고 제목·해설·출처는 페이지 본문 블록에 쓴다. 넓은 그림은 그 블록의 `layout`을 `flexible`로 둔다.
- **대표 수치·결론**: 네이티브 콜아웃을 쓴다. 표시 줄과 본문을 별도 인용 문단으로 나눈다: `> [!CALLOUT] 💡` / `>` / `> **결론** …`. `[!NOTE]`·`[!WARNING]`은 지원하지 않는다.
- **표·체크리스트**: GFM 표와 `- [ ]`를 그대로 쓴다. 페이지 본문의 HTML·CSS는 글자로 보이므로 쓰지 않는다(표 셀의 정해진 태그만 예외).
- **Mermaid**: Pages는 `mermaid` 코드 블록을 다이어그램 미리보기로 그린다. Visualize를 쓸 수 없을 때만 대안으로 쓴다.
- 문서의 H1은 페이지 제목으로 쓰고 본문 첫 제목으로 되풀이하지 않는다.
- `create_page_visualization`의 승인 동작은 실측하지 않았다. 거부되면 아래 승인 동작처럼 사람이 처리한다.

```sh
codex exec --skip-git-repo-check -s read-only \
  "Use the Pages write-page skill. Read ./report.md and create a PRIVATE page (omit space_id and parent_page_id). Use its H1 as the page title, not as body text. Put the key takeaways in a callout. Insert ./figs/<slug>.svg right after the section '<섹션 제목>' with create_page_visualization: wrap the SVG in a minimal HTML document that keeps it at its viewBox width and scrolls horizontally when narrower. Use only facts from the file. Print: RESULT page_id=<id> url=<url>"
```

### Sites

프로젝트 폴더에서 실행한다. 빌드하고 `.openai/hosting.json`을 써야 하므로 `-s workspace-write`로 실행한다.
```sh
codex exec -C ./my-site -s workspace-write \
  "Use the Sites skill. Deploy this project as a private Site. Print: RESULT url=<deployed url> version=<saved_version_id>"
```
- 새 Site는 비공개(소유자 + 워크스페이스 관리자)로 시작한다. 공개 범위는 `update_site_access`로 바꾸거나 UI에서 바꾼다.
- 저장만 하려면 `save_site_version`을 쓴다(배포하지 않음).

## 승인 동작 (2026-10-13 실측, codex-cli 0.161.0)

| 도구 | `exec -s read-only` 기본 설정 |
|---|---|
| create_page, read_page, list_sites | 승인 없이 실행됨 |
| trash_page (destructive) | 거부됨: `requires approval, but approval policy is never`. `-c apps.*.approval_mode`로도 풀리지 않음 |

- destructive 도구(trash/delete/공유 변경 등)는 사람이 처리한다. 브라우저 UI에서 하거나, 대화형 `codex`에서 직접 승인한다.
- `--dangerously-bypass-approvals-and-sandbox`를 쓰면 실행된다. 다만 셸 샌드박스까지 꺼지므로 사용자가 명시적으로 요청했을 때만 쓴다. 쓸 때는 프롬프트를 "셸 금지 + 도구 1개"로 좁힌다.

## 발행 전 필수 점검

- 사외 서비스로 반출하는 것이다. 개인정보(연락처·이메일·계좌·주민번호·건강정보 등), 비밀값, 내부 전용 데이터를 제거한 뒤 넘긴다.
- 공개/외부 공유는 사용자가 명시한 경우에만 한다.
- 비용: 호출마다 Codex 모델 턴 1회(약 35k 토큰 실측)가 든다.
