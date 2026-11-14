import { View, div } from "gpui-kit";
import { appHome, exec, focused, nextCommand, panes, props, readTextFile, run, spaces, theme } from "herdr";
import { boxes, neighbour } from "./split.js";

const DIRECTIONS = ["left", "right", "up", "down"];
const DOCS = 'cat "${XDG_STATE_HOME:-$HOME/.local/state}/herdr-core/${HC_SESSION:-default}/docs.json"';
const MAP = { width: 96, height: 60, gap: 4, pad: 10, shown: 1200 };

async function readJson(read) {
  try {
    return JSON.parse(await read());
  } catch {
    return null;
  }
}

export default class ZenPanes extends View {
  init(_props, cx) {
    this.pending = null;
    this.layout = null;
    this.loading = null;
    this.shownFor = null;
    this.flashes = 0;
    this.lastZoomed = null;
    cx.spawn(async (cx) => {
      for (;;) {
        await this.handle(await nextCommand(), cx);
      }
    });
  }

  async handle(command, cx) {
    const [name, direction] = command.split(":");
    if (name !== "go" || !DIRECTIONS.includes(direction)) return;
    const zoomed = this.zoomed();
    if (!zoomed) {
      run("pane.go", { direction });
      return;
    }
    const layout = await this.load(zoomed.tab);
    if (!layout) {
      this.pending = { tab: zoomed.tab, direction };
      run("pane.zoom", { pane: zoomed.pane });
      cx.notify();
      return;
    }
    const view = await readJson(() => readTextFile(`${appHome()}/view.json`));
    if (this.zoomed()?.pane !== zoomed.pane) return;
    const target = neighbour(layout.boxes, zoomed.pane, direction, view?.tabs?.[zoomed.tab]?.before ?? []);
    if (!target) {
      this.flash(zoomed.pane, cx);
      cx.notify();
      return;
    }
    run("pane.zoom", { pane: target });
    run("pane.focus", { pane: target });
  }

  zoomed() {
    const all = panes();
    const tab = all.find((p) => p.pane === focused()?.pane)?.tab;
    return tab ? all.find((p) => p.tab === tab && p.zoomed) ?? null : null;
  }

  async load(tab) {
    const machine = spaces().find((s) => s.tabs.some((t) => t.id === tab))?.machine ?? null;
    const prefix = machine ? `${machine}/` : "";
    const docs = await readJson(async () => (await exec("sh", ["-c", DOCS], machine ? { on: machine } : {})).stdout);
    const root = docs?.["herdr-app"]?.value?.spaces
      ?.flatMap((s) => s.tabs ?? [])
      .find((t) => prefix + t.id === tab)?.root;
    if (!root) return null;
    const all = Object.fromEntries(Object.entries(boxes(root)).map(([id, box]) => [prefix + id, box]));
    const ids = panes().filter((p) => p.tab === tab).map((p) => p.pane);
    if (ids.length !== Object.keys(all).length || !ids.every((id) => all[id])) return null;
    this.layout = { tab, key: ids.join(), boxes: all };
    return this.layout;
  }

  current(tab, cx) {
    const key = panes().filter((p) => p.tab === tab).map((p) => p.pane).join();
    if (this.layout?.tab === tab && this.layout.key === key) return this.layout;
    if (this.loading !== key) {
      this.loading = key;
      cx.spawn(async (cx) => {
        if (!(await this.load(tab))) {
          await cx.sleep(1000);
          this.loading = null;
        }
        cx.notify();
      });
    }
    return null;
  }

  flash(pane, cx) {
    const flash = ++this.flashes;
    this.shownFor = pane;
    cx.spawn(async (cx) => {
      await cx.sleep(MAP.shown);
      if (flash !== this.flashes) return;
      this.shownFor = null;
      cx.notify();
    });
  }

  render(cx) {
    const move = this.pending;
    if (move && !panes().some((p) => p.tab === move.tab && p.zoomed)) {
      this.pending = null;
      if (focused()?.tab === move.tab) {
        run("pane.go", { direction: move.direction });
        run("pane.zoom", {});
      }
    }
    const zoomed = this.zoomed();
    if ((zoomed?.pane ?? null) !== this.lastZoomed) {
      this.lastZoomed = zoomed?.pane ?? null;
      if (zoomed) this.flash(zoomed.pane, cx);
    }
    if (props()?.map === false || !zoomed || this.shownFor !== zoomed.pane) return div();
    const layout = this.current(zoomed.tab, cx);
    if (!layout) return div();
    const t = theme();
    const { width, height, gap, pad } = MAP;
    return div().relative().w(width + 2 * pad).h(height + 2 * pad)
      .rounded(12).bg(t.popover).border(1).border_color(t.border)
      .children(Object.entries(layout.boxes).map(([id, b]) =>
        div().absolute()
          .left(pad - 1 + b.x * width + gap / 2).top(pad - 1 + b.y * height + gap / 2)
          .w(Math.max(b.w * width - gap, 1)).h(Math.max(b.h * height - gap, 1))
          .rounded(4).bg(id === zoomed.pane ? t.accent : t.dim)));
  }
}
