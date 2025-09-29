# SKIEN: News Threads Tracker — Product Spec v0

## 1) Vision & Scope
Track evolving news topics as *threads* you can browse visually (graph + timeline), rather than rows in a spreadsheet. You’ll zoom from a high‑level topic map (e.g., **US Tariffs / “Trump tariffs”**) down to specific *claims/events* (“Announced X% tariff on … on 2025‑01‑05”, “Follow‑up press conference clarifies … on 2025‑01‑09”).

**MVP goals**
- Import stories from Google Sheets/CSV; normalize and de‑duplicate.
- Manually (and optionally, automatically) group stories into **Topics**.
- Create **Threads** within a Topic and link items with typed edges (e.g., *follow‑up*, *contradiction*, *amplification*).
- Two core views: **Graph View** (zoomable, branchy) and **Timeline View** (linear, date‑ordered with thread lanes).
- Fast filtering, search, and detail panel for a selected node.

**Out of scope (for MVP)**
- Web scraping/crawling at scale.
- ML topic modeling beyond simple keyword heuristics.
- Multi‑user auth/roles.

---

## 2) Core Concepts & Data Glossary
- **Story**: A single news item (article, post, transcript, video). Holds URL, source, published date, title, excerpt, tags.
- **Event/Claim**: The atomic thing you track on a timeline (may map 1:1 with a Story, or be extracted from a Story). Example: *“Candidate announced 10% tariff on 2025‑03‑01.”*
- **Topic**: A named umbrella (e.g., *US Tariffs*). Contains many Threads.
- **Thread**: A sequence or cluster of related events/claims inside a Topic (e.g., *“2025 Tariff Proposal rollouts”*). Threads can branch.
- **Edge**: A typed relationship connecting two Events/Claims (follow‑up, refutes, clarifies, repeats, policy‑action, source‑update).
- **Entity** (optional for later): Named people/orgs/places referenced.

---

## 3) Information Architecture & Views

### 3.1 Global Layout
- **Top Nav**: Topics, Add/Import, Search, Settings.
- **Left Sidebar**: Topic/Thread browser with quick filters (date range, tags, source).
- **Main Panel**: Switchable **Graph** / **Timeline** / **Table** tabs.
- **Right Panel** (drawer): Details of the selected node (Event/Claim/Story), with metadata and links.

### 3.2 Graph View (Zoomable Topic Map)
- **Nodes**: Events/Claims (primary). Optional Story nodes as secondary/child badges.
- **Edges**: Typed and color/shape‑encoded (e.g., *follow‑up* solid, *refute* dashed, *amplify* dotted).
- **Layouts**:
  - *By Time*: top‑to‑bottom chronology (good for threads).
  - *Force‑directed*: cluster by tag/entity (good for exploration).
- **Controls**: zoom (scroll), pan (drag), fit‑to‑screen, search focus, legend toggle, edge type filter, time slider.
- **Selection**: clicking a node highlights its immediate neighborhood + opens details panel.

### 3.3 Timeline View (Thread Lanes)
- Multiple **lanes** per Thread inside a Topic. Each Event/Claim is a card on its lane with date, short title, and badges for tags/entities/sources.
- Drag‑to‑zoom, pinch‑zoom; Shift+wheel for horizontal pan.
- Hover shows quick context; click opens details panel.

### 3.4 Table View
- Compact spreadsheet‑like grid for bulk edit/sanity checks (title, date, URL, tags, topic, thread, duplicate flags). Supports inline edits.

### 3.5 Detail Panel (Right Drawer)
- **Header**: Title + date + thread/topic chips.
- **Meta**: Source, author, URL, captured at, tags.
- **Quote/Claim**: the sentence/summary you’re tracking.
- **Evidence**: list of Stories that support this claim (one or many).
- **Relations**: incoming/outgoing edges with mini‑graph.
- **Actions**: edit, re‑assign to thread, add link, mark duplicate, open source URL.

---

## 4) User Stories & Acceptance Criteria

### Import & Normalize
1. *As a user, I can import a CSV/Google Sheet export* so that stories populate the database.
   - **AC**: Upload CSV; show column mapping step; preview 20 rows; run import; display summary (inserted, updated, skipped duplicates).
2. *As a user, I can de‑duplicate stories* by URL/title similarity.
   - **AC**: System flags potential dupes; user merges or dismisses.

### Organize
3. *As a user, I can create Topics and Threads, and assign events/stories to them.*
   - **AC**: In details panel and bulk table, I can set topic/thread. Threads ordered by first event date.
4. *As a user, I can create edges between events and choose a relation type.*
   - **AC**: Edge types are selectable; graph updates immediately; undo supported.

### Explore
5. *As a user, I can zoom/pan a Topic graph and filter by date range, tags, edge types.*
   - **AC**: Interactive controls respond <100ms to UI actions; graph re‑layouts under 1s for ≤500 nodes.
6. *As a user, I can switch to a Timeline view to read a thread chronologically.*
   - **AC**: Events rendered in lanes per thread; zoom and pan work smoothly.

### Edit
7. *As a user, I can edit event/claim text and attach one or more story sources.*
   - **AC**: Inline edit with autosave; source list shows favicons and status.

### Find
8. *As a user, I can search by keyword and jump to a node in graph/timeline.*
   - **AC**: Search bar with type‑ahead across title, claim, tags; hitting Enter focuses/centers the node.

---

## 5) Data Model (SQLite + ORM)
> Suggested ORM: **SQLAlchemy** (or **SQLModel** if you prefer Pydantic‑style models). Start simple; keep indices on dates and foreign keys.

**story**
- id (PK)
- url (unique)
- title
- source_name
- author
- published_at (date)
- captured_at (datetime default now)
- summary (text)
- raw_text (text, optional)

**event_claim**
- id (PK)
- topic_id (FK -> topic)
- thread_id (FK -> thread, nullable)
- story_primary_id (FK -> story, nullable)
- claim_text (text)
- event_date (date)
- importance (int, optional)

**event_story_link** (many stories can support one event)
- event_id (FK -> event_claim)
- story_id (FK -> story)
- note (text, optional)
- PRIMARY KEY (event_id, story_id)

**topic**
- id (PK)
- name (unique)
- description (text)
- color (string, optional)

**thread**
- id (PK)
- topic_id (FK -> topic)
- name
- description (text)
- start_date (computed or manual)

**edge**
- id (PK)
- src_event_id (FK -> event_claim)
- dst_event_id (FK -> event_claim)
- relation (enum: follow_up, refutes, clarifies, repeats, action, other)

**tag**
- id (PK)
- name (unique)

**story_tag**
- story_id (FK -> story)
- tag_id (FK -> tag)
- PRIMARY KEY (story_id, tag_id)

*Indexes*: story.url (unique), event_claim.event_date, edge.src_event_id, edge.dst_event_id, thread.topic_id.

---

## 6) Technical Architecture

**Stack & Structure**
- Flask app with Blueprints: `core` (home, search), `topics`, `threads`, `events`, `stories`, `importer`, `api`.
- Server‑rendered HTML (Jinja + **Bootstrap**), progressively enhanced with **htmx** (+ **Alpine.js** for small interactivity).
- Graph rendering with **Cytoscape.js** (pan/zoom, layouts, styling). Timeline with **Vis Timeline** or **Timeglider/Timescale** alternative; fallback: build a simple SVG timeline with D3 for MVP.
- Packaging: `app/` (blueprints, models, services), `static/` (js/css), `templates/` (Jinja), `migrations/` (Alembic).

**Why htmx?**
- Keeps Flask in control (no heavy SPA). You can swap partials (graph JSON, table rows, details drawer) without page reloads.

**API endpoints (JSON)**
- `GET /api/topics/:id/graph?from=YYYY-MM-DD&to=YYYY-MM-DD&edges=follow_up,refutes&layout=time|force` → nodes, edges.
- `GET /api/topics/:id/timeline` → events grouped by thread.
- `POST /api/events` (create), `PATCH /api/events/:id` (edit), `POST /api/edges` (create).
- `GET /api/search?q=` → matching events/stories.

**Server services**
- `import_service`: CSV parsing, column mapping, dedupe.
- `link_service`: create/validate typed edges, prevent cycles if needed.
- `suggest_service` (optional later): heuristics to suggest thread/topic/edges based on tags/keywords.

---

## 7) Interaction Design Details

**Graph View**
- Legend describes edge types.
- Mini‑map (toggle) shows your viewport relative to the full graph.
- Node styling: date intensity (older = lighter), importance size scale.
- Keyboard: `+/-` zoom, `f` fit to screen, `l` switch layout, `t` open timeline tab.

**Timeline View**
- Thread lanes in distinct subtle colors.
- Time scrubber with snap‑to events.
- Multi‑select to create edges directly from timeline (drag from one card to another).

**Table View**
- Bulk select → assign thread/topic, tag add/remove, delete.
- Inline editing (enter to save), with optimistic feedback.

**Details Drawer**
- Quickly add a relation: "Connect to…" search box filters events in the same topic; choose relation type.

---

## 8) Import Workflow (from Google Sheets/CSV)
1. Export your sheet to CSV.
2. Upload CSV → mapping step (map your columns to: title, url, source, author, published_at, tags comma‑sep, summary).
3. Preview + validate dates/URLs.
4. Run import.
5. Dedupe pass:
   - Exact URL match ⇒ same story.
   - Title similarity (normalize, Jaro‑Winkler ≥ 0.92) **and** same source ±3 days ⇒ likely duplicate.
   - Show review queue after import.

---

## 9) Edge Semantics & Validation
- **follow_up**: B happens after A and references/extends A.
- **refutes**: B contradicts A.
- **clarifies**: B qualifies A without contradicting.
- **repeats**: B restates A (e.g., rally quote repeats press release).
- **action**: B is a concrete policy/action following A statement.

**Rules**
- Prevent self‑loops.
- Optional: prevent time‑travel (dst date < src date) unless flagged as correction.
- Show warnings on cycles if layout = DAG.

---

## 10) Hard Parts & Mitigations
- **Graph performance**: Keep nodes per view ≤ 800. Use server filters (date window, thread selection). Lazy‑load neighbors on expand.
- **Ambiguity linking**: Provide great manual tools; record *link confidence*; keep an *Unsorted* bin.
- **Chronology drift**: Sources update timestamps; store both `published_at` and `captured_at`.
- **Data hygiene**: Normalize sources (domain only), canonicalize URLs, trim UTM.
- **Editing friction**: Keyboard shortcuts and inline edits reduce cognitive load.

---

## 11) Accessibility & UX Quality
- Keyboard navigable graph controls and timeline.
- WCAG‑friendly color palette and sufficient contrast.
- Prefer text labels + icon; expose edge relation text on hover/focus.

---

## 12) Security & Privacy
- Local app initially (no auth). If exposed: enable Flask‑Login and CSRF.
- Sanitize imported HTML; never render raw external content.

---

## 13) Build Plan (Milestones)
**M1: Data plumbing** (models, importer, dedupe, simple table view)
**M2: Topic/Thread management** (create/edit, assign)
**M3: Timeline** (thread lanes + detail drawer)
**M4: Graph** (Cytoscape, edges, layouts, filters)
**M5: Polish** (search focus, keyboard, mini‑map, bulk edit)

---

## 14) Nice‑to‑Have (post‑MVP)
- Simple NLP assist: keyword extraction to suggest topics/threads (spaCy, YAKE, KeyBERT).
- Entity extraction to cluster by person/org.
- Snapshot export: PNG of current graph/timeline.
- Change log/versioning for edits.
- Browser extension “Add to Tracker”.

---

## 15) Example Data Shapes
**Graph API response**
```json
{
  "nodes": [
    {"id": "e_101", "label": "Announces 10% tariff", "date": "2025-03-01", "threadId": 12, "importance": 3},
    {"id": "e_112", "label": "Clarifies exemptions", "date": "2025-03-05", "threadId": 12}
  ],
  "edges": [
    {"id": "x1", "source": "e_101", "target": "e_112", "relation": "clarifies"}
  ]
}
```

**Timeline API response**
```json
{
  "threads": [
    {"id": 12, "name": "2025 proposal rollout", "events": [
      {"id": 101, "title": "Announces 10% tariff", "date": "2025-03-01"},
      {"id": 112, "title": "Clarifies exemptions", "date": "2025-03-05"}
    ]}
  ]
}
```

---

## 16) Visual Design Notes (Bootstrap‑first)
- Use Bootstrap grid; cards for event nodes in timeline; badges for tags.
- Keep colors muted; use accent for selected thread.
- Provide a *Legend* off‑canvas with edge types and examples.

---

## 17) Testing & Quality
- Seed DB with 50–200 items; measure load times.
- Unit tests for importer + dedupe.
- Snapshot tests for graph JSON API.

---

## 18) Open Questions (for later)
- Do Events always derive from Stories, or can you create free‑standing Events?
- Should edges be directional only, or allow undirected for *related*?
- Do we need per‑Topic custom edge types?
- Export formats desired (CSV/JSON/PNG)?



---

## 19) Lo‑Fi Wireframes (v0)
> Text‑only wireframes to lock layout and interactions before visuals. Each block shows anatomy, controls, and key states.

### 19.1 Graph View — Topic Map
```
┌───────────────────────────────────────────────────────────────────────────┐
│ LOGO  Topics ▾  Add/Import  Search [───────────────]  Settings ⚙        │
├───────────────┬──────────────────────────────────────────────────────────┤
│ Topics/Filters│  [Layout: •Time  ○Force]   [Fit] [+] [−]   Legend ⓘ     │
│ ┌───────────┐ │  ┌────────────────────────────────────────────────────┐  │
│ │ Topic ▾   │ │  │                                                    │  │
│ │ • US Tar… │ │  │      o e12                                        │  │
│ │   Threads │ │  │     /  \\                                         │  │
│ │   ◦ 2025…│ │  │  o e10   o e13  — — — — — — — — time →             │  │
│ │   ◦ 2024…│ │  │   |        \\                                     │  │
│ │   ◦ Unsort│ │  │  o e11     o e14 (refutes)                        │  │
│ └───────────┘ │  │                                                    │  │
│ Filters        │  │   [mini‑map ▣]                                    │  │
│ [Date ▯▯]     │  └────────────────────────────────────────────────────┘  │
│ [Tags ▯▯]     │         ◁──────────────── time slider ───────────────▷   │
│ Edge types:   │  follow‑up ■  refutes ▒  clarifies ░  repeats ●  action ◆ │
│  ■ ▒ ░ ● ◆    │                                                          │
├───────────────┴──────────────────────────────────────────────────────────┤
│ Details Drawer → (collapsed by default; opens on node select)            │
└───────────────────────────────────────────────────────────────────────────┘
```
**Interactions**
- Click node → opens Details Drawer; highlights 1‑hop neighbors; dims others.
- Drag background to pan; wheel to zoom; `f` = Fit, `l` = toggle layout, `t` = switch to Timeline.
- Time slider filters nodes by `event_date`; edges to hidden nodes show stub caps.
- Legend toggles show/hide edge types.

**States**
- *Empty*: show CTA “Import stories to start” with link to importer.
- *Loading*: skeleton for graph area + disabled controls.
- *Dense*: auto‑cluster nodes; show “Expand neighbors” button on cluster.

---

### 19.2 Timeline View — Thread Lanes
```
┌───────────────────────────────────────────────────────────────────────────┐
│ LOGO  Topic: US Tariffs ▾   Threads: [All ▾]   Search [─────]   Zoom [▭] │
├───────────────────────────────────────────────────────────────────────────┤
│  ◁  2025‑01  |  2025‑02  |  2025‑03  |  2025‑04  |  2025‑05  |  ▷       │
│───────────────────────────────────────────────────────────────────────────│
│ Thread A ─┬─┌───────e10───────┐───────┌──e12──┐─────────────┌─e15─┐     │
│           │ │ Announce 10%    │       │ Clar. │             │ Act │     │
│           │ └──────────────────┘       └───────┘             └─────┘     │
│───────────┼──────────────────────────────────────────────────────────────│
│ Thread B ─┬─────┌──e20──┐────────┌────e21 (refutes)────┐─────────────── │
│           │      │ Leak │        │  Rally quote        │               │
│           │      └──────┘        └─────────────────────┘               │
│───────────┼──────────────────────────────────────────────────────────────│
│ Thread C ─┬──────────┌─e30─┐─────────────────────────────────────────── │
│           │          │ OpEd│                                           │
│           │          └─────┘                                           │
├───────────┴──────────────────────────────────────────────────────────────┤
│ Details Drawer → (opens when card clicked)                               │
└───────────────────────────────────────────────────────────────────────────┘
```
**Interactions**
- Drag horizontally to pan; scroll to zoom timeline scale; Shift+scroll for fine pan.
- Click card → focuses date, opens Details Drawer, highlights related cards; edges drawn as subtle connectors across lanes.
- Multi‑select (Ctrl/Cmd+click) cards → “Create relation” toolbar appears.

**States**
- *Sparse*: cards show full titles; *Dense*: truncate + show tag badges only.
- *Filter by Thread*: left sidebar checkboxes toggle lanes.

---

### 19.3 Details Drawer — Event/Claim
```
┌───────────────────────────────────────────────────────────────┐
│ ◄ Back  |  Event e12                                         │
│ Announced 10% tariff on imported X                            │
│ 2025‑03‑01  • Thread: 2025 rollout • Topic: US Tariffs        │
├───────────────────────────────────────────────────────────────┤
│ Sources (2)                                                   │
│  • [Site A] Title…  (2025‑03‑01)  ↗ Open                      │
│  • [Site B] Title…  (2025‑03‑01)  ↗ Open                      │
├───────────────────────────────────────────────────────────────┤
│ Tags: [tariffs] [manufacturing] [campaign]                    │
├───────────────────────────────────────────────────────────────┤
│ Relations                                                     │
│  → clarifies e10   (2025‑03‑05)                               │
│  ↔ repeats   e08   (2025‑03‑02)                               │
│  ✕ refutes   e14   (2025‑03‑06)                               │
│  [Add relation] [type ▾] [search events…]                     │
├───────────────────────────────────────────────────────────────┤
│ Notes                                                         │
│  [………………………………………………………………………………………………………]                    │
├───────────────────────────────────────────────────────────────┤
│ Actions: [Edit] [Reassign Thread] [Mark Duplicate] [Delete]   │
└───────────────────────────────────────────────────────────────┘
```
**Interactions**
- Inline edit `claim_text`; autosave on blur; show toast “Saved”.
- “Add relation” opens quick‑finder (same topic) with keyboard navigation.
- “Open” source launches in new tab; favicon + domain visible.

**States**
- *Read‑only mode* (future): hide destructive actions.
- *No sources linked*: CTA to attach from existing stories.

---

### 19.4 Mobile / Narrow Viewports
```
┌Top Bar: Topic ▾   Search 🔎   Menu ☰┐
│ Graph ▣  Timeline ▭                 │
└─────────────────────────────────────┘
[Graph fills screen; two‑finger pan/zoom]
[Tap node] → bottom sheet drawer 75% height with details.
[Timeline] → vertical list grouped by threads; cards stack; horizontal swipe to move through dates.
```

---

### 19.5 Component Inventory (Bootstrap/htmx mapping)
- **Navbar**: `.navbar .form-control` search; keyboard focus trap.
- **Sidebar**: `.offcanvas` on mobile; checkboxes for edge types; date range as two inputs.
- **Graph Canvas**: `<div id="cy">` (Cytoscape); controls as floating `.btn-group`.
- **Timeline**: `<div id="timeline">` (Vis Timeline or custom SVG in a scroll container).
- **Details Drawer**: `.offcanvas-end` with sections (sources, tags, relations, actions).
- **Toasts**: `.toast` bottom‑right for saves/errors.

---

### 19.6 Key Flows
1) **Focus a node from search** → type‑ahead selects event → graph zooms/centers; drawer opens.
2) **Create relation from timeline** → multi‑select two cards → toolbar “Create relation” → choose type → confirm; graph updates too.
3) **Filter by date** → adjust slider → both Graph and Timeline tabs respect filter.

---

### 19.7 Open Questions for Wireframes
- Do we show Story nodes as separate pills attached to Events in Graph, or only in Drawer?
- Should the Timeline lane height auto‑expand for dense months, or truncate with a “+N more” chip?
- Where should the mini‑map live on mobile?
