# Screenshots Checklist

Shots needed for the README and GitHub social preview. Save to
`docs/screenshots/` using the exact filenames below so the README links
resolve.

## Capture setup

- **Viewport:** 1440×900, browser zoom 100%, bookmarks bar hidden
- **Theme:** dark for the hero and most shots; one light shot for contrast
- **Data:** a repository with real scale — CodeAtlas itself works well
  (313 files, 282 edges)
- **State:** warm cache, no error toasts on screen, no personal paths
  visible in the header (use a generic path like `C:/projects/codeatlas`)
- **Crop:** to the browser viewport, no OS chrome or tab bar
- **Format:** PNG, 2× device pixel ratio if available

---

## Required shots

### 1. `overview.png` — hero

**Page:** Repository Overview (`/`)
**Angle:** Full viewport, sidebar expanded, scrolled to top.
**Must show:** brand lockup with the serif "Repository Intelligence" line,
the four stat cards with real numbers, system health with all three services
green, and at least two repository cards below.
**Why:** this is the README hero and the social preview — it has to read as
a product in one glance.

### 2. `graph.png` — dependency map

**Page:** Dependency Map (`/graph`)
**Angle:** Full viewport with a hub file selected so neighbour highlighting
and the animated edges are visible, and the inspector panel open on the
right.
**Must show:** dimmed background nodes, highlighted neighbours, the file
inspector with fan-in/fan-out, the minimap, and the category legend.
**Tip:** select something with 8–15 connections. Too few looks empty; too
many looks like noise.

### 3. `chat.png` — Ask CodeAtlas

**Page:** Ask CodeAtlas (`/chat`)
**Angle:** Full viewport mid-conversation, scrolled so a complete answer is
visible with its metadata row.
**Must show:** a user question, a markdown answer containing a syntax-
highlighted code block, the confidence badge, the chunk/token/time badges,
and the referenced-files panel populated.
**Why:** this is the differentiator — the citations and confidence are the
point.

### 4. `insights.png` — repository insights

**Page:** Insights (`/report`)
**Angle:** Scrolled so both distribution charts are fully visible with the
stat cards above them.
**Must show:** the four summary cards, both bar charts with readable labels.
**Tip:** capture after the charts have faded in, not mid-animation.

---

## Recommended extras

### 5. `scan-result.png` — repository ready

**Page:** Repositories after a successful scan.
**Angle:** Cropped to the result card.
**Must show:** the "Repository Ready" heading, the four metrics, language
badges, and the graph summary line. Good for the Features section.

### 6. `insights-issues.png` — issue detection

**Page:** Insights, scrolled to Potential issues.
**Angle:** Cropped to the issues card.
**Must show:** either the clean "Nothing needs your attention" state or a
populated coupling/unresolved-imports table. The clean state photographs
better.

### 7. `light-mode.png` — theme contrast

**Page:** Repository Overview in light theme.
**Angle:** Same framing as shot 1.
**Why:** shows the warm palette holds up in both themes.

### 8. `empty-state.png` — first run

**Page:** Repository Overview with no repositories tracked (clear history in
Settings first).
**Angle:** Cropped to the empty state block.
**Must show:** "Every great repository starts with a scan." with the call to
action.

### 9. `api-docs.png` — OpenAPI

**Page:** `http://127.0.0.1:8000/docs`
**Angle:** Endpoints collapsed, all three tags visible.
**Must show:** Repository, AI, and System groupings with all seven
endpoints.

### 10. `mobile.png` — responsive

**Page:** Repository Overview at 390×844.
**Must show:** the collapsed sidebar and hamburger, cards stacked to one
column.

---

## Social preview

GitHub renders 1280×640. Either crop `overview.png` to that ratio, or make a
composite: the graph on the left, a chat answer with its confidence badge on
the right, with the project name and one line of description.

## Checklist

- [ ] `overview.png`
- [ ] `graph.png`
- [ ] `chat.png`
- [ ] `insights.png`
- [ ] `scan-result.png`
- [ ] `insights-issues.png`
- [ ] `light-mode.png`
- [ ] `empty-state.png`
- [ ] `api-docs.png`
- [ ] `mobile.png`
- [ ] Social preview (1280×640)
- [ ] No absolute personal paths or API keys visible in any shot
