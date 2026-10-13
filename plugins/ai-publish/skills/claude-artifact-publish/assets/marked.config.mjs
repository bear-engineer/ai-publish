// `marked -c` 설정. SKILL.md의 "문서 발행" 명령이 marked@18.1.1·marked-cjk-friendly@0.1.2와 함께 쓴다.
// 1. CommonMark는 `**60%**가`, `**"용어"**는`처럼 문장부호로 끝난 강조 뒤에 한글이 붙으면 `**`를 그대로 출력한다.
//    marked-cjk-friendly가 이 경우를 강조로 읽는다.
// 2. `![캡션](그림.svg)`만 있는 문단은 SVG를 인라인한 <figure>로 바꾼다. 아티팩트는 단일 파일이라 외부 그림을 못 읽는다.
// 3. mermaid 코드 블록은 뷰어에서 그려지지 않으므로 변환을 멈춘다.
// 4. YAML frontmatter는 본문에 섞이지 않게 yaml 코드 블록으로 옮긴다.
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

// 확장은 marked와 같은 npx 임시 설치에 있으므로 이 파일이 아니라 marked 실행 파일 기준으로 찾는다.
const extensionPath = createRequire(process.argv[1]).resolve("marked-cjk-friendly");
const { default: markedCjkFriendly } = await import(pathToFileURL(extensionPath).href);

const escapeHtml = (text) => text.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

function diagramFigure({ href, text }) {
  const svg = readFileSync(decodeURI(href), "utf8").replace(/^<\?xml[^>]*>\s*/, "");
  const width = /viewBox="[\d.]+ [\d.]+ ([\d.]+) [\d.]+"/.exec(svg)?.[1];
  if (!width) throw new Error(`${href}: viewBox가 없다. diagram-design의 export_svg.py 출력을 쓴다.`);
  const caption = escapeHtml(text);
  return `<figure class="diagram" style="--w:${width}px"><div class="diagram-container" tabindex="0" role="region" aria-label="${caption}">${svg}</div><figcaption>${caption}</figcaption></figure>\n`;
}

export default (marked) =>
  marked.use(markedCjkFriendly(), {
    hooks: {
      preprocess: (markdown) => markdown.replace(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/, "```yaml\n$1\n```\n"),
    },
    renderer: {
      paragraph({ tokens }) {
        const [only] = tokens;
        if (tokens.length === 1 && only.type === "image" && /\.svg$/i.test(only.href)) return diagramFigure(only);
        return false;
      },
      code({ lang }) {
        if (lang === "mermaid") {
          throw new Error("mermaid 블록은 아티팩트에서 그려지지 않는다. diagram-design으로 다시 그려 ![캡션](그림.svg)로 넣는다.");
        }
        return false;
      },
    },
  });
