# WeakPoint📉

A playground for TD Reply employees — technical and non-technical alike — to experiment with AI programming. Anyone is welcome to clone the repo, branch off, and add a feature. Yes, *anyone* — yes, that means **you**! ✨ Never written a line of code? Perfect. Bring an idea, team up with your favorite AI, and ship something amazing. There are no bad ideas, only unshipped ones. Go forth and build — we believe in you! 🚀💫

Terminal-only PowerPoint clone. Vim-style UI, built on [Textual](https://textual.textualize.io/).

## Contribute

Zero to first pull request, even if you've never written code before.

### Stuck on a command? Ask your AI.

Some of the words you'll see below (`terminal`, `git`, `uv`, `branch`, `pull request`) might be unfamiliar — that's expected, and figuring them out *is* the exercise. Don't get stuck silently. Paste the command (or the error you got) into your AI assistant and ask it to explain, walk you through it on your machine, or fix the problem. Doing that *is* AI programming. There is no "cheating" here — the goal is to get comfortable using AI as your collaborator.

Prompts that work well:

- "I'm on macOS and I don't have `uv` installed. How do I install it?"
- "I ran `git clone ...` and got `command not found: git`. What do I do?"
- "Walk me through opening a pull request on GitHub from the web UI."
- "I want to add a feature that does X to WeakPoint. Where in the code should I start?"

### 1. Pick an AI coding assistant

Pick whichever sounds good — they're all great. If you're not sure, pick one and ask *it* to compare.

- **OpenAI Codex** — OpenAI's coding agent, runs in your terminal. **Has a free plan**, so a great place to start.
- **Google Antigravity** — Google's agentic coding IDE. **Has a free plan**, so also a great place to start.
- **Claude Code** — Anthropic's coding agent, runs in your terminal (paid)
- **Cursor** — a full code editor with AI built in, more visual and less terminal (paid)

Each one has its own install instructions. Search the tool's name and follow them — or, even better, set up a different AI first and ask it to walk you through installing the one you actually want. Yes, that's allowed. That's the whole point.

### 2. Get git and GitHub working

You'll need:

- `git` installed on your machine
- a free account at [github.com](https://github.com), and access to the [td-berlin](https://github.com/td-berlin) org (ask in Slack if you don't have it yet)

If `git` isn't installed, or you've never used GitHub before, **don't fight it alone** — paste exactly that into your AI assistant. A prompt like *"I'm on macOS, I don't have git installed and I've never used GitHub. Walk me through getting set up step by step."* gets you there in a few minutes.

### 3. Get the repo and run the demo

In a terminal:

```
git clone https://github.com/td-berlin/weakpoint.git
cd weakpoint
uv sync
python weakpoint demo/demo.json
```

If `uv` isn't installed, ask your AI for the one-liner. (It's `curl -LsSf https://astral.sh/uv/install.sh | sh` on macOS/Linux — but please feel free to ask your AI to explain what that does before you run it.)

### 4. Branch off and build

```
git checkout -b ab/my_feature
```

Replace `ab` with your initials and `my_feature` with a short name for what you're building. Then go build something — pick from [Suggested features](#suggested-features) at the bottom of this README or invent your own. Lean on your AI to navigate the code, propose changes, and explain anything that looks like alphabet soup.

### 5. Commit and open a pull request

```
git add .
git commit -m "Add my feature"
git push -u origin ab/my_feature
```

Then go to [github.com/td-berlin/weakpoint](https://github.com/td-berlin/weakpoint), click **Compare & pull request**, and target `main`.

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

## Suggested features

- Command to toggle "help"
- Contours around thumbnails
- Use arrows instead of `HJKL` to move/resize boxes
- Default box size and position
- Upload from PPT or PDF
- Improve error handling (e.g. don't crash if the user enters a non-defined color)
- Support more shapes
- Support vertical text alignment
- Support updating slide order
