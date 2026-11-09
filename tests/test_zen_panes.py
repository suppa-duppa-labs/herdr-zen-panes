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
export const calls = [];
export const panes = () => ["p1", "p2"].map((pane) => ({ pane, tab: "c1", zoomed: false }));
export const focused = () => ({ space: "s1", tab: "c1", pane: "p1" });
export const nextCommand = () => new Promise(() => {});
export const run = (name, args) => {
  calls.push([name, args]);
  return null;
};
"""

COMMANDS = """import { calls } from "./herdr.js";
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

SPLITS = """import { View, div } from "gpui-kit";
import { boxes, neighbour } from "./split.js";
const block = (id, weight) => ({ type: "block", id, ...(weight ? { size: { weight } } : {}) });
const grid = boxes({ type: "row", children: [
  { type: "column", children: [block("lt"), block("lb")] },
  { type: "column", children: [block("rt"), block("rb")] } ] });
const t = boxes({ type: "row", children: [
  { type: "column", children: [block("top"), { type: "row", children: [block("bl"), block("br")] }] } ] });
const uneven = boxes({ type: "row", children: [block("a", 0.25), { type: "column", size: { weight: 0.75 }, children: [block("b"), block("c")] }] });
const expect = (got, want, what) => {
  if (got !== want) throw new Error(`${what}: got ${got}, expected ${want}`);
};
export default class Checked extends View {
  init() {
    %s
  }
  render() {
    return div();
  }
}
"""

COMMAND_CASES = {
    "moves like pane.go when not zoomed": """
      this.handle("go:left", cx);
      expect([["pane.go", { direction: "left" }]]);""",
    "ignores other commands": """
      this.handle("go:sideways", cx);
      this.handle("swap:left", cx);
      expect([]);""",
}

SPLIT_CASES = {
    "finds each neighbour in a grid": """
      expect(neighbour(grid, "lt", "right"), "rt", "lt right");
      expect(neighbour(grid, "lt", "down"), "lb", "lt down");
      expect(neighbour(grid, "rb", "up"), "rt", "rb up");
      expect(neighbour(grid, "rb", "left"), "lb", "rb left");""",
    "finds no neighbour at the edges": """
      for (const [pane, direction] of [["lt", "left"], ["lt", "up"], ["rb", "right"], ["rb", "down"]]) {
        expect(neighbour(grid, pane, direction), null, `${pane} ${direction}`);
      }
      expect(neighbour(t, "top", "up"), null, "top up");
      expect(neighbour(t, "top", "left"), null, "top left");
      expect(neighbour(t, "br", "right"), null, "br right");""",
    "goes up from either bottom pane of a T to the top": """
      expect(neighbour(t, "bl", "up"), "top", "bl up");
      expect(neighbour(t, "br", "up"), "top", "br up");""",
    "goes down from the top of a T to the bottom pane used last": """
      expect(neighbour(t, "top", "down"), "bl", "no history");
      expect(neighbour(t, "top", "down", ["bl", "br"]), "br", "br last");
      expect(neighbour(t, "top", "down", ["br", "bl"]), "bl", "bl last");""",
    "follows split weights": """
      expect(uneven.a.w, 0.25, "a width");
      expect(uneven.b.x, 0.25, "b left");
      expect(neighbour(uneven, "a", "right", ["c"]), "c", "a right");
      expect(neighbour(uneven, "c", "left"), "a", "c left");""",
    "knows no pane outside the tree": """
      expect(neighbour(grid, "nope", "left"), null, "unknown pane");""",
}


def check(folder: Path, home: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "HERDR_APP_HOME": str(home)}
    return subprocess.run([APP, "check", str(folder)], capture_output=True, text=True, timeout=60, env=env)


def test_mod_passes_check_as_shipped(tmp_path):
    folder = shutil.copytree(MOD, tmp_path / "mod")
    result = check(folder, tmp_path / "home")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("case", COMMAND_CASES)
def test_commands(tmp_path, case):
    folder = shutil.copytree(MOD, tmp_path / "mod")
    source, shimmed = re.subn(r'^(import .*) from "herdr";$', r'\1 from "./herdr.js";', (MOD / "main.js").read_text(), flags=re.M)
    assert shimmed == 1
    (folder / "zen.js").write_text(source)
    (folder / "herdr.js").write_text(HERDR_SHIM)
    (folder / "main.js").write_text(COMMANDS % COMMAND_CASES[case])
    result = check(folder, tmp_path / "home")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("case", SPLIT_CASES)
def test_splits(tmp_path, case):
    folder = shutil.copytree(MOD, tmp_path / "mod")
    (folder / "main.js").write_text(SPLITS % SPLIT_CASES[case])
    result = check(folder, tmp_path / "home")
    assert result.returncode == 0, result.stdout + result.stderr
