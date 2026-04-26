# memes/

Drop images here. The bot picks them up and posts one to X every 8h.

## Convention

Each meme is a **pair**: the image + a `.txt` sidecar with the caption.

```
memes/
  01-tuskegee.png        ← image (png / jpg / jpeg / gif / webp)
  01-tuskegee.txt        ← caption (plain text, ≤ 280 chars)
  02-mockingbird.jpg
  02-mockingbird.txt
  ...
```

**Filename rules:**
- Same basename for image + caption
- No spaces in filenames (use `-` or `_`)
- Numeric prefix for ordering (bot posts oldest first)
- Image formats supported: `png`, `jpg`, `jpeg`, `gif`, `webp`
- Image size: under 5MB (X limit)
- Caption: under 280 characters

**Caption formatting:**
- Plain UTF-8 text, no markdown
- Newlines preserved (single `\n` between lines)
- No URLs needed (X profile already links priorprotocol.fun)
- No `$PRIOR` cashtag in captions (looks shilly)
- Voice: lowercase, dry, on-brand. Match MEMES.md captions or write your own.

## How the bot picks a meme

1. Globs `memes/*.{png,jpg,jpeg,gif,webp}`
2. Filters out anything already posted (tracked in `data/memes-state.json`)
3. Sorts by filename (alphabetical → numeric prefix gives you control)
4. Reads the matching `.txt` sidecar for the caption
5. Uploads media via X v1.1, posts via v2
6. Logs the post to `data/log.json` with `type: "meme"`
7. Marks filename as posted in `data/memes-state.json`

## Cadence

- Default: every 8h via `prior-memes.yml` workflow → 3 memes/day max
- Manual fire: `gh workflow run prior-memes.yml --field dry_run=true|false`
- Pause: comment out the `schedule:` block in `.github/workflows/prior-memes.yml`

## Re-posting a meme

Memes are one-shot by default. To re-post:
- Edit `data/memes-state.json` and remove the filename from `posted` array
- Or rename the file (e.g., `01-tuskegee.png` → `01-tuskegee-v2.png`)

## Source for prompts

`MEMES.md` in the repo root has 66 Gemini-ready prompts. Captions in that file are designed to work as the `.txt` sidecar — copy them straight in.
