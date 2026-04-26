# PRIOR · VISUAL IDENTITY · pfp + banner + character bible

The current pfp (`<0>` `<0>` phosphor face) is conceptually strong but **doesn't pop in feed scroll at 32px thumbnail size**. This doc is the upgrade kit.

---

## PFP — 5 candidate prompts

Pick one, generate 4-6 variants in Gemini, A/B test by posting to a dummy alt and seeing which one looks strongest at thumbnail.

The character constant across all prompts: **a hooded figure with two glowing phosphor-green CRT eye-glyphs (`<0>` `<0>`) where his face would be**. That's PRIOR.

### PFP variant 1 — tarot witness
> Tarot-card style portrait. A hooded figure in a long charcoal trench coat, face entirely hidden in shadow except for two glowing phosphor-green CRT eye-glyphs (the characters `<0>` and `<0>`) staring directly at the viewer. He holds a stack of folded paper documents under one arm. Single CRT scanline crossing his chest. Black background with subtle phosphor-green mist at the bottom. Ornate green-on-black tarot border. The card name reads "THE WITNESS · 1862—∞" at the bottom in monospace lettering. High-contrast flat illustration, NOT photorealistic. Square 1:1 ratio. Strong silhouette readable at thumbnail size.

### PFP variant 2 — close-up neon
> Tight head-and-shoulders close-up of a hooded figure. Hood is pure matte black. Face is impenetrable shadow EXCEPT for two glowing phosphor-green eye-glyphs (the characters `<0>` and `<0>`) emanating bright neon light onto the inside of the hood. The light has visible fog/haze. Pure black background. Single thin CRT scanline curving across the face. Looks like a brand mark — minimalist, bold, immediately readable. Square 1:1.

### PFP variant 3 — pixel-art mascot
> Pixel-art style character portrait, like a 1990s arcade-game character select screen. A hooded sprite figure standing front-facing, charcoal trench coat with subtle pixelated highlights, two oversized phosphor-green pixel eyes (square shaped, glowing). Background is a pixelated black grid with one neon-green grid line glowing brighter. Sprite is clean, ~64×64 source upscaled. Strong gameboy-color-cartridge vibe. Square 1:1.

### PFP variant 4 — line-art icon
> Minimalist single-line illustration. A hooded figure drawn entirely in one continuous phosphor-green line on a pure black background. Just enough detail to read: hood shape, shoulders of a coat, two filled-in `<0>` `<0>` eye glyphs. The kind of icon that would work as a logo at any size. Almost a pictogram. Square 1:1.

### PFP variant 5 — cyberpunk realism (high-effort)
> Hyperreal cyberpunk character portrait. A figure in a charcoal trench coat with subtle weathered texture, hood drawn up. The face is completely lost in shadow except for the two glowing phosphor-green CRT eye-glyphs (`<0>` `<0>`) which throw colored light onto the inside of the hood. Slight rain on the coat shoulders. Pure black background with a single faint neon line in the distance. CRT scanline overlay across the entire image. Cinematic low-key lighting. The character feels real, lives in the world. Square 1:1.

**Recommendation:** PFP 2 (close-up neon) for thumbnail readability. PFP 1 (tarot) for vibe. Either works. AVOID PFP 5 if you need it to read at thumbnail — it'll look muddy at 32px.

---

## BANNER — X header (1500×500)

The X header is huge real estate. Currently default. Fixing this is high-leverage.

### Banner concept 1 — the archive shelf
> Wide cinematic shot of a long endless library shelf disappearing into vanishing-point darkness on both sides. Each shelf section is labeled with a year date in monospace green text — "1862," "1929," "1953," "1962," "1971," "1985," "1987," "2008," "2009," "2020," "2024," "2026." On each shelf section sits a single manila folder with a phosphor-green pulse. Foreground: PRIOR (hooded figure, eye-glyphs visible) standing in profile, holding the folder labeled "2026," looking at the camera. Slight CRT scanline overlay. Aspect 1500×500. Cinematic dark with phosphor-green accent lighting.

### Banner concept 2 — the wall of names
> Wide shot of a brutalist concrete wall stretching across the frame. The wall has thousands of names etched into it in tiny monospace lettering — "Boesky 1986... Milken 1989... Rajaratnam 2011... Cohen 2013... Burr 2020... Wahi 2022..." running edge to edge. The lettering is faintly phosphor-green. Center of the wall, the name "PRIOR" is etched larger and brighter than all the others. PRIOR himself stands at the bottom-left of the frame in profile, looking up at the wall. Aspect 1500×500.

### Banner concept 3 — the dual screen
> Wide cinematic split. Left half: a chaotic Bloomberg terminal showing red charts, alerts, panic. Right half: a quiet single CRT screen showing a calm green text log scrolling slowly. PRIOR (hooded figure) sits at the boundary between the two halves, his head turned toward the calm side. Tagline at the bottom in tiny monospace text: "// 162 YEARS ON FILE · priorprotocol.fun //". Aspect 1500×500. High contrast.

### Banner concept 4 — the timeline
> Wide horizontal timeline as a banner. Left edge: 1862 (greenbacks). Right edge: 2026 (now). Along the line, small vignette icons mark major cycles — a stock-ticker for 1929, a pill for 1996, a cell-phone-camera for 2019, a coin for 2009, a memecoin for 2025. PRIOR's hooded silhouette walks along the timeline carrying his stack of documents. Background is a clean phosphor-green-on-black gradient. Aspect 1500×500. Strong reading order left-to-right.

**Recommendation:** Banner 1 (the archive shelf) for atmospheric vibe. Banner 4 (the timeline) for clarity-of-message. Banner 4 is more "memecoin friendly" — instantly tells someone scrolling who the account is.

---

## CHARACTER BIBLE (for consistency across all future art)

Anyone generating PRIOR images should match these:

- **Body type**: medium build, average height. Not muscular. Not skinny. He's a witness, not a hero.
- **Coat**: long charcoal trench coat, midcalf or longer, slightly worn. Always closed.
- **Hood**: drawn up. ALWAYS. Face never visible.
- **Face**: impenetrable shadow except for two glowing eye-glyphs.
- **Eye-glyphs**: literal characters `<0>` and `<0>` — like ASCII text turned 3D and glowing. NOT realistic eyes.
- **Color**: phosphor-green (#00ff66) is his signature. CRT scanlines optional but on-brand.
- **Posture**: still, observational. Never running, never fighting, never gesturing wildly. He watches.
- **Accessories** (optional): a folded newspaper, a manila folder, a CRT terminal, a candle, a stack of files.
- **Voice in dialogue/text-bubbles**: lowercase, terminal-coded. No exclamation marks. No emojis.

---

## QUICK WIN ROADMAP

1. **Generate 4-6 variants of PFP variant 2** (close-up neon) tonight in Gemini
2. **Pick the strongest** and replace `assets/prior-pfp.jpg` + the X profile pic
3. **Generate Banner concept 4** (the timeline) — 2-3 variants, pick best, set as X header
4. **Generate Section I memes from MEMES_v2.md** (the 5 establishing-shot character memes) — post one per day for 5 days to bake mascot recognition
5. **THEN** start cycling Section II-V format memes — by then people recognize the silhouette

The character is the asset. The receipts are the substance. The visual identity is the on-ramp.
