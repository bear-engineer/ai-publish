#!/usr/bin/env node
// 발행 입력 고정과 영수증 기록. 형식과 규칙은 ../references/publish-flow.md 4절.
//   freeze <정본.md> <출력 디렉터리>   정본과 그 정본이 참조하는 로컬 자산을 복사하고 input.json을 쓴다
//   tree <Site 프로젝트>               프로젝트 파일 목록의 입력 digest를 낸다(복사하지 않음)
//   merge <영수증> <정본 이름> <대상> <항목 JSON>   대상 항목 하나만 합친다
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, statSync, writeFileSync } from "node:fs";
import { basename, dirname, isAbsolute, join, normalize, sep } from "node:path";

const sha = (buf) => createHash("sha256").update(buf).digest("hex");
// 경로 순서와 무관한 입력 digest. 경로·내용 중 하나라도 바뀌면 달라진다.
const digest = (files) => sha(JSON.stringify(Object.keys(files).sort().map((f) => [f, files[f]])));
const posix = (p) => p.split(sep).join("/");

function freeze(doc, out) {
  const dir = dirname(doc);
  const md = readFileSync(doc);
  const refs = new Set();
  for (const [, href] of md.toString("utf8").matchAll(/!\[[^\]]*\]\(\s*<?([^)\s>]+)/g)) {
    if (/^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith("#")) continue; // http·data·visualize 등은 로컬 파일이 아니다
    const rel = normalize(decodeURI(href.split(/[?#]/)[0]));
    if (isAbsolute(rel) || rel.split(sep)[0] === "..") throw new Error(`${href}: 정본 폴더 밖 자산이다. 정본 폴더 안으로 옮긴다`);
    refs.add(rel);
    const dark = rel.replace(/\.svg$/i, "-dark.svg"); // marked.config.mjs가 함께 읽는 다크 짝
    if (dark !== rel && existsSync(join(dir, dark))) refs.add(dark);
  }
  mkdirSync(out, { recursive: true });
  const files = { [basename(doc)]: sha(md) };
  writeFileSync(join(out, basename(doc)), md);
  for (const rel of refs) {
    const buf = readFileSync(join(dir, rel)); // 한 번 읽은 바이트를 복사하고 해시한다
    mkdirSync(dirname(join(out, rel)), { recursive: true });
    writeFileSync(join(out, rel), buf);
    files[posix(rel)] = sha(buf);
  }
  const manifest = { source: basename(doc), sha256: files[basename(doc)], input: digest(files), files };
  writeFileSync(join(out, "input.json"), JSON.stringify(manifest, null, 2) + "\n");
  return { sha256: manifest.sha256, input: manifest.input, files: Object.keys(files).length };
}

const SKIP = /^(\.git|\.openai|node_modules)(\/|$)/; // .openai/hosting.json은 Sites가 배포 때 쓴다

function walk(root, rel = "") {
  return readdirSync(join(root, rel), { withFileTypes: true }).flatMap((e) => {
    const p = rel ? `${rel}/${e.name}` : e.name;
    if (SKIP.test(p)) return [];
    return e.isDirectory() ? walk(root, p) : [p];
  });
}

function tree(root) {
  let list;
  try {
    const out = execFileSync("git", ["-C", root, "ls-files", "-co", "--exclude-standard", "-z"], { stdio: ["ignore", "pipe", "ignore"] });
    list = out.toString("utf8").split("\0").filter(Boolean);
  } catch {
    list = walk(root); // git 저장소가 아니면 전부(.git·.openai·node_modules 제외)
  }
  const files = {};
  for (const f of list.filter((f) => !SKIP.test(f)).sort()) {
    const p = join(root, f);
    if (existsSync(p) && statSync(p).isFile()) files[f] = sha(readFileSync(p));
  }
  return { sha256: null, input: digest(files), files: Object.keys(files).length };
}

function merge(file, source, target, entry) {
  const r = existsSync(file) ? JSON.parse(readFileSync(file, "utf8")) : { source, targets: {} };
  const next = JSON.parse(entry);
  for (const k of ["id", "url", "version"]) if (next[k] == null) delete next[k]; // null은 "모름"이다. 알던 값을 지우지 않는다
  r.targets[target] = { ...r.targets[target], ...next, at: new Date().toISOString() };
  writeFileSync(file + ".tmp", JSON.stringify(r, null, 2) + "\n");
  renameSync(file + ".tmp", file);
  return r.targets[target];
}

const [cmd, ...args] = process.argv.slice(2);
const run = { freeze, tree, merge }[cmd];
if (!run) {
  console.error("usage: receipt.mjs freeze <doc.md> <outdir> | tree <project> | merge <receipt> <source> <target> <entry-json>");
  process.exit(2);
}
console.log(JSON.stringify(run(...args)));
