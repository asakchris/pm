# Code Review — PM MVP

**Date:** 2026-04-13  
**Scope:** Full repository — backend, frontend, Docker configuration, tests  
**Severity legend:** 🔴 Must fix | 🟡 Should fix | 🔵 Consider

---

## Backend

### 🔴 `int()` conversions in `ai.py` can raise unhandled `ValueError`

**File:** `backend/app/ai.py:137, 172, 195, 209, 215, 232, 253`

The AI model returns `columnId` and `cardId` as strings (schema-specified). Every usage does `int(action.columnId)` or `int(action.cardId)` with no guard:

```python
(int(action.columnId), board_id),  # ai.py:137
```

If the model returns a non-numeric string (e.g., `"col-3"`, `"none"`, or a hallucinated name), this raises `ValueError`, which FastAPI converts to an unhandled 500 with no useful detail. Add validation at parse time or wrap each conversion:

```python
try:
    column_id_int = int(action.columnId)
except ValueError:
    continue  # or log and skip
```

Or add a validator to the action models in `models.py`:

```python
class CreateCardAction(BaseModel):
    columnId: str

    @field_validator("columnId")
    @classmethod
    def must_be_numeric(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("columnId must be a numeric string")
        return v
```

---

### 🔴 Static file path traversal

**File:** `backend/app/routes/static.py:47`

```python
requested_path = STATIC_DIR / full_path
```

FastAPI's `{full_path:path}` path parameter does not strip `../` sequences. A request to `/../../../etc/passwd` constructs a path outside `STATIC_DIR` and then serves the file if it exists. Fix:

```python
requested_path = (STATIC_DIR / full_path).resolve()
if not str(requested_path).startswith(str(STATIC_DIR.resolve())):
    return HTMLResponse("Not found", status_code=404)
```

---

### 🟡 `get_db` is duplicated

**Files:** `backend/app/database.py:78-83` and `backend/app/dependencies.py:5-13`

Both files define an identical `get_db` generator. Routes import from `dependencies`, so `database.get_db` is dead code. Remove it from `database.py`.

---

### 🟡 AI action failures are silent

**File:** `backend/app/ai.py:139-140, 173-174, 197-198, 250-251`

When a referenced column or card doesn't exist, `apply_actions` silently `continue`s:

```python
if not column:
    continue  # no feedback, chat response says "Done!"
```

The user receives a success response with no indication that one or more actions were skipped. At minimum, collect skipped actions and include them in the log or the `ChatResponse`.

---

### 🟡 Position normalisation logic is duplicated

**Files:** `backend/app/routes/board.py` (create/update card and column), `backend/app/ai.py:148-152, 224-228`

The same three-line pattern appears five times:

```python
if insert_position is None or insert_position > len(ids):
    insert_position = len(ids)
if insert_position < 0:
    insert_position = 0
```

Extract to a helper in `database.py`:

```python
def clamp_position(position: int | None, count: int) -> int:
    if position is None or position > count:
        return count
    return max(0, position)
```

---

### 🟡 AI action models have no field validation

**File:** `backend/app/models.py:35-60`

`CreateCardAction.title` has no `min_length`, so the AI can create cards with empty titles — which `CardCreate` (used by the REST API) correctly rejects. Align them:

```python
class CreateCardAction(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    details: str = Field(default="", max_length=5000)
```

---

### 🟡 No CORS middleware

**File:** `backend/app/main.py`

Frontend running via `npm run dev` (port 3000) cannot call the backend (port 8000) without CORS headers. In Docker where both origins are the same domain it works, but local development without Docker requires:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 🟡 No rate limiting on `/api/chat`

**File:** `backend/app/routes/chat.py`

Every request to `/api/chat` makes a paid OpenRouter API call with no throttle. A misbehaving client or looping script will exhaust the API budget silently. Add a simple per-user cooldown in the route handler.

---

### 🔵 `ChatResponse.board` is loosely typed

**File:** `backend/app/models.py:82`

```python
board: dict | None = None
```

The actual structure is the same `BoardResponse` returned by `/api/board`. Typing it as `dict` loses schema documentation and IDE support. Consider a shared `BoardPayload` TypedDict or Pydantic model.

---

### 🔵 Fallback HTML still says "PM MVP"

**File:** `backend/app/routes/static.py:17`

The `FALLBACK_HTML` constant (shown when no static build is present) has `<title>PM MVP</title>`. The app is now "Kanban Studio". Minor, but worth aligning.

---

### 🔵 No startup logging for missing config

**File:** `backend/app/main.py`

If `OPENROUTER_API_KEY` is absent, the app starts without error and fails only on the first chat request. A startup warning via `logging.warning` would help operators catch misconfiguration earlier.

---

## Frontend

### 🟡 Double ID prefix in `KanbanColumn` and `KanbanCard`

**Files:** `frontend/src/components/KanbanColumn.tsx:59`, `frontend/src/components/KanbanCard.tsx:15`

After `toBoardData()` in `api.ts`, card IDs are already prefixed (e.g., `"card-1"`). But both components add the prefix again via template literals:

```typescript
// KanbanColumn.tsx:59 — cardId is already "card-1", creates "card-card-1"
items={column.cardIds.map((cardId) => `card-${cardId}`)}

// KanbanCard.tsx:15 — card.id is already "card-1", creates "card-card-1"
id: `card-${card.id}`,
```

This does **not** break drag-and-drop today because both values are consistently double-prefixed so the `SortableContext` items and `useSortable` IDs still match. API calls are safe because `handleDragEnd` in `KanbanBoard.tsx:88` reads `event.active.data.current?.cardId` (which uses `card.id` directly, not the sortable ID). However, the `data-testid` on cards at `KanbanCard.tsx:35` also ends up as `card-card-1`, which could break E2E tests that query by that attribute.

Fix by passing IDs through directly (they are already prefixed):

```typescript
// KanbanColumn.tsx:59
items={column.cardIds}

// KanbanCard.tsx:15
id: card.id,
```

---

### 🟡 Board refresh on every operation replaces optimistic state

**File:** `frontend/src/app/page.tsx`

Every mutation (add card, delete card, move card) calls `refreshBoard()` after the API responds. This causes a full board re-render on every user interaction. Drag-and-drop state is already applied optimistically via `setBoard` in `KanbanBoard.tsx`, so the refresh stomps the local state with the server state unnecessarily for operations that don't need it. For delete and rename, this is harmless but wasteful. For move, the board refresh races with the optimistic update.

Consider only refreshing after chat AI updates (where the board genuinely changes in ways the frontend doesn't know about) and relying on local state mutations for user-driven CRUD.

---

### 🟡 `data-testid` on cards will be `card-card-N` due to double prefix

**File:** `frontend/src/components/KanbanCard.tsx:35`

```typescript
data-testid={`card-${card.id}`}
```

With `card.id = "card-1"`, this renders `data-testid="card-card-1"`. If any E2E test ever selects cards by testid pattern, they must use `card-card-1` to match — which is non-obvious and fragile. Fixing the double prefix (see above) resolves this automatically.

---

### 🟡 `page.test.tsx` uses `initialData` (static mock), not API responses

**File:** `frontend/src/app/page.test.tsx`

The page tests render with static `initialData` from `kanban.ts`, bypassing the `fetchBoard` → `toBoardData` pipeline. This means tests won't catch breakage in the `api.ts` → board state conversion path. Tests should mock `fetchBoard` and return backend-shaped data so the full transformation is exercised.

---

### 🔵 No tests for chat error handling

**File:** `frontend/src/components/ChatSidebar.test.tsx`

The two existing tests only cover the happy path (submit and display). There are no tests for:
- Network error during chat (`fetch` rejects)
- Non-OK HTTP response (e.g., 500)
- Empty `response` field in the reply

---

### 🔵 `NewCardForm` has no test file

**File:** `frontend/src/components/NewCardForm.tsx`

The form logic (expand on click, submit, clear after submit) is untested. Given it's the primary entry point for card creation, it warrants at least a basic unit test.

---

## Docker / Infrastructure

### 🟡 `docs/` was missing from Docker image until recently fixed

**File:** `Dockerfile` (now fixed in this session)

`docs/kanban-schema.json` is referenced by `test_schema_json_structure` via a relative path resolving to `/app/docs/`. The `COPY docs /app/docs` line was absent, causing the test to fail in Docker. This was fixed; noting it here so the pattern isn't repeated if new test files reference other repo-root assets.

---

### 🔵 Authentication is `X-User` header with no secret

**File:** `backend/app/dependencies.py:18-19`

```python
def get_username(x_user: str | None = Header(default=None)) -> str:
    return x_user or DEFAULT_USER
```

This is intentional for the MVP (single user, local Docker). The risk is clear: any client that sets `X-User: alice` gets Alice's board. This is fine for the stated scope but must not be deployed to a shared or internet-accessible host without replacing with real authentication.

---

## Test Gaps Summary

| Area | Gap |
|------|-----|
| `test_ai_actions.py` | No test for `int()` ValueError when model returns non-numeric ID |
| `test_ai_actions.py` | No boundary tests: `position=-1`, `position=999` |
| `test_board_api.py` | No test for moving card across columns via `PATCH /api/cards/{id}` |
| `frontend/page.test.tsx` | Uses static mock data, bypasses `toBoardData` transform |
| `frontend/ChatSidebar.test.tsx` | No error-state coverage (network failures, 5xx) |
| Frontend | `NewCardForm` is entirely untested |

---

## Priority Order

1. **Fix `int()` conversion crash** (`ai.py`) — can produce unhandled 500s in production with no actionable error
2. **Fix static file path traversal** (`routes/static.py`) — low exploitation risk in Docker but trivial to fix
3. **Fix double ID prefix** (`KanbanColumn.tsx`, `KanbanCard.tsx`) — works today but is incorrect and fragile
4. **Remove duplicate `get_db`** (`database.py`) — dead code, causes confusion
5. **Add CORS middleware** — needed for local development without Docker
6. **Surface AI action failures** in chat response
7. **Add rate limiting** to `/api/chat`
8. Remaining 🔵 items as time permits
