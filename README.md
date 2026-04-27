# WeakPoint📉

A playground for TD Reply employees — technical and non-technical alike — to experiment with AI programming. Anyone is welcome to clone the repo, branch off, and add a feature. Yes, *anyone* — yes, that means **you**! ✨ Never written a line of code? Perfect. Bring an idea, team up with your favorite AI, and ship something amazing. There are no bad ideas, only unshipped ones. Go forth and build — we believe in you! 🚀💫

Terminal-only PowerPoint clone. Vim-style UI, built on [Textual](https://textual.textualize.io/).

## Install

```
uv sync                    # or: pip install -e .
uv sync --extra dev        # include pytest
```

## Launch

```
python weakpoint                    # blank deck
python weakpoint path/deck.json     # open an existing deck
python weakpoint demo/demo.json     # try the bundled demo
```

## Modes

- **NORMAL** (default) — navigate, select, move, resize.
- **COMMAND** — opened with `:`, typed commands (see below).
- **INSERT** — opened with `i` on a selected text box, edit its contents.

`Esc` cancels COMMAND or INSERT and returns to NORMAL.

## NORMAL-mode keys

| Key | Action |
|---|---|
| `n` / `N` | next / previous slide |
| `a` | append new slide after current |
| `A` | insert new slide before current |
| `dd` | delete current slide |
| `Tab` / `Shift+Tab` | cycle selection through items on the slide |
| `Esc` | deselect |
| `h` `j` `k` `l` | move selected item 1 cell (left / down / up / right) |
| `H` `J` `K` `L` | resize selected (shrink-w / grow-h / shrink-h / grow-w) |
| `x` | delete selected item |
| `b` | toggle bold on selected text box |
| `i` | edit selected text box's text |
| `p` | enter present mode |
| `:` | enter COMMAND mode |
| `q` | quit (refused if unsaved — use `:q!` or `:wq`) |

## COMMAND-mode verbs

Typed after `:` then `Enter`.

```
box X Y W H [TEXT]        add text box at X,Y sized WxH (0,0 is top-left)
image PATH                add image (default 40x12 box centered)
title TEXT                set current slide's title
align left|center|right   align text in selected box
color NAME|#rrggbb        set selected box's color
bullets on|off            toggle "• " prefix on each line
numbered on|off           toggle "1. ", "2. " prefix (overrides bullets)
w [PATH]                  save (PATH required on first save)
wq [PATH]                 save and quit
o PATH                    open deck (refused if unsaved)
o! PATH                   open deck, discarding unsaved changes
q                         quit (refused if unsaved)
q!                        quit, discarding unsaved changes
```

## Present mode

Launched with `p`. Fullscreen slide, no chrome.

| Key | Action |
|---|---|
| `→` / `Space` | next slide |
| `←` / `Backspace` | previous slide |
| `q` / `Esc` | return to editor |

## Canvas geometry

Slides are a fixed **100 × 30 cell** grid. All coordinates in `:box` and moves/resizes are in cell units. Terminal bigger → letterboxed. Terminal smaller → clipped (bindings still work; resize your terminal).

## Deck file format

Single JSON file, typically `.wpt.json`. Version `1`. Images referenced by path — relative paths resolve against the deck file's directory.

## Line breaks

The command bar is single-line (Enter submits), so to put multiple lines inside
a box, type the literal escape `\n` — it's converted to a real newline when the
text enters the model:

```
:box 0 0 20 5 line one\nline two
```

With `:bullets on` or `:numbered on` each logical line gets its own prefix, so
`a\nb\nc` with bullets renders as `• a`, `• b`, `• c`. Editing a multi-line box
with `i` pre-fills the bar with `\n` escapes so you can round-trip it.

## Tips

- Images render as colored ASCII at their current box size. Resizing re-renders.
- High-contrast source images (silhouettes, logos) look best.
- The command bar pre-fills with the current box's text when you press `i`.

## Contribute

1. Clone the repo.
2. Open a branch named `initials/feature_name` (e.g. `ab/feature_name`).
3. Build your feature.
4. Open a pull request against `main`.

### Suggested features

- Command to toggle "help"
- Contours around thumbnails
- Use arrows instead of `HJKL` to move/resize boxes
- Default box size and position
- Upload from PPT or PDF
- Improve error handling (e.g. don't crash if the user enters a non-defined color)
- Support more shapes
- Support vertical text alignment
- Support updating slide order
