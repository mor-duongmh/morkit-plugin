# Test-case wording conventions

Mined from a real project test-case workbook. The skill MUST mimic this style when expanding cases (Step 6). Goal: output indistinguishable from cases a human QA on this team would write.

## Columns the skill fills

| Col | Field | Convention |
|-----|-------|------------|
| B | Test Case Description | Terse imperative. `Check "<thing>"`. Quote UI labels. **Blank on continuation rows.** Also used alone as a **section header** row. |
| C | Pre-Condition | Sparse — often blank. Used for data-state or context variants: `No data`, `Have data`, `User accesses URL`. |
| D | Test Case Procedure | Numbered steps `1. … \n 2. …` OR short freeform (`Check UI`, `1. Check default`). Imperative verbs. |
| E | Expected Output | Multiline, concrete, bulleted/numbered. Real values, not vague. |

## Description (B) patterns
- `Check "Radaro Media Viewer" page`
- `Check the URL path`
- `Check "Image" tab`
- `Check zoom in/out`
- `Check pagination`
- `Check button "Download"`

Rules:
- Start with `Check` for verification cases. Quote exact UI labels/buttons/tabs.
- One description = one logical item. Its variations go in **continuation rows** (blank B), each with its own C/D/E.

## Continuation rows (blank B)
One item, multiple checks. Example (`Check Grid view`):

| B | C | D | E |
|---|---|---|---|
| Check Grid view | No data | Check the display | - Display "No media found" |
| *(blank)* | Have data | 1. Click on "Image" tab | The grid view displays the full image list from the database |
| *(blank)* | | 1. Check default | Highlight on the first image |
| *(blank)* | | 1. Check the sorting | - Image list sorted by database |

In `cases.json`: ONE case with `description: "Check Grid view"` + a `rows[]` of 4 rows.

## Procedure (D) patterns
- `1. Open Radaro Media Viewer page`
- `1. Hover your mouse over the fields. \n 2. Click on each field.`
- `1. Access \n 2. Zoom in/ Zoom out the screen`
- `1. While on page 1, click the [>] button.`
- `Check UI` (freeform when a single inspection)

Use literal `\n` between numbered steps. Keep steps atomic + imperative.

## Expected Output (E) patterns
- `The screen "Radaro Media Viewer" page is displayed.`
- Multiline structural list:
  ```
  Header:
   - Logo
   - Job ID
   - Menu tab
  Left Sidebar:
   - ...
  ```
- Boundary/abnormal with concrete values:
  - `- Zoom stops at maximum allowed level (400%) \n - Image remains viewable`
  - `- Show image 1 \n - Button [<] disable`
  - `- Display screen "No media found"`

Rules:
- Always concrete. Put real limits (400%, 25%), real button states (disable/enable), real messages ("No media found").
- Multiline OK; use `\n`. Writer enables wrap-text.
- Every written row MUST have non-empty Expected (column A auto-ID depends on it).

## Normal vs abnormal coverage
Embed both. Examples of abnormal/edge to always consider:
- Empty/no-data states.
- Boundary limits (min/max zoom, first/last page, pagination disable states).
- Invalid input, special chars, oversized input.
- Permission-denied / not-logged-in.
- Error/timeout responses.

(Viewpoint + normal/abnormal tags live in scope.md as metadata; they are NOT written to the Excel — the template has no column for them.)

## Output language
B/C/D/E text is written in the **output language** chosen per run (en / vi / ja). The sample above is English. Keep UI labels verbatim regardless of language (they appear as shown in the app).
