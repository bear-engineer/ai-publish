# ai-publish

로컬 HTML·문서·웹 프로젝트를 **Claude artifacts**와 **ChatGPT Pages/Sites**로 발행·갱신하는 Agent Skills 묶음.

새 서버나 도구를 구현하는 extension이 아니라, 에이전트에게 기존 CLI 호출 방법과 안전 규칙을 알려주는 두 개의 스킬이다. Claude artifact 스킬에는 읽기용 페이지 템플릿과 Markdown 변환 설정이 함께 들어 있다. 현재 저장소는 Claude Code 플러그인 마켓플레이스 구조이며, Pi에서도 스킬 경로를 지정해 사용할 수 있다.

## 할 수 있는 일

| 대상 | 입력과 용도 | 실행 경로 |
|---|---|---|
| Claude artifact | Markdown 보고서를 읽기용 페이지(목차·표 스크롤·다크 모드)로 발행하고 diagram-design 그림을 함께 넣음. HTML·CSV·JSON·YAML 발행, 기존 artifact 갱신·조회 | `marked` 변환 + `claude-artifacts` CLI |
| ChatGPT Page | Markdown 보고서·문서를 비공개 페이지로 생성·수정 | Codex CLI의 `chatgpt_space.*` 도구 |
| ChatGPT Site | 웹 프로젝트를 비공개 사이트로 배포하거나 버전만 저장 | Codex CLI의 `sites.*` 도구 |

기본은 비공개 생성이다. 공개·외부 공유는 별도 요청과 공유 범위 확인이 필요하다.

## 사용 시작

### Pi

저장소를 받은 뒤 루트에서 실행한다.

```sh
pi --skill ./plugins/ai-publish/skills
```

이 명령은 해당 실행에서 두 스킬을 로드한다. Pi 0.87.1에서 실제 스킬 탐색과 명령 등록을 확인했다. 서비스 로그인과 원격 발행 성공까지 보장하는 것은 아니다.

Pi에서 자연어로 요청하거나 스킬을 직접 지정한다.

```text
/skill:claude-artifact-publish ./report.html을 비공개 artifact로 올려줘
/skill:chatgpt-publish ./report.md를 비공개 ChatGPT Page로 발행해줘
/skill:chatgpt-publish ./my-site를 비공개 ChatGPT Site로 배포해줘
```

입력 경로는 사용자가 준비한 파일·프로젝트 예시이며 이 저장소에 포함되지 않는다. 기존 결과를 갱신하려면 요청에 ID 또는 URL을 함께 준다.

### Claude Code

GitHub 마켓플레이스를 등록하고 플러그인을 설치한다. 로컬 clone이나 저장소 루트에서 실행할 필요가 없다.

```sh
claude plugin marketplace add bear-engineer/ai-publish
claude plugin install ai-publish@ai-publish
```

설치 명령은 Claude Code의 사용자 설정을 변경한다. 설치 후 새 세션에서 “이 파일을 Claude artifact로 올려줘” 또는 “이 보고서를 ChatGPT Page로 발행해줘”처럼 요청한다.

`claude plugin marketplace add .`는 로컬 checkout의 변경을 시험하는 개발용이다. 공개 저장소에서 설치할 때는 위 GitHub 경로를 사용한다.

## 필요한 환경

- **Claude artifact:** Node.js/npm의 `npx`, Claude Code, `claude /login` 완료(Pro/Max/Team/Enterprise). `claude-artifacts@0.1.14`, Markdown 변환용 `marked@18.1.1`·`marked-cjk-friendly@0.1.2`를 버전 고정해 `npx`로 받는다. 그림을 넣으려면 diagram-design 스킬과 SVG 추출용 `python3`가 필요하다.
- **ChatGPT Page/Site:** Codex CLI, ChatGPT 계정으로 `codex login`, `apps=true`. Site에는 `sites@openai-curated-remote` 플러그인 활성화도 필요하다.
- **Pi에서 사용:** 위 서비스별 준비와 별개로 Pi가 설치되어 있어야 한다. 이 스킬 묶음 자체에는 빌드 단계나 서버가 없다.

ChatGPT 쪽 전제조건은 다음 읽기 전용 명령으로 확인할 수 있다.

```sh
codex --version
codex features list | grep '^apps '
codex plugin list --marketplace openai-curated-remote | grep '^sites@openai-curated-remote '
```

승인 동작의 실측 기준은 `codex-cli 0.161.0`이다. 다른 버전에서는 스킬 문서의 동작이 달라질 수 있다.

## 제약과 안전

- **사외 반출:** 발행 전에 개인정보·비밀값·내부 전용 데이터를 제거한다. 토큰을 프롬프트·로그·저장소에 넣지 않는다.
- **Claude는 비공식 연동:** CLI가 macOS Keychain의 `Claude Code-credentials` 또는 `CLAUDE_CODE_OAUTH_TOKEN`을 읽어 비공식 API를 호출한다. Anthropic의 변경으로 깨질 수 있으며 공식 연동을 보장하지 않는다.
- **artifact는 단일 문서:** 자체 완결 HTML과 인라인 CSS/JS를 우선한다. 백엔드·다중 라우트는 지원하지 않고 외부 CDN은 뷰어 CSP에 막힐 수 있다. 조직/공개 공유는 브라우저의 **Share**에서 처리한다.
- **추가 모델 호출:** ChatGPT 발행은 `codex exec` 모델 턴 1회를 사용한다. Claude의 정상 CLI 경로에는 별도 LLM 턴이 없지만, 실패 시 `claude -p` 대안은 별도 모델 호출이다.
- **샌드박스와 원격 작업은 별개:** Pages의 `read-only`는 원격 페이지 생성을 막지 않는다. Sites는 대상 프로젝트에 `.openai/hosting.json`을 작성하므로 `workspace-write`를 사용한다.
- **공유 범위:** 새 Claude artifact는 본인만, 새 Site는 소유자와 워크스페이스 관리자가 볼 수 있다. 비공개가 “어떤 다른 사용자도 접근할 수 없음”을 뜻하는 것은 아니다.
- **파괴적 작업:** ChatGPT의 삭제·공유 변경은 사람이 UI나 대화형 Codex에서 처리한다. 승인 우회를 기본 사용법으로 삼지 않는다. 검증 목적으로 생성·삭제·공유 변경을 실행하지 않는다.

## Pi packages 페이지에 올릴 수 있나?

**콘텐츠와 스킬 형식은 적합하다.** Pi packages는 실행 코드가 있는 extension뿐 아니라 `SKILL.md`만 제공하는 skills 패키지도 지원한다. 이 저장소의 두 스킬은 Pi에서 직접 로드할 수 있다.

**현재 저장소가 npm 패키지로 준비된 것은 아니다.** [Pi packages 카탈로그](https://pi.dev/packages)는 npm에 발행된 패키지를 소개한다. 이 저장소에는 아직 `package.json`이 없으므로 `pi install npm:ai-publish`가 가능하다고 안내하지 않는다.

카탈로그 등재 대상으로 배포하려면 다음이 필요하다.

1. 사용 가능한 npm 패키지 이름과 버전 등 메타데이터를 정한다.
2. 루트 `package.json`에 `keywords: ["pi-package"]`와 `pi.skills: ["./plugins/ai-publish/skills"]`를 선언한다. 스킬이 표준 루트 `skills/`가 아닌 곳에 있기 때문에 경로를 명시한다.
3. 두 스킬이 실제 npm 배포 파일에 포함되는지 확인하고 npm에 발행한다.

`pi-package` 키워드는 카탈로그 탐색 대상이 되는 조건이며, 등록 완료나 게시 시점을 보장하는 것은 아니다. 이번 저장소 상태에서는 Pi의 `--skill` 직접 로드와 Claude Code 마켓플레이스 설치를 안내한다.

공식 형식과 배포 규칙: [Pi Packages](https://pi.dev/docs/latest/packages), [Pi Skills](https://pi.dev/docs/latest/skills).

## 상세 절차와 개발

- [Claude artifact 스킬](plugins/ai-publish/skills/claude-artifact-publish/SKILL.md): 생성·갱신·조회·삭제 명령, 인증과 공유 제약.
- [ChatGPT Pages/Sites 스킬](plugins/ai-publish/skills/chatgpt-publish/SKILL.md): 발행 명령, 결과 형식, 승인 동작.
- [Repository Guidelines](AGENTS.md): 저장소 구조와 매니페스트·스킬 정합성 검사.

CLI 발행 명령의 정본은 각 `SKILL.md`다. 저장소 메타데이터의 기본 검증은 다음과 같다. 현재 `author` 누락 경고 1건이 있으며 `--strict`는 이 경고로 실패한다.

```sh
claude plugin validate .
claude plugin validate plugins/ai-publish
```
