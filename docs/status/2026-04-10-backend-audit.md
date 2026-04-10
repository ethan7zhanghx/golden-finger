# Backend audit — 2026-04-10

## Observation

The top-level issue thread asked for a factual project-progress update after earlier work was mistakenly pushed to the wrong repository. On the BE branch checked out for this task, the working tree initially only contained documentation, while the PM thread claimed migrated code already existed in `golden-finger`.

## Competing hypotheses

1. The migrated implementation never reached `golden-finger`.
2. The migrated implementation existed, but only on another branch and was not present on the current BE branch.
3. The PM status comment overstated the available backend runtime state.

## Evidence

### For hypothesis 2
- `git log --all` showed migrated commits on branch `agent/pm/2e410f21` (`2f7ddd0`, `25ac5f7`, `7ce5306`).
- `git ls-tree -r --name-only 7ce5306` showed `backend/`, `frontend/`, and `docker-compose.yml` files.
- The current BE branch head before reconciliation only exposed docs files.

### For hypothesis 3
- After reconciling the PM branch commits onto the BE branch, backend AI workflow code and API skeleton were present.
- Running `python3 -m unittest backend.tests_ai.test_workflows` initially failed under the local Python 3.9 runtime with:
  - `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`
- Root cause: runtime-evaluated PEP 604 union annotations in files lacking `from __future__ import annotations`.

## Root cause

The previously migrated code was real, but it lived on a different branch and the current BE branch was not carrying it forward. In addition, the migrated backend skeleton had a Python-version compatibility bug that broke the AI workflow test suite on Python 3.9 before execution could proceed.

## Minimal fix applied

1. Cherry-picked the migrated implementation commits onto the current BE branch:
   - `2f7ddd0` — migrate M2 code
   - `25ac5f7` — fix test import paths
   - `7ce5306` — add backend API skeleton and docker-compose
2. Added postponed annotation evaluation to restore Python 3.9 compatibility:
   - `backend/ai/workflow_router.py`
   - `backend/app/tasks/celery_app.py`

## Current backend status after reconciliation

### Present
- AI workflow modules for `worldview`, `selling_point`, `hook`
- Prompt templates and JSON schemas
- FastAPI skeleton with AI-oriented routes/services
- Celery app placeholder wiring
- Docker Compose skeleton
- Frontend scaffold migrated alongside backend base

### Still missing for the backend core
- Database models and migrations
- Project CRUD APIs
- Auth/JWT flow
- Step/asset persistence APIs
- End-to-end runtime verification with installed dependencies and a real ERNIE integration

## Verification

- `git log --oneline --decorate --graph --all --max-count=12` confirms the migrated commits are now on the BE branch.
- `python3 -m unittest backend.tests_ai.test_workflows` now passes locally under Python 3.9.

## Risks / remaining gaps

- No dependency installation or FastAPI app boot verification was performed in this session.
- Placeholder AI service / Celery wiring is not yet production-ready.
- The repository still needs backend persistence and auth before the MVP can be considered complete.

## Suggested next step

Implement the database layer and project CRUD as the next backend milestone, then verify with API-level tests and app startup checks.
