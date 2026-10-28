# memv4.md

## V4 implementation specification: continual learning, authorized cross-project lessons, consolidation, and verified hard purge

**Parent specification:** `MEMORY.md`  
**Required predecessors:** `memv1.md`, `memv2.md`, and `memv3.md`  
**V4 source phases:** Phases 7 and 8 of `MEMORY.md`  
**Product:** AI Virtual Pod  
**Purpose:** Complete the memory implementation by letting the Virtual Pod extract evidence-backed lesson candidates at task completion, validate and activate lessons through an explicit authority-controlled lifecycle, retrieve sanitized cross-project lessons only when authorized, safely deduplicate and consolidate lessons, and execute verifiable hard purges of memory content and derived copies.

**Important status statement:** This document is an implementation specification, not evidence that V1, V2, or V3 is already deployed or passing. V4 MUST verify the real repository and completed predecessor handoffs before changing behavior.

---

## 0. How to use this specification

The terms **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are normative.

1. `MEMORY.md` defines the target architecture and semantics.
2. `memv1.md` defines V1's actual implementation boundary and handoff.
3. `memv2.md` adds controlled JSONL import, `memory_items`, `memory_chunks`, full-text search, exact lookup, and progressive disclosure.
4. `memv3.md` adds gated pgvector semantic retrieval and RRF while preserving V2 behavior.
5. This file defines only the additional V4 work: lesson extraction and lifecycle, authorized cross-project reuse, deduplication, evidence-preserving consolidation, and hard-purge verification.

If a conflict is found, do not quietly choose whichever wording is easiest. Stop the affected change, document the conflict, inspect the actual predecessor implementation, and record a deliberate resolution in the repository. Preserve existing runtime behavior unless a needed correction has been approved.

### 0.1 Binding architectural rules

- PostgreSQL remains the canonical store for the structured records assigned to it by the source-of-truth matrix.
- Approved Markdown, source code, transcripts, and other project artifacts remain canonical at their existing locations. Memory records and chunks point to them; they do not replace them.
- `memory_items` holds bounded, durable memory records, including lessons. Do not create a separate lesson database or parallel lesson file store.
- `memory_chunks` and embeddings are derived, rebuildable retrieval indexes, never authority.
- Use the existing memory facade and worker/job runner. Add behavior to them; do not build a memory microservice, second worker platform, new vector database, or new general-purpose graph database.
- The existing Graphify workflow remains for codebase relationships. `memory_links` records only explicit relationships among memory records, decisions, events, tasks, and evidence.
- One logical fact has one canonical writable owner. No new dual-writes to PostgreSQL and JSONL or to multiple task stores.
- Extracted content starts as `proposed`. An LLM, high embedding similarity, successful job, or repeated appearance MUST NOT automatically activate a lesson.
- Cross-project visibility is an authorization decision enforced by application logic and SQL, not a prompt instruction.
- Deletion must stop retrieval immediately and hard purge must verify the removal of in-scope derived copies.
- Never store secrets, credentials, hidden model reasoning, or arbitrary raw tool-call streams as lessons.
- V4 must not introduce retrieval rerankers, query rewriting agents, reinforcement learning, custom memory models, or automated ranking optimization. V4 completes the specified lifecycle and maintenance work only.

---

## 1. V4 outcome

At the end of V4, the Virtual Pod must be able to:

1. Explicitly request lesson extraction when a task completes, using its final checkpoint, meaningful events, evidence, and artifact references.
2. Create structured, source-backed lesson candidates with `status = 'proposed'` and `memory_type = 'lesson'`.
3. Validate candidates through an authorized review path, keep validated and active as separate states, and refuse unsupported or under-specified lessons.
4. Activate validated lessons only under an explicit approval/policy decision.
5. Retrieve active lessons within their authorized task, repository, or project scope using the existing `search_memory` facade and V3 retrieval pipeline.
6. Promote a genuinely reusable, sanitized lesson to `cross_project` scope only after an authorized review and audit trail.
7. Detect exact duplicates deterministically; identify near-duplicates and contradictions as candidates for review; merge only compatible records without losing evidence or scope controls.
8. Consolidate repetitive evidence into a proposed reusable lesson while preserving original sources, exceptions, limitations, and links.
9. Logically delete or hard-purge authorized memory records, their chunks, embeddings, derived summaries, cached copies owned by the system, and pending jobs that could recreate them.
10. Verify a hard purge across SQL, exact lookup, full text search, vector retrieval, details retrieval, job queues, and known in-system derived copies before reporting success.
11. Complete the original `MEMORY.md` Phases 7 and 8 acceptance criteria without changing the Virtual Pod's primary purpose.

V4 is not complete when extraction code runs or lessons appear in a table. It is complete when agents can use validated lessons safely, real cross-project retrieval stays within permission boundaries, consolidation lowers duplicate noise without destroying evidence, and purge verification demonstrates absence of in-scope content.

---

## 2. Mandatory V1, V2, and V3 entry gate

V4 MUST NOT begin until each predecessor has a real handoff and test evidence. A document that says tests passed is not sufficient by itself; verify the repository implementation and run its test commands.

### 2.1 V1 gate: continuity and decision traceability

Verify all of the following:

- PostgreSQL owns each cut-over structured record type, and no independent writer continues to update that same state in JSONL or another store.
- `projects`, tasks/checkpoints, decisions, and append-only events have the documented ownership and constraints.
- `get_current_context`, `record_event`, and `update_task_checkpoint` work through the existing facade.
- Task checkpoints survive restart and permit a new session to resume.
- Checkpoint updates use optimistic concurrency.
- Decision approval and supersession are transactional, and current context excludes superseded guidance.
- Source references remain references, not copied source-of-truth documents.
- V1 acceptance tests, especially `MEMORY.md` §28.1 and §28.7, pass.

### 2.2 V2 gate: controlled migration and keyword retrieval

Verify:

- JSONL imports were performed by record type, reported malformed or conflicting records, and passed idempotency checks.
- Each migrated record type has a documented single-writer cutover. There are no ongoing independent dual-writes.
- `memory_items` and `memory_chunks` exist under the project's migration mechanism.
- Exact lookup, PostgreSQL full text search, mandatory project/scope/status filters, compact result envelopes, `get_memory_details`, and progressive disclosure work.
- Source freshness is checked against the canonical source.
- The five-task memory-enabled versus memory-disabled evaluation exists, with original task inputs and expected evidence preserved.
- `MEMORY.md` §28.2 and §28.4 and the V2 regression suite pass.

### 2.3 V3 gate: semantic retrieval

Verify:

- V3 was implemented only after a real semantic miss demonstrated the need; if not, V3 may be deferred and V4 must not silently assume vectors exist.
- The embedding provider/model identifier and vector dimension are pinned and documented.
- Only selected eligible sections are embedded. The same model/version is used for stored chunks and query embeddings.
- `search_memory` retains deterministic exact lookup, keyword retrieval, mandatory authorization/status/scope/freshness filtering, RRF, deduplication, compact results, source references, and fallback to V2 search.
- Stale chunks and embeddings cannot be returned as current after a source change or deletion.
- Retrieval logging avoids raw query/content by default and has the documented retention/access behavior.
- The V3 semantic and project-boundary tests, V1/V2 regression tests, and V3 evaluation pass.

### 2.4 If a gate fails

Stop V4 implementation at the failed predecessor gate. Fix the predecessor under its own specification, update its handoff, and rerun its tests. Do not describe predecessor repairs as V4 functionality. V4 can still produce a repository audit and proposed implementation plan, but it cannot be marked implemented or complete.

### 2.5 Record the gate result

Before code changes, record in the V4 handoff:

- Path to V1, V2, and V3 handoffs.
- Exact test commands and observed results.
- Actual schema and APIs inspected.
- Which existing job runner, authorization service, logging facilities, migrations, and agent task-completion hook will be reused.
- Any unresolved ownership, security, or source-of-truth issue.

---

## 3. Exact V4 scope and exclusions

### 3.1 Included work

| Original `MEMORY.md` section | V4 implementation |
|---|---|
| Phase 7 | Lesson proposal and validation; task-end extraction; explicit activation; authorized cross-project promotion and retrieval. |
| Phase 8 | Exact deduplication; near-duplicate and contradiction candidates; consolidation with evidence links; stale derived-copy cleanup; hard-purge workflow and verification; focused maintenance metrics. |
| §8.6 | Extend the existing `memory_items` representation for lesson fields only where fields or equivalent constraints are missing. |
| §8.7 | Add or reuse `memory_links` for explicit provenance, derivation, duplicate, applicability, contradiction, extension, and supersession relationships. |
| §8.9 | Extend the existing job mechanism for extraction, consolidation, and purge tasks; do not introduce a second queue. |
| §10 | Explicit, bounded lesson extraction from completed task evidence. |
| §11 | Exact duplicate handling, candidate-based near-duplicate detection, evidence-backed conflict review. |
| §12 | `proposed → validated → active` lifecycle and permitted terminal/history states. |
| §16.4 and Appendix C.12 | Authorized logical deletion, hard purge of in-scope memory copies, and verification. |
| §17 | Evidence-preserving durable consolidation; runtime task checkpoint compaction remains V1 behavior. |
| §20 | Explicitly authorized, sanitized cross-project lesson promotion and retrieval. |
| §22 | Reuse or minimally extend reliable background jobs with idempotency, retries, cancellation, and traceability. |
| §23 | Implement or extend `propose_lesson`, `validate_or_activate_lesson`, `delete_memory`, `supersede_memory`, and `search_memory` behavior using the existing facade. |
| §28.5, §28.6, §28.8, §28.13, §28.14 | Cross-project lesson isolation, inference labeling, purge verification, consolidation provenance, and prompt-injection safety. |

### 3.2 Explicitly out of scope for V4

V4 MUST NOT add:

- A new memory database or vector database.
- A memory microservice or a second worker system.
- A graph database or broad code relationship graph.
- A custom memory-trained model, model fine tuning, reinforcement learning, or retrieval-policy training.
- A separate reranker, autonomous query rewriting agent, or agentic multi-step retrieval planner.
- Autonomous activation of LLM-generated lessons.
- Automatic cross-project promotion without explicit authorization and review.
- Blanket ingestion or embedding of all transcripts, tool calls, logs, files, or source code.
- Destructive compaction of original transcripts, approved artifacts, source code, Git history, required audit records, or decision evidence.
- A separate lesson store when `memory_items` can represent lessons.
- A separate relationship graph service when `memory_links` can represent the required explicit relationships.
- New general-purpose CLI/TUI work solely for memory. Reuse existing developer and admin surfaces where available.
- Automatic memory quality optimization, learned ranking, generic recency decay, or unexplained scoring rules.
- A recurring expensive consolidation process unless actual workload demonstrates it is useful and maintainers approve it.

V4 may add narrow configuration, schema constraints, and internal APIs required for its included work. Every addition must trace to one of the included requirements above.

---

## 4. V4 architecture: extend, do not replace

### 4.1 Component ownership

| Component | V4 responsibility | Required constraint |
|---|---|---|
| Existing agent task-completion lifecycle | Explicitly enqueue lesson extraction for a completed task using stable task/checkpoint identity | No extraction per tool call; no blocking the successful task response on LLM processing. |
| Existing memory facade | Provide lesson APIs, enforce authorization, use existing search behavior, return structured job status | No duplicate public interface or direct database writes from agents. |
| PostgreSQL `memory_items` | Own durable lesson records and lifecycle state | One canonical lesson row per independently meaningful lesson. |
| PostgreSQL `memory_links` | Record typed connections and provenance | Create only explicit, justified links. No implicit graph semantics. |
| PostgreSQL `memory_events` | Append meaningful extraction, validation, activation, promotion, merge, invalidation, purge, and consolidation events | No raw sensitive content in audit payloads. Normal events remain append-only. |
| Existing `memory_chunks` | Index eligible active lesson content for V2/V3 search | Chunk content/status/version must be checked against canonical `memory_items` at retrieval time. |
| V3 embedding fields | Store embeddings only for eligible current chunks under the pinned model | Reuse V3 model/dimension/provider decisions; V4 does not select a new model. |
| Existing job runner / `memory_jobs` | Run bounded extraction, consolidation, reindex, and purge work | Reuse the runner; extend job types only as required. |
| Existing authorization service | Authorize candidate creation, validation, activation, promotion, retrieval, deletion, and purge | SQL and service enforcement; never rely on prompt instructions. |
| Existing source artifact resolver | Resolve and verify evidence references | Broken or inaccessible evidence is reported, never fabricated. |
| Existing Graphify | Continue codebase relationship analysis | No V4 changes to Graphify's role. |

### 4.2 Component/data flow

```text
Task reaches completed state
        |
        v
Existing task completion transaction
  - checkpoint/version is finalized
  - task.completed event is recorded
  - idempotent extraction job is enqueued
        |
        v
Existing worker claims extraction job
        |
        v
Load bounded evidence set with permissions
  - final checkpoint
  - relevant task events and decisions
  - cited test/evidence results
  - changed artifact/source references
        |
        v
Extract schema-valid candidate lessons
        |
        v
Redact/validate source refs and scope
        |
        v
Exact dedupe + lexical/vector candidate lookup
        |
        +--> same claim: attach new provenance or skip duplicate
        +--> possible duplicate/conflict: create review candidate
        +--> distinct supported lesson: create proposed memory_item
        +--> unsupported/low-value content: reject and record category
        |
        v
Authorized reviewer validates candidate
        |
        v
Authorized activation/promotion decision
        |
        +--> active project/repository lesson
        +--> separately sanitized cross_project lesson
        |
        v
Idempotent reindex and optional bounded consolidation job
        |
        v
Existing search_memory retrieves only currently eligible,
source-backed, authorized active lessons with citations
```

### 4.3 Truth remains separate from learning

- Current task state comes from V1's canonical task/checkpoint system.
- Current approved decisions come from V1's canonical decision system and approved artifact references.
- Lesson lifecycle state comes from `memory_items` after V4's schema checks and controlled transitions.
- Search candidates come from the V2/V3 derived `memory_chunks` index.
- Relationships come from `memory_links` if installed, or the smallest approved migration that adds it.
- Extraction or consolidation output is a proposal, not current truth.
- No embedding score, duplicate detector, extraction model, or consolidation model can approve an architecture decision or change a project requirement.

---

## 5. V4 schema changes and migration rules

Before writing a migration, inspect the actual V1/V2/V3 schema. The tables and fields below define required semantics. If an equivalent field or constraint already exists, reuse it. Do not create duplicate columns under different names.

### 5.1 `memory_items`: lessons use the existing table

V4 MUST use the existing `memory_items` table for lessons. Do not create a `lessons` table.

The record must support these semantic fields, either as existing columns or through a forward migration:

| Field / concept | Required V4 meaning |
|---|---|
| `id` | Stable UUID or equivalent canonical identifier. Never reuse an ID after deletion. |
| `project_id` | Originating project for a project-owned lesson. Nullable only for a truly cross-project lesson under the project's existing schema contract. Null MUST NOT imply public access. |
| `memory_type` | `lesson` for extracted/reusable lessons. Existing non-lesson types retain their V2 meanings. |
| `scope` | Existing supported scope enum such as `task`, `repository`, `project`, or `cross_project`. Only use values the actual schema accepts after a reviewed migration. |
| `status` | Lifecycle state: `proposed`, `validated`, `active`, `superseded`, `invalidated`, `archived`, or `deleted`. Preserve existing statuses and transition semantics. |
| `title` | Short, descriptive and non-sensitive title. |
| `content` | One actionable lesson, expressed as bounded prose. Not a transcript or a bundle of unrelated rules. |
| `abstract` | Optional compact retrieval summary derived from the lesson, never authoritative instead of `content`. |
| `applicability` | Structured statement of task types, repositories, tools, conditions, environments, and other scope that defines when the lesson applies. |
| `limitations` | Known exceptions, preconditions, and failure boundaries. Empty only where genuinely none are known, not because extraction skipped the field. |
| `confidence` | Existing controlled confidence value. This is descriptive metadata, not a substitute for validation. |
| `source_refs` | Evidence references with stable source identity and source version/hash/locator where available. |
| `created_by` | Actor or system component that submitted the candidate. |
| `validated_by`, `validated_at` | Authorized reviewer/policy identity and time for validation, if required by the existing schema. |
| `created_at`, `updated_at` | Database timestamps for creation and current row update. |
| `valid_from`, `valid_until` | Optional temporal applicability boundaries where known. |
| `supersedes_id` | Optional direct replacement link if an equivalent existing field is used; also keep a typed `memory_links` relation where required by the parent contract. |
| `dedupe_key` | Deterministic key for exact normalized duplicates when safely derivable. It is not a fuzzy-match score. |
| `metadata` | Small, non-sensitive extra metadata; not a substitute for required typed fields. |

Required constraints and behavior:

1. `memory_type = 'lesson'` candidates MUST include actionable content, applicability, limitations, and at least one usable evidence reference unless an authorized curated policy lesson qualifies for the documented exception.
2. `status = 'proposed'` and `status = 'validated'` MUST NOT be included in ordinary agent guidance by default.
3. `status = 'active'` MUST be backed by recorded validation and explicit activation authorization/policy.
4. A project-scoped lesson MUST be owned by the actual originating project or repository according to the audited source-of-truth map.
5. A `cross_project` lesson MUST have an explicit promotion audit, sanitization result, reviewer identity, and authorization basis. A null `project_id` by itself is never sufficient.
6. Updates that alter the lesson's meaning create a new version or successor record with provenance; do not silently rewrite history.
7. Scope changes are audited and must not widen access to the original private evidence.
8. `deleted` lessons stop retrieval immediately, before asynchronous cleanup finishes.

### 5.2 `memory_links`: add or reuse only the required explicit relationship table

Reuse `memory_links` if it already exists. If it does not exist, add it with a forward migration, indexes, and the smallest required constraints.

The logical record must support:

- `id`
- optional `project_id` or origin scope according to actual schema conventions
- `from_type`, `from_id`
- `relation`
- `to_type`, `to_id`
- `created_by`, `created_at`
- bounded, non-sensitive `metadata`

Required relations are the parent-specification meanings: `supports`, `contradicts`, `extends`, `supersedes`, `derived_from`, `applies_to`, `example_of`, `caused_by`, and `related_to`. Reuse existing values. Add a value only when a concrete V4 relationship is missing and its direction/meaning is documented.

Direction rules:

- For `derived_from`, the derived lesson points to its source evidence.
- For `supersedes`, the new record points to the record it replaces.
- For `supports`, document a single direction and use it consistently. Recommended: evidence/source points to the claim it supports, while `source_refs` remain the inline provenance contract.
- For `contradicts`, the relation records disagreement only; it never decides which side wins.
- For `applies_to`, the lesson points to the concrete task, repository, or project where the rule is applicable.
- For `example_of`, the concrete example points to the generalized lesson.

Do not add large-scale code edges or imitate Graphify. If a relationship crosses projects, its visibility must not disclose private titles, source paths, or identifiers to an unauthorized caller.

### 5.3 `memory_chunks`: no separate lesson index

Continue using V2 `memory_chunks` with the V3 embedding extension. A lesson that is eligible for agent retrieval is indexed through the same source-aware indexer. Chunk metadata must reference the canonical `memory_item` ID, item version/content hash, scope, current status snapshot, and source version.

- Proposed and validated lesson content may be accessible to authorized reviewers through review APIs, but MUST NOT leak through general `search_memory` results.
- Active lessons may be indexed for ordinary search.
- Superseded, invalidated, archived, deleted, or out-of-validity lessons are excluded from default guidance regardless of stale chunk metadata.
- A status or scope change invalidates eligibility immediately. Reindexing is asynchronous, but the canonical source join prevents stale retrieval.
- Do not store a second lesson copy in the chunk table as an independently writable canonical record.

### 5.4 `memory_jobs` or the existing worker

Reuse V3's job runner or existing application worker. Extend job types/validators to support, as required:

- `extract_lesson`
- `consolidate_memories`
- `purge_memory`
- existing `reindex_source` / embedding jobs as needed after lesson status/content changes

Do not create a second queue or worker process if the existing one can execute these jobs. Job records must remain bounded, idempotent, traceable, and safe to retry after process interruption.

The job payload stores IDs, versions, scope identifiers, idempotency keys, and bounded non-sensitive configuration. Do not put full transcript bodies, full lesson text, credentials, or secret-bearing source content into a job payload when the worker can fetch the authorized source by ID at execution time.

### 5.5 Event schema

Reuse `memory_events`. Add event types only for meaningful V4 state transitions and job outcomes, using the existing namespaced event envelope:

- `lesson.extraction_requested`
- `lesson.candidate_created`
- `lesson.candidate_rejected` (category/reason code only, no rejected sensitive body)
- `lesson.validated`
- `lesson.activated`
- `lesson.invalidated`
- `lesson.promoted_cross_project`
- `lesson.duplicate_detected`
- `lesson.merged`
- `memory.consolidation_proposed`
- `memory.consolidation_accepted`
- `memory.purge_requested`
- `memory.purge_completed`
- `memory.purge_blocked`

Before adding an event type, check actual existing naming conventions and reuse an equivalent if available. Event records should contain actor, project/scope, target IDs where policy permits, event timestamp, reason category, and source references or hashes. Do not store the full content being purged in a purge event. Normal events remain append-only; privacy/legal purge may remove content from event rows only under the approved hard-purge procedure.

### 5.6 Migration rules

1. Inspect actual table definitions and completed migration history.
2. Create a forward migration through the project's existing tool.
3. Add only missing columns, indexes, constraints, and the relationship table if needed.
4. Do not rewrite V1, V2, or V3 migrations that may have already been applied.
5. Do not migrate lesson candidates from JSONL as an unbounded backfill in V4. Historic structured records already migrated in V2 remain as they are; the V4 extraction process applies to explicitly eligible completed tasks and explicit historical backfill commands only if separately approved.
6. Keep one canonical writable store. Any pre-existing lessons in Markdown/JSONL remain canonical according to the already audited owner until an explicit record-type cutover is verified.
7. Migration tests must pass on both a clean database and an upgrade path from the actual V3 schema.

---

## 6. Lesson lifecycle: exact state transitions

### 6.1 State meaning

| State | Meaning | Default agent retrieval |
|---|---|---|
| `proposed` | Newly extracted or suggested; not trusted as guidance | No |
| `validated` | Evidence, scope, limitations, and wording reviewed; activation not yet granted | No |
| `active` | Explicitly approved for applicable authorized retrieval | Yes, only under filters/applicability |
| `superseded` | Replaced by a successor or validated consolidation | No for current guidance; historical lookup may return it with status |
| `invalidated` | Evidence shows the lesson is wrong, unsafe, or no longer applicable | No |
| `archived` | Retained for explicit history/debugging and excluded from default guidance | No |
| `deleted` | Logically removed from ordinary retrieval; purge policy determines physical removal | No |

### 6.2 Allowed transitions

```text
proposed -> validated -> active
    |           |         |
    v           v         +-> superseded
invalidated  archived      +-> invalidated
    |           |          +-> archived
    +-> deleted  +-> deleted
active -> archived / invalidated / superseded / deleted
validated -> invalidated / archived / deleted
proposed -> archived / invalidated / deleted
```

A direct transition is permitted only when its reason and authorizing actor are recorded. A model output cannot transition itself to `validated` or `active`. A failed candidate may be rejected without creating a durable lesson row; a small reason-coded event may be retained if doing so does not store sensitive content.

### 6.3 Required invariants

1. Only `active` lessons can enter default agent guidance.
2. Validation and activation are distinct operations, even when an explicit authorized policy allows them to occur together. Such combined transitions must record both decisions and the policy/reviewer.
3. `validated_by` and `validated_at` are required for human-reviewed lessons. For a deterministic policy, record the policy ID/version and execution evidence in the existing authorized audit fields or metadata.
4. Active lessons require supported evidence or the explicitly permitted curated-policy exception.
5. Inferences remain labelled as inferences. They cannot be presented as verified fact just because they have been activated as a qualified hypothesis or operational heuristic.
6. Current project decisions and approved artifacts outrank lessons. A lesson cannot override current requirements or permission policy.
7. Any content/scope change that affects retrieval triggers canonical version change and chunk invalidation. An old embedding may never restore old content to eligibility.
8. Every scope promotion, supersession, merge, invalidation, and purge is traceable without repeating sensitive content in the event record.

---

## 7. Explicit lesson extraction at task completion

### 7.1 Trigger contract

Extraction is explicitly triggered when a task is marked completed through the existing task lifecycle or when an authorized user invokes the existing task-end extraction operation. It is not triggered by every message, tool call, code edit, or intermediate event.

When the final task completion is committed:

1. Commit the canonical task status and final checkpoint through the existing V1 transaction.
2. Record or reuse the existing `task.completed` event.
3. Insert an idempotent `extract_lesson` job request in the same transaction, or through the existing transactional job/outbox mechanism.
4. Build the job idempotency key from stable identity, such as `task_id + final_checkpoint_version + extractor_contract_version`.
5. Return the task completion result without waiting for LLM extraction. Report extraction job status separately where the runtime supports it.

If the task is reopened or its final checkpoint changes materially after completion, do not blindly reuse the previous result. A new explicit extraction cycle may be queued using a new checkpoint version and idempotency key. An unchanged retry returns the existing job/result without duplicate candidates.

### 7.2 Minimum eligible inputs

The worker must gather a bounded, authorized evidence set for the task:

- final task checkpoint and relevant task status transitions
- evidence-backed handoff/final summary
- meaningful failure/fix events and verified test outcomes
- decisions made or referenced during the task
- changed files/artifacts and stable commit/version references
- relevant transcript/meeting sections only if their source type is approved and a specific source range is available
- reviewer/user corrections that are part of canonical history

Do not provide every raw tool call by default. Do not read unrelated projects. Respect source permissions before loading content. Do not embed credentials or secret-bearing content in the extractor prompt. If source material is inaccessible, stale, missing, or too large, report that condition and either skip it or extract only from the accessible evidence.

### 7.3 What may become a candidate

Extract only small actionable lessons supported by the task's observed outcome. Examples:

- a verified failure mode and the fix that resolved it
- a repository-specific command or test prerequisite not obvious from code
- a repeated implementation pattern that measurably worked in equivalent conditions
- a concrete design trade-off supported by the decision and result
- a constraint or limitation discovered during implementation
- a meaningful unsuccessful approach that should not be repeated in the same applicability conditions

Do not extract routine successful commands, generalities such as “test carefully,” unsupported causal claims, private details unrelated to engineering, secrets, hidden reasoning, or facts already represented by a canonical current decision unless a lesson adds distinct actionable guidance.

### 7.4 Extraction output contract

The extractor must return machine-readable schema-validated candidates. The logical shape is:

```json
{
  "task_id": "stable-task-id",
  "checkpoint_version": 12,
  "candidates": [
    {
      "memory_type": "lesson",
      "title": "Run integration tests with the local Redis service",
      "content": "Tests under tests/integration/ require the local Redis service from the development compose configuration; unit tests do not.",
      "scope": "repository",
      "applicability": {
        "task_types": ["integration_testing"],
        "repository": "current_repository",
        "conditions": ["tests under tests/integration/"]
      },
      "limitations": "Not required for pure unit tests.",
      "confidence": "medium",
      "evidence_refs": [
        {
          "type": "test_run",
          "ref": "actual-test-run-id",
          "version": "actual-commit-or-content-hash",
          "locator": "test name or log section"
        }
      ],
      "inference": false
    }
  ]
}
```

The example is illustrative. Production output must use actual IDs and actual source references. A candidate with fabricated source refs is rejected.

The extractor MUST:

- produce zero or more candidates, including an empty array when no durable lesson is justified
- separate directly observed facts from inference
- state applicability and limitations
- cite the evidence supporting each claim
- preserve source version/locator where available
- avoid promoting a local observation into a global rule
- avoid secret, personal, or unrelated content
- never include hidden chain-of-thought
- never set status to `validated` or `active`
- never change decisions, tasks, permissions, or canonical artifact content

### 7.5 Candidate validation before insertion

Before creating a `memory_items` row, validate every candidate:

1. Validate against the strict schema and allowed enums.
2. Normalize bounded text for deterministic duplicate checks without altering evidence meaning.
3. Resolve every source reference and verify it points to evidence the actor/job may access.
4. Check that the source version is current or explicitly mark the evidence historical.
5. Apply secret detection/redaction and source-class policy.
6. Reject unsupported claims, vague generalities, hidden reasoning, and candidates with missing required applicability/limitations.
7. Set `memory_type = 'lesson'`, `status = 'proposed'`, and the narrowest defensible scope.
8. Record the extraction job ID, task ID, checkpoint version, extractor contract/model identifiers where safe, and candidate provenance in existing fields/metadata.
9. Use an idempotent key for each candidate derived from extraction job identity plus normalized candidate identity. Repeated worker execution must not create duplicate rows.
10. Do not create candidate chunks eligible for ordinary search; review access goes through explicit reviewer APIs.

If all candidates are rejected, the job may succeed with zero created lessons. Record reason categories and counts, not the full rejected sensitive text.

### 7.6 Job retry and idempotency

- A retry loads current job state and source versions before processing.
- A completed extraction job with the same idempotency key returns its prior result.
- If a source version changed since the job was created, either refresh the authorized input set and explicitly create a new job version, or mark the job stale/cancelled. Do not process stale input as current.
- A purge request must cancel/invalidate extraction jobs referencing the purged target or source identity.
- Jobs use bounded retries. Transient provider errors may retry; permission failures and schema-invalid results do not retry indefinitely.
- The worker must never resurrect a candidate after a user rejected it or a relevant source was purged. Check current source/purge state immediately before commit.

---

## 8. Lesson review, validation, and activation

### 8.1 Reviewer interface

Reuse the existing code review, approval, task, or admin surface. V4 does not require a new application or UI. If no suitable review surface exists, add the smallest internal command or API consistent with the repository's conventions.

A reviewer must be able to see:

- title and proposed lesson content
- scope and applicability
- limitations/exceptions
- confidence and whether any statement is inferred
- evidence references, source versions, and relevant excerpts under that reviewer's permissions
- exact/near-duplicate candidates and active contradictory lessons
- intended effect of validation, activation, or cross-project promotion
- why the extractor suggested the lesson

Do not expose the source content to a reviewer who lacks permission to see it. If the reviewer cannot examine sufficient evidence, they must not validate the candidate.

### 8.2 Validation checklist

A lesson may transition from `proposed` to `validated` only when the reviewer or documented deterministic verification confirms:

1. The lesson is actionable and expresses one reusable unit.
2. The evidence exists and supports every material claim.
3. The lesson does not overstate causal certainty.
4. Scope matches the evidence: task, repository, project, or cross-project candidate.
5. Applicability conditions and limitations are explicit enough to avoid misuse.
6. Relevant active decisions and lessons have been checked for contradiction.
7. The lesson does not contain secrets, unauthorized personal data, private project specifics in a public scope, or copied untrusted instructions.
8. The same lesson is not already active with compatible scope.
9. Any inferred content is clearly labelled and the proposed operational use is safe.
10. Its source refs are stable enough for later audit or are explicitly marked as limited/unavailable.

Acceptable validation evidence includes a reviewer who inspects the source, repeated results under equivalent conditions with links, a deterministic test, a repository convention, or a curated policy from an authorized maintainer. “The model gave it high confidence” is not validation.

### 8.3 Validation versus activation

Validation means the evidence and wording are acceptable. Activation means the lesson is permitted to influence relevant future agent tasks. These are distinct.

- A validated lesson can remain inactive while its scope or applicability is under review.
- An active lesson must have an explicit activation actor or policy decision.
- The API may provide a combined validate-and-activate operation only when the caller explicitly requests both, is authorized for both, and the audit event records both transitions and the reason.
- Extraction jobs never activate lessons.
- Cross-project promotion is a separate scope decision and must not happen as a side effect of local activation.

### 8.4 API behavior

Use or extend the existing facade contracts:

`propose_lesson(candidate)`

- Validates and creates a `proposed` item, with evidence and idempotency, or returns an existing exact duplicate/candidate result.
- Does not activate the item.

`validate_or_activate_lesson(memory_id, reviewer, evidence)`

- Rechecks actor authorization and current status.
- Supports explicit validation and activation transitions according to an unambiguous action parameter or separate internal methods; do not infer the requested action from prose.
- Validates required evidence and state transitions.
- Records event, reviewer, timestamp, and reason.
- Queues indexing only when the resulting state becomes eligible for ordinary retrieval.

If the existing public signature cannot express the requested action unambiguously, preserve compatibility and add a typed optional action or a distinct facade method; document the choice. Do not create overlapping APIs with inconsistent semantics.

### 8.5 Rejection and invalidation

- A proposed candidate can be rejected or invalidated without ever becoming active.
- A validated/active lesson later shown to be wrong transitions to `invalidated` or is superseded by a justified replacement; do not silently edit its claim.
- A rejected candidate must not be recreated by retrying the same extraction job. Persist an idempotency/rejection record or equivalent non-sensitive event marker.
- If the same fact is proposed later with materially new evidence, it may be re-reviewed under a new candidate identity that references the earlier rejected candidate, where useful.

---

## 9. Cross-project promotion and retrieval

### 9.1 Default is project local

An extracted lesson inherits the narrowest defensible scope. It starts as `task`, `repository`, or `project` based on the evidence. `cross_project` is never the default and is not inferred from a generic-sounding title.

### 9.2 Promotion creates a separately sanitized record

Do not broaden the permissions of a private project lesson in place. To promote one:

1. Select a validated source lesson and its evidence.
2. Ask the authorized reviewer to confirm the lesson has value outside the originating project.
3. Create a separately scoped cross-project candidate with generalized, sanitized content, explicit applicability, and limitations.
4. Remove or generalize project-specific identifiers, customer/private information, internal endpoints, private architecture details, proprietary paths, and secrets unless an explicit policy authorizes their release.
5. Preserve internal provenance through restricted `derived_from`/`supports` links or equivalent authorized metadata.
6. Do not disclose source project titles, file paths, incident descriptions, task IDs, or private snippets to consumers of the generalized lesson unless they have permission to see them.
7. Validate the generalized lesson's evidence and scope, then explicitly activate it as `cross_project` using an authorized actor/policy.
8. Record the source lesson ID, promotion reviewer, scope change, sanitization/policy outcome, and event. Use stable identifiers internally while filtering them from unauthorized result payloads.
9. Index the cross-project lesson only after activation.

The resulting cross-project lesson is a separate canonical `memory_item`. Its permission scope must not be broader than the sanitized text and approval authorize. The original project lesson remains in its original scope and status.

### 9.3 Authorization contract

Reuse the application's current actor identity and authorization service. Do not invent a parallel role system. Define permissions through existing conventions equivalent to:

- `memory.lesson.propose` within the caller's allowed task/project
- `memory.lesson.review` for evidence the reviewer may access
- `memory.lesson.activate` for the target scope
- `memory.lesson.promote_cross_project` for approved global/org-wide reuse
- `memory.delete` for logical deletion
- `memory.hard_purge` for physical removal
- `memory.consolidate` for proposing or approving consolidations

The names are illustrative action names, not a demand to add a new permissions framework. Map them to existing authorization primitives and document the mapping.

### 9.4 Retrieval rules for cross-project lessons

The existing `search_memory(query, project_id, scope, filters, limit, actor)` facade remains the only ordinary search entry point.

Before candidate retrieval, enforce in SQL or the existing trusted authorization layer:

1. The caller is allowed to access the current project/task.
2. The requested scope is permitted for the actor.
3. `cross_project` is included only if the policy permits the caller to use shared lessons.
4. Only `status = 'active'` lessons are eligible for default lesson guidance.
5. The lesson is within `valid_from` / `valid_until`, where specified.
6. Applicability matches the task/repository conditions sufficiently to avoid generic overreach.
7. The canonical lesson is not deleted, superseded, invalidated, archived, or marked inaccessible.
8. The matching chunk and embedding reference the current canonical lesson version.

The query must not return snippets, title, path, source reference, or “an inaccessible match exists” information from an unauthorized project. Check filters before ranking candidates; do not fetch global nearest neighbors and filter the result afterward.

### 9.5 Applicability, not global injection

Do not prepend every cross-project lesson to every agent prompt. Search cross-project lessons only for task-directed retrieval or when the task-start context has a clear applicability signal. Return a small compact candidate set with source/provenance as permitted. A lesson is advice supported by evidence, not higher-priority instructions or authorization policy.

### 9.6 Cross-project test fixtures

At minimum, test three cases:

- An authorized project can retrieve a validated/active sanitized cross-project lesson applicable to its task.
- An unauthorized project cannot retrieve a private originating lesson, its source path, title, snippets, or source IDs.
- An authorized project does not receive a cross-project lesson whose applicability or limitations exclude the current task.

---

## 10. Exact deduplication, near duplicates, and contradictions

### 10.1 Staged matching strategy

Use this order and stop early when the answer is unambiguous:

1. **Idempotency identity:** same extraction job/candidate key means the same attempt; return the previous result.
2. **Exact normalized duplicate:** same stable `dedupe_key` or normalized content hash, compatible scope, compatible applicability, and same underlying claim.
3. **Structured identity:** same task/test/error/decision/source identity, using actual stable IDs.
4. **Lexical candidates:** existing V2 full-text search over permitted, current records.
5. **Semantic candidates:** existing V3 vector/hybrid results with the same SQL authorization filters.
6. **Relation decision:** deterministic exact rule or explicit reviewer/model suggestion classifies the relationship. For near matches, the model may recommend but cannot mutate active truth without the required review.

Do not use a single universal similarity threshold as proof of identity. A threshold can propose candidates for examination; it cannot prove two claims are compatible.

### 10.2 Exact duplicate rules

Two lessons can be treated as exact duplicates only when all of the following are true:

- Their normalized claim and recommended action express the same meaning.
- Scope and visibility are compatible.
- Applicability and limitations are compatible.
- Their validity periods do not conflict.
- Their evidence does not contradict the claim or show distinct contexts that should remain separate.

When an exact duplicate is detected:

1. Do not create another active copy.
2. Attach additional provenance/evidence to the surviving record or add appropriate source links.
3. Record a duplicate-detected/merged event if a durable action occurred.
4. If duplicate active records already exist, select a survivor deterministically or by authorized review, transfer useful evidence links, then supersede the duplicate only after verifying the survivor is valid and preserves the evidence.
5. Do not hard delete merely to make the table smaller.
6. Reindex the survivor if its indexed text/provenance changed; invalidate stale duplicate chunks before they can be returned as current guidance.

The process must be transactional for canonical row status, links, and events. Index generation can be asynchronous because retrieval rechecks canonical status.

### 10.3 Near-duplicate candidate rules

A near duplicate is only a candidate when text meaning, applicability, or evidence is similar but not identical. The candidate assessment must record:

- the two or more candidate IDs
- their current status/scope and validity periods
- similarities and meaningful differences
- evidence supporting each claim
- proposed relation: `same_claim`, `extends`, `contradicts`, `context_specific`, or `unrelated`
- a recommended action and its reason

This assessment may be implemented as an internal typed payload rather than a permanent new table. Persist a review item only when the repository needs to track it beyond the job. Do not create a dedicated duplicate-management service.

### 10.4 Relation decision rules

- **Same claim, same scope:** attach evidence to a canonical survivor; supersede duplicate active copies after safe transfer.
- **Compatible extra detail:** retain both and use `extends` or `supports` where useful.
- **Conflicting claims:** create `contradicts` links, record a conflict, and keep both until evidence/reviewer resolves the conflict. Do not choose by score or recency alone.
- **One lesson is a specific example of a general lesson:** retain the specific evidence and use `example_of` where useful.
- **New evidence invalidates an old lesson:** transition old lesson to `invalidated` or create a replacement and supersede it with evidence.
- **Different scopes:** do not merge a private project lesson into a broader lesson automatically. Use the explicit cross-project promotion process instead.
- **Different valid-time periods:** preserve time distinctions rather than calling them duplicates.

### 10.5 Required relationship invariants

- Database-owned link endpoints must use real stable IDs and foreign keys where practical.
- External sources use the established typed source-ref convention.
- Duplicate/supersession links must not cross an authorization boundary in a way that exposes private metadata.
- A link is evidence of an explicit relationship, not authority to merge or broaden access.
- Deleting a record must remove or safely redact in-scope link metadata during hard purge; no link may resurrect or reveal purged content.

---

## 11. Durable consolidation and compaction

### 11.1 Consolidation has a narrow purpose

Consolidation reduces duplicate retrieval noise and turns repeated supported experience into a better bounded lesson. It does not replace project artifacts, full transcript history, decision records, test results, or task checkpoints. It does not run a custom learning model or freely rewrite active memory.

### 11.2 When consolidation may be scheduled

Reuse the existing worker/job system. Enqueue a bounded consolidation job when one of these triggers occurs:

- Task-end extraction creates candidate lessons that overlap with existing lessons.
- An authorized reviewer asks to consolidate a known set of related memory IDs.
- A meaningful meeting/decision workflow explicitly requests lesson extraction and there are enough relevant records.
- A maintainer-approved maintenance run identifies a bounded backlog of likely duplicate/related records and there is demonstrated retrieval noise.

Do not trigger expensive consolidation after every message/tool call. Do not introduce a schedule just because a scheduler is available. If there is no worthwhile candidate group, the job completes as a no-op.

### 11.3 Input selection

A consolidation job must:

1. Receive stable candidate IDs or a bounded project/scope/topic selector.
2. Enforce the caller/job's allowed project and scope.
3. Select only current, relevant records with compatible visibility.
4. Load canonical lesson content and evidence references, not just their snippets or embeddings.
5. Recheck source versions and current status.
6. Include contradictory evidence/lessons when relevant to avoid premature generalization.
7. Bound record count, input bytes/tokens, and job duration.
8. Exclude purged, deleted, inaccessible, stale, or secret-bearing content.

Never build one consolidation prompt from unrelated or differently authorized projects. Cross-project consolidation operates only on evidence that is explicitly eligible and does not reveal source projects.

### 11.4 Consolidation output contract

The consolidator proposes one or more candidate lesson records containing:

- concise title
- one actionable claim/recommendation
- precise applicability conditions
- limitations and material exceptions
- evidence references for each material claim
- list of input memory IDs considered
- explanation of what was generalized and what was deliberately not generalized
- known contradictions or unresolved points
- proposed scope no broader than the evidence supports
- source/version identities used to create the proposal

The output is schema-validated, source-validated, redacted, and inserted as `proposed`. It does not automatically replace, merge, supersede, validate, activate, or delete its inputs.

### 11.5 Evidence-preserving consolidation process

1. Build the candidate group using exact identities, full-text candidates, V3 semantic candidates, or an explicitly chosen set of IDs.
2. Check scope, permissions, active status, valid times, and contradictory evidence.
3. Have the consolidator propose a replacement abstraction only if evidence supports one.
4. Validate every source reference and confirm it supports the proposed language.
5. Link the candidate to input evidence using `derived_from`; link examples using `example_of` where appropriate; record contradictions where unresolved.
6. Create the new record as `proposed` with an audit event and idempotency key.
7. Route the candidate through the normal validation and activation path.
8. Only after the new candidate is active and confirmed as a faithful replacement may a reviewer approve superseding redundant old lessons.
9. Transfer evidence links before old records become non-current.
10. Reindex the active survivor and ensure stale/old chunks cannot still appear as current results.
11. Keep historical source records and evidence unless a separate deletion request or approved retention policy requires their removal.

For an exact duplicate where semantics and scope are proven identical, a deterministic provenance attachment can avoid creating a new lesson candidate. For near-duplicate groups, the new abstraction remains proposed until normal validation.

### 11.6 Compaction boundaries

V4 may compact durable memory into bounded lesson candidates and compact retrieval context. It MUST NOT destructively compact:

- full meeting transcripts
- original decision rationale or approval evidence
- approved Markdown/PRD/architecture artifacts
- source code or Git history
- canonical task checkpoints needed for resumption
- events/audit information retained by policy
- important failure evidence needed to understand a decision change

Runtime context compaction remains the V1 checkpoint mechanism. V4 consolidation must not introduce a second checkpoint store or overwrite the original checkpoint/history with a generated summary.

### 11.7 Consolidation quality guardrails

- A single incident in one project does not justify a universal rule.
- A pattern observed repeatedly under equivalent conditions must still state its applicability conditions.
- Preserve exceptions, environment assumptions, tool/model versions, and time limitations where they matter.
- Do not overfit a general lesson to a specific task or generalize one project's private constraints into cross-project advice.
- Don't treat two similarly worded but contradictory claims as duplicates.
- Don't consider a consolidation successful merely because it reduced row count. It should reduce redundant candidate exposure while preserving correct task outcomes and evidence traceability.

---

## 12. Logical deletion and hard purge

### 12.1 Two distinct operations

**Logical deletion** immediately removes a record from normal retrieval while retaining permitted audit/state data. It is suitable for ordinary stale or unwanted memories when physical removal is not required.

**Hard purge** physically removes in-scope content and derived copies when required for privacy, security, legal policy, or an explicit authorized request. Hard purge is a workflow with verification, not just `DELETE FROM memory_items`.

### 12.2 Purge scope must be explicit

Before execution, resolve what the request covers:

- the selected `memory_item` and all its in-system derived copies
- explicitly linked derived lessons and summaries whose content comes from the target
- specific selected source artifacts or transcript sections, only when those source artifacts are within the request and the actor has permission to delete them

Do not automatically delete a complete Git repository, meeting transcript, or approved artifact merely because a lesson references it. Conversely, do not claim that a phrase is fully erased from memory search if the same eligible source text intentionally remains indexed elsewhere. Record the exact in-scope IDs/source identities and any uncontrolled external source or backup that cannot be purged by this implementation.

### 12.3 Start the purge: immediate retrieval safety

When `delete_memory(ids, mode='hard_purge', reason_category=...)` is authorized:

1. Validate the exact target IDs, scope, caller permissions, and request idempotency.
2. Expand the target set to known derived lesson records and derived copies according to the purge scope; never expand across an unauthorized scope.
3. In one transaction, set all target memory records to `deleted` where rows remain, mark related chunks stale/ineligible, cancel or invalidate jobs that could recreate them, insert a `memory.purge_requested` event with IDs/hash references and a reason category only, and queue an idempotent `purge_memory` job using the existing job mechanism.
4. Commit before returning a job/request ID. Ordinary retrieval must exclude targets immediately, even while physical cleanup is pending.
5. Do not include deleted text in the purge job payload. Store stable target identities, source-version IDs or one-way source identity hashes, authorization result, and the purge request ID.
6. Return a pending status until physical deletion and verification complete. Never report success at queue time.

If the source is already deleted or the purge request is repeated, treat it idempotently and return the existing outcome, provided the same target and request intent match.

### 12.4 Purge worker inventory

Before physical deletion, locate in-scope copies from known ownership paths:

- `memory_items` target content, abstracts, cue terms, metadata, and source refs as covered by request
- `memory_links` rows that contain sensitive target metadata or expose purged source identifiers
- `memory_chunks` content, titles, search vectors, and all embedding columns
- embeddings and derived data attached to all chunk versions, not only current chunks
- consolidated lesson content derived from target evidence, when its substance still reveals the purged content
- cache entries, materialized/profile summaries, temporary exports, and local app-owned index copies if they exist
- queued/running extraction, indexing, embedding, and consolidation jobs whose payload or inputs could recreate the target
- memory-owned log/error payloads that accidentally captured the sensitive content
- any importer/reindex path that could reintroduce the same source identity

Do not assume that every listed store exists. Audit the actual repository and remove all copies that actually exist. Record inspected stores and outcome categories in the purge result without storing the deleted content again.

### 12.5 Perform the hard purge

The worker must:

1. Claim the purge job idempotently and recheck the authorization/request state.
2. Mark a durable no-content purge marker for the target source identity/record identity, using the existing event/audit mechanism or the smallest necessary table if the current architecture cannot prevent resurrection otherwise. The marker may contain stable IDs, hashes, scope, and reason category, but MUST NOT contain purged content or reversible text.
3. Cancel or invalidate all jobs whose inputs include the purged target. Workers must check current purge state before committing output.
4. Delete target lesson rows when the request requires hard deletion, and delete/redact any permitted source/event copies within the explicit request scope. Preserve only policy-permitted minimal audit information.
5. Delete dependent chunks and their `search_vector`/embedding data, including old versions; do not just set `is_stale=true` for a hard purge.
6. Remove or redact dependent link metadata and derived summaries/caches/exports under system control.
7. Ensure all copies are deleted under a bounded, retryable workflow. If a transaction spanning all rows is feasible, use it; otherwise use an explicit multi-step purge job with durable progress and a final verification barrier.
8. Ensure later reindexing/import/extraction refuses to recreate records matching the purge marker unless an authorized new source explicitly supersedes the request under policy. A generic stale retry is not such authorization.
9. Emit a completion audit event containing no purged text, after cleanup and verification succeed.

### 12.6 Append-only events and privacy exception

Normal `memory_events` remain append-only. Hard purge is the documented exception for records that actually contain content which policy requires removing. The preferred design is for event summaries/payloads to contain IDs, reason codes, source refs, and changed fields rather than full lesson text, so event rows do not usually need deletion.

If a source event contains the sensitive text itself, follow the authorized privacy/legal purge procedure for that event content and its indexes. Keep a minimal, non-content-bearing purge marker when permitted. Do not retain deleted content in `correction_of`, the event summary, source excerpts, SQL error strings, stack traces, job payloads, or a supposedly audit-only JSON field.

### 12.7 Source artifacts and backups

A memory purge does not automatically erase an original artifact that is outside the memory system's ownership. The purge outcome must explicitly state one of:

- `completed`: all in-scope, system-controlled copies were physically removed and verified;
- `completed_with_external_source_retained`: all in-scope memory-owned copies were removed, but an explicitly out-of-scope or uncontrolled source/backup remains and is identified by permitted reference;
- `blocked`: authorization, source control, provider retention, or verification failure prevents a truthful completion claim.

Do not claim deletion from external logs, backups, Git history, or an embedding provider unless that subsystem's documented retention/deletion mechanism confirms it. If the request includes canonical source deletion, perform it only through that source system's authorized workflow and verify it separately.

### 12.8 Hard-purge verification barrier

A purge job may be marked successful only after automated verification confirms, for the specified purge scope:

- target content is no longer returned by direct SQL/details APIs
- exact identifier lookup does not return content
- full-text search returns no target content or eligible chunk
- pgvector/vector search returns no target content or embedding-bearing chunk
- no old/stale chunk version for the target remains in scope
- known derived lessons and summaries were deleted or verified non-revealing according to the request
- no queued/running job can re-create the target; stale worker attempts fail their pre-commit purge-state check
- memory-owned caches, exports and logs within the audited inventory are cleared or redacted
- a second idempotent verification pass reaches the same result

If verification fails, keep the purge state pending/blocked, report a redacted failure category, retry only when safe, and do not report success. The verifier may compare target IDs, hashes, or source fingerprints but must not print deleted content into logs.

### 12.9 Preventing resurrection

Every relevant entry point must respect purge markers:

- extraction candidate commit checks whether any source identity was purged or invalidated
- indexing verifies current source eligibility and purge state immediately before commit
- embedding job verifies the exact chunk/source version is current and not purged
- consolidation checks whether any input or evidence reference is purged and rejects stale proposals
- import/reindex logic respects a purge marker for the same stable source identity; if migration sources are still writable, the source-of-truth owner must resolve this rather than allowing silent reinsertion
- a worker's retry cannot override a newer deletion/purge request

A deliberate future decision to restore a deleted source must be explicit, authorized, and audited. Reappearance in an old file, cached job payload, or retry is not a valid restore request.

---

## 13. API contracts added or extended by V4

The memory facade remains internal to the application unless the existing system genuinely exposes it through a service. Do not build a network service just for these operations.

### 13.1 Task-end extraction

Recommended operation: `request_lesson_extraction(task_id, final_checkpoint_version, actor, idempotency_key)`.

Behavior:

- authorizes access to the task and its evidence
- verifies task completion or an explicitly permitted manual extraction request
- enqueues an idempotent `extract_lesson` job
- returns `job_id`, status, and task/checkpoint identity
- does not return or imply that lessons have already been extracted

If an equivalent task-end action already exists, extend it rather than creating a redundant public API.

### 13.2 `propose_lesson(candidate)`

- Creates or resolves a `proposed` lesson candidate.
- Requires evidence refs, applicability, limitations, creator, scope, and idempotency where applicable.
- Performs exact duplicate checks and returns a stable outcome (`created`, `existing_exact_duplicate`, `rejected_validation`, or `conflict`).
- Never activates the lesson.

### 13.3 `validate_or_activate_lesson(memory_id, reviewer, evidence)`

Preserve the existing facade method if it exists. Its behavior must explicitly distinguish validation from activation. Use a typed action or separate internal functions if the present signature is ambiguous.

- rechecks actor permissions and current status
- verifies evidence, applicability, limitations, conflicts, and source freshness
- applies only an allowed state transition
- appends the event and records reviewer/time/reason
- queues indexing only when ordinary retrieval becomes allowed
- responds with the canonical status/version, not a vector-index status as authority

### 13.4 Cross-project promotion

Recommended internal operation: `promote_lesson_cross_project(memory_id, sanitized_candidate, actor, review_evidence)`.

- requires existing cross-project promotion permission
- requires a validated source lesson or equivalent explicit review of source evidence
- creates a distinct sanitized `proposed` cross-project item
- preserves internal provenance links without disclosing restricted evidence to downstream consumers
- does not change the original project's scope or ACL
- then routes through the normal validation and activation lifecycle

### 13.5 Consolidation

Recommended internal operation: `request_memory_consolidation(memory_ids, actor, idempotency_key)`.

- requires an authorized actor or approved task-end workflow
- enforces bounded inputs and common scope/permissions
- creates a job and returns its status
- produces a proposed record only; it does not automatically activate, supersede, or delete source records

### 13.6 `delete_memory(ids, mode, reason_category)`

Keep the existing facade signature if possible. For `mode = logical`, immediately exclude targets from normal retrieval and record the permitted state transition. For `mode = hard_purge`, initiate the verified purge workflow. Return a structured state such as `removed_from_retrieval`, `purge_pending`, `purge_completed`, `completed_with_external_source_retained`, or `blocked`; do not overload a boolean to imply physical deletion has succeeded.

### 13.7 Existing API compatibility

The following V1/V2/V3 behavior must remain compatible:

- `get_current_context(project_id, task_id)`
- `record_event(event)`
- `update_task_checkpoint(task_id, checkpoint, expected_version)`
- `search_memory(query, project_id, scope, filters, limit, actor)`
- `get_memory_details(ids, project_id, actor)`
- `reindex_source(source_ref, source_version)`

V4 can add optional typed fields to a response where backward compatible, but it must not change the meaning or authorization rules of existing fields. Search still returns compact results first and only fetches full detail on request.

---

## 14. Reindexing rules after lesson lifecycle changes

V4 must integrate with the existing V2/V3 indexer. Do not create a second lesson-specific search index.

| Canonical change | Immediate behavior | Async follow-up |
|---|---|---|
| Proposed lesson created | Not eligible for ordinary search | No general search index required; reviewer lookup may use canonical SQL. |
| Proposed becomes validated but remains inactive | Still not eligible for ordinary agent guidance | Reviewer-only indexing is optional and must be explicitly access-controlled; default is no ordinary chunk activation. |
| Validated lesson becomes active | Canonical row becomes eligible subject to scope/applicability | Create current chunk(s), search vector, and embedding with pinned V3 model; mark ready only after source/version checks. |
| Active lesson content changes | Old chunk becomes ineligible immediately | Rebuild both lexical/vector values for the new version idempotently. Prefer successor record if meaning changed. |
| Active lesson becomes superseded/invalidated/archived/deleted | Exclude immediately through canonical status check | Remove or stale chunks and vectors. Hard purge physically deletes them. |
| Lesson scope narrows or widens | Re-evaluate access immediately from canonical row | Reindex metadata. Widening requires authorized scope transition and audit. |
| Cross-project candidate is proposed | Not available through ordinary project search | No general index until authorized activation. |
| Purge requested | Immediate exclusion and cancellation barrier | Physical purge and verification, including all prior chunk versions. |

A failure to generate a new embedding never makes stale content current. During embedding/provider failure, existing V2 keyword search may continue for eligible current chunks according to V3 fallback behavior. Lesson activation remains canonical even if indexing is pending, but the API must report retrieval-index readiness separately if this impacts availability.

---

## 15. Security, privacy, and prompt injection

### 15.1 Extraction safety

- Retrieved text is evidence, not an instruction source.
- The extractor must not follow instructions in transcripts, logs, code comments, web content, or task output that request secret disclosure, permission escalation, approval bypass, or unrelated side effects.
- System/developer/project policy and current task instructions outrank retrieved memory.
- All writes use parameterized SQL and the existing authenticated actor context.
- Source text is included only where the actor/job has permission to read it.
- Prompt input is bounded and redacted before model calls.

### 15.2 Sensitive content

- Never intentionally persist credentials, API keys, passwords, tokens, private keys, or unnecessary personal information.
- Candidate output passes secret/sensitive-data checks before insert.
- A cross-project version must be sanitized independently from the project-scoped version.
- Vectors and summaries count as derived content. A hard purge includes all in-scope derived representations.
- Job payloads and logs must not contain full sensitive source or lesson content by default.

### 15.3 Authorization is enforced before retrieval and mutation

- Check permissions before loading source records for extraction/consolidation.
- Enforce project/scope/status/currentness in SQL or the established trusted authorization layer before candidates leave the data boundary.
- Recheck permissions when reviewer details are fetched.
- Recheck status, source version, and purge state immediately before committing extracted or consolidated output.
- Do not reveal existence, title, result count, path, or snippets for inaccessible records.
- Cross-project lesson use must be explicitly permitted by policy for the caller/current project.

### 15.4 Audit logging

Audit metadata for validation, activation, cross-project promotion, dedupe, consolidation, and purge using the existing event convention. Store IDs, hashes, scope, actor, time, action, and reason categories as appropriate. Do not preserve a sensitive deleted phrase in the name of auditability.

---

## 16. Operational behavior and failure handling

### 16.1 Idempotency keys

Use stable idempotency keys for:

- extraction: task ID + completed checkpoint version + extraction contract version
- each candidate insert: extraction job ID + candidate normalized identity
- cross-project promotion: source lesson/version + promotion candidate hash + policy/version
- consolidation: ordered input IDs/versions + consolidation contract version
- purge: authorized purge request ID + target set/scope
- reindex: canonical source ID + source version + chunking config/model version

Do not use a new random key on every retry. If a key is reused with different logical input, return an explicit idempotency conflict rather than overwrite the original result.

### 16.2 Transaction boundaries

Use one PostgreSQL transaction for each canonical transition where possible:

- task completion event plus extraction job creation
- candidate creation plus provenance event and idempotency identity
- validation/activation state change plus reviewer metadata and event
- cross-project promotion candidate plus restricted provenance links and event
- duplicate merge status changes, links, and merge event
- purge request state, immediate retrieval exclusion, job cancellation flags, purge job creation, and purge-request event

The LLM call, embedding call, or lengthy source reading must not hold a database transaction open. Background results are committed only after current source version, permissions, and purge state are rechecked.

### 16.3 Retry policy

- Retry transient provider/network/timeout/serialization errors with bounded exponential backoff and jitter using the existing job runner.
- Do not automatically retry permission denial, deleted/purged target, invalid state transition, or schema-invalid output indefinitely.
- Rejected/invalid output can be retried only under a revised, bounded attempt with a documented reason.
- If a purge request is pending, block any downstream job that would reproduce the target until its purge marker no longer permits that identity (normally it never does without a deliberate authorized restore).
- Dead jobs must be visible in existing diagnostics, not retried forever.

### 16.4 Concurrency

- Use optimistic version checks for lesson modifications and review decisions.
- A reviewer cannot activate a record that became invalidated, superseded, deleted, or purged after the review screen loaded.
- Use row locks or compare-and-swap for survivor selection during merging.
- If two extraction jobs create semantically similar candidates concurrently, deterministic uniqueness/idempotency protects exact duplicates; near-duplicate resolution remains a separate candidate/review step.
- A purge always wins over an in-flight extraction/index/consolidation job when it targets the same source lineage.

### 16.5 Backups and restore

Follow the repository's actual PostgreSQL backup/restore strategy. After restoring a backup, restore purge markers and reapply retention/deletion state before exposing memory retrieval. A restore must not make a previously purged record available again. Do not claim backups are purged unless the actual retention/rotation process confirms it.

### 16.6 Minimal operational measures

Record only metrics that support operation:

- extraction jobs requested/succeeded/failed, candidate count, rejected count and reason categories
- lesson review queue size and time-to-review where available
- active lesson count by scope, with no sensitive content in metrics
- exact duplicates skipped, near-duplicate proposals, validated merges, unresolved contradictions
- consolidation jobs and source count per job
- purge requested/completed/blocked, verification failures, and time to final status
- stale chunks removed and reindex failures
- V1/V2/V3 regression results and the existing task evaluation outcomes

Do not build a dashboard product merely because these metrics exist. Reuse current logging/metrics, and add only operationally necessary instrumentation.

---

## 17. Implementation sequence and gates

Perform the steps in order. Each step has an exit gate. If a step fails, fix it before proceeding.

### Step 0: Verify predecessor handoffs and actual schema

- Verify V1, V2, V3 code and tests against the repository.
- Inspect actual `memory_items`, `memory_chunks`, `memory_events`, `memory_links` if present, `memory_jobs`/worker, authorization service, source resolver, and migration mechanism.
- Confirm V2/V3 search filters are applied before candidate content leaves the database.
- Confirm how active status/currentness and source versions are checked.
- Produce a V4 audit note with re-use map, schema diff, missing tests, and conflicts.

**Exit gate:** no unresolved single-writer, authorization, or predecessor correctness issue remains.

### Step 1: Minimal forward migration

- Add only missing lesson fields/status constraints/indexes and `memory_links` if absent.
- Extend the existing job schema/validators for V4 job types if necessary.
- Add purge idempotency marker behavior through existing events/jobs, or the smallest table only if required to prevent resurrection.
- Add no new DB, service, or job platform.

**Exit gate:** migration works from both clean schema and the actual V3 schema; constraints and rollback notes are tested.

### Step 2: Lesson model and lifecycle facade

- Implement schema validation for lesson records.
- Implement allowed state transitions and authorization checks.
- Implement `propose_lesson` and explicit validate/activate action semantics.
- Write events transactionally and add status/currentness tests.

**Exit gate:** proposed/validated lessons are never returned as default guidance and only authorized actors can activate lessons.

### Step 3: Task-end extraction trigger

- Integrate with the existing task completion hook.
- Enqueue idempotent extraction job after final checkpoint/task event is committed.
- Load a bounded, authorized evidence set and call the extractor.
- Strictly validate/redact results, source refs and idempotency before candidate insertion.
- Keep the task completion path non-blocking except for durable job enqueue.

**Exit gate:** repeated task completion retries produce no duplicate candidates; no evidence means no lesson; no extracted item is auto-activated.

### Step 4: Reviewer validation and activation

- Reuse existing review surface or the smallest internal approval interface.
- Display source references and limitations under the reviewer's permissions.
- Record explicit validate, activate, reject, invalidation, and supersession actions.
- Queue indexing only after activation.

**Exit gate:** all allowed/forbidden lifecycle transitions are tested and audited.

### Step 5: Cross-project promotion and retrieval

- Implement separately sanitized cross-project candidate creation.
- Map promotion/retrieval to existing actor authorization policy.
- Add restricted provenance links without leaking private source identifiers in the general search response.
- Activate and index only after review.
- Use the existing `search_memory` facade and V3 filters/RRF.

**Exit gate:** authorized reusable lesson is discoverable; project-private record and metadata cannot leak; out-of-scope lesson is not presented as applicable.

### Step 6: Exact deduplication and candidate matching

- Add normalized deterministic duplicate identity where safe.
- Use V2/V3 search to find possible matches after authorization filters.
- Apply same-claim/scope/applicability/time rules.
- Attach evidence for exact duplicates or create review candidates for near duplicates/contradictions.
- Implement an atomic merge/supersession transaction for approved outcomes.

**Exit gate:** duplicates are not multiplied by retries, conflicts are not silently resolved, and merges preserve source links.

### Step 7: Evidence-preserving consolidation

- Implement bounded consolidation jobs using explicit eligible input IDs/scope.
- Generate proposed candidate(s) with complete input provenance, applicability, limitations and exceptions.
- Route through the same validation/activation workflow.
- Supersede redundant lessons only after the consolidation is active and evidence links have been transferred.

**Exit gate:** consolidation does not destructively replace original sources and cannot make unsupported broader claims active.

### Step 8: Hard-purge lifecycle

- Implement immediate retrieval exclusion and job cancellation on purge request.
- Inventory actual derived copies and jobs.
- Physically remove in-scope lesson/chunk/embedding/link/cache/export/log copies.
- Add anti-resurrection checks to extraction, indexing, embedding, and consolidation commits.
- Implement multi-path verification and a truthful final status.

**Exit gate:** hard-purge tests confirm SQL, exact, keyword, vector and detail lookups cannot return the target; worker retries cannot recreate it.

### Step 9: Full evaluation and handoff

- Run all predecessor suites.
- Run V4 lifecycle, cross-project, dedupe, consolidation, purge, and prompt-injection tests.
- Run memory-on versus memory-off tasks using the existing benchmark and report whether active lessons improved outcomes.
- Complete Appendix E with actual evidence.

**Exit gate:** all required tests pass, limitations are explicit, and no later-phase or forbidden infrastructure was added.

---

## 18. Acceptance tests

These are behavioral tests. Creating tables or passing unit tests alone does not satisfy V4.

### 18.1 Full V1 regression suite

Run every V1 test, including restart/resume from checkpoint, current decision precedence, checkpoint concurrency, event idempotency, transactional supersession, project isolation, and source preservation. Any regression blocks V4 completion.

### 18.2 Full V2 regression suite

Run idempotent JSONL import, no-dual-writer cutover tests, exact identifier lookup, keyword search, progressive disclosure, source freshness, project/scope/status filtering, and the five-task evaluation baseline. Any regression blocks V4 completion.

### 18.3 Full V3 regression suite

Run semantic equivalent retrieval, exact/keyword priority, RRF, source deduplication, project isolation for vector results, pinned model/dimension checks, idempotent embedding generation, stale chunk invalidation, provider outage fallback, and retrieval-log privacy. Any regression blocks V4 completion.

### 18.4 Task-end extraction idempotency

Given a completed task with stable checkpoint version and evidence, repeated task-completion retries enqueue one logical extraction job and create no duplicate lesson candidates. Given a task with no reusable learning, the extractor returns zero candidates. A task that has not completed is not automatically extracted unless an authorized explicit operation requests it.

### 18.5 Unsupported candidate rejection

Given an extractor output with missing source refs, fabricated IDs, vague advice, unlabelled inference, secret-bearing content, wrong scope, or invalid fields, the candidate is rejected or quarantined. It must not become active or appear in ordinary search. The rejection log does not contain the unsafe text.

### 18.6 §28.6 inference labeling

Given an LLM-generated inference without direct verification, it remains marked as inference and proposed. Search must not present it as a verified current fact. If it later qualifies as a validated operational hypothesis, its inferred nature and limitations remain clear in every result/detail representation.

### 18.7 Lifecycle and authorization

- Unauthorized actors cannot validate, activate, promote, supersede, or delete a lesson.
- A proposed lesson is not ordinary guidance.
- A validated but inactive lesson is not ordinary guidance.
- Only an authorized explicit activation makes it eligible.
- A stale reviewer action fails if status/version changed after review loaded.
- Superseded/invalidated/archived/deleted items are excluded from default current guidance.
- Every state change is accompanied by the corresponding allowed event or audited record.

### 18.8 §28.5 cross-project lesson

Given a validated and activated sanitized cross-project lesson, an authorized unrelated project with matching task applicability can retrieve it through `search_memory`. Given a project-private lesson with similar text, the caller does not receive it, its title, snippet, source path, project name, source identifier, count, or existence signal. A lesson whose limitations exclude the target task is not returned as applicable advice. Test SQL filtering and `get_memory_details`, not just prompt behavior.

### 18.9 Cross-project promotion sanitation

Given a project-specific candidate containing internal endpoint names, client/customer identifiers, proprietary paths, incident context, or secret-like strings, promotion either redacts/generalizes the information under an approved policy or is rejected. The original private item retains its original scope. The cross-project record is a separately reviewed canonical item and has an auditable provenance relation without exposing restricted source details to downstream unauthorized readers.

### 18.10 Exact deduplication

Given identical normalized lesson candidates from a retried or separate task extraction, only one active canonical lesson remains for that claim/scope/applicability; additional compatible evidence is linked to the survivor. The system records a duplicate outcome and never drops evidence silently.

### 18.11 Near-duplicate and contradiction handling

Given two semantically similar but contextually different lessons, the system does not merge them automatically. Given a real contradiction, both claims and their evidence remain traceable and an explicit unresolved conflict or authorized resolution is recorded. An embedding score alone cannot supersede a record.

### 18.12 Consolidation preserves evidence (§28.13)

Given several compatible lessons, consolidation creates a proposed abstraction with all relevant source links, applicability, limitations and exceptions. Before validation/activation, original lessons remain active. After a reviewer approves a faithful replacement, redundant records can be superseded atomically after evidence links are transferred. Original transcripts, decision records, artifacts and source history remain untouched. The consolidated rule is not stronger or broader than the evidence supports.

### 18.13 Hard purge verification (§28.8)

Given an authorized hard-purge request for a lesson:

1. The target is immediately excluded from normal retrieval when the request commits.
2. The purge job deletes in-scope `memory_items`, old and current `memory_chunks`, embeddings, full-text index data, derived summaries, dependent links and applicable caches/exports/log content.
3. Pending/running extraction, consolidation, embedding and reindex jobs cannot recreate the target.
4. The purge verifier tests direct SQL/details, exact lookup, keyword search, vector search, historical chunk versions and known cache/job paths.
5. A second verification pass confirms the result.
6. The user-facing result is `completed`, `completed_with_external_source_retained`, or `blocked` according to the actual evidence. It is never “completed” merely because a job was queued.
7. Audit markers contain no purged text.

### 18.14 Purge race and resurrection test

Start extraction, embedding, and consolidation jobs, then issue a hard purge while at least one job is pending/running. After all jobs settle and retry, no target content or derivatives reappear. Test worker pre-commit checks and a simulated process restart between purge steps.

### 18.15 Prompt injection resistance (§28.14)

Given task/event/transcript text that instructs the model to leak data, bypass approval, or broaden scope, the extractor/consolidator treats it as untrusted evidence and does not obey it. No secret is inserted into a candidate or cross-project lesson.

### 18.16 Retrieval still improves tasks

Rerun the same five real tasks selected in V2 and the unchanged V3 evaluation. If lessons are expected to help, add tasks whose correct outcome genuinely depends on reusable prior lessons, using canonical evidence and the same model/tool/repository conditions in memory-on and memory-off runs. Report:

- evidence retrieval accuracy
- applicable lesson precision and coverage
- scope/authorization errors
- task completion quality
- regressions caused by irrelevant/stale lessons
- latency, token use, and provider/job costs where measurable

The evaluation is an engineering release gate, not a claim of statistical generality. Do not curate examples solely to inflate the V4 result.

### 18.17 Full-suite requirement

All V1, V2, V3, and V4 tests must pass together. V4 cannot be declared done if its isolated unit tests pass but an inherited path leaks an inactive lesson, exposes another project, revives stale content, or fails purge verification.

---

## 19. Definition of done

V4 is complete only when all conditions below are met:

### Predecessor integrity

- [ ] V1, V2, and V3 handoffs are present and verified against repository reality.
- [ ] All predecessor test suites pass against the current commit.
- [ ] Existing canonical source ownership and single-writer rules are unchanged.

### Lesson extraction and validation

- [ ] Task completion queues an idempotent, bounded extraction job.
- [ ] Extraction uses authorized evidence and stable source refs.
- [ ] Invalid or unsupported candidates are rejected safely.
- [ ] Every extracted candidate starts as `proposed`.
- [ ] Validation and activation are distinct and permission-checked.
- [ ] Inferences remain labelled and cannot silently become fact.

### Cross-project reuse

- [ ] Promotion creates a separate sanitized record.
- [ ] Promotion is explicitly authorized, validated, activated, and audited.
- [ ] Search enforces access filters before candidate content leaves the database.
- [ ] Private source identifiers and text are not disclosed to unauthorized projects.
- [ ] Applicable cross-project lessons are retrievable through the existing `search_memory` facade.

### Deduplication and consolidation

- [ ] Exact duplicate handling is idempotent and preserves provenance.
- [ ] Near duplicates and contradictions are candidate-based, not auto-merged by similarity alone.
- [ ] Consolidation input is bounded and scope compatible.
- [ ] Consolidated lessons preserve evidence, limitations, exceptions and source versions.
- [ ] Redundant lessons are superseded only after an approved replacement is active and links are transferred.
- [ ] Original artifacts, transcripts, decisions and history are not destructively compacted.

### Hard purge

- [ ] Logical deletion immediately excludes targets from ordinary retrieval.
- [ ] Hard purge removes all in-scope memory-owned content and derived copies.
- [ ] Workers, retries, importers, and reindexers cannot resurrect a purged target.
- [ ] Direct, exact, keyword, vector, detail, job and known cache verifications pass.
- [ ] Completion status accurately reports sources/backups outside the purge system's control.

### Operations and scope control

- [ ] Existing worker, migrations, authorization, logging, and facade were reused where possible.
- [ ] No additional database, memory service, graph engine, custom learned model, reranker, query rewriting agent, or RL retrieval layer was introduced.
- [ ] Current task evaluation demonstrates practical value or clearly documents that benefits were not demonstrated.
- [ ] Appendix E handoff is complete, reviewed, and references the actual commit/PR and test output.

---

## 20. Explicitly deferred even after V4

The original phases 0 through 8 will be implemented when the predecessor gates and V4 criteria pass. The following are not implied by “complete V4” and remain out of scope unless a separate future decision authorizes them:

- training or fine-tuning a dedicated memory model
- reinforcement learning or automatic optimization of retrieval policies
- a separate LLM reranker or query rewriting agent
- a new graph database or independent vector store
- automatic activation of unreviewed LLM-generated lessons
- global injection of every active lesson into every agent context
- deletion claims for uncontrolled external sources or backups
- arbitrary indexing of all transcripts, tool outputs, logs, or source files
- a memory-specific microservice or product UI/dashboard

The purpose is successful, accountable Virtual Pod delivery. More infrastructure is not evidence of a better memory system.

---

## 21. Troubleshooting guide

| Symptom | First diagnosis | Correct response | Must not do |
|---|---|---|---|
| No lesson extracted from task | Was task complete? Was the idempotent job queued? Were relevant sources accessible? | Fix trigger/evidence selection and record the reason for zero candidates | Extract every tool call as a workaround |
| Extractor creates many generic lessons | Review extraction prompt/schema and candidate rejection rules | Tighten actionable-value/evidence validation | Automatically activate to clear the queue |
| Correct lesson is proposed but never used | Check validation, activation, scope, index state, applicability and query | Fix the broken lifecycle/index step | Bypass status filters or inject proposed lessons globally |
| Cross-project lesson leaks source information | Audit scope promotion, relation lookup, snippet builders and SQL authorization | Disable affected path, fix policy/query, rerun leakage tests | Remove only the visible citation and leave snippet/title leaking |
| Two related lessons conflict | Inspect conditions, valid times, sources and reviewer evidence | Record `contradicts` or supersede only after authorized resolution | Choose the higher vector score or newest row blindly |
| Consolidation creates an overly broad rule | Compare generated text to each source and limitations | Reject or narrow candidate; keep original lessons | Activate because it is shorter or reduces row count |
| Duplicate grows after retries | Check idempotency keys and unique constraints | Fix candidate identity and transaction boundary | Add periodic deletion to hide duplicate creation bugs |
| A purged lesson reappears | Inspect worker commit checks, chunks, source refs, importer and purge marker | Block retrieval, re-purge, fix resurrection path and add regression test | Treat reappearance as a harmless stale index issue |
| Purge cannot verify all copies | Find ownership boundary and external retention limitation | Mark blocked or completed with external source retained, with facts | Claim complete erasure without verification |
| Search returns an inactive candidate | Inspect canonical status join and chunk eligibility | Fix the facade/SQL filter before release | Hide it only in agent prompt text |

---

## Appendix A. Suggested candidate and consolidation contracts

These are logical shapes; reuse existing naming and schema conventions in the code.

### A.1 Extraction result

```json
{
  "task_id": "actual-task-id",
  "checkpoint_version": 12,
  "extractor_contract_version": "v1",
  "candidates": [],
  "rejections": {
    "unsupported": 0,
    "duplicate": 0,
    "sensitive": 0,
    "invalid_schema": 0
  }
}
```

The counts must be real. Do not include rejected raw content or hidden reasoning.

### A.2 Lesson record body

```json
{
  "memory_type": "lesson",
  "status": "proposed",
  "title": "A specific actionable lesson",
  "content": "One bounded recommendation backed by evidence.",
  "scope": "repository",
  "applicability": {
    "task_types": [],
    "repository_conditions": [],
    "environment_conditions": []
  },
  "limitations": "Known exceptions and conditions.",
  "confidence": "medium",
  "source_refs": [],
  "metadata": {
    "extraction_job_id": "actual-job-id",
    "source_task_id": "actual-task-id",
    "checkpoint_version": 12,
    "inference": false
  }
}
```

`status` is always `proposed` for extraction output. The service, not the LLM, sets canonical identity, timestamps, validated fields, audit fields, and final scope authorization.

### A.3 Consolidation proposal

```json
{
  "input_memory_ids": ["actual-id-1", "actual-id-2"],
  "proposed_lesson": {
    "title": "Generalized but bounded lesson",
    "content": "A single supported claim with a concrete action.",
    "applicability": {},
    "limitations": "Exceptions retained from the evidence.",
    "scope": "project",
    "source_refs": []
  },
  "meaningful_differences": [],
  "contradictions": [],
  "omitted_details_and_reason": []
}
```

The worker validates IDs, reads canonical evidence, verifies that the proposed lesson is no stronger than the evidence, and creates a `proposed` `memory_item`. It must not trust an LLM-supplied scope, permission, source URL, or ID without validation.

### A.4 Purge result

```json
{
  "purge_request_id": "actual-request-id",
  "status": "completed",
  "scope": "memory_item_and_system_owned_derivatives",
  "verified_paths": {
    "canonical_memory_rows": true,
    "chunks_and_embeddings": true,
    "exact_lookup": true,
    "keyword_search": true,
    "vector_search": true,
    "pending_jobs": true,
    "known_caches_exports_logs": true
  },
  "external_source_retained": false,
  "failure_categories": []
}
```

The example is illustrative. Emit `completed` only when every required in-scope verification is true. Do not include the deleted content or raw query in the result.

---

## Appendix B. Example end-to-end flows

### B.1 Completed task produces a useful lesson

1. Developer agent completes Task T with final checkpoint version 8 and verified test output.
2. V1 commits task completion and the checkpoint/event; the existing job mechanism receives one `extract_lesson` job.
3. Worker reads only the authorized final checkpoint, relevant failure/fix events, and referenced test output.
4. Extractor proposes a repository-scoped lesson about an integration test prerequisite and includes the actual test run and compose-file source refs.
5. Validator confirms the source refs and schema; exact duplicate lookup finds no existing lesson.
6. A `proposed` `memory_item` is inserted with an idempotency identity and `derived_from` links.
7. Authorized reviewer verifies applicability and limitation, transitions it to `validated`, then explicitly activates it.
8. Existing indexer generates the current chunk and embedding; `search_memory` can now return it in applicable authorized contexts.
9. Replaying Task T's completion does not create another copy.

### B.2 Lesson is useful to another project

1. Project A has an active repository lesson about testing an integration dependency.
2. An authorized reviewer determines that the engineering lesson generalizes without source-specific details.
3. A separate generalized cross-project candidate is created. Source project paths, incident details, and internal identifiers are not copied into consumer-visible content.
4. Restricted provenance links remain available to authorized reviewers.
5. The new item is validated and activated at `cross_project` scope by an authorized reviewer/policy.
6. Project B can retrieve the sanitized lesson only if its actor/project policy allows cross-project lessons and its task matches applicability.
7. Project B cannot read the private source lesson or learn the origin project's title/path from the returned result.

### B.3 Consolidating repeated lessons

1. Several project-scoped lessons describe the same verified test prerequisite under compatible conditions.
2. Existing lexical/vector search finds the bounded candidate group after access filtering.
3. Consolidation reads the canonical evidence, notes the shared rule and exception, and creates a proposed generalized lesson with links to every relevant input.
4. Reviewer validates and activates the generalized lesson.
5. An authorized merge operation attaches source links to the survivor and supersedes redundant duplicate lessons in a transaction.
6. The original task events, test runs, transcript sections, and artifacts remain preserved.
7. Current search returns the survivor; historical searches can still inspect superseded lessons and their status.

### B.4 Hard-purge prevents resurrection

1. An authorized request targets lesson L and the system-owned derivatives in its purge scope.
2. The transaction marks L deleted/ineligible, invalidates chunks, cancels related work, records a content-free purge request, and queues purge job P.
3. A concurrent embedding or consolidation worker attempts to commit output derived from L; it observes the purge marker and aborts.
4. P deletes L, all old/current chunks, vector data, dependent in-scope summaries/links/log payloads, and pending job copies.
5. The verifier checks direct SQL, exact lookup, full-text search, vector search, detail APIs, queues, caches, and a second pass.
6. Only after verification does the API report the accurate final purge result. An external source that remains is explicitly disclosed as retained or the request is marked blocked if it prevents the requested scope from being fulfilled.

---

## Appendix E. V4 implementation handoff

Complete this template using actual repository evidence. Do not guess or mark unrun tests as passed. If a section is blocked or not applicable, explain why.

# MEMV4 implementation handoff

## 1. Implementation summary

- V4 status: `PASS` / `PASS WITH DOCUMENTED LIMITATIONS` / `BLOCKED`
- Implemented sections of this specification:
- Sections not implemented and reasons:
- Commit/PR reference:
- Reviewer and review date:

## 2. Predecessor verification

- Repository audit path:
- V1 handoff path:
- V1 test command/result:
- V2 handoff path:
- V2 test command/result:
- JSONL cutover/no-dual-writer evidence:
- V2 five-task evaluation path:
- V3 handoff path:
- V3 test command/result:
- V3 demonstrated semantic need and evaluation:
- Actual canonical source-of-truth matrix rechecked:

## 3. Existing code reused

- Agent task-completion hook:
- Memory facade:
- `memory_items` and migration mechanism:
- `memory_chunks` and V2/V3 indexer:
- `memory_events`:
- `memory_links` or decision for adding it:
- Existing worker/job runner:
- Authorization service and permission mapping:
- Source resolver:
- Logging/metrics/tracing:
- Cache/export locations inspected:

## 4. Schema and migration

- Migration identifier:
- Fields/constraints added or reused:
- Relation semantics/direction verified:
- Job types added/reused:
- `memory_items` status and scope constraint tests:
- Clean database migration result:
- Upgrade-from-V3 migration result:
- Rollback/forward-recovery note:

## 5. Task-end extraction

- Trigger location:
- Idempotency key format:
- Final checkpoint/event/source inputs used:
- Source types intentionally excluded:
- Extractor contract/model version:
- Secret redaction/schema validation method:
- Candidates proposed:
- Candidates rejected by reason category:
- Retry/no-duplicate evidence:
- Confirmation no candidate auto-activates:

## 6. Validation and activation

- Review surface/API location:
- Permission checks for proposal, validation, activation:
- State transition tests:
- Evidence review behavior:
- Inference labeling behavior:
- Rejection/retry behavior:
- Indexing begins only after eligible activation: yes/no and evidence

## 7. Cross-project promotion and access

- Promotion API/workflow:
- Permission mapping:
- Sanitization/redaction policy:
- Restricted provenance storage and visibility behavior:
- SQL scope/access filters verified:
- `MEMORY.md` §28.5 result:
- Negative leakage test result:
- Applicability/limitations test result:

## 8. Deduplication and consolidation

- Exact duplicate key/normalization:
- Exact dedupe transaction and evidence-link behavior:
- Near-duplicate candidate mechanism:
- Contradiction workflow:
- Consolidation input bounds:
- Consolidation idempotency key:
- Provenance/exception-preservation checks:
- Validation and activation workflow for proposed consolidation:
- Supersession/old-record treatment:
- `MEMORY.md` §28.13 result:

## 9. Hard purge

- Purge API/action and authorization:
- Defined purge scope:
- Immediate retrieval exclusion behavior:
- Job cancellation and pre-commit checks:
- In-scope storage/cache/export/log inventory:
- Embedding and all historical chunk version deletion result:
- Anti-resurrection marker implementation:
- Direct SQL/details verification:
- Exact lookup verification:
- Full-text search verification:
- Vector search verification:
- Pending/running job race test:
- Second verification pass:
- External source/backup limitations:
- Final result categories used:
- `MEMORY.md` §28.8 result:

## 10. API compatibility

- `get_current_context` regression:
- `record_event` regression:
- `update_task_checkpoint` regression:
- `search_memory` exact/keyword/vector regression:
- `get_memory_details` authorization regression:
- `reindex_source` freshness regression:
- `propose_lesson` behavior:
- `validate_or_activate_lesson` behavior:
- `delete_memory` logical/hard behavior:
- Any backward-compatible response additions:

## 11. Tests and evaluation

- Full V1 suite command/result:
- Full V2 suite command/result:
- Full V3 suite command/result:
- V4 extraction idempotency result:
- Unsupported candidate rejection result:
- `MEMORY.md` §28.5 cross-project result:
- `MEMORY.md` §28.6 inference result:
- `MEMORY.md` §28.8 hard-purge result:
- `MEMORY.md` §28.13 consolidation provenance result:
- `MEMORY.md` §28.14 prompt-injection result:
- Purge race/resurrection result:
- Memory-enabled versus memory-disabled task results:
- Regressions observed and remediations:

## 12. Canonical truth, privacy, and scope

- Confirmation that no second writable source of truth was introduced:
- Confirmation that original source artifacts were not destructively compacted:
- Confirmation that cross-project lesson content was separately sanitized:
- Confirmation that proposed/validated lessons do not enter ordinary guidance:
- Confirmation that purge event/job payloads contain no deleted content:
- Confirmation that restored backups cannot revive purged lessons without reapplying purge state:

## 13. Deferred work and known gaps

- Explicitly deferred work:
- Known gaps/blockers:
- Impact and owner:
- Whether any gap prevents V4 completion:
- Confirmation that no custom memory model, RL, reranker, query rewriting agent, graph database, vector database, or memory microservice was added:

## 14. Final result

- V4 status: `PASS` / `PASS WITH DOCUMENTED LIMITATIONS` / `BLOCKED`
- Evidence location for each acceptance test:
- Reviewer:
- Date:
- Commit/PR:
- Confirmation that V4 implements only the Phase 7/8 delta on top of V1/V2/V3:
- Confirmation that all predecessor gates remain passing:

---

## Final V4 operating rule

**Extract only at explicit task completion from evidence that the agent is allowed to read; store every extracted lesson as proposed; validate and activate through an authorized, auditable workflow; promote cross-project lessons only as separately sanitized records; deduplicate deterministically and review near duplicates; consolidate into proposed abstractions without destroying sources; and mark a hard purge complete only after every in-scope derived copy is removed and verification passes. Reuse the existing PostgreSQL, memory facade, search/indexing, authorization, and job infrastructure. Do not let the memory subsystem become a separate product.**
