# memv3.md

## V3 implementation specification: semantic retrieval with pgvector

**Purpose:** Extend the working V1 and V2 memory implementation with semantic retrieval only when measured V2 failures show that keyword retrieval is insufficient. V3 adds pinned embeddings, pgvector search, Reciprocal Rank Fusion (RRF), source freshness invalidation, and minimal retrieval logging. It does not add continual learning.

**Required predecessors:** `MEMORY.md`, `memv1.md`, and `memv2.md`.

**Version boundary:** V3 implements Phase 6 of `MEMORY.md`. It must not implement the V4 learning scope.

---

## 0. How to use this specification

This document is a build contract, not a claim that the repository has already been inspected or that V1/V2 are implemented. Before changing code, inspect the actual repository and the completed Appendix E handoffs for V1 and V2. Reuse the existing memory facade, PostgreSQL schema, migration framework, source indexer, authorization layer, observability, and job runner wherever they already exist.

The section numbers in `MEMORY.md` are the controlling reference for the broader architecture. This document narrows those instructions to the V3 implementation sequence and removes ambiguity about scope.

### 0.1 Authority order

When two instructions appear inconsistent, resolve them in this order:

1. Security, authorization, privacy, and data deletion requirements.
2. V1 invariants for canonical state, decisions, checkpoints, events, and transaction boundaries.
3. V2 invariants for controlled import, one canonical writer per record type, `memory_items`, `memory_chunks`, exact lookup, keyword search, and progressive disclosure.
4. This document's V3 additions for embeddings and hybrid retrieval.
5. The broader `MEMORY.md` architecture where it does not conflict with a version boundary.

Do not reinterpret a later phase as permission to redesign a working earlier phase.

### 0.2 Binding language

“Must” and “must not” are requirements. “May” indicates an optional action requiring an evidence based reason. A missing prerequisite is a stop condition, not permission to guess.

---

## 1. V3 outcome

V3 is complete when the existing `search_memory` API can combine V2 exact and full text retrieval with pgvector semantic retrieval, fuse the ranked candidates, apply exactly the same project, scope, authorization, status, and freshness filters before content is returned, cite the source of every result, and remain safe when embeddings or the embedding provider are unavailable.

V3 must prove its value with real queries that V2 struggled to answer because the words in the query differ from the words in the stored source. V3 must not be started merely because embeddings are fashionable or pgvector is easy to install.

### 1.1 Concrete user visible behavior

A developer asks, “What did we learn from the earlier service that kept dropping jobs after restart?” The recorded evidence might say, “Background jobs were lost because worker leases were not renewed after process recovery.” A lexical search can miss the relationship between “dropping jobs” and “worker leases were not renewed.” Semantic retrieval should be able to surface the relevant evidence, with its project scope, status, and source reference.

This is a retrieval improvement only. It does not allow the search score to change a decision's status, approve a lesson, infer a new fact, or convert a source excerpt into authoritative truth.

### 1.2 Definition of success

Success requires all of the following:

1. V1 and V2 pass before V3 changes are made.
2. A written V2 evaluation identifies a genuine semantic retrieval gap after indexing and query defects are ruled out.
3. One embedding model and one dimension are pinned for the active vector index.
4. Only explicitly eligible, source backed chunks are embedded.
5. Vector queries enforce the same mandatory filters as V2 inside SQL before returned candidates can leave the database query.
6. Existing exact identifier behavior remains deterministic and takes precedence.
7. Hybrid retrieval uses RRF and deduplicates repeated chunks from the same canonical source section.
8. Source changes make old chunks and embeddings ineligible before replacement embeddings are considered current.
9. Search remains usable through the V2 keyword path if embedding generation fails or semantic retrieval is disabled.
10. The V3 tests and all applicable V1/V2 regression tests pass.
11. The evaluation shows improved recovery of semantically phrased evidence without project leakage or material regression in exact queries.
12. Appendix E is complete and accurately records what was actually implemented.

---

## 2. Mandatory V2 entry gate

### 2.1 Verify V1 and V2 are real and passing

Before implementing V3, locate the completed V1 and V2 handoffs and verify their claims against the repository. Run their actual documented tests. Confirm:

- PostgreSQL is the sole writable canonical store for each record type that has been cut over.
- Project/task/decision/event semantics and checkpoint optimistic concurrency still work.
- Decision approval and supersession remain atomic.
- JSONL import is idempotent and cut over only for record types whose migration was verified.
- There is no dual write between PostgreSQL and JSONL for a cut over record type.
- `memory_items` and `memory_chunks` exist under the existing migration mechanism.
- Direct ID lookup, keyword search, project/scope/status filtering, source citations, and progressive disclosure work.
- The V2 memory-on versus memory-off evaluation on five real tasks exists and has been reviewed.
- V2 tests for import idempotency, source freshness, and project boundaries pass.

If V1 or V2 has not passed, stop. Repair the predecessor separately and update its handoff. Do not label predecessor repair as V3 work.

### 2.2 Prove the need for semantic retrieval

Review unsuccessful V2 queries from the five-task evaluation and any real agent sessions collected under the project's normal privacy policy. Classify each miss into one of these causes:

| Miss category | Example | Required action |
|---|---|---|
| Missing indexed source | The relevant decision was never represented by a searchable chunk | Fix V2 indexing; do not add embeddings to compensate |
| Incorrect source mapping | Chunk points to the wrong artifact or version | Fix V2 provenance and indexing |
| Incorrect filters | The right record was excluded because scope/status mapping is wrong | Fix V2 filter behavior |
| Exact identifier bug | A task ID or file name is not found | Fix deterministic V2 lookup |
| Keyword configuration bug | Search terms are mishandled by parsing or tokenization | Fix V2 lexical search first |
| True semantic mismatch | A valid current source is indexed and authorized, but the query and source use different wording | Candidate V3 use case |
| Ambiguous or unsupported question | No source contains evidence that answers the query | Improve agent clarification or evidence workflow, not embeddings |

V3 is approved only when at least one material, real semantic mismatch remains after fixing the first five implementation defects. Write down the query, expected source, V2 result, miss category, and reason vector retrieval should help. If no such case exists, do not build V3 yet. Keep V2 and record “V3 deferred: no demonstrated semantic retrieval need” in the handoff.

### 2.3 Establish the V2 baseline before changes

Preserve the existing V2 benchmark inputs and outputs. For each evaluation query, record at minimum:

- Query intent and project context.
- Expected canonical source IDs and relevant source sections.
- Exact lookup result, if applicable.
- Keyword result IDs and their ranks.
- Whether the expected source is indexed and eligible.
- Current latency and approximate prompt tokens used by compact results.
- Any excluded project, status, or scope fixture that must never appear.

Do not alter the tasks to make V3 appear successful. Use the same canonical data and query wording for the pre-change and post-change comparison.

---

## 3. Exact V3 scope

### 3.1 Included

1. Repository and predecessor audit specific to semantic retrieval.
2. A pinned embedding provider/model/version and exact output dimension.
3. A forward PostgreSQL migration enabling pgvector and adding the minimal embedding fields/index structures to the existing chunk index.
4. An allowlist for eligible source types and statuses.
5. Embedding of selected V2 chunks only, using the same pinned model for query embeddings and stored chunk embeddings.
6. Reuse of the existing source-aware chunking from V2 unless an evaluation demonstrates a concrete chunk boundary defect.
7. Idempotent generation and updating of embeddings for eligible, current chunks.
8. pgvector retrieval with project, scope, authorization, status, and freshness filters enforced in the SQL query.
9. Hybrid retrieval combining V2 lexical results and vector results using Reciprocal Rank Fusion.
10. Integration behind the existing `search_memory` facade, preserving `get_memory_details` and the V1 APIs.
11. Stale embedding invalidation when a source or chunk changes.
12. A minimal retrieval log, reusing the existing observability system if it can safely record the required metadata.
13. Regression and semantic acceptance testing, including a rerun of the V2 five-task comparison.
14. Appendix E V3 handoff.

### 3.2 Explicitly forbidden in V3

Do not implement any of the following:

1. Lesson extraction at task end or automatic lesson proposals.
2. Lesson state transitions such as `proposed → validated → active` as a learning workflow.
3. Cross-project lesson promotion or automatic access to another project's memory.
4. Background consolidation, “dreaming,” automatic summarization of task trajectories, or memory compaction.
5. Automatic semantic duplicate merging or autonomous contradiction resolution.
6. A new memory microservice, separate vector database, or graph database.
7. A second writable store for any existing record type.
8. A new job/queue framework when the repository already has a suitable worker or task runner.
9. A custom embedding model, fine tuning, retrieval training, or reinforcement learning.
10. A separate reranker model, agentic multi-step retrieval planner, query rewriting model, or LLM reranking.
11. ANN index tuning before exact pgvector retrieval is measured and shown to be too slow.
12. Indexing every file, source code file, tool output, transcript line, or event by default.
13. Replacing Graphify or using it as the general memory store.
14. Rewriting canonical Markdown, meeting transcripts, or original JSONL source artifacts to simplify indexing.
15. Hard purge workflows or the V4 continual learning scope. Existing deletion safety still applies: deleted records must immediately be ineligible and their derived embeddings must not be returned.

If an implementation idea falls into this list, record it as deferred work and do not ship it in V3.

---

## 4. Architecture: reuse V1 and V2

### 4.1 Component responsibilities

| Component | Responsibility in V3 | Change permitted? |
|---|---|---|
| Existing agent lifecycle | Calls `get_current_context` at task start, calls `search_memory` when relevant, uses source backed evidence | Small integration changes only if needed to pass the existing actor/project context |
| Existing memory facade | Stable public interface for memory operations | Extend internals of `search_memory`; do not bypass it |
| PostgreSQL canonical tables | Own project, task, decision, event, and memory item state according to V1/V2 ownership | Forward migrations only |
| `memory_chunks` | Rebuildable source-aware text index; now also holds or links the selected chunk embedding | Add only required vector metadata/column(s) |
| V2 exact lookup | Resolve IDs and exact keys deterministically | Must remain first-class and unchanged in meaning |
| V2 full text retrieval | Retrieve candidates based on lexical overlap | Retained and run as one input to hybrid retrieval |
| Embedding adapter | Calls the chosen embedding model for a chunk or query | New small module using current provider/client conventions |
| Existing worker/job runner | Retries and runs index work if one exists | Reuse; do not introduce an independent queue |
| Existing authorization layer | Determines actor permissions and project access | Must remain the source of access decisions |
| Retrieval log/telemetry | Records limited metadata needed to debug and evaluate retrieval | Reuse existing telemetry; add a minimal table only if required |
| Canonical artifacts and source refs | Retain original source and provenance | Do not rewrite or move them for V3 |
| Graphify | Code relationship analysis | Unchanged |

### 4.2 Search data flow

```text
Agent / developer
        |
        v
search_memory(query, project_id, scope, filters, limit, actor)
        |
        +--> Validate input and authorize actor/project/scope
        |
        +--> Deterministic exact ID/path lookup when applicable
        |
        +--> V2 full text retrieval --------------------+
        |                                               |
        +--> Embed query using pinned model             |
        |       |                                       |
        |       v                                       |
        |    pgvector retrieval ------------------------+
        |                                               |
        +-----------------------------------------------+
                                |
                                v
                 RRF fusion and source deduplication
                                |
                                v
             Revalidate canonical status/source freshness
                                |
                                v
                Compact results + source references
                                |
                                v
                   Agent opens details if needed
```

Exact identifier lookup remains deterministic and must not wait for embedding service availability. In the ordinary query path, the facade may run lexical and vector retrieval in parallel after authorization, or sequentially if that fits the existing architecture. Parallel execution is an optimization, not a new service requirement.

### 4.3 Indexing and update data flow

```text
Canonical record or approved source section changes
        |
        v
V2 source/chunk indexing logic computes source_version and content_hash
        |
        v
Mark previous chunk version stale/ineligible immediately
        |
        v
Build eligible source-aware V2 chunk(s)
        |
        v
Compute embedding input and input hash
        |
        v
Call pinned embedding model
        |
        v
Verify chunk version is still current
        |
        v
Store vector + model/version metadata idempotently
        |
        v
Mark embedding ready for retrieval
```

A failed or delayed embedding job never restores an old chunk to current status. During failure, the V2 keyword path continues to operate on the current eligible text chunks.

### 4.4 No new canonical source

`memory_chunks` is a derived retrieval index, not authority. Embeddings are derived data. Canonical project state remains in the V1 structured tables and approved artifacts according to the existing source-of-truth matrix. The V2 memory item and chunk model remains in force. V3 does not change a source's meaning, status, permissions, or ownership because of a vector score.

---

## 5. Embedding model pinning and provider policy

### 5.1 Required decision before migration

Do not begin a vector migration until the repository audit and a short architecture decision record identify:

1. Exact embedding provider or local runtime.
2. Exact model identifier and version, not an alias such as `latest`.
3. Exact vector dimension returned by that model.
4. Similarity metric used for retrieval.
5. Whether vectors are normalized by the provider or by local code.
6. Whether source text or query text leaves the environment.
7. Data handling approval for the actual memory classes being embedded.
8. Request timeout, retry, rate limit, batching, and cost controls.
9. Maximum model input length and the behavior when input is too long.
10. Model upgrade and full-reindex procedure.

The choice must fit the existing deployment, privacy rules, operational budget, and availability requirements. Do not invent a model choice in code before this decision is recorded. If external processing is not authorized for a source class, do not embed that class with the external provider.

### 5.2 Configuration contract

Use the existing configuration mechanism. The following names are illustrative unless the project already has equivalents:

```text
MEMORY_VECTOR_ENABLED=true|false
MEMORY_EMBEDDING_PROVIDER=<provider-or-local-runtime>
MEMORY_EMBEDDING_MODEL_ID=<exact-pinned-model-id>
MEMORY_EMBEDDING_DIMENSION=<verified-integer>
MEMORY_EMBEDDING_METRIC=cosine
MEMORY_EMBEDDING_TIMEOUT_MS=<bounded-integer>
MEMORY_EMBEDDING_MAX_ATTEMPTS=<bounded-integer>
MEMORY_EMBEDDING_BATCH_SIZE=<bounded-integer>
MEMORY_VECTOR_CANDIDATE_LIMIT=<bounded-integer>
MEMORY_RRF_K=60
MEMORY_RETRIEVAL_LOG_ENABLED=true|false
```

Do not create a standalone configuration framework just for these values. Reuse existing environment, settings, and secret management conventions. Database credentials and provider secrets must never be stored in memory rows or source artifacts.

### 5.3 Pinning invariants

1. Query embeddings and stored chunk embeddings must come from the same pinned model family and compatible model version.
2. All vectors in one active vector column/index must have the configured dimension and comparable embedding semantics.
3. Store the exact model ID/version alongside each generated embedding for validation and diagnostics.
4. Refuse to compare a vector with a different configured model ID, even when the dimensions happen to match.
5. Validate provider response dimension before writing the vector.
6. Do not silently change the configured model when a provider alias changes.
7. A model change is a deliberate migration and re-embedding operation, not a normal application deployment side effect.
8. If the provider response is malformed or has the wrong dimension, mark the job failed and keep that chunk out of vector retrieval.

### 5.4 Model upgrade procedure

V3 should support one active model/dimension pair, not arbitrary mixed-model search. If the model later changes:

1. Record the change and its rationale.
2. Determine whether the dimension changed. If yes, the database column/index must be migrated or a separate temporary rebuild column/table used for a controlled switch.
3. Re-embed all currently eligible chunks with the new model.
4. Verify all selected chunks have valid embeddings for the new model.
5. Switch the configured active model/index atomically or under an explicit maintenance gate.
6. Remove or retire old vectors only after rollback no longer needs them and retention rules permit.
7. Rerun the semantic, exact lookup, boundary, freshness, and task outcome tests.

Do not mix vectors from old and new models in the same retrieval ranking during a partial rollout. If supporting a blue/green index would require a new complex deployment system, use a documented maintenance-window reindex instead.

### 5.5 Similarity metric

Use cosine distance as the initial metric unless the selected embedding model's documented behavior and repository benchmark justify another supported metric. Use the same metric consistently in SQL and tests. The vector distance is a candidate-ranking signal; it is not a truth or confidence score. Do not expose raw distance as a user facing probability or certainty estimate.

---

## 6. What gets embedded

### 6.1 Allowlist, not crawl everything

Reuse V2's source indexing and chunking. Add a small, explicit eligibility policy for semantic indexing. The initial eligible categories should be selected from real repository records and may include:

- Current approved decisions and their rationale.
- Explicit source-backed memory items whose type is approved for search.
- Selected incident, failure, and fix summaries when represented as eligible V2 records.
- Selected meeting segments containing decisions or meaningful unresolved context, when they have been deliberately indexed.
- Task summaries/checkpoints only if the V2 evaluation demonstrates that they help find relevant past work.
- Approved sections of Markdown artifacts where normal exact/keyword lookup is insufficient.

The list must match real V2 source types and actual authorization rules. Do not invent a new type just to force a source into the vector index.

### 6.2 Never embed by default

Do not embed:

- Every file in the repository.
- Every source code file. Existing code search and Graphify remain the default for code relationships and symbol lookups.
- Every raw tool call, terminal output, chat turn, or JSONL line.
- Credentials, secrets, API keys, tokens, or unredacted sensitive data.
- Deleted, inaccessible, superseded, stale, or otherwise ineligible sources for current-guidance retrieval.
- Content that the actor is not permitted to send to the selected embedding provider.
- Duplicate copies of the same source because it happens to exist in multiple folders.

If a real use case later shows that code chunks must be embedded, document that as a measured extension instead of silently enabling repository-wide embedding.

### 6.3 Eligibility contract

Eligibility is checked from canonical source metadata and the configured allowlist before generating an embedding. A copied status in `memory_chunks` is only a convenience field; it is not the final authority. Before a vector candidate is returned, the query must join to or otherwise verify the current canonical source status and access scope.

A candidate is ineligible if any of these are true:

- The source has been deleted or marked unavailable.
- The source version does not match the current indexed version.
- The chunk is marked stale.
- The record's status is not eligible for the requested query mode.
- The actor cannot access the project or scope.
- The chunk was generated with a model ID that is not the configured active model.
- The embedding status is not `ready` or the vector is null.

### 6.4 Embedded input content

Construct the embedding input deterministically from a compact semantic payload, normally:

1. Source title.
2. Relevant section or decision heading.
3. Chunk content.
4. A short, safe record-type label if that label helps disambiguate the content.

Do not include secret-bearing paths, provider credentials, actor tokens, database-only metadata, full source trees, or unrelated adjacent chunks in the embedding input. Metadata needed for filtering is stored separately and must not be inferred from the vector.

Record a hash of the normalized embedding input. If the input hash, pinned model ID, or required model version is unchanged and a valid vector already exists, the indexer must not call the provider again.

### 6.5 Input length and truncation

The indexer must respect the selected model's maximum input length. Prefer the existing source-aware chunk boundaries. If a chunk exceeds the model limit:

1. Reuse or improve V2's deterministic chunk splitting only for that measured case.
2. Preserve headings and source anchors in every derived chunk.
3. Do not silently truncate the end of a decision, error/fix explanation, or source excerpt.
4. Ensure each resulting chunk still points to its exact source ID, version, and anchor.
5. Test deterministic rebuild behavior.

Do not use an LLM to rewrite or summarize content as part of V3 embedding preparation. That is not part of this version.

---

## 7. Database changes

### 7.1 Migration principles

1. Use the existing migration framework and the current V2 schema as the starting point.
2. Create a forward-only V3 migration. Never edit a migration that has already been applied in an environment.
3. Do not replace or rename V1/V2 tables for stylistic reasons.
4. Do not introduce a second database.
5. Enable pgvector through the approved PostgreSQL migration/deployment process. Do not make application startup silently attempt privileged extension installation.
6. Run the migration against a clean V1-to-V2 test database and a copy of a realistic existing database.
7. Verify rollback or disable procedures. A rollback must not delete canonical records or source artifacts.
8. Keep the V2 keyword index operational if vector columns or jobs are unavailable.

### 7.2 Where embeddings live

Prefer adding embedding fields to the existing `memory_chunks` table because that table is already the rebuildable, source-aware search index. Do not create a separate vector database. Do not create a new `memory_embeddings` table unless the repository audit reveals a hard schema limitation that cannot be handled safely with a forward migration; if that exception is required, record the reason and keep one-to-one source version ownership clear.

The migration must add the equivalent of these fields, adapting names to the existing naming conventions:

| Field | Type/meaning | Required invariant |
|---|---|---|
| `embedding` | `vector(N)` where `N` is the verified configured dimension | Null until valid generation succeeds; only one active model/dimension per index |
| `embedding_model_id` | Text identifier | Exact pinned model identifier used for this vector |
| `embedding_input_hash` | Stable hash of normalized embedding input | Prevents unnecessary recomputation and identifies input changes |
| `embedding_status` | Controlled value such as `pending`, `ready`, `failed`, `not_eligible` | Only `ready` vectors are eligible for vector retrieval |
| `embedding_generated_at` | Timestamp, nullable | Set only after a valid vector has been stored |
| `embedding_error_code` | Optional bounded code, not raw provider error body | Supports operational debugging without leaking secrets |

Use the equivalent existing freshness, content hash, source version, `is_stale`, status, and indexing timestamps already defined in V2. Do not duplicate these fields under new names. If one of the required embedding semantics is already represented by a sound existing field, reuse it.

### 7.3 Dimension is a migration-time constant

`N` must be substituted with the exact dimension confirmed from the selected model. Do not commit a literal placeholder such as `N` or `EMBEDDING_DIMENSION` into executable SQL. Do not choose a random dimension and hope the runtime matches it.

The migration should define the vector column using the database type syntax supported by the installed pgvector version. The build must validate the installed extension/version and the selected PostgreSQL deployment before finalizing SQL.

### 7.4 Constraints and indexes

At minimum:

- `embedding_status` is constrained to the documented enum/check set.
- A row with `embedding_status = 'ready'` must have a non-null vector, model ID, input hash, and generation timestamp.
- A row with a non-null vector must have a model ID equal to the active model policy for that index.
- The unique source identity/version/chunk identity rules from V2 remain intact.
- Stale chunks are never eligible in vector SQL regardless of whether their old vector remains physically present.
- Existing GIN/full text indexes remain active and tested.

Start with exact pgvector scanning on the eligible filtered set. Do not add HNSW, IVFFlat, or other approximate nearest-neighbor indexes until a benchmark on the real corpus demonstrates that exact vector search violates the accepted latency objective and the proposed approximate index is measured for recall. Index optimization is not the default V3 task.

### 7.5 Embedding state machine

Use a small state set:

- `not_eligible`: current policy excludes this chunk.
- `pending`: this source version is eligible and needs an embedding.
- `ready`: a valid vector exists for the exact current input hash and active model.
- `failed`: generation failed after the configured bounded retry policy.

Transition rules:

```text
new eligible chunk              -> pending
pending + valid provider result -> ready
pending + exhausted retries     -> failed
failed + explicit retry         -> pending
any source version change       -> old chunk stale; new current chunk pending
source becomes ineligible       -> not_eligible and excluded immediately
source deletion/status loss     -> excluded immediately; vector cleanup follows existing deletion policy
```

Do not mark a chunk `ready` before the database write is committed. If source state changes while a provider request is in flight, the result must be discarded rather than attached to the new source version.

---

## 8. Embedding generation and indexing lifecycle

### 8.1 Reuse the V2 indexer

Extend the existing indexing pipeline after it has created or updated a current V2 chunk. Do not build a second crawler that independently scans the repository. The V2 indexer owns source discovery, source references, chunk IDs, source versions, and lexical index data. V3 adds the embedding stage to eligible chunks.

### 8.2 Idempotency key

An embedding work item is uniquely identified by the tuple:

```text
(chunk_id, source_version, content_hash, embedding_input_hash, embedding_model_id)
```

If the same tuple has already completed successfully, do not generate it again. If it is pending, do not enqueue a second active job. A retried job may run more than once but must leave one consistent ready vector for the same tuple.

Use the existing job runner if present. If no background runner exists, use the simplest existing application mechanism that can safely retry bounded work. Do not create a general-purpose orchestration service for this feature.

### 8.3 Job payload

A job payload should contain identifiers and version information, not duplicate a large copy of the source text:

```json
{
  "job_type": "embed_memory_chunk",
  "chunk_id": "<chunk-uuid>",
  "source_version": "<source-version-or-hash>",
  "content_hash": "<chunk-content-hash>",
  "embedding_input_hash": "<normalized-input-hash>",
  "embedding_model_id": "<pinned-model-id>"
}
```

The worker fetches the current eligible text, revalidates authorization policy and hashes, generates an embedding, validates dimension and model ID, then writes it only if the chunk is still current. If the chunk changed while the job was running, discard the vector result and arrange indexing for the current version.

### 8.4 Provider failures

- Apply a bounded timeout.
- Retry transient rate limit, network, and server failures with bounded exponential backoff and jitter, using the repository's existing retry convention if available.
- Do not retry invalid input or a dimension mismatch indefinitely.
- Do not include provider response bodies, source content, credentials, or raw query text in errors.
- Mark failed work visibly and allow a safe retry command or existing job retry mechanism.
- Keep exact and keyword search available throughout an embedding outage.
- Do not block task execution waiting for every eligible corpus item to be embedded.

### 8.5 Backfill procedure

Run an explicit, repeatable backfill command or job for existing V2 chunks. Do not start a full backfill automatically at application startup.

The command must support:

- Dry run and counts by source type, status, and eligibility reason.
- A bounded batch size.
- Resume after interruption.
- Explicit provider/model configuration check.
- Rate/cost controls.
- Summary counts for eligible, already ready, newly embedded, skipped, failed, and stale-during-processing chunks.
- A safe no-vector mode for deployments where the provider is unavailable or not approved.

Run a small canary batch first. Inspect result quality, source mapping, rate limits, and costs. Then continue in bounded batches. Exact counts and batch size should be configured from the actual environment, not invented in this specification.

### 8.6 Deletion and status transitions

When the canonical source is deleted, hidden, superseded, or becomes ineligible for current retrieval, the retrieval query must exclude it immediately through canonical status and freshness joins. Any existing vector must not cause it to appear in search. Physical vector cleanup must follow the established deletion/retention policy and must not recreate the deleted source.

V3 does not implement the V4 hard-purge workflow. It does still enforce all existing V1/V2 deletion safety requirements, including immediate exclusion and ensuring pending embedding jobs cannot resurrect deleted or stale content.

---

## 9. Query embedding

### 9.1 When to generate a query vector

Only generate a query embedding for a nonempty, authorized query that reaches the semantic search path. Exact identifier queries should be resolved deterministically first. If exact lookup fully satisfies the request under existing API semantics, do not require a provider call just to return the exact source.

### 9.2 Query preprocessing

Preprocessing must be deterministic and minimal. Trim surrounding whitespace and enforce the existing query length limit. Preserve meaningful words, technical terminology, names, versions, and identifiers. Do not have an LLM rewrite the query in V3. Do not remove terms purely to increase semantic recall.

Use the same pinned model as the stored chunk vectors. Validate the generated query vector dimension before sending it to SQL. If query embedding fails, record the failure metadata and fall back to the V2 exact/keyword path.

### 9.3 No sensitive query persistence by default

Do not store complete raw query strings in a retrieval log by default. The query is sent to the embedding provider only under the approved data handling policy. If the selected provider does not permit the relevant query data to leave the environment, disable semantic retrieval for that query/source class and use keyword search.

### 9.4 Empty and invalid vectors

A malformed vector, empty model response, NaN/infinite values, wrong dimension, or unsupported model ID is an error. It must not be saved or compared. Record a bounded error code, fall back to V2 search, and do not mark the query or chunk embedding as successful.

---

## 10. Vector retrieval with pgvector

### 10.1 Required candidate filters

Vector retrieval uses the exact same mandatory filter semantics as V2 keyword retrieval. Before candidates are returned, SQL must enforce:

1. Authorized actor and project access.
2. Explicit `project_id` matching the requested project for project-scoped search.
3. Requested allowed scope and any higher level visibility boundary.
4. Canonical source status eligibility for the current query mode.
5. Source is not deleted, hidden, or otherwise unavailable.
6. Chunk is not stale and its source version is current.
7. Embedding status is `ready`.
8. Vector is not null.
9. Embedding model ID matches the configured active model.
10. Requested record types and time bounds, when supplied.
11. The source type is allowed by the semantic indexing policy.

Filters are not applied after candidates have been selected. A highly similar but inaccessible record must not have its title, snippet, path, ID, or existence disclosed. Query parameters must be passed safely through the repository's database abstraction.

### 10.2 Canonical validation

The query must join `memory_chunks` to its current canonical source or invoke the existing currentness validation mechanism before returning a candidate. Copied `memory_status`, scope, or source version fields are insufficient as the sole authority. V1 canonical decision status and V2 source mapping remain decisive.

### 10.3 Candidate limit

Use a bounded candidate pool. Start with a configurable pool size sufficient for RRF (for example 20 to 50 candidates per method if the corpus and latency allow), then validate it on the actual task set. The final `limit` for the API remains bounded by V2's compact result contract. Do not retrieve unbounded vectors and truncate only after loading content.

The initial implementation should use exact vector search over eligible rows. This is easier to reason about and gives a strong baseline for relevance evaluation. Add an approximate index only in a separately justified change after measuring real latency and recall. Do not use an approximate index to mask missing SQL filters.

### 10.4 Metric and ordering

For cosine distance, lower distance indicates closer vectors. Keep the distance internal to candidate ranking unless the API has a specific documented diagnostic field. Do not call `1 - distance` a probability or confidence score. Use a deterministic secondary sort such as canonical ID/chunk ID to make tie behavior repeatable.

### 10.5 Vector results are only candidates

A vector match does not establish that the text is true, approved, current, relevant to the exact task constraints, or permitted. The search facade must preserve source status and provenance in the result. Agents must inspect canonical decisions or source details before treating a result as current approved guidance.

---

## 11. Hybrid retrieval and Reciprocal Rank Fusion

### 11.1 Retrieval order

The `search_memory` facade must preserve V2's existing behavior and add one semantic candidate source. The preferred flow is:

1. Validate the request and authorize project/scope.
2. Attempt exact ID/path lookup when the query matches a supported identifier pattern.
3. If an exact accessible match fully satisfies the direct lookup contract, return it first; do not allow semantic ranking to demote it.
4. Run V2 full text retrieval against eligible chunks.
5. Generate the query embedding using the active pinned model.
6. Run pgvector retrieval using the same mandatory filters as V2.
7. If semantic retrieval is unavailable, use the V2 exact/keyword result path and record a fallback reason.
8. Fuse lexical and vector rankings using RRF.
9. Deduplicate multiple chunks from the same source section or canonical source, retaining the best source-backed snippet according to the V2 result contract.
10. Revalidate current canonical status and source freshness.
11. Return compact results with source references and bounded metadata.
12. Let the caller use `get_memory_details` for full source-backed content.

The implementation may run keyword and vector retrieval in parallel after authorization if supported by the existing database/provider architecture. This must not change ordering, permissions, fallback, or result semantics.

### 11.2 RRF formula

For each candidate, calculate:

\[
\operatorname{RRF}(d) = \sum_{r \in R} \frac{1}{k + \operatorname{rank}_{r}(d)}
\]

Where:

- `R` is the set of retrieval result lists, initially full text and vector.
- `rank_r(d)` is the one-based rank of candidate `d` in result list `r`.
- `k` is a configurable rank constant, initially 60 unless evaluation justifies another value.
- A candidate absent from one list contributes zero for that list.

Ranks are one-based. Do not combine incompatible raw PostgreSQL text rank values and vector distances arithmetically. RRF uses ranks, not raw score scales.

### 11.3 Exact match treatment

Exact identifier lookup remains a deterministic first-priority path. It is not made “just another vector candidate.” If the existing V2 API combines exact and keyword results, preserve that contract: exact match at the top, with the remainder optionally fused. A query that specifies a known decision ID must never return a semantically similar different decision instead of the addressed record.

### 11.4 Deduplication

A canonical record can produce multiple chunks and therefore appear in both lexical and vector result lists. Deduplicate after ranking by the stable source section identity if one exists; otherwise use canonical source identity plus source anchor. Do not deduplicate distinct decisions merely because their text is similar.

When multiple chunks from one source are matched:

1. Keep the best fused chunk as the compact result by default.
2. Preserve its exact source anchor and source version.
3. Optionally include a bounded `matched_chunk_count` for debugging if existing API response conventions allow it.
4. Do not concatenate multiple distant chunks into one snippet without a documented need.

### 11.5 Relevance filters and score thresholds

Do not begin with an arbitrary cosine distance threshold that hides potentially relevant results. First measure the rank behavior and false positive rate on the real evaluation queries. RRF ranks lexical/vector candidates; canonical filters remove invalid candidates. If evaluation later justifies a semantic distance threshold, document the measured basis, model, metric, and expected failure behavior. Treat it as configuration, not a universal truth.

### 11.6 Stable output

For equal RRF scores, use stable secondary ordering, for example exact match flag, then best lexical/vector rank, then canonical source ID. Do not rely on nondeterministic database row order. Existing output fields remain unchanged unless adding optional fields is backward compatible.

### 11.7 Fallback rules

| Failure | Required behavior |
|---|---|
| Query embedding provider timeout | Run/return V2 exact and keyword retrieval; mark semantic fallback in internal metadata |
| Provider rate limited | Apply bounded retry if latency budget permits; otherwise fall back |
| Wrong query vector dimension | Reject vector path; fall back; log bounded error code |
| pgvector unavailable or query fails | Fall back to V2 search; surface operational diagnostic without raw SQL |
| No current vectors indexed | Return V2 results and identify vector coverage in diagnostics |
| Vector list empty but lexical list nonempty | Return lexical results unchanged, correctly cited |
| Lexical list empty but vector results exist | Return vector results only after all filters and canonical status checks; source-backed citations are mandatory |
| Exact ID found | Preserve the exact ID result at highest priority |
| Authorization denied | Do not run retrieval outside authorized scope or disclose inaccessible result existence |

Fallback must not silently represent keyword-only results as if hybrid search succeeded. The user-facing result may remain stable, but internal `retrieval_mode` and logs must identify the actual mode.

---

## 12. `search_memory` API extension

### 12.1 Keep the existing public signature

V3 extends the implementation of the V2 facade function, not the API surface with a competing endpoint. Preserve the existing parameters and semantics:

```text
search_memory(query, project_id, scope, filters, limit, actor)
```

If the repository uses a typed request object or different casing, keep the existing contract. Do not introduce a duplicate endpoint such as `search_vector_memory` unless there is a concrete existing framework requirement and it is approved.

### 12.2 Required response semantics

The response must preserve V2 compact result fields and may add backward-compatible metadata such as:

```json
{
  "project_id": "<project-uuid>",
  "results": [
    {
      "id": "<canonical-or-memory-item-id>",
      "title": "<short title>",
      "snippet": "<bounded source-backed excerpt>",
      "source_type": "<type>",
      "source_ref": "<source uri/path/record ref>",
      "source_version": "<current source version>",
      "status": "<canonical status>",
      "scope": "<authorized scope>",
      "matched_by": ["keyword", "vector"],
      "rank": 1
    }
  ],
  "has_more": false,
  "retrieval_mode": "hybrid"
}
```

This is a shape example, not an instruction to rename fields that already exist in V2. Keep the current source reference and access semantics exactly. `matched_by` may contain `exact_id`, `keyword`, and/or `vector`. The values must reflect the actual retrieval sources that found the candidate. `retrieval_mode` must distinguish `exact`, `full_text`, `hybrid`, and any documented fallback mode in a way consistent with existing conventions.

### 12.3 Do not return full details automatically

V2's progressive disclosure contract remains binding. Search returns compact snippets and source references. Full details are fetched by `get_memory_details` after the agent selects relevant IDs. Semantic search does not justify injecting full transcripts or documents into every agent prompt.

### 12.4 Existing API compatibility

- `get_current_context` remains the source for current project/task context.
- `record_event` retains its V1 event contract.
- `update_task_checkpoint` retains V1 optimistic concurrency.
- `get_memory_details` retains V2 access and freshness checks.
- `search_memory` retains its request semantics and mandatory filters.

No agent is allowed to call pgvector directly. All retrieval goes through the existing facade so there is one place to enforce permissions, currentness, compact result shaping, and observability.

### 12.5 Query-side fallback policy

The facade should not make task execution depend on the embedding provider. If vector retrieval is disabled or fails, `search_memory` must return valid V2 results when those exist. Use the existing error envelope when database access itself fails. Do not return an empty successful result if the request was not actually processed; distinguish no matches from semantic fallback or total retrieval failure according to repository conventions.

---

## 13. Source changes, invalidation, and freshness

### 13.1 Source version is the boundary

The vector is attached to one specific `memory_chunks` row/version and a normalized embedding input hash. When source content or embedding input changes, the previous embedding is no longer eligible for current search. Do not update a chunk's text in place and leave its old vector marked ready.

### 13.2 Update sequence

When the source changes:

1. Detect the canonical source version/content hash change using V2's existing mechanism.
2. In the same safe indexing transaction or immediate follow-up operation, mark old chunks stale/ineligible before search can return them as current.
3. Create the current chunk records using the existing V2 chunker and source anchors.
4. Generate new lexical search vectors as V2 does.
5. Mark eligible embeddings pending; mark excluded records `not_eligible`.
6. Enqueue embedding generation with the source version, content hash, input hash, and model ID.
7. Store a vector only when the source version and input hash still match after the provider response.
8. Mark `ready` only after the vector data and its status commit successfully.
9. Verify that a retry does not create duplicate chunks or embeddings.

For an unstructured artifact update, use the existing version/hash discipline. Do not assume file modification time alone reliably proves content identity.

### 13.3 Do not revive a stale source after failed reindex

If new embedding generation fails, the current chunk stays in the database with its correct text/source version and lexical search capability; its vector stays unavailable. The old vector remains ineligible. Failed indexing must not cause the system to roll back to searching content that is no longer current.

### 13.4 Deletion and status update

If a source is deleted, access is revoked, or canonical status changes so it is no longer eligible for default retrieval:

1. The SQL eligibility join must exclude it immediately.
2. A stale chunk's vector may not be returned even while physical cleanup is pending.
3. Pending embedding jobs must recheck status and abort.
4. No retry is allowed to recreate or republish the removed vector.
5. Physical deletion or retention follows the existing source deletion policy.

V3 must not add the V4 hard-purge management workflow, but it cannot weaken V1/V2 deletion or visibility requirements.

### 13.5 Reindexing is idempotent and rebuildable

A repeated reindex of the same source version and same model must produce no duplicate chunks and no unnecessary embedding regeneration. A full reindex command must be explicit and bounded. Rebuilding embeddings from eligible source text must not alter canonical decision, task, event, or memory records.

---

## 14. Retrieval logging and evaluation instrumentation

### 14.1 Reuse existing telemetry first

Inspect the existing logger, tracing, metrics, and event conventions. Reuse them if they can record the required metadata with appropriate redaction and retention. Do not add a database table solely because this document names a “retrieval log.” Add a small `memory_retrieval_log` table only if existing telemetry is insufficient for reproducible evaluation and the need is documented.

Do not store retrieval diagnostics in the canonical `memory_events` history if that table is reserved for meaningful project state/events. Ordinary reads should not pollute the event stream used for decisions and task history.

### 14.2 Minimum logged fields

Log only bounded operational metadata:

- Timestamp and request/correlation ID.
- Project ID and a safe actor identifier or role.
- Query class such as `exact_id`, `keyword`, `semantic`, `hybrid`, or `fallback`.
- Retrieval methods actually used.
- Candidate counts from lexical and vector paths.
- Candidate source IDs or stable candidate identifiers where security policy permits; do not include source text.
- Selected result IDs and final ranks.
- Active model ID/version and vector-index coverage state.
- Authorization/filter outcome category, without exposing inaccessible record details.
- End-to-end retrieval latency and per-path latency where available.
- Whether a provider/database fallback occurred, using a bounded error category.
- Compact output token estimate, if the runtime already measures it.

### 14.3 Do not log raw content by default

Do not persist full user prompts, raw query text, full snippets, full source contents, embedding vectors, credentials, or provider response bodies in retrieval logs. If query level evaluation needs to tie runs together, use an existing secure trace ID or a carefully scoped keyed fingerprint. A plain hash of a short predictable query is not necessarily anonymization.

### 14.4 Retention and access

Use the repository's established operational log retention and access model. Retrieval logs are diagnostics, not memory and not a source for future agent context. They must not appear as searchable memory chunks. Restrict access to project-scoped logs according to existing policy.

### 14.5 Metrics

Collect enough data to answer:

- Did semantic retrieval run, or did the request fall back to V2?
- Was the expected source within the lexical top-k, vector top-k, or fused top-k?
- Did hybrid retrieval improve reciprocal rank of the expected source?
- How often did a vector candidate fail canonical status, scope, or freshness validation?
- How many eligible chunks lack ready embeddings, and why?
- How long did embedding generation and each retrieval path take?
- What is the provider error rate, retry rate, and approximate cost where measurable?
- Does the feature improve actual task outcomes rather than only retrieval metrics?

Metrics should help decide whether V3 is useful and whether the operational burden is justified. Do not optimize a proxy metric while task quality worsens.

---

## 15. Security and access boundaries

### 15.1 Same authorization as V2

Vector search must not create a new global search pathway. A request requires explicit project context and trusted actor/authorization context under the existing API. Do not infer permission from the query, source title, embedding similarity, or the presence of a row in `memory_chunks`.

### 15.2 Filter inside the database query

Apply project, scope, canonical status, source freshness, embedding readiness, and model ID conditions inside the vector SQL query before candidate rows are returned to application code. Do not query global top-k and filter inaccessible rows afterward. Post-filtering can both leak information and crowd eligible sources out of the top-k.

### 15.3 Untrusted content remains untrusted

Embedding does not make source content trustworthy. Retrieved content may contain instructions intended to manipulate an agent. Return it as quoted or labeled source material, not as system instructions. Preserve V2 prompt-injection protections and source attribution.

### 15.4 Provider data handling

If an external provider is used, confirm that the selected source classes and queries may be transmitted to it. Avoid sending secret-bearing context. Where a source class is disallowed, keep it on the lexical path or exclude it from semantic indexing as per the established policy. Do not log provider request bodies for debugging.

### 15.5 Do not reveal inaccessible existence

If a highly similar vector belongs to an inaccessible project, it must never be exposed through its title, snippet, path, ID, rank, count, or an error message that implies its existence. Apply the filters inside SQL. This requirement is explicitly tested.

---

## 16. V3 acceptance tests

Tests must exercise behavior through the memory facade and database, not only mock the vector adapter. Use a controlled embedding provider fixture for deterministic tests. Add at least one provider contract test for dimension validation. Keep all applicable V1 and V2 tests unchanged and running.

### 16.1 §28.3 semantic equivalent retrieval

Create a fixture with a valid, accessible, current source-backed memory item or decision. Phrase the stored evidence and query differently but with the same meaning. Example:

- Stored evidence: “The worker lost queued jobs after restart because its lease renewal was not resumed during recovery.”
- Query: “Why were background tasks disappearing when the service rebooted?”

Expected:

1. The source is eligible, indexed, and has a current vector.
2. `search_memory` returns the expected source within the configured compact top-k for the semantic query.
3. The result contains the correct source ID/reference, version, scope, and status.
4. A source that only sounds similar but does not support the answer is not incorrectly labeled as evidence.
5. The test verifies the complete facade path including mandatory filters and compact response shaping.

Use a deterministic fake embedding service for unit/integration tests. Maintain a small model/provider smoke test separately if the environment supports provider calls. Do not make the main automated test suite depend on network access or a paid model endpoint.

### 16.2 Same-scope project boundary with vector retrieval

Create two projects, A and B, and a highly similar source in B that the actor is not allowed to access. Query from A. Verify:

1. No content, title, source path, IDs, counts, or rank data from B appear in the response.
2. The vector SQL includes the project and authorization filters before ranking/limit.
3. The inaccessible vector candidate does not crowd the valid A result out of the top-k.
4. The same result holds when the B vector is more similar than every A vector.
5. Direct details retrieval cannot use a returned or guessed B ID to reveal the source.

This explicitly reruns `MEMORY.md` §28.4 under vector retrieval. No test passes merely because the application filtered the final response after selecting global vector candidates.

### 16.3 Exact identifier regression

Given a known decision, task, artifact, or memory item ID, search by exact identifier. Verify that the correct record is returned deterministically, is not displaced by a more similar vector, follows the status rules, and does not disclose an inaccessible record. Test both found and unknown identifiers.

### 16.4 Keyword regression and hybrid fusion

Use fixtures where:

- The relevant item is strong in keyword and vector search.
- The relevant item is strong only in keyword search because the query includes a rare exact term.
- The relevant item is strong only in vector search because wording differs.
- Two different chunks map to the same source.

Verify RRF ranks expected candidates deterministically, does not treat raw distance as a rank, does not duplicate the same source section, and preserves exact match priority.

### 16.5 Model/dimension validation

Verify:

- Correctly shaped vectors are stored and retrieved.
- Wrong dimension results are rejected before database insertion.
- Wrong model ID results are rejected.
- Null, malformed, or non-finite vector values do not become ready embeddings.
- A vector created with a different active model is not returned.
- Query embeddings and stored vectors use the same configured model ID.

### 16.6 Idempotent embedding generation

Run the indexing/backfill operation twice for an unchanged eligible chunk. Verify no duplicate chunk, no duplicate logical embedding, and no unnecessary second provider call. Simulate retry of the same job and ensure the final row is consistent.

### 16.7 Stale chunk invalidation (§28.9)

1. Index and embed a source version and verify retrieval.
2. Change the canonical source content/version.
3. Verify the old chunk stops being eligible immediately.
4. Before the new embedding finishes, verify the old content is not returned as current; keyword retrieval of the new text may already work.
5. Finish embedding the new version and verify the new text/vector is used.
6. Run the reindex operation again and verify idempotency.
7. Simulate a slow embedding job from the old version finishing after the source has changed. Verify the worker discards it.

### 16.8 Soft deletion and status change safety

Logically delete or deactivate a source using the established V1/V2 behavior. Verify it is immediately absent from exact, keyword, and vector retrieval. Verify a pending or retried embedding job cannot make it visible again. Do not implement the V4 hard-purge workflow as part of this test.

### 16.9 Provider outage fallback

Simulate provider timeout, rate limiting, malformed query vector, and pgvector unavailability. Verify:

- V2 exact and full text behavior is still available.
- A known exact ID still succeeds without needing an embedding.
- The result indicates the actual retrieval mode/fallback in internal metadata.
- Failures have bounded retries and no raw secrets or provider bodies in logs.
- The request does not hang waiting for all corpus embeddings.

### 16.10 Retrieval log privacy and usefulness

Verify the retrieval log records the method, counts/ranks or selected source IDs, timing, model ID, and fallback status as specified. Verify it does not capture raw query text, source bodies, complete prompts, embedding vectors, or credentials by default. Verify the log is not indexed as memory.

### 16.11 Rerun the V2 five real task evaluation

Repeat the exact five real tasks used in V2. Keep query wording, canonical data, model, tools, task instructions, and project state unchanged as far as possible. Compare three modes where practical:

1. Memory retrieval off, as in V2 baseline.
2. V2 exact plus keyword search.
3. V3 hybrid exact plus keyword plus vector search.

For each task, record:

- Whether expected evidence was found.
- Expected source rank in keyword-only and hybrid mode.
- Whether semantic retrieval recovered a previously missed source.
- Whether irrelevant or inaccessible records were returned.
- Number of search/detail calls and source artifacts opened.
- Latency and compact prompt token usage where measurable.
- Final task outcome quality and a human review against canonical evidence.

Five tasks are an engineering gate, not a statistically definitive benchmark. V3 must improve at least one task tied to the documented semantic miss or show a measured, repeatable retrieval improvement on the predeclared semantic query set. It must not regress exact lookup, source freshness, or any security boundary. If the evaluation shows no practical improvement, disable semantic retrieval by default and document the result rather than claiming success.

### 16.12 Full regression suite

Run:

- All V1 schema, restart, checkpoint resume, decision supersession, event, and deletion tests.
- All V2 importer idempotency, cutover/no-dual-write, exact ID, keyword search, project boundary, freshness, progressive disclosure, and source preservation tests.
- All V3 tests in this section.

No V3-only test can replace a V1/V2 regression test.

---

## 17. Implementation sequence and gates

Complete each step, run its tests, and record the result before starting the next step. Do not batch all changes into one large unverified implementation.

### Step 0: Audit and go/no-go decision

Actions:

1. Read `MEMORY.md`, `memv1.md`, and `memv2.md`.
2. Inspect V1/V2 handoffs and run their tests.
3. Inspect actual `memory_chunks` schema, migration mechanism, indexer, `search_memory`, `get_memory_details`, authorization, and observability.
4. Review the five real V2 evaluation tasks and identify the true semantic miss.
5. Write the V3 go/no-go note, including expected sources and why V2 fails.

Gate: if V1/V2 tests fail or no genuine semantic need exists, stop before schema changes.

### Step 1: Pin embedding model and provider policy

Actions:

1. Select and document exact provider/model/version based on operational and privacy requirements.
2. Verify dimension, supported input length, request format, and output semantics.
3. Record similarity metric and normalization behavior.
4. Set timeout, retry, batch, and cost limits.
5. Validate a few representative, approved chunks without writing vectors to production.

Gate: no database vector migration until the model and dimension are confirmed.

### Step 2: Design the minimal schema migration

Actions:

1. Confirm installed PostgreSQL and pgvector compatibility.
2. Create a forward migration using the existing tool.
3. Add only embedding fields, extension enabling, and required constraints/index structures.
4. Preserve V2 full text indexes and all source identity keys.
5. Test on clean and representative V2 database snapshots.

Gate: migration succeeds, constraints behave correctly, and no canonical data is changed.

### Step 3: Add the eligibility and embedding adapter

Actions:

1. Define an explicit allowlist using existing V2 source types and statuses.
2. Define deterministic embedding input from title/section/content.
3. Add dimension/model/input-hash validation.
4. Add provider timeout, bounded retries, and safe error codes.
5. Add deterministic fake provider tests.

Gate: ineligible sources cannot be embedded; repeated identical input reuses its ready vector.

### Step 4: Add version-safe embedding jobs/backfill

Actions:

1. Extend the existing V2 indexer or job runner.
2. Use the idempotency tuple from §8.2.
3. Implement bounded explicit backfill with dry run, resume, and summary counts.
4. Recheck source version before and after provider call.
5. Mark old chunks stale before new vectors are eligible.

Gate: duplicate runs are safe, stale jobs cannot write current vectors, and keyword search remains functional.

### Step 5: Implement filtered vector retrieval

Actions:

1. Add vector candidate retrieval to the existing repository/data-access layer.
2. Apply all §10.1 filters inside SQL.
3. Join canonical source/status data.
4. Enforce active model ID and ready status.
5. Begin with exact vector search; do not add approximate indexing unless a separate measured need is accepted.

Gate: vector query passes the cross-project test where the inaccessible record is more similar than every accessible record.

### Step 6: Integrate RRF into `search_memory`

Actions:

1. Preserve exact identifier priority.
2. Preserve the V2 lexical candidate list.
3. Add vector candidate list and RRF fusion.
4. Deduplicate by canonical source section identity.
5. Preserve compact result shape, source citations, pagination, and access filters.
6. Add honest retrieval mode/fallback metadata.

Gate: API contract tests show no breaking behavior and the hybrid ranking tests pass.

### Step 7: Add retrieval instrumentation and reindex invalidation

Actions:

1. Reuse existing logs/traces if suitable; otherwise add the smallest safe retrieval log.
2. Ensure raw queries and source content are not logged by default.
3. Verify source changes invalidate old chunks and embeddings.
4. Verify pending jobs cannot revive stale/deleted records.

Gate: privacy tests, stale-chunk tests, and provider outage fallback tests pass.

### Step 8: Run V3 acceptance tests and evaluation

Actions:

1. Run semantic equivalent retrieval test.
2. Run vector project boundary test.
3. Run exact lookup and full keyword regressions.
4. Run model/dimension and idempotency tests.
5. Run stale chunk invalidation and failure fallback tests.
6. Rerun the five real tasks using memory off, V2 keyword, and V3 hybrid modes where practical.
7. Review every false positive and false negative against canonical source evidence.

Gate: no open security/privacy failures; no broken predecessor behavior; practical retrieval gain is demonstrated or semantic mode remains disabled by default.

### Step 9: Complete the handoff before any V4 work begins

Document implemented sections, migration identifiers, model choice, embedding policy, backfill counts, tests, evaluation results, known issues, and explicitly deferred V4 items using Appendix E below. Do not start V4 until the V3 handoff accurately reflects the repository and all required gates pass.

---

## 18. Operational controls and rollback

### 18.1 Feature flags

Use the existing configuration mechanism to allow semantic retrieval to be disabled without breaking V2. At minimum, the application must support a safe mode where the existing exact and full text paths still work. Do not implement a large feature flag platform.

When semantic retrieval is disabled:

- Exact lookup remains unchanged.
- V2 full text search remains unchanged.
- The API reports the actual full text/exact retrieval mode.
- No vector provider calls are made for searches.
- Existing embeddings may remain stored but are unused; retention policy still applies.

### 18.2 Rollback

A safe rollback can disable vector retrieval while leaving V2 search intact. If the schema migration must be rolled back, use the repository's migration policy and ensure no canonical data or source artifacts are lost. Avoid dropping vector columns automatically in a deployment rollback if that would destroy useful derived data and is not required for compatibility.

A provider outage should generally trigger retrieval fallback, not an application-wide memory outage. A PostgreSQL failure remains an ordinary memory storage/search failure under the established error contract.

### 18.3 Monitoring and alerts

Use existing metrics and alert patterns. At minimum, the team should be able to detect:

- Embedding jobs accumulating in pending/failed state.
- An unusual rise in provider errors or retry exhaustion.
- Low ready embedding coverage among eligible chunks.
- Frequent vector fallback or pgvector query failure.
- Unexpected latency increase.
- Stale vectors attempting to be served, which should be zero after canonical validation.
- Cross-project filter violations, which should be zero and treated as a serious defect.

Do not add a monitoring stack solely for V3.

### 18.4 Recovery and rebuild

Embeddings are derived, rebuildable data. Given eligible source text, source version hashes, and the pinned model, a controlled reindex should be able to recreate current vectors. A reindex must not regenerate or rewrite canonical project/task/decision state. If the provider or model is unavailable, keyword retrieval remains the fallback and the system must not pretend the semantic index is complete.

---

## 19. V3 definition of done

V3 is done only when every requirement below is true.

### Predecessor integrity

- [ ] V1 and V2 handoffs exist and have been verified against the repository.
- [ ] All applicable V1 and V2 tests pass.
- [ ] A real V2 semantic miss was documented before implementation.
- [ ] No second writable source of truth was introduced.
- [ ] Existing memory facade and job/indexing patterns were reused.

### Model and data

- [ ] The embedding provider, model/version, dimension, metric, and data handling policy are documented.
- [ ] Query and chunk vectors use the same pinned model.
- [ ] The migration uses the verified vector dimension and the existing migration framework.
- [ ] Only allowlisted source chunks are embedded.
- [ ] No secrets or disallowed source classes are sent to the provider.
- [ ] Embedding input and source versions are traceable.
- [ ] Embedding generation is idempotent and safe under retries.

### Retrieval correctness

- [ ] `search_memory` is the one agent-facing search facade.
- [ ] Exact ID/path retrieval retains deterministic priority.
- [ ] Vector retrieval uses the same mandatory filters as V2 inside SQL.
- [ ] Hybrid retrieval uses RRF, with stable ties and source deduplication.
- [ ] Compact results preserve source references and canonical status.
- [ ] Full details remain opt-in through `get_memory_details`.
- [ ] Query/provider/vector failures fall back safely to V2 behavior.

### Freshness and privacy

- [ ] Source changes invalidate old chunks/embeddings immediately for search.
- [ ] Slow or retried embedding jobs cannot attach vectors to a stale source version.
- [ ] Deleted or inaccessible records cannot appear in vector results.
- [ ] Retrieval logs avoid raw query and source content by default.
- [ ] Prompt injection protections and source labeling remain intact.

### Tests and evidence

- [ ] §28.3 semantic equivalent retrieval passes.
- [ ] §28.4 project boundary passes under vector retrieval, including the “more similar but inaccessible” fixture.
- [ ] Exact ID and keyword regressions pass.
- [ ] Model/dimension, idempotency, freshness, and fallback tests pass.
- [ ] All V1/V2 regression tests pass.
- [ ] The five real task evaluation has been repeated and reviewed.
- [ ] V3 demonstrates practical improvement, or semantic mode is left disabled with the failed rationale recorded.
- [ ] Appendix E handoff is complete.

---

## 20. Explicitly deferred to V4

V3 must leave all of the following unimplemented:

- Automatic task-end lesson extraction.
- Lesson lifecycle and validation workflow.
- Cross-project retrieval/promotion of reusable lessons.
- Semantic deduplication or automatic memory merging.
- Automated consolidation, compaction, and memory “dreaming.”
- Hard purge workflow and verification beyond existing V1/V2 deletion safety.
- Automated memory quality optimization or learned retrieval policies.
- Rerankers, query rewriting, reinforcement learning, and retrieval training.

V3 only makes it easier to find existing, authorized, source-backed information when the wording differs. It does not make the agents learn from experience or grant them broader access.

---

## 21. Troubleshooting decision table

| Symptom | Diagnose first | V3 response | Must not do |
|---|---|---|---|
| Expected memory absent from both keyword and vector results | Was the source indexed and eligible? Did it have a current chunk? | Fix V2 indexing/source mapping first | Increase vector top-k to mask missing data |
| Semantic query finds nothing but paraphrase fixture works | Is query input valid? Is the query embedding using the active model? | Inspect provider logs and candidate counts | Add an LLM query rewriting agent immediately |
| Very similar wrong record ranks first | Is the stored source actually relevant and eligible? Is the chunk too broad? | Review chunk boundaries and evaluation; preserve source evidence | Treat a distance score as truth or add a broad global threshold without evaluation |
| Old content appears after update | Is stale invalidation atomic/early enough? Are joins using canonical status? | Fix invalidation before any ranking change | Hide stale content only in final response |
| Private project's source appears | Are project/access filters inside vector SQL? | Treat as a critical security defect; block release | Filter after fetching global nearest neighbors |
| Exact ID returns a different record | Is direct lookup first and deterministic? | Fix V2 exact path/fusion priority | Let vector score override the ID |
| Provider failures break all search | Is fallback wired through the facade? | Restore keyword fallback | Make every task wait for embeddings |
| Embeddings are repeatedly regenerated | Are input hash/model/source version stable? | Fix idempotency key and job state | Add a separate scheduler without investigating current jobs |
| Vector search is too slow | Is exact search measured on the eligible set? | Profile SQL and filtered row counts; make an evidence-based optimization proposal | Add approximate indexes before a baseline |
| Results are not better than V2 | Are there remaining real semantic misses? | Disable by default or defer V3 if no benefit | Claim success solely because vectors exist |

---

## Appendix A. Developer checklist

Before merging any V3 pull request, confirm:

- [ ] `MEMORY.md`, `memv1.md`, and `memv2.md` were reviewed.
- [ ] V1/V2 test evidence was checked in the actual repository.
- [ ] A real semantic gap justified V3.
- [ ] The active embedding model and dimension are pinned and documented.
- [ ] The extension/column migration is forward-only and uses the current migration tooling.
- [ ] Eligibility is allowlist-based; no repository-wide embedding was enabled accidentally.
- [ ] The embedding input hash and source-version checks are deterministic.
- [ ] Query and stored vectors use the same model and metric.
- [ ] Vector SQL applies every V2 authorization/status/scope/freshness filter before candidate return.
- [ ] Exact ID lookup retains highest priority.
- [ ] RRF operates on ranks, not raw scores.
- [ ] Results are deduplicated and carry valid source refs.
- [ ] Full details are still returned only through `get_memory_details`.
- [ ] Stale vectors cannot be returned or revived by slow jobs.
- [ ] Provider outage gracefully falls back to V2.
- [ ] Retrieval logging is bounded and does not store raw query/source content by default.
- [ ] Semantic, boundary, stale-source, idempotency, provider-failure, and regression tests pass.
- [ ] The real task evaluation demonstrates useful change.
- [ ] The Appendix E handoff is completed.

---

## Appendix E. V3 implementation handoff

Complete this template with repository evidence before declaring V3 done or starting V4. Do not fill unknown values by assumption. Use `Not implemented`, `Not applicable`, or `Blocked` where honest.

# MEMV3 implementation handoff

## Implemented sections

- Sections implemented: 
- Sections not implemented: 
- Reason for each omission: 
- Actual files/modules changed: 

## Predecessor verification

- V1 handoff location: 
- V1 test command and result: 
- V2 handoff location: 
- V2 test command and result: 
- Actual canonical source-of-truth matrix verified: 
- JSONL cutover/no-dual-write status verified: 
- V2 five-task evaluation location: 

## V3 go/no-go evidence

- Real semantic miss query: 
- Expected source ID/reference: 
- V2 result/rank: 
- Miss category and why V2 fixes were insufficient: 
- Decision to build V3 and reviewer: 

## Existing code reused

- Search facade: 
- V2 chunk/indexer: 
- PostgreSQL migration framework: 
- Authorization and scope checks: 
- Worker/job runner: 
- Logging/metrics/tracing: 
- Other reused modules: 

## Model and provider decision

- Provider/runtime: 
- Exact model ID/version: 
- Vector dimension: 
- Similarity metric: 
- Normalization policy: 
- Maximum input length and chunk policy: 
- External data handling approval and excluded source classes: 
- Timeout/retry/batch/cost policy: 
- Model upgrade/reindex procedure: 

## Database and indexing

- Migration identifier: 
- pgvector version/extension validation: 
- `memory_chunks` embedding fields added/reused: 
- Vector index type, or reason exact search is used: 
- Eligibility allowlist: 
- Initial eligible chunk count: 
- Embedded successfully: 
- Already ready/skipped: 
- Failed and reason categories: 
- Stale during processing: 
- Backfill command and dry-run result: 
- Rebuild procedure: 

## Retrieval behavior

- `search_memory` implementation location: 
- Exact lookup precedence verified: 
- Keyword candidate count configuration: 
- Vector candidate count configuration: 
- RRF constant and rationale: 
- Source deduplication key: 
- Required authorization/status/scope/source-version filters verified in SQL: 
- Fallback behavior: 
- `retrieval_mode` values: 
- Compact response/provenance compatibility: 

## Source freshness and failure behavior

- Source update invalidation behavior: 
- Slow-job/version-mismatch behavior: 
- Deletion/status exclusion behavior: 
- Provider outage behavior: 
- pgvector/database failure behavior: 
- Idempotent retry behavior: 

## Retrieval log and privacy

- Existing logging reused or new mechanism: 
- Fields recorded: 
- Confirmation raw query/source bodies are not stored by default: 
- Retention/access policy: 

## Tests

- §28.3 semantic equivalent retrieval: pass/fail and test name
- §28.4 vector project boundary: pass/fail and test name
- Exact ID regression: pass/fail
- Keyword regression: pass/fail
- RRF/fusion/deduplication: pass/fail
- Model/dimension validation: pass/fail
- Embedding idempotency: pass/fail
- §28.9 stale chunk invalidation: pass/fail
- Deletion/status safety: pass/fail
- Provider outage fallback: pass/fail
- Retrieval log privacy: pass/fail
- Full V1 regression suite: pass/fail
- Full V2 regression suite: pass/fail
- Full V3 test command and result: 

## Evaluation findings

- V2 baseline task results: 
- V3 hybrid results: 
- Previously missed semantic cases recovered: 
- Exact/keyword behavior regressions: 
- Inaccessible or irrelevant results observed: 
- Task outcome change: 
- Latency/token/cost observations: 
- Remaining failure modes: 
- Is semantic retrieval enabled by default? Why? 

## Deferred work, explicitly not implemented

Confirm these remain deferred to V4:

- [ ] Lesson extraction/validation lifecycle
- [ ] Cross-project lessons
- [ ] Semantic deduplication and consolidation
- [ ] Background memory compaction/dreaming
- [ ] Hard purge workflow beyond existing safety
- [ ] Learned ranking, reranker, query rewriting, or RL
- [ ] Any new graph/vector database or memory microservice

## Known gaps and blockers

- Gap/blocker: 
- Impact: 
- Owner or follow-up: 
- Whether it prevents V4 from starting: 

## Final result

- V3 status: `PASS` / `PASS WITH DOCUMENTED LIMITATIONS` / `BLOCKED` / `DEFERRED`
- Reviewer: 
- Review date: 
- Commit/PR reference: 
- Confirmation that no V4 feature was implemented: 
- Confirmation that canonical write ownership is unchanged: 

---

## Final V3 operating rule

**Only add semantic retrieval when real V2 failures prove it is needed. Keep PostgreSQL and the existing memory facade authoritative, embed only selected current source-backed chunks with one pinned model, filter access inside SQL, combine vector and lexical ranks with RRF, invalidate stale vectors immediately, preserve V2 fallback, and prove improvement before moving on.**
