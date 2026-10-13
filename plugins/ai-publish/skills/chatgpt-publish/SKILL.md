---
name: chatgpt-publish
description: omp 결과물을 ChatGPT Pages(Space 문서)나 ChatGPT Sites(호스팅 웹사이트)로 발행·수정할 때 사용. Codex CLI(`codex exec`)의 ChatGPT apps 도구(chatgpt_space.*, sites.*)를 대리 호출한다.
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
