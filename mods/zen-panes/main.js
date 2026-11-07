import { View, div } from "gpui-kit";
import { focused, nextCommand, panes, run } from "herdr";

const DIRECTIONS = ["left", "right", "up", "down"];

export default class ZenPanes extends View {
  init(_props, cx) {
    this.pending = null;
    cx.spawn(async (cx) => {
      for (;;) {
        this.handle(await nextCommand(), cx);
      }
    });
  }

  handle(command, cx) {
    const [name, direction] = command.split(":");
    if (name !== "go" || !DIRECTIONS.includes(direction)) return;
    const all = panes();
    const tab = all.find((p) => p.pane === focused()?.pane)?.tab;
    const zoomed = tab && all.find((p) => p.tab === tab && p.zoomed);
    if (!zoomed) {
      run("pane.go", { direction });
      return;
    }
    this.pending = { tab, direction };
    run("pane.zoom", { pane: zoomed.pane });
    cx.notify();
  }

  render() {
    const move = this.pending;
    if (move && !panes().some((p) => p.tab === move.tab && p.zoomed)) {
      this.pending = null;
      if (focused()?.tab === move.tab) {
        run("pane.go", { direction: move.direction });
        run("pane.zoom", {});
      }
    }
    return div();
  }
}
