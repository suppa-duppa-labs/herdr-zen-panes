# Zen panes for Herdr

Keep a zoomed pane zoomed while you move between panes in the [Herdr](https://herdr.dev) desktop app.
With a pane zoomed, moving left, right, up or down shows the pane next to it, zoomed.
With no pane that way, nothing changes.
With nothing zoomed, moving works as it always does.
A small map of the tab shows for a second when you zoom or move, with the zoomed pane lit.

![Zen panes](preview.png)

## Install

Ask the agent in your Herdr window:

```text
Read ~/.config/herdr-app/AGENTS.md, then add this mod: github.com/suppa-duppa-labs/herdr-zen-panes
```

Or by hand, on the computer that runs the Herdr app (run it again to update):

```sh
mkdir -p ~/.config/herdr-app/mods && curl -fsSL https://github.com/suppa-duppa-labs/herdr-zen-panes/archive/main.tar.gz | tar -xz -C ~/.config/herdr-app/mods --strip-components=2 herdr-zen-panes-main/mods/zen-panes
```

## Turn it on

Start it once in each layout you use; it opens a small window that only shows the map, which Herdr brings back on every start:

```sh
herdr-app do mod.open --name zen-panes
```

Run it again to turn it off.

Then, in `~/.config/herdr-app/keys.json`, change your `pane.go` keys to these, in the section where they are now:

```json
"ctrl-a h": "zen-panes.go:left",
"ctrl-a j": "zen-panes.go:down",
"ctrl-a k": "zen-panes.go:up",
"ctrl-a l": "zen-panes.go:right",
"ctrl-a left": "zen-panes.go:left",
"ctrl-a down": "zen-panes.go:down",
"ctrl-a up": "zen-panes.go:up",
"ctrl-a right": "zen-panes.go:right"
```

A key bound in `terminal` wins over the same key in `global`, so a leftover `pane.go` there keeps zoom from moving.

To hide the map, set `"map": false` in `mods/zen-panes/mod.json`, then run the command above twice.

## Notes

Tested with Herdr app 0.1.12, from terminal panes and mod panes.
In a layout where it isn't started, the keys show an unknown command error.
The mod reads how each tab is split from herdr-core's own state on the tab's machine; if it can't, it unzooms, moves and zooms again, and the full layout can show for one frame.
[RECIPE.md](RECIPE.md) is the brief to build the mod from scratch.
MIT, see [LICENSE](LICENSE).
