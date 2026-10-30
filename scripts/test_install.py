"""install.py 계획 규칙 검사. 실행: python3 -m unittest discover -s scripts -v"""
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import install  # noqa: E402

REPO = Path("/repo/ai-publish")


def kinds(acts):
    return [kind for kind, _, _ in acts]


class CodexLinks(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.skills = self.root / "skills"
        self.src = [self.root / "repo" / n for n in ("chatgpt-publish", "claude-artifact-publish")]
        for s in self.src:
            s.mkdir(parents=True)

    def test_빈_디렉터리에_링크를_걸고_다시_실행하면_바꿀_것이_없다(self):
        install.apply(install.plan_codex(self.skills, self.src))
        for s in self.src:
            self.assertEqual((self.skills / s.name).resolve(), s.resolve())
        self.assertEqual(kinds(install.plan_codex(self.skills, self.src)), ["ok", "ok", "warn"])

    def test_다른_곳을_가리키는_링크와_실제_디렉터리는_거부하고_건드리지_않는다(self):
        self.skills.mkdir()
        (self.skills / "chatgpt-publish").symlink_to(self.root / "elsewhere")
        (self.skills / "claude-artifact-publish").mkdir()
        acts = install.plan_codex(self.skills, self.src)
        self.assertEqual(kinds(acts)[:2], ["refuse", "refuse"])
        install.apply(acts)
        self.assertEqual(os.readlink(self.skills / "chatgpt-publish"), str(self.root / "elsewhere"))
        self.assertFalse((self.skills / "claude-artifact-publish").is_symlink())

    def test_dry_run은_링크를_만들지_않고_거부가_있으면_종료_코드_1(self):
        os.environ["CODEX_HOME"] = str(self.root)
        self.addCleanup(os.environ.pop, "CODEX_HOME")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(install.main(["codex", "--dry-run"]), 0)
        self.assertFalse(self.skills.exists())
        self.skills.mkdir()
        (self.skills / "chatgpt-publish").mkdir()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(install.main(["codex"]), 1)
        self.assertFalse((self.skills / "claude-artifact-publish").exists())


class MarketplacePlugins(unittest.TestCase):
    def plan(self, markets, installed, deps=()):
        return install.plan_marketplace("omp", markets, installed, "0.4.0", REPO, deps, ["upgrade"])

    def test_마켓플레이스와_플러그인이_없으면_추가하고_설치한다(self):
        acts = self.plan({}, {}, (install.DEP_ID,))
        self.assertEqual([a[2] for a in acts], [
            ["omp", "plugin", "marketplace", "add", str(REPO)],
            ["omp", "plugin", "install", install.PLUGIN_ID],
            ["omp", "plugin", "install", install.DEP_ID],
        ])

    def test_다른_원본을_가리키는_마켓플레이스는_거부하고_아무것도_실행하지_않는다(self):
        for src in ("/other/checkout", "bear-engineer/ai-publish"):
            self.assertEqual(kinds(self.plan({install.NAME: src}, {})), ["refuse"])

    def test_버전이_다르면_갱신하고_같으면_그대로_둔다(self):
        markets = {install.NAME: str(REPO)}
        old = self.plan(markets, {install.PLUGIN_ID: "0.3.2"})
        self.assertEqual(old[1][2], ["omp", "plugin", "upgrade", install.PLUGIN_ID])
        self.assertEqual(kinds(self.plan(markets, {install.PLUGIN_ID: "0.4.0"})), ["ok", "ok"])

    def test_다른_마켓플레이스의_같은_플러그인은_경고한다(self):
        acts = self.plan({install.NAME: str(REPO)}, {install.PLUGIN_ID: "0.4.0", "ai-publish@other": "0.1.0"})
        self.assertEqual(kinds(acts)[-1], "warn")


if __name__ == "__main__":
    unittest.main()
