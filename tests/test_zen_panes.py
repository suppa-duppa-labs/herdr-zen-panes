import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

MOD = Path(__file__).resolve().parents[1] / "mods" / "zen-panes"
APP = os.environ.get("HERDR_APP") or shutil.which("herdr-app")

pytestmark = pytest.mark.skipif(not APP, reason="set HERDR_APP to the herdr-app binary")

HERDR_SHIM = """export * from "herdr";
export const state = { focused: { space: "s1", tab: "c1", pane: "p1" }, zoomed: null };
export const calls = [];
export const panes = () => ["p1", "p2", "p3"].map((pane) => ({ pane, tab: "c1", zoomed: state.zoomed === pane }));
export const focused = () => state.focused;
export const nextCommand = () => new Promise(() => {});
export const run = (name, args) => {
  calls.push([name, args]);
  return null;
};
"""

WRAPPER = """import { calls, state } from "./herdr.js";
import ZenPanes from "./zen.js";
const expect = (want) => {
  const got = JSON.stringify(calls);
  if (got !== JSON.stringify(want)) throw new Error(`ran ${got}, expected ${JSON.stringify(want)}`);
  calls.length = 0;
};
export default class Checked extends ZenPanes {
  init(props, cx) {
    super.init(props, cx);
    %s
  }
}
"""

CASES = {
    "moves like pane.go when not zoomed": """
      this.handle("go:left", cx);
      expect([["pane.go", { direction: "left" }]]);
      this.render(cx);
      expect([]);""",
    "unzooms, then moves and zooms once the tab is unzoomed": """
      state.zoomed = "p1";
      this.handle("go:right", cx);
      expect([["pane.zoom", { pane: "p1" }]]);
      this.render(cx);
      expect([]);
      state.zoomed = null;
      this.render(cx);
      expect([["pane.go", { direction: "right" }], ["pane.zoom", {}]]);
      this.render(cx);
      expect([]);""",
    "unzooms the zoomed pane even when another one has focus": """
      state.zoomed = "p2";
      this.handle("go:down", cx);
      expect([["pane.zoom", { pane: "p2" }]]);""",
    "ignores other commands": """
      this.handle("go:sideways", cx);
      this.handle("swap:left", cx);
      expect([]);""",
    "drops the move when another tab is shown before the unzoom lands": """
      state.zoomed = "p1";
      this.handle("go:up", cx);
      expect([["pane.zoom", { pane: "p1" }]]);
      state.zoomed = null;
      state.focused = { space: "s1", tab: "c2", pane: "p9" };
      this.render(cx);
      expect([]);""",
}


def check(folder: Path, home: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "HERDR_APP_HOME": str(home)}
    return subprocess.run([APP, "check", str(folder)], capture_output=True, text=True, timeout=60, env=env)


def test_mod_passes_check_as_shipped(tmp_path):
    folder = shutil.copytree(MOD, tmp_path / "mod")
    result = check(folder, tmp_path / "home")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("case", CASES)
def test_commands(tmp_path, case):
    folder = shutil.copytree(MOD, tmp_path / "mod")
    source, shimmed = re.subn(r'^(import .*) from "herdr";$', r'\1 from "./herdr.js";', (MOD / "main.js").read_text(), flags=re.M)
    assert shimmed == 1
    (folder / "zen.js").write_text(source)
    (folder / "herdr.js").write_text(HERDR_SHIM)
    (folder / "main.js").write_text(WRAPPER % CASES[case])
    result = check(folder, tmp_path / "home")
    assert result.returncode == 0, result.stdout + result.stderr
