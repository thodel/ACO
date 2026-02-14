# Session-by-Session Council Timeline (Ephesus 431)

This file records uncertainties and data gaps that must be resolved before a
day-by-day council session timeline can be built with reliable scholarly value.
It is intentionally conservative: anything not explicitly supported by data in
this repo or a cited primary/secondary source is listed here as open.

## Scope and Definition Uncertainties
- Which timeline scope is desired?
  - Only June–July 431 council sessions?
  - Include pre-council preparations and post-council fallout (431–433)?
- Which body/bodies are in scope?
  - Only the main (Cyrillian) sessions?
  - Also include the counter-synod sessions held by the Antiochene party?
- How to represent parallel or overlapping sessions on the same day?
  - Separate lanes or a merged day with concurrent sessions?

## Session Calendar and Numbering
- Exact date for each session (day/month) is not represented in current data.
- Session numbering schemes differ across editions; a canonical mapping is needed.
- Calendar system (Julian vs local calendar) must be explicit for all dates.
- Are there sessions with disputed dates or disputed numbering? If yes, how to
  represent variants (alternate dates, confidence scores, footnotes)?

## Document-to-Session Mapping
- No explicit mapping exists between ACO document IDs and council sessions.
- Some documents are read or referenced in later sessions; rules for mapping
  read-in documents vs. authored-in-session documents are unclear.
- Some documents are dated only by year or season; day-level anchoring is not
  currently possible without external sources.

## Participants and Attendance
- Attendance lists per session are not extracted from the texts.
- Role annotations (bishop, presbyter, imperial official, monk, notary, etc.)
  are not present in the register dataset.
- Name normalization across languages (Greek/Latin) and variants is incomplete.

## Outcomes and Decisions
- No structured data for session outcomes exists (e.g., depositions, condemnations,
  doctrinal statements, procedural motions).
- Need a controlled vocabulary for outcome types, plus citations for each outcome.

## Data Source and Provenance
- The repository does not currently include a session list or session dates.
- Required sources to consult and cite are not yet specified in-project.
  - Primary: ACO acts, session headings, acta, and notarial notes.
  - Secondary: modern reconstructions of the session calendar and proceedings.
- Provenance for each session data point must be recorded (source and page/line).

## Representing Uncertainty in the UI
- Decide how to represent approximate or disputed dates:
  - Date ranges, fuzzy bands, or confidence markers.
- Decide how to show alternative session numbering or dating.

## Proposed Minimal Data Model (Tentative)
This is a candidate schema; it is not validated by sources yet.

```
session_id: string            # e.g., "sess-01" (stable internal id)
date: string|null             # YYYY-MM-DD (Julian) or null if unknown
date_range: [string,string]|null  # for approximate dates
session_number: string|null   # "I", "II", "III" with edition mapping
body: string                  # "cyrillian" | "antiochene" | "other" (TBD)
location: string|null         # usually "Ephesus" but may vary
documents: [doc_id]           # ACO doc ids read/issued in session
participants: [person_id]     # normalized person ids
outcomes: [{type, summary, source_ref}]
sources: [{citation, page, note}]
confidence: number            # 0..1
```

## Immediate Next Steps (To Resolve Uncertainties)
- Define the exact scope and which synods/bodies to include.
- Compile a session calendar with dates and numbering from a primary source.
- Build an explicit document-to-session mapping table.
- Extract participant lists where available and link to register entries.
- Agree on how to model and display uncertainty in the visualization.
