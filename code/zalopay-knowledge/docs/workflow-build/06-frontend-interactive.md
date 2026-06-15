# Phase 6 — Interactive frontend (OPTIONAL, post-demo)

> **Not required for the demo.** The executor (Phase 5) returns a step-by-step markdown answer
> that the existing chat UI already renders. Do this phase only if there's time to make
> checklists tickable and gates clickable.

## Goal

Render workflow steps as interactive elements (checklist with checkboxes, gate options,
per-step progress) instead of plain markdown.

## Background (verified in repo)

- API client: `frontend/src/lib/apiClient.ts` (`chatStream`, SSE parser).
- Chat hook: `frontend/src/hooks/useChat.ts` (handles `start`/`node`/`pipeline`/`error`/`done`).
- Renderer: `frontend/src/components/chat/AssistantMessage.tsx` → `AnswerCard`.
- Types: `frontend/src/lib/types.ts`. Response schema: `app/api/schemas.py` (`ChatResponse`,
  `ClarifyingQuestion` is the only interactive element today).

## What to build

1. **Backend schema** (`app/api/schemas.py`): add optional `workflow_steps: list[WorkflowStepView]`
   to `ChatResponse`, where `WorkflowStepView` has `id`, `title`, `type`
   (`checklist`/`gate`/`action`/`info`), `status` (`pending`/`done`/`skipped`), and type-specific
   payload (`items: [{label, checked}]` for checklist; `options: [{label}]` for gate; `jira_key`
   / `jira_url` for action). Have the executor (Phase 5) populate this alongside the markdown
   `answer` so the UI can choose either rendering.
2. **TS types** (`frontend/src/lib/types.ts`): mirror `WorkflowStepView`.
3. **Component** (`frontend/src/components/chat/WorkflowSteps.tsx`): render the steps —
   checkboxes for checklist items, buttons for gate options, a Jira link chip for actions, and a
   per-step status indicator. Wire into `AssistantMessage.tsx` when `workflow_steps` is present.
4. **(Stretch) interactivity loop**: ticking a checklist / choosing a gate option sends a
   follow-up message (reuse the existing `onClarifySelect`/`onSuggestedSelect` pattern in
   `useChat.ts`) — this would require the executor to support a multi-turn/resumable mode,
   which is explicitly **out of scope** for the demo. Keep this read-only unless that work is
   scheduled.

## Tests

- `frontend` Vitest for `WorkflowSteps.tsx` rendering each step type.
- `npm run typecheck`. Backend: extend the chat contract test to allow the new optional field.

## Verify

`make fe-build`, `npm run typecheck`, `npm test`.

---

## Copy-paste Agent Prompt

> You are working in `code/zalopay-knowledge/`. Implement **Phase 6 (optional)**: render workflow
> steps as interactive UI. Phase 5 is merged and the executor returns a markdown `answer`.
>
> 1. Read `app/api/schemas.py` (`ChatResponse`, `ClarifyingQuestion`),
>    `frontend/src/lib/types.ts`, `frontend/src/components/chat/AssistantMessage.tsx`,
>    `frontend/src/hooks/useChat.ts`.
> 2. Add an optional `workflow_steps: list[WorkflowStepView]` field to `ChatResponse` and have
>    the Phase 5 executor populate it (id, title, type, status, and type-specific payload:
>    checklist items, gate options, jira_key/url for actions). Mirror the type in
>    `frontend/src/lib/types.ts`.
> 3. Create `frontend/src/components/chat/WorkflowSteps.tsx` rendering checklist checkboxes,
>    gate option buttons, Jira link chips, and per-step status. Show it from `AssistantMessage.tsx`
>    when `workflow_steps` is present; otherwise fall back to the markdown answer.
> 4. Keep it **read-only** (no resumable execution) unless multi-turn execution is separately
>    scheduled. Add a Vitest for the component and update the chat contract test for the new
>    optional field.
>
> Run `make fe-build`, `npm run typecheck`, `npm test`. Report changes + output.
