# Zen panes

Moving between panes keeps zoom on: with a pane zoomed, `zen-panes.go:<direction>` zooms the pane next to it in that direction, straight from one zoomed pane to the next.
With no pane that way it does nothing; with nothing zoomed it is `pane.go`.

![Zen panes](preview.png)

**What you see:**

- With a pane zoomed, a move key swaps the zoomed pane for its neighbour in that direction; the tab never unzooms.
- A move with no pane that way changes nothing: zoom and focus stay as they are.
- For 1.2 seconds after zoom lands on a pane, or after a move with no pane that way, a small map of the tab shows in the middle of the window: each pane a rounded block in `dim`, the zoomed one in `accent`, on a `popover` card with a `border` edge and 12 px corners.
- With nothing zoomed, the move key focuses the neighbour as `pane.go` does, and no map shows.

**How it behaves:**

- `zen-panes.go:left`, `:right`, `:up` and `:down`, bound in `keys.json` like any `<mod>.<command>`.
- Not zoomed: runs `pane.go {direction}`, so its errors (a focused layout terminal block) show as `pane.go`'s.
- Zoomed: reads the tab's split tree, finds the neighbour, then runs `pane.zoom {pane: neighbour}` and `pane.focus {pane: neighbour}`.
  `pane.zoom` on another pane of a zoomed tab moves the zoom there directly.
- The split tree comes from herdr-core's `docs.json` (`${XDG_STATE_HOME:-$HOME/.local/state}/herdr-core/${HC_SESSION:-default}/docs.json`), read with `exec` on the tab's machine; the tab is `spaces[].tabs[]` under `herdr-app.value`, with ids that get the `<machine>/` prefix the app uses for other machines.
- Each `row` splits its box across, each `column` down, by the children's `size.weight` (1 when missing), into boxes in a unit square.
- The neighbour is chosen as `pane.go` chooses: the boxes that overlap on the other axis and start at or past that edge, the nearest first, then the one focused most recently (the tab's `before` list in `view.json`), then the one sharing the longest edge.
- If the tree can't be read, or doesn't hold exactly the tab's panes yet (a split the app hasn't saved), the move falls back to unzoom, then `pane.go` and `pane.zoom` on the first render that sees the tab unzoomed.
- The zoomed pane is found by the focused pane's tab in `panes()`, so it works from terminal panes and mod panes alike.
- Any other command is ignored.
- `props.map: false` (set in `mod.json`'s `overlay.props`) turns the map off.

**Built from:**

- One mod, `zen-panes`, `place: "none"`, whose `mod.json` `overlay` is `{ kind: "window", key: "zen-panes", keep: true, frame: "none", props: { map: true } }`: `mod.open {name: "zen-panes"}` opens it as a kept window of the shown layout, which Herdr reopens on every start and whenever that layout is shown again; `mod.open` again closes it.
- `split.js`: `boxes(root)` and `neighbour(boxes, from, direction, history)`.
- `main.js`: `nextCommand()` in a loop started from `init`, `focused()`, `panes()`, `spaces()`, `exec`, `readTextFile`, `appHome()`, `run("pane.go" | "pane.zoom" | "pane.focus")`, `theme()`; `render()` draws the map or an empty `div()`, which gives the window no size.

**Watch out:**

- `pane.go` finds neighbours from the panes' on-screen bounds, among the panes shown; while zoomed only the zoomed pane is shown, so `pane.go` does nothing.
- Mods get no pane geometry and no split tree from the app (`panes()` has none, `layout()` is the window's layout, not the tabs'), and `hc` has no command for `doc.get`, so the core's state file is the only place to read the tree.
- A window's spot can't follow a pane: it is where it was dropped, else centred, and clamped to stay 48 px on screen. That is why the map shows centred for a moment instead of on the zoomed pane's edges.
- A window covers what's under it while it has a size, so the map shows only briefly and is empty the rest of the time.
- `cx.notify()` is not allowed during `render`.
- `<mod>.<command>` reaches shown copies only, and overlays count as shown; a window overlay needs no layout edit, so it works in shipped layouts too.
- Windows close on a layout switch; kept ones come back only with the layout they were opened in.
- A `terminal` key binding beats the same key in `global`: the move keys must replace `pane.go` in whichever section holds it.

**Done when:**

- `herdr-app check mods/zen-panes` passes.
- After `herdr-app do mod.open --name zen-panes`, `herdr-app status` lists `zen-panes` under overlays and it is still listed after a restart.
- In a tab split into a 2 by 2 grid with one pane zoomed, each move key zooms the neighbour that way and focuses it, and the map shows it lit.
- In a T (one pane on top, two below), moving down from the top zooms the bottom pane used last.
- A move toward an edge with no pane leaves `view.json` unchanged.
- With nothing zoomed, a move key focuses the neighbour and nothing zooms.
- The same works with a mod pane (a Files pane) focused.
