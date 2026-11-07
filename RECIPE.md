# Zen panes

Moving between panes keeps zoom on: with a pane zoomed, `zen-panes.go:<direction>` shows the pane next to it in that direction, zoomed in its place.
With nothing zoomed it is `pane.go`.
The mod draws nothing.

![Zen panes](preview.png)

**What you see:**

- Nothing of the mod itself: it runs as a window overlay with no frame and nothing in it, so it has no size.
- With a pane zoomed, a move key swaps the zoomed pane for its neighbour in that direction; the tab stays zoomed.
- With nothing zoomed, the move key focuses the neighbour as `pane.go` does.

**How it behaves:**

- `zen-panes.go:left`, `:right`, `:up` and `:down`, bound in `keys.json` like any `<mod>.<command>`.
- Not zoomed: runs `pane.go {direction}`, so its errors (a focused layout terminal block) show as `pane.go`'s.
- Zoomed: runs `pane.zoom {pane}` on the zoomed pane to unzoom the tab, then, on the first render that sees the tab unzoomed, `pane.go {direction}` and `pane.zoom` with no pane, which zooms whichever pane has focus by then.
- No neighbour that way: the same pane is zoomed again.
- The zoomed pane is found by the focused pane's tab in `panes()`, so it works from terminal panes and mod panes alike.
- If another tab is shown before the unzoom lands, the move is dropped.
- Any other command is ignored.

**Built from:**

- One mod, `zen-panes`, `place: "none"`, whose `mod.json` `overlay` is `{ kind: "window", key: "zen-panes", keep: true, frame: "none" }`: `mod.open {name: "zen-panes"}` opens it as a kept window of the shown layout, which Herdr reopens on every start and whenever that layout is shown again; `mod.open` again closes it.
- `main.js`: `nextCommand()` in a loop started from `init`, `focused()`, `panes()`, `run("pane.go")`, `run("pane.zoom")`; `render()` returns an empty `div()`.

**Watch out:**

- `pane.go` finds neighbours from the panes' on-screen bounds, among the panes shown; while zoomed only the zoomed pane is shown, so `pane.go` does nothing, and mods can't read pane geometry to find the neighbour themselves.
- The bounds are recorded while a frame is drawn, so `pane.go` has to wait for a frame of the unzoomed layout; running unzoom, `pane.go` and zoom back to back moves nowhere.
  That one frame can show.
- `<mod>.<command>` reaches shown copies only, and overlays count as shown; a window overlay needs no layout edit, so it works in shipped layouts too, unlike a layout or floating block.
- A window overlay doesn't take the keyboard and, with no frame and no content, covers nothing.
- Windows close on a layout switch; kept ones come back only with the layout they were opened in.
- A `terminal` key binding beats the same key in `global`: the move keys must replace `pane.go` in whichever section holds it.

**Done when:**

- `herdr-app check mods/zen-panes` passes.
- After `herdr-app do mod.open --name zen-panes`, `herdr-app status` lists `zen-panes` under overlays, the window looks unchanged, and it is still listed after a restart.
- With two panes side by side, the left one zoomed, `zen-panes.go:right` shows the right one zoomed and focused.
- With nothing zoomed, `zen-panes.go:right` focuses the right pane and nothing zooms.
- With the left pane zoomed, `zen-panes.go:left` leaves it zoomed and focused.
- The same works with a mod pane (a Files pane) focused.
