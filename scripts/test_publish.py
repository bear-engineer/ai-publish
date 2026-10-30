"""발행 절차 오프라인 회귀. 실행: python3 -m unittest discover -s scripts -v (node·zsh·git 필요, 네트워크 없음)"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "plugins/ai-publish/skills/claude-artifact-publish"
RECEIPT = SKILL / "scripts/receipt.mjs"


def receipt(*args, check=True):
    p = subprocess.run(["node", str(RECEIPT), *map(str, args)], capture_output=True, text=True)
    if check and p.returncode:
        raise AssertionError(p.stderr)
    return p


@unittest.skipUnless(shutil.which("node"), "node 필요")
class Receipt(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.d = Path(tmp.name)

    def test_결과를_모르는_갱신이_null을_돌려줘도_알던_ID_URL_버전은_남는다(self):
        f = self.d / "report.publish.json"
        receipt("merge", f, "report.md", "pages", '{"state":"verified","sha256":"a","id":"known-page","url":"https://x/p","version":"7"}')
        receipt("merge", f, "report.md", "artifact", '{"state":"verified","id":"art-1"}')
        receipt("merge", f, "report.md", "pages", '{"state":"unknown","id":null,"url":null,"version":null,"evidence":"timeout"}')
        t = json.loads(f.read_text())["targets"]
        self.assertEqual((t["pages"]["state"], t["pages"]["id"], t["pages"]["url"], t["pages"]["version"]),
                         ("unknown", "known-page", "https://x/p", "7"))
        self.assertEqual(t["artifact"]["id"], "art-1")
        self.assertFalse(Path(str(f) + ".tmp").exists())

    def freeze(self, out="out"):
        return json.loads(receipt("freeze", self.d / "doc/report.md", self.d / out).stdout)

    def test_그림만_바뀌어도_input은_달라지고_정본_sha256은_그대로다(self):
        (self.d / "doc/figs").mkdir(parents=True)
        (self.d / "doc/report.md").write_text("# T\n\n![추이](figs/trend.svg)\n\n![외부](https://e.x/a.png)\n")
        (self.d / "doc/figs/trend.svg").write_text("OLD")
        (self.d / "doc/figs/trend-dark.svg").write_text("DARK")
        a = self.freeze("a")
        files = json.loads((self.d / "a/input.json").read_text())["files"]
        self.assertEqual(sorted(files), ["figs/trend-dark.svg", "figs/trend.svg", "report.md"])
        self.assertEqual((self.d / "a/figs/trend.svg").read_text(), "OLD")
        (self.d / "doc/figs/trend.svg").write_text("NEW")
        b = self.freeze("b")
        self.assertEqual(a["sha256"], b["sha256"])
        self.assertNotEqual(a["input"], b["input"])

    def test_정본_폴더_밖_자산은_고정하지_않고_실패한다(self):
        (self.d / "doc").mkdir()
        (self.d / "doc/report.md").write_text("![x](../x.svg)\n")
        self.assertNotEqual(receipt("freeze", self.d / "doc/report.md", self.d / "o", check=False).returncode, 0)

    def test_Site_입력은_프로젝트_파일로_정하고_배포_기록과_의존성_폴더는_뺀다(self):
        site = self.d / "site"
        (site / "node_modules/x").mkdir(parents=True)
        (site / ".openai").mkdir()
        (site / "index.html").write_text("v1")
        before = json.loads(receipt("tree", site).stdout)
        (site / ".openai/hosting.json").write_text("{}")
        (site / "node_modules/x/i.js").write_text("x")
        self.assertEqual(json.loads(receipt("tree", site).stdout)["input"], before["input"])
        (site / "index.html").write_text("v2")
        after = json.loads(receipt("tree", site).stdout)
        self.assertNotEqual(after["input"], before["input"])
        self.assertIsNone(after["sha256"])

    @unittest.skipUnless(shutil.which("git"), "git 필요")
    def test_git_프로젝트는_gitignore된_빌드_산출물을_입력에서_뺀다(self):
        site = self.d / "gsite"
        site.mkdir()
        subprocess.run(["git", "init", "-q", str(site)], check=True)
        (site / ".gitignore").write_text("dist/\n")
        (site / "index.html").write_text("v1")
        before = json.loads(receipt("tree", site).stdout)
        (site / "dist").mkdir()
        (site / "dist/out.js").write_text("built")
        self.assertEqual(json.loads(receipt("tree", site).stdout)["input"], before["input"])


QUICK_VALIDATE = Path.home() / ".codex/skills/.system/skill-creator/scripts/quick_validate.py"


@unittest.skipUnless(QUICK_VALIDATE.is_file(), "Codex skill-creator 필요")
class CodexSkillValidation(unittest.TestCase):
    def test_Codex에_링크하는_두_스킬이_Codex_검증을_통과한다(self):
        for skill in sorted((REPO / "plugins/ai-publish/skills").iterdir()):
            r = subprocess.run(["python3", str(QUICK_VALIDATE), str(skill)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{skill.name}: {r.stdout}{r.stderr}")


@unittest.skipUnless(shutil.which("zsh"), "zsh 필요")
class ZshInvocation(unittest.TestCase):
    def test_문서의_artifact_CLI_호출이_zsh에서_인자_그대로_npx에_전달된다(self):
        text = (SKILL / "SKILL.md").read_text()
        self.assertEqual(len(re.findall(r"\$A\b", text)), 0, 'A="npx …"; $A 형태는 zsh에서 명령 하나로 읽힌다')
        fn = re.search(r"^A\(\) \{.*\}", text, re.M).group(0)
        with tempfile.TemporaryDirectory() as bindir:
            stub = Path(bindir) / "npx"
            stub.write_text('#!/bin/sh\nprintf "%s|" "$@"\n')
            stub.chmod(0o755)
            env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}")
            out = subprocess.run(["zsh", "-f", "-c", f'{fn}\nA read "id 1" --content --output json'],
                                 capture_output=True, text=True, env=env)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, "-y|claude-artifacts@0.1.14|read|id 1|--content|--output|json|")


if __name__ == "__main__":
    unittest.main()
