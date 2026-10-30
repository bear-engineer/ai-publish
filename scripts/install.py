#!/usr/bin/env python3
"""ai-publish 설치기. Codex는 사용자 스킬 링크, Claude Code·omp는 이 checkout을 원본으로 하는 마켓플레이스 플러그인.

    python3 scripts/install.py codex claude omp --dry-run

여러 번 실행해도 같은 결과다. 지우거나 덮어쓰지 않는다. 다른 곳을 가리키는 링크, 링크가 아닌 기존 디렉터리,
다른 원본을 가리키는 `ai-publish` 마켓플레이스가 있으면 그 대상은 아무것도 바꾸지 않고 종료 코드 1로 끝난다.
npx 설치는 실행하지 않는다.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "ai-publish"
NAME = "ai-publish"
PLUGIN_ID = f"{NAME}@{NAME}"
DEP_ID = f"diagram-design@{NAME}"


def plugin_version():
    return json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]


def skill_dirs():
    return sorted(p for p in (PLUGIN / "skills").iterdir() if (p / "SKILL.md").is_file())


def plan_codex(skills_dir, sources):
    """Codex 사용자 스킬 디렉터리에 스킬 링크를 건다. 행동은 (종류, 설명, 인자) 튜플."""
    acts = []
    for src in sources:
        dest = skills_dir / src.name
        if dest.is_symlink():
            raw = os.readlink(dest)
            if (dest.parent / raw).resolve() == src.resolve():  # 절대 경로 raw면 parent가 무시된다
                acts.append(("ok", f"{dest} -> {src}", None))
            else:
                acts.append(("refuse", f"{dest}는 다른 곳({raw})을 가리키는 링크다. 직접 정리한 뒤 다시 실행한다", None))
        elif dest.exists():
            acts.append(("refuse", f"{dest}가 링크가 아닌 파일·디렉터리로 있다(복사 설치?). 직접 정리한 뒤 다시 실행한다", None))
        else:
            acts.append(("link", f"{dest} -> {src}", (src, dest)))
    if not (skills_dir / "diagram-design").exists():
        acts.append(("warn", f"{skills_dir / 'diagram-design'} 없음. 그림을 쓰려면 diagram-design 스킬을 따로 둔다", None))
    return acts


def plan_marketplace(cli, markets, installed, version, repo, deps, update_cmd):
    """markets: 마켓플레이스 이름 -> 원본(경로·저장소), installed: 플러그인 id -> 버전."""
    acts = []
    src = markets.get(NAME)
    if src is None:
        acts.append(("run", f"마켓플레이스 {NAME} 추가 ({repo})", [cli, "plugin", "marketplace", "add", str(repo)]))
    elif not Path(src).expanduser().is_absolute() or Path(src).expanduser().resolve() != repo.resolve():
        return [("refuse", f"마켓플레이스 {NAME}가 다른 원본({src})을 가리킨다. 이 checkout으로 바꾸려면 직접 정리한다", None)]
    else:
        acts.append(("ok", f"마켓플레이스 {NAME} -> {src}", None))
    have = installed.get(PLUGIN_ID)
    if have is None:
        acts.append(("run", f"{PLUGIN_ID} 설치", [cli, "plugin", "install", PLUGIN_ID]))
    elif have != version:
        acts.append(("run", f"{PLUGIN_ID} {have} -> {version}", [cli, "plugin", *update_cmd, PLUGIN_ID]))
    else:
        acts.append(("ok", f"{PLUGIN_ID} {have}", None))
    for dep in deps:
        if dep in installed:
            acts.append(("ok", f"{dep} {installed[dep]}", None))
        else:
            acts.append(("run", f"{dep} 설치(의존성 자동 설치 없음)", [cli, "plugin", "install", dep]))
    for pid in sorted(installed):
        if pid.startswith(f"{NAME}@") and pid != PLUGIN_ID:
            acts.append(("warn", f"{pid}도 설치돼 있다. 같은 스킬이 두 벌이 된다", None))
    return acts


def cli_json(argv):
    return json.loads(subprocess.run(argv, check=True, capture_output=True, text=True).stdout)


def gather_claude():
    markets = {m["name"]: m.get("path") or m.get("repo") or m.get("url") or "?" for m in cli_json(["claude", "plugin", "marketplace", "list", "--json"])}
    installed = {p["id"]: p.get("version") for p in cli_json(["claude", "plugin", "list", "--json"])}
    return markets, installed


def gather_omp():
    # ponytail: omp 18.13의 marketplace list는 --json을 무시하고 "  이름  원본" 줄만 낸다. JSON이 생기면 그것으로 바꾼다.
    text = subprocess.run(["omp", "plugin", "marketplace", "list"], check=True, capture_output=True, text=True).stdout
    markets = dict(m.groups() for m in re.finditer(r"^\s+(\S+)\s+(\S.*?)\s*$", text, re.M))
    installed = {m["id"]: (m["entries"] or [{}])[0].get("version") for m in cli_json(["omp", "plugin", "list", "--json"])["marketplace"]}
    return markets, installed


def plan(target):
    if target == "codex":
        home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
        return plan_codex(home / "skills", skill_dirs())
    if not shutil.which(target):
        return [("warn", f"{target} CLI가 없어 건너뛴다", None)]
    version = plugin_version()
    if target == "claude":
        acts = plan_marketplace("claude", *gather_claude(), version, REPO, (), ["update"])
        user_skills = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "skills"
        for src in skill_dirs():
            if os.path.lexists(user_skills / src.name):
                acts.append(("warn", f"{user_skills / src.name}가 있어 플러그인 스킬과 겹친다", None))
        return acts
    return plan_marketplace("omp", *gather_omp(), version, REPO, (DEP_ID,), ["upgrade"])


def apply(acts):
    for kind, _, arg in acts:
        if kind == "link":
            src, dest = arg
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.symlink_to(src, target_is_directory=True)
        elif kind == "run":
            subprocess.run(arg, check=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("targets", nargs="+", choices=["codex", "claude", "omp"])
    ap.add_argument("--dry-run", action="store_true", help="계획만 보여 주고 바꾸지 않는다")
    args = ap.parse_args(argv)
    refused = False
    for target in dict.fromkeys(args.targets):
        acts = plan(target)
        blocked = any(kind == "refuse" for kind, _, _ in acts)
        refused |= blocked
        for kind, desc, arg in acts:
            cmd = f"  $ {' '.join(arg)}" if kind == "run" else ""
            print(f"[{target}] {kind}: {desc}{cmd}")
        if blocked:
            print(f"[{target}] 거부 항목이 있어 이 대상은 바꾸지 않았다")
        elif args.dry_run:
            print(f"[{target}] dry-run: 바꾸지 않았다")
        else:
            apply(acts)
    if any(t in args.targets for t in ("claude", "omp")) and not args.dry_run:
        print("Claude Code·omp는 새 세션(또는 재시작)부터 바뀐 플러그인을 읽는다.")
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
