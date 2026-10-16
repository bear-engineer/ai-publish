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

CLI는 `<!doctype html>`로 시작하는 파일을 바꾸지 않고 올린다. 그래서 본문을 HTML로 변환해 이 스킬의 `assets/page.html` 뒤에 붙여 올린다. `page.html`은 읽기용 글꼴 크기·줄 간격·폭, 다크 모드, 표만 가로로 스크롤, 목차를 맡는다. 목차는 소제목이 3개 이상일 때 생기며, 넓은 화면에서는 왼쪽에 고정되어 읽는 위치를 표시하고, 좁은 화면에서는 오른쪽 아래 목차 버튼을 누르면 바텀시트로 열린다. 경로는 이 스킬 디렉터리 기준이다.

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

## 긴 문서는 인포그래픽으로

본문이 길면(대략 3,000자 이상이거나 `##` 섹션 5개 이상) 발행 전에 섹션마다 그림·표·수치 카드로 보이면 더 빨리 읽히는지 따진다. diagram-design에는 45가지 타입이 있으니 흐름도와 막대에 머물지 말고 아래 표에서 내용에 맞는 타입을 고른다. 표의 영문 설명은 upstream README 그대로이며, 모양은 [갤러리](https://cathrynlavery.github.io/diagram-design/)에서 본다. 문단이나 표로 충분한 내용은 그리지 않는다.

| 원문에 있는 것 | 쓸 것 (README 설명) |
|---|---|
| 대표 수치 2~4개 | 첫머리 수치 카드(아래) |
| 항목별 수치 비교 | Bar chart (Categorical comparison). 정확한 값 조회가 목적이면 표 |
| 시간 추이, 두 시점 비교, 순위 변화 | Line chart (Trends over time; slopegraph·ridgeline·streamgraph·bump 변형) |
| 시작값에서 끝값까지 증감 분해 | Waterfall (Running total + signed bridges) |
| 구성비, 순위 계층·단계별 이탈 | Treemap (Part-of-whole by area; marimekko 변형), Pyramid / funnel (Ranked hierarchy or drop-off) |
| 갈라지고 합쳐지는 양 | Sankey (Quantities that split + merge) |
| 행×열 값, 분포·상관 | Heatmap (Value per row × column cell), Scatter plot (Distribution + correlation; bubble·beeswarm 변형) |
| 다기준 비교, 2축 위치, 주기적 크기 | Radar / spider (Multi-axis comparison), Quadrant (Two-axis positioning), Polar chart (Cyclic magnitude · linear radius) |
| 사건·마일스톤, 기간 일정 | Timeline (Events on an axis), Gantt (Tasks + phases on a timeline) |
| 조건 분기와 판단 | Flowchart (Decision logic) |
| 부서·역할을 오가는 절차 | Swimlane (Cross-functional flow), Process (Multi-actor sequential workflow) |
| 고객 접점과 뒤편 지원 절차 | Service blueprint (Frontstage and backstage on a shared stage grid) |
| 시스템 간 호출 순서 | Sequence (Messages over time) |
| 상태와 전이 | State machine (States + transitions) |
| 구성 요소와 연결, 변경 전후 | Architecture (Components + connections), Architecture delta (Before · Changes · After topology) |
| 전체 스택 개요, 레거시 현황 | High-Level (End-to-end stack on a cluster), IT current-state (Legacy landscape + modernization) |
| 실행 위치 | Deployment (Zones, hosts + artifacts) |
| 의존 관계, 클래스 구조 | Dependency graph (Fan-in, ranks + cycles), UML class (Classes, operations + typed relations) |
| 부모→자식 분해, 조직·담당 | Tree (Parent → children), Org chart (Ownership + routing) |
| 추상화 계층 | Layer stack (Stacked abstractions) |
| 포함 관계 | Nested (Hierarchy by containment) |
| 한 대상의 부품·층을 떼어 보이기(분해도, 조립 순서) | Exploded axonometric (Parts pulled apart on one axis) |
| 한 층·부지를 비스듬히 위에서 본 배치 | Axonometric plan (Rooms and buildings on one plate) |
| 집합 겹침 | Venn (Set overlap) |
| 원인 분석, 강화 고리 | Fishbone (Grouped causes → one effect), Loop / flywheel (Reinforcing cycle + shared hub) |
| 가치 사슬과 진화 단계 | Wardley map (Value chain × evolution) |
| 사용자 경험, 진행 중 작업, 릴리스 범위 | User journey (Stages, actions + sentiment), Kanban (Work in progress by state), Story map (Backbone × release slices) |
| 데이터 모델 | ER / data model (Entities + fields), Database schema (Physical tables + column FKs) |
| 데이터 플랫폼 | Data flow (Role-scoped pipeline steps), Medallion (Multi-tier data storage), DP integration (Sources → core → consumers), DP security matrix (Per-role access permissions) |

계층 구조는 계층의 성격으로 고른다. 쌓인 추상화는 Layer stack, 포함은 Nested, 부모→자식은 Tree, 보고 체계는 Org chart, 순위는 Pyramid, 한 대상을 층·부품으로 분해해 보여 주는 것은 Exploded axonometric이다. 표에 딱 맞는 행이 없으면 diagram-design `SKILL.md`의 타입 선택표를 따른다. 대기열·병목, 정책 통과·실패, 신뢰 경계, 통제 위치, 생애주기처럼 동작이 핵심이면 diagram-design의 semantic pattern을 먼저 고른다.

타입마다 minimal light, minimal dark, full-editorial 세 변형이 있다. 페이지 안 그림은 minimal light를 `<slug>.svg`로, minimal dark를 `<slug>-dark.svg`로 짝지어 넣는다. full-editorial은 제목·설명이 붙은 단독 그림이라, 그림 하나가 문서 전체인 경우에만 쓴다.

- 대표 수치는 첫 요약 문단 바로 뒤에, 그림은 그 그림이 설명하는 문단 바로 뒤에 둔다. 섹션 하나에 그림 하나가 기본이고, 노드가 9개를 넘으면 개요 그림과 상세 그림으로 나눈다.
- 캡션에는 제목 대신 읽어야 할 결론을 쓴다. 예: "실패 18건 중 11건이 설정 드리프트".
- 원문에 있는 사실과 숫자만 쓴다. 새 수치, 추정, 반올림 변경은 하지 않는다.
- 그림이 대신하는 긴 문단은 줄이되 빠지는 정보는 표나 `<details>`로 옮긴다. 원문을 크게 바꿨으면 무엇을 시각화했는지 사용자에게 알린다.

수치 카드는 빈 줄 없이 Markdown에 그대로 쓴다. 빈 줄이 있으면 그 뒤가 Markdown으로 다시 읽힌다. 첫 카드가 대표 수치로 넓어지고 숫자가 강조색이 된다.

```html
<div class="stats">
<div><b>0.9%</b><span>배포 실패율, 2.8%에서</span></div>
<div><b>9분</b><span>평균 배포 시간, 14분에서</span></div>
<div><b>47회</b><span>주간 배포, 31회에서</span></div>
</div>
```

## 그림 (diagram-design)

구조·흐름·관계·수치를 보여 줄 그림은 diagram-design 스킬로 그린다. 스킨은 이 스킬의 `assets/page.html`과 색·글꼴이 같은 diagram-design 프로필 `ai-publish`다(2026-10-13 사용자 결정, `~/.diagram-design/profiles/ai-publish.md`). 아티팩트용 그림에서는 첫 다이어그램 스킨 질문을 다시 하지 않는다.

- diagram-design은 ai-publish의 의존성이다. Claude Code는 `ai-publish@ai-publish`를 설치할 때 이 마켓플레이스에 커밋으로 고정된 `diagram-design@ai-publish`를 함께 설치한다. omp는 의존성을 자동 설치하지 않으므로 `omp plugin install diagram-design@ai-publish`로, Pi는 `pi install https://github.com/cathrynlavery/diagram-design`로 따로 설치한다.
- diagram-design의 `references/style-guide.md` 맨 앞 프로필 헤더가 `slug: ai-publish`가 아니면(스킬 업데이트로 초기화 등) 그 스킬의 `load ai-publish`로 되돌린 뒤 그린다.
- 프로필이 없는 환경에서는 diagram-design 온보딩의 로컬 폴더 방식으로 이 스킬의 `assets/`를 지정해 만들고 `ai-publish`로 저장한다. `page.html`에 없는 역할은 soft `#8b867d`/`#868075`, rule-solid `#c6c4c0`/`rgba(167,162,154,0.25)`이고, link와 제목·콜아웃 글꼴(Instrument Serif)은 기본값을 둔다.

1. diagram-design으로 `<slug>.html`을 만든다. 크기는 기본 `doc-inline`(viewBox 960)이다.
2. SVG를 뽑는다: `python3 <diagram-design 디렉터리>/scripts/export_svg.py <slug>.html <slug>.svg`
3. Markdown에 그림만 있는 한 줄을 넣는다: `![그림 설명](<slug>.svg)`. 변환할 때 SVG가 인라인된 `<figure>`가 되고, 설명은 캡션이 된다.

- 넓은 화면에서는 그림이 본문 폭 밖으로 viewBox 너비까지 넓어지고, 좁은 화면에서는 그림만 가로로 스크롤한다. 글자가 작아지지 않게 SVG는 viewBox 너비 아래로 줄이지 않는다.
- Mermaid 코드 블록은 뷰어에서 그려지지 않는다. 남아 있으면 변환이 멈춘다. diagram-design의 Mermaid 가져오기로 다시 그려 위 2·3단계로 바꾼다.
- 노드 이름·기술 라벨은 페이지와 같은 시스템 글꼴을 쓴다. 제목·콜아웃의 Instrument Serif만 Google Fonts에서 받으며, 뷰어 CSP가 막으면 시스템 serif로 바뀐다.
- 라이트에서는 그림 종이색이 본문과 같아 테두리 없이 이어진다. 다크 모드까지 맞추려면 같은 그림을 diagram-design 다크 변형으로 `<slug>-dark.html`에 그리고 `<slug>-dark.svg`로 뽑아 옆에 둔다. 있으면 다크 모드에서 자동으로 바뀌고, 없으면 밝은 그림이 둥근 카드로 남는다.

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
