# memv2.md

## V2 implementation specification: searchable memory and controlled JSONL migration

**Parent specification:** `MEMORY.md`  
**Required predecessor:** completed, tested, and handed off `memv1.md`  
**Purpose:** extend the working V1 continuity system with reliable legacy JSONL migration and bounded keyword retrieval.  
**Version boundary:** V2 implements Phases 3 and 5 of `MEMORY.md`. It does not implement Phase 6, 7, or 8.

## 0. The outcome V2 must deliver

At the end of V2, an authorized agent must be able to search for an exact identifier or a phrase, receive a compact list of relevant records with provenance, and request the full detail of selected records. The same agent must be able to resume work using V1 task checkpoints and current decisions. Historical JSONL records selected for migration must be imported idempotently, verified, and cut over one record type at a time without leaving two writable sources of truth.

V2 is complete only when all of the following are true:

1. V1 still passes its complete test suite without regressions.
2. The repository audit has identified the actual JSONL readers, writers, schemas, stable identifiers, and file ownership.
3. Each migrated JSONL record type has one documented canonical owner after cutover.
4. Re-running an import does not create duplicate target records or duplicate events.
5. `memory_items` and `memory_chunks` support PostgreSQL full text search. There are no embeddings or vector columns in V2.
6. Exact ID lookup and keyword retrieval enforce project, scope, status, and authorization filters before returning results.
7. Search results are compact and source backed. Full details are fetched only when requested.
8. The exact identifier test, project boundary test, and five real task memory on versus memory off evaluation pass.
9. The Appendix E handoff template at the end of this file is complete and accurate.

## 1. Binding implementation rules

1. Read `MEMORY.md` and `memv1.md` before changing code. Treat them as the architecture and predecessor contract.
2. Inspect the actual repository before deciding paths, framework conventions, database libraries, migration tooling, or test commands. Reuse the existing code and patterns where they are sound.
3. V1 must already be implemented and pass its tests. If it has not passed, stop and fix V1. Do not build V2 on a failing foundation.
4. Keep PostgreSQL as the only writable canonical store for each record type after that type is cut over.
5. Do not create a second writable source of truth. In particular, do not write a record to PostgreSQL and then independently append a competing version to JSONL.
6. Keep JSONL, Markdown, meeting transcripts, and Git history intact. Importing data does not authorize rewriting or deleting the source files.
7. Migrate one record type at a time. Each type has its own inventory, import, verification, cutover, rollback plan, and handoff note.
8. Imports must be explicit commands or controlled jobs. No hidden import at application startup, agent startup, or first database access.
9. Import must be idempotent and resumable after interruption. It must report inserted, already imported, updated by an explicitly approved reconciliation rule, skipped, invalid, and failed records separately.
10. Exact identifiers are resolved deterministically. Do not make an LLM decide whether an exact ID exists or which record an ID means.
11. Apply authorization, project, scope, and status filters in SQL before returning candidates. Filtering after results have entered the prompt is too late.
12. `memory_chunks` is a rebuildable index. It is not the canonical copy of a decision, task, event, or memory item.
13. `memory_items` stores bounded, explicit memory records. It is not a general dumping ground for every tool call, transcript line, or arbitrary file.
14. Use PostgreSQL full text search only. Do not add pgvector, embeddings, semantic retrieval, reranking models, or vector infrastructure in V2.
15. Do not build lesson extraction, lesson validation, cross project learning, automatic consolidation, memory dreaming, or autonomous memory rewriting in V2.
16. Do not build anything listed under Section 26 of `MEMORY.md` merely because it might be convenient.
17. Preserve the V1 APIs and their semantics. Add the two V2 APIs, `search_memory` and `get_memory_details`, through the existing memory facade rather than bypassing it from agents.
18. Any ambiguity about ownership, data meaning, or safe cutover is a blocker to that record type's cutover, not permission to guess.

## 2. Scope and explicit exclusions

### 2.1 Included in V2

1. Phase 3: JSONL inventory, schema mapping, idempotent import, reconciliation, verification, controlled cutover, and one canonical writer per record type.
2. Phase 5: direct ID lookup, keyword search with PostgreSQL full text search, mandatory filters, compact result envelopes, and full detail retrieval on request.
3. New `memory_items` table for explicitly represented memory records.
4. New `memory_chunks` table with a PostgreSQL `tsvector` search column and source/version metadata.
5. Indexing of selected eligible source content for keyword search.
6. Source references from imported records and search results back to original files or artifacts.
7. Tests for exact identifier retrieval, project isolation, importer idempotency, source preservation, progressive disclosure, and five real tasks with memory on versus off.

### 2.2 Explicitly not included in V2

1. pgvector, any vector column, embeddings, embedding generation, vector indexes, or semantic similarity search.
2. Any embedding model selection or pinning. That is V3 work.
3. Reciprocal Rank Fusion or any fusion between keyword and vector result lists. V2 has no vector result list.
4. Automated extraction of lessons from completed tasks.
5. Lesson statuses `proposed`, `validated`, and `active` as a learning pipeline.
6. Cross project retrieval or promotion of lessons across projects.
7. Automated duplicate merging or semantic contradiction resolution.
8. Background consolidation, memory compaction, or memory quality optimization.
9. Hard purge workflow for derived vector indexes. V2 must still honor ordinary record deletion and ensure deleted or inaccessible records are not returned by search.
10. A new graph database, separate vector database, memory microservice, custom model, or independent queue service.
11. Replacing Graphify. Graphify continues to serve code relationship analysis.
12. Rewriting existing Markdown, JSONL, or transcript content just to make it uniform.

If a proposed change belongs to an excluded item, record it as deferred work and do not implement it in V2.

## 3. Preconditions and V1 gate

Before changing code, locate the completed V1 handoff and verify its claims against the repository.

### 3.1 Required V1 evidence

The V1 handoff must identify:

1. The canonical project, task, decision, and event tables.
2. The actual migration mechanism and how migrations are run in development and tests.
3. The existing memory facade and the three V1 API implementations.
4. How task checkpoint versions and optimistic concurrency work.
5. How decision supersession is performed atomically.
6. The JSONL files deliberately left unmigrated, their known writers, and the historical gaps.
7. The complete passing V1 test command and results.

### 3.2 If the V1 evidence is missing

Perform a repository audit and report the missing evidence. Do not infer that V1 works just because schema files exist. Run the tests. If a V1 invariant fails, fix V1 first and record that work separately from V2. Do not conceal V1 fixes inside the V2 feature branch.

### 3.3 Repository audit for V2

Inspect and record:

1. All JSONL files and their actual record types.
2. Every reader and writer of each file type, including agents, orchestration code, scripts, tests, and CLI commands.
3. Whether each JSONL file represents current state, append only history, an export, or source evidence.
4. Existing IDs, timestamp fields, actor fields, schema versions, and reference relationships.
5. Whether the V1 PostgreSQL records overlap with the legacy records.
6. Existing search functions, if any, and whether they can be reused without violating the V2 contract.
7. Existing permissions and project access checks.
8. Current dependency and migration conventions.

Produce a source of truth matrix before writing an importer. Use the template below.

| Record type | Existing source path | Existing readers | Existing writers | Stable source identity | Target table | Current canonical owner | Planned cutover | Rollback procedure |
|---|---|---|---|---|---|---|---|---|
| Fill from repository audit | | | | | | | | |

Do not invent a universal schema based on filenames. Inspect real records and identify variants.

## 4. V2 architecture

V2 extends the V1 architecture. It does not replace it.

### 4.1 Components

1. **Existing agent and orchestration layer:** calls the memory facade at task start and when it needs to search for prior evidence.
2. **Existing memory facade:** keeps V1 continuity APIs and exposes V2 search APIs.
3. **PostgreSQL canonical tables:** `projects`, `tasks`, `decisions`, and `memory_events` from V1, plus `memory_items` and `memory_chunks` from V2.
4. **Importer:** an explicit, bounded tool for one selected JSONL record type per run. It validates, maps, imports, and reports results.
5. **Source artifact layer:** existing JSONL, Markdown, transcripts, Git commits, and code remain preserved as evidence and source material.
6. **PostgreSQL full text index:** indexes only approved content selected for V2 keyword retrieval.
7. **Existing authorization and project boundary checks:** are applied before search results can be returned.

Do not add a separate search service. PostgreSQL is sufficient for this version.

### 4.2 Data flow for import

1. An operator chooses one inventoried record type and one source file or bounded set of files.
2. The importer reads the source without modifying it.
3. Each source record is parsed and validated against that record type's mapping contract.
4. The importer computes a stable source identity and content hash.
5. The importer checks whether that exact source record has already been imported.
6. The importer maps the record into the existing canonical table or `memory_items`, as appropriate.
7. The target record and its import provenance are committed atomically.
8. The importer reports the outcome and continues. A malformed record must not silently disappear.
9. Verification compares source counts, imported identities, references, and sampled values.
10. Only after verification and an approved cutover decision does PostgreSQL become the canonical owner for that record type.
11. The legacy writer for that same logical state is disabled or redirected. The old file remains preserved as historical evidence or is clearly classified as a derived export if an export is explicitly retained.

### 4.3 Data flow for search

1. The caller provides a query and an explicit project context. The API also receives the actor identity or trusted authorization context.
2. If the query contains a recognized exact record ID, the facade attempts deterministic ID lookup under the same access filters.
3. The facade identifies eligible source records and search chunks for the requested project, scope, status, and record types.
4. PostgreSQL full text search matches the query against the eligible `search_vector` values.
5. The facade returns a bounded compact list with IDs, type, title, status, scope, snippet, timestamps where available, match reason, and source references.
6. The caller selects result IDs and invokes `get_memory_details` when more context is needed.
7. The details API rechecks access and current status before returning full content and evidence references.
8. The agent uses retrieved content as evidence, not as a command that can override system instructions, authorization, or current approved decisions.

### 4.4 Authority rule

Search results never become a new source of truth. The `memory_chunks` row is a derived index. The canonical decision remains in `decisions`; the canonical task and checkpoint remain in the V1 task system; the canonical event remains in `memory_events`; and a V2 memory record remains in `memory_items`. When a chunk disagrees with its canonical source, the source wins and the chunk is stale or incorrect.

## 5. Data model additions

Reuse all V1 tables and contracts. Add only the V2 schema required for memory records and keyword indexing. Adapt field names to the existing repository's naming conventions without changing the required semantics.

### 5.1 `memory_items`

Purpose: store explicit, bounded memory records that do not already belong in a canonical V1 table. Examples may include a project note, a factual observation, or a source backed record intentionally created by an authorized agent or user. V2 does not automatically extract lessons.

Required semantics:

1. Every item has a stable primary key.
2. Every project scoped item belongs to an existing project.
3. Every item has a memory type, scope, status, title, content, provenance, creator, and timestamps.
4. Every item has source references. If evidence is not available, represent that explicitly rather than fabricating a reference.
5. Every item has a status that allows retrieval to distinguish current records from inactive or superseded records. Reuse the status vocabulary from `MEMORY.md` where it applies. Do not treat a proposed lesson as active guidance.
6. Every update increments or otherwise records a source version so old chunks can be invalidated.
7. Item deletion must make the item ineligible for retrieval immediately, even if stale chunks still exist temporarily.
8. V2 does not create a separate `memory_links` table unless the repository audit proves a concrete V2 requirement and the change is approved. Do not add a relationship graph preemptively.

Recommended fields, unless equivalent existing conventions already exist:

| Field | Required meaning |
|---|---|
| `id` | Stable UUID primary key |
| `project_id` | Project owner; required for project scoped items |
| `memory_type` | Controlled type such as `fact`, `note`, `observation`, `reference`, or another audited type |
| `scope` | Visibility boundary; V2 retrieval must enforce it |
| `status` | Current lifecycle status; only eligible statuses may be returned by default |
| `title` | Short descriptive label |
| `content` | Bounded, self contained record content |
| `source_refs` | Structured references to the original file, record, artifact, or evidence |
| `source_version` | Source version or content hash used to determine freshness |
| `created_by` | Agent or human responsible for creation |
| `created_at` | Original creation time when known, otherwise import time plus explicit timestamp provenance |
| `updated_at` | Last canonical update time |
| `metadata` | Small structured extension field, not a substitute for typed fields |
| `deleted_at` | Optional deletion marker if the V1 conventions use soft deletion |

Use constraints for controlled status and scope values where the repository supports them. Do not create a schema that makes a record globally visible merely because `project_id` is null.

### 5.2 `memory_chunks`

Purpose: provide a rebuildable keyword index over selected canonical records or source sections. In V2 this table has full text search only.

Required fields:

| Field | Required meaning |
|---|---|
| `id` | Stable chunk UUID |
| `project_id` | Project boundary for authorization filtering |
| `source_type` | Type of canonical source, for example `memory_item`, `decision`, `memory_event`, `task_checkpoint`, or an approved artifact type |
| `source_id` | Stable ID of the canonical source record |
| `source_ref` | Path or URI to the original artifact or source record |
| `source_version` | Version or content hash of the source used to make this chunk |
| `chunk_index` | Stable position of this chunk within that source version |
| `title` | Short label inherited from the source or section |
| `content` | Searchable chunk text, bounded to a sensible size |
| `content_hash` | Hash of normalized chunk content for idempotent indexing |
| `search_vector` | PostgreSQL `tsvector` derived from eligible searchable fields |
| `visibility_scope` | Access scope inherited from the canonical source |
| `memory_status` | Status snapshot used as a convenience, never as sole authority |
| `created_at` | Chunk creation time |
| `indexed_at` | Last successful indexing time |
| `is_stale` | Whether this chunk no longer matches the current source version |

Do not add `embedding`, `embedding_model`, vector indexes, or vector extension dependencies in V2.

Recommended integrity rules:

1. A source version and chunk index must not create duplicate chunks when reindexed.
2. A chunk points to exactly one canonical source identity and one source version.
3. Search must join or validate against the canonical source before returning a result.
4. Chunks marked stale are excluded from normal retrieval.
5. A source update invalidates old chunks before new chunks are considered current.
6. Rebuilding chunks must be deterministic for the same source version and chunking configuration.

### 5.3 Search vector generation

Use PostgreSQL text search functions and a GIN index. Choose the text search configuration deliberately based on the actual language of project records. For primarily English technical records, `english` is a reasonable initial configuration, but test it against identifiers, file paths, code symbols, error messages, and acronyms before finalizing it.

The indexer should:

1. Normalize whitespace without altering the canonical source.
2. Preserve identifiers, filenames, symbols, error codes, and exact quoted terms in searchable text.
3. Generate `search_vector` from a documented combination of title and content. Use weighting if it improves measured results and document the weighting.
4. Use a GIN index for `search_vector`.
5. Include a separate deterministic exact identifier path. Full text tokenization is not a substitute for exact ID lookup.
6. Rebuild the search vector when indexed text changes.

Do not build a custom tokenizer in V2 unless an actual evaluation shows PostgreSQL's standard configuration cannot handle a critical query class. If identifiers containing punctuation are not found by full text search, the exact identifier path must still work.

### 5.4 Schema migration

Create a new forward migration using the repository's existing migration tool. Do not edit an already applied migration to add V2 columns. Do not create a parallel migration system.

The migration must:

1. Add `memory_items` and `memory_chunks` with required constraints and indexes.
2. Add only the smallest provenance fields required by the importer if those fields do not already exist.
3. Avoid adding a vector extension or embedding column.
4. Be safe to run in a clean test database and on the V1 schema.
5. Have a documented rollback procedure that does not delete imported source files or canonical records.
6. Include migration tests and a schema inspection assertion that V2 contains no embedding column or vector index.

## 6. Import contracts and idempotency

### 6.1 One record type per import

The importer must accept a specific record type and an explicit source path or bounded set of paths. It must refuse to import an unknown record type. It must not silently infer that every line in a file has the same shape.

The operator must be able to run a dry run that parses and validates records, reports proposed mappings and conflicts, and makes no canonical data changes. The actual import is a separate explicit action.

### 6.2 Stable source identity

Use the following identity precedence:

1. A stable source record ID, namespaced by source system and record type.
2. If no stable ID exists, a deterministic identity derived from the source path and a documented stable key in the record.
3. If no stable key exists, a deterministic fingerprint based on normalized record content and a stable source location such as file path plus line number. Record that this identity is location dependent and may change if the file is reordered.

Do not use the current time or a random UUID as the import idempotency key. Preserve the original source ID and timestamp as provenance even if the database primary key must be mapped to a UUID.

### 6.3 Idempotency contract

For each source record, calculate:

* `source_identity`: stable identity according to Section 6.2.
* `source_hash`: hash of the normalized source record content.
* `mapping_version`: version of the mapping code/schema.
* `target_identity`: canonical database record ID.

A repeated import of the same source identity and source hash must produce no duplicate target row, no duplicate event, and no duplicate chunk. It must be reported as already imported or unchanged.

If the same source identity has a different source hash, do not overwrite the canonical target automatically. The importer must classify the change and apply only a documented, approved reconciliation rule. If the source type has already been cut over to PostgreSQL, a changed legacy file is not automatically allowed to overwrite the newer canonical record. Report a conflict for human review.

### 6.4 Import provenance

For every imported record, retain enough provenance to answer:

1. Which file and record produced this row?
2. Which original ID and timestamp did it have?
3. Which mapping version imported it?
4. What was the source content hash?
5. When did import occur?
6. Was the record inserted, skipped, reconciled, or rejected?
7. What canonical target ID was assigned?

Prefer extending the existing event or provenance conventions with a stable import identity and uniqueness constraint. Add a dedicated import ledger only if the existing V1 event schema cannot guarantee atomic, unique import tracking. If a ledger is required, keep it minimal, document why it is necessary, and ensure the target write and import marker commit in the same transaction.

### 6.5 Transaction boundary

The target record and the durable idempotency marker must be committed atomically. If the process crashes before commit, neither should remain. If it crashes after commit, the next run should recognize the imported record and not duplicate it.

Use bounded transactions. Do not hold one transaction open for an entire large file. Process records or small batches with a clear retry boundary, and emit a final report even when some records fail.

### 6.6 Invalid records and partial success

Do not silently discard malformed JSON, invalid timestamps, missing IDs, unsupported status values, or broken references. For each failure, report file path, line or record identity, reason, and whether retry or manual repair is needed. Do not print sensitive record content in logs.

The importer must support partial success and safe resumption. A failed record must not prevent already committed records from being recognized on the next run.

### 6.7 Mapping and conflict rules

For each record type, write a mapping document that defines:

1. Source schema and known schema variants.
2. Required and optional fields.
3. Timestamp parsing and timezone rules.
4. Identity mapping.
5. Status mapping.
6. Actor mapping.
7. Source reference mapping.
8. Target table and target fields.
9. Duplicate detection rule.
10. Conflict handling rule.
11. Validation rule and sample expected output.

Never resolve a conflict by silently selecting the most recently modified file. Currentness follows the canonical ownership decision and the record's explicit status/version semantics, not filesystem modification time alone.

## 7. Controlled migration and cutover

### 7.1 Migration states

Each record type moves through these operational states:

1. `audited`: source and writers are understood.
2. `mapping_defined`: source to target mapping and conflict rules are documented.
3. `dry_run_passed`: dry run validation completed with reviewed output.
4. `imported`: records were imported, with a report of failures and skipped rows.
5. `verified`: counts, identities, references, and sampled values passed verification.
6. `cutover_approved`: owner approved PostgreSQL as canonical for this type.
7. `cut_over`: all new writes use the PostgreSQL facade and legacy canonical writer is disabled or redirected.
8. `archived_or_exported`: legacy file has an explicit role and remains preserved.

Do not skip `verified`. Do not call a type cut over just because the importer exited successfully.

### 7.2 Verification before cutover

For each record type:

1. Compare total source records to the sum of imported, already imported, explicitly skipped, invalid, and failed records.
2. Verify unique source identities and target identities.
3. Check all expected foreign references and source references.
4. Compare counts by status and relevant time range.
5. Sample records from the beginning, middle, and end of the source and compare source fields to target fields.
6. Verify that current decisions remain consistent with V1 decision status rules.
7. Verify that task checkpoints and project ownership were not changed by unrelated imports.
8. Run exact ID reads through the memory facade.
9. Confirm there is no remaining active writer that can independently mutate the same logical state in JSONL.
10. Record the verification output and the person or process that approved cutover.

Counts alone are insufficient. A million duplicated rows can have matching counts and still be wrong.

### 7.3 Cutover and no dual writes

At cutover:

1. The PostgreSQL-backed facade becomes the only canonical writer for that record type.
2. Disable or redirect the old JSONL writer in the same deployment or controlled release that changes ownership.
3. Do not write to both PostgreSQL and JSONL as independent state stores.
4. If a compatibility export is required, generate it one way from PostgreSQL and mark it as a derived export. No runtime logic may read the export as an alternative canonical truth after cutover.
5. Keep the original JSONL as immutable historical evidence, or archive it without deleting it.
6. Record the cutover commit, time, record type, imported range, verification evidence, and rollback procedure.

### 7.4 Rollback

Rollback must not restore two writers. If a cutover causes a production issue, choose one canonical owner for the rollback window. If ownership must return to JSONL, stop PostgreSQL writes first, export or reconcile the delta in a controlled process, verify it, then re-enable the legacy writer. Never allow both to accept independent writes while the rollback is in progress.

### 7.5 Recommended order

Choose order based on the audit, not a fixed assumption. Prefer the smallest record type with stable IDs, low ambiguity, and clear historical value. Do not import all meeting transcripts or every line of all JSONL files merely because they exist. Preserve large transcripts as files and index only selected, meaningful sections in `memory_chunks`.

## 8. Indexing source content

### 8.1 Eligible sources

Only index content that has a clear purpose in task execution or retrieval, such as:

1. Explicit `memory_items` records.
2. Current and historical decisions when the caller's status filter permits them.
3. Selected structured events that provide useful evidence.
4. Task checkpoints where search is useful and the caller is authorized.
5. Selected sections of Markdown, meeting transcripts, or other artifacts when their source references and access boundaries are known.

Do not index every tool call, every log line, every code file, or every transcript line by default. Code relationship questions continue to use the codebase and Graphify.

### 8.2 Chunking rules for V2

Chunking is for keyword retrieval, not semantic context optimization. Use deterministic boundaries such as a complete memory item, a decision record, a Markdown heading section, or a transcript segment with known offsets. Avoid arbitrary character slicing when a meaningful section boundary exists.

Every chunk must preserve a source reference to the original artifact and, where applicable, the original record ID and section or line range. Do not change the canonical source when creating chunks.

Use a documented maximum chunk size appropriate to the existing model context and search result size. Keep chunks small enough that a compact snippet can be returned cheaply, but large enough to retain relevant identifiers and the surrounding statement. Set the value through configuration or a constant with tests. Do not implement elaborate adaptive chunking in V2.

### 8.3 Index lifecycle

When a canonical source is created or updated:

1. Determine whether the source type is eligible for V2 keyword search.
2. Read the canonical source and compute its current source version or content hash.
3. Mark existing chunks for older source versions stale before making the new version eligible.
4. Generate deterministic chunks for the new source version.
5. Upsert chunks using the source identity, source version, and chunk index uniqueness rule.
6. Generate `search_vector` values and commit the new chunks.
7. Confirm current chunks are searchable and old chunks are excluded.

V2 may perform indexing synchronously for small, explicit writes if it is reliable and fast. Reuse an existing background job mechanism if the repository already has one and asynchronous indexing is needed. Do not add a separate queue service. If indexing fails, the canonical source remains valid; the API must report or log that its index is stale rather than pretending it was indexed.

### 8.4 Rebuildability

Chunks must be rebuildable from canonical source content and the documented chunking configuration. A rebuild must not create duplicates. A rebuild must not resurrect deleted content or inaccessible sources. Keep the source version and content hash so stale index records can be identified and removed from eligibility.

## 9. Retrieval contract

### 9.1 Required inputs

`search_memory` must receive:

* `query`: nonempty text.
* `project_id`: explicit project context unless the existing authorization model provides a safe, explicit global context.
* `actor` or trusted authorization context.
* `scope`: allowed scope or scopes.
* `filters`: optional record types, statuses, date bounds, and other supported typed filters.
* `limit`: bounded result count.

Do not infer project access from the query text. Do not allow a caller to omit authorization and receive all projects by default.

### 9.2 Mandatory filtering before ranking

Apply these filters in SQL before candidate rows are returned:

1. Actor authorization for the requested project.
2. Project ID, including validation that a source belongs to that project.
3. Requested visibility scope and any higher level access boundary.
4. Canonical source status, with current eligible statuses as the default.
5. Chunk freshness, excluding stale chunks.
6. Source visibility or deletion state.
7. Requested record types and date bounds when supplied.

Do not rely solely on copied `memory_status` or `visibility_scope` values in a chunk. Join to or validate against the canonical source so a status change or deletion cannot leave a record searchable as current.

### 9.3 Exact identifier lookup

Before full text search, detect whether the query contains an exact ID in a supported format. Resolve it through direct parameterized SQL against known canonical IDs and source ID mappings. Keep this logic deterministic and bounded.

If exact ID lookup finds an accessible record, include it at the top of the results and label the match reason `exact_id`. Still enforce all access and status rules. If the ID exists but is inaccessible, do not disclose whether it exists. If it is not found, continue with keyword search when appropriate.

Do not interpret any arbitrary long number or token as a database ID unless it matches the documented ID format or an explicit source ID field.

### 9.4 Keyword search

Use PostgreSQL full text search against `memory_chunks.search_vector` with a GIN index. Query parsing must use parameterized database operations. Never concatenate user input into raw SQL.

The keyword retrieval path should:

1. Normalize the query without destroying meaningful punctuation or identifiers.
2. Run exact ID lookup first when applicable.
3. Build a PostgreSQL text search query using the selected text search configuration.
4. Apply mandatory filters before ranking and limiting.
5. Rank matching chunks using PostgreSQL's supported text ranking function.
6. Collapse multiple chunks from the same canonical source where appropriate, keeping the best matching chunk as the compact snippet.
7. Return a bounded list and a stable pagination mechanism if pagination is required.

If PostgreSQL full text search does not handle an exact identifier reliably, use the direct identifier path or a narrowly scoped exact field match. Do not pretend that full text search alone covers every identifier format.

### 9.5 Default result limit and context budget

Use a conservative default of 5 compact results and enforce a configured hard maximum. The exact maximum should follow existing repository conventions; do not let a caller request an unbounded result set. The API should return `has_more` or a stable cursor if additional results are available.

Search returns snippets, not full transcripts or whole documents. If the query needs detailed evidence, the caller explicitly requests the details for selected result IDs.

### 9.6 Compact result envelope

Return a stable machine readable response. Adapt property naming to the codebase but preserve the following semantics:

```json
{
  "query": "Where is the current checkpoint for task TSK-123?",
  "project_id": "project-uuid",
  "results": [
    {
      "id": "canonical-record-uuid",
      "source_type": "task_checkpoint",
      "source_id": "task-uuid",
      "title": "Task checkpoint",
      "snippet": "Implementation is complete; integration tests remain.",
      "status": "in_progress",
      "scope": "project",
      "updated_at": "2026-10-28T08:00:00Z",
      "match_reasons": ["exact_id", "keyword_match"],
      "source_refs": ["tasks/TSK-123/checkpoint.md"]
    }
  ],
  "has_more": false,
  "retrieval_mode": "exact_and_full_text"
}
```

Do not include full content by default. Do not include secrets or paths the actor is not allowed to see. Do not claim semantic similarity in V2. The retrieval mode must make clear that results came from exact lookup and/or full text search.

### 9.7 Full detail envelope

`get_memory_details` receives a bounded list of canonical result IDs and the caller's project and authorization context. It rechecks access, status, and deletion state for each ID. It returns only accessible records and includes:

1. Canonical record ID and type.
2. Full canonical content or the relevant source excerpt.
3. Current status and scope.
4. Creation and update timestamps where known.
5. Source references, including source file and section or line range where available.
6. Source version or hash where applicable.
7. Relationships already represented by existing canonical tables, such as a decision's source event, without creating a graph subsystem.
8. A clear unavailable or stale indication when the source reference no longer resolves.

Do not silently substitute a different record if a requested ID is missing. Return an explicit per ID not found or inaccessible result without leaking sensitive existence details.

### 9.8 Progressive disclosure

The expected pattern is:

1. Search returns a compact index of candidate records.
2. The agent selects the one or few likely relevant records.
3. The agent calls `get_memory_details` for those IDs.
4. The agent reads the source artifact directly when the record points to a file and the file provides stronger evidence.

Do not fetch every matching full record automatically. Do not create a separate timeline API in V2 unless one already exists and can be reused without scope expansion.

### 9.9 Source backed answers

Important implementation or architecture claims influenced by memory should retain the record IDs or source references used. If search returns no useful result, the agent must say that no matching stored evidence was found and continue using repository inspection or other appropriate evidence. It must not fabricate a remembered decision.

## 10. API contracts

Add these APIs to the existing memory facade. Preserve the V1 facade and its error conventions.

### 10.1 `search_memory(query, project_id, scope, filters, limit, actor)`

Purpose: return compact, authorized, source backed candidates using exact ID lookup and PostgreSQL full text search.

Required behavior:

1. Validate the query and bounded limit.
2. Validate the actor's access to the project and requested scopes.
3. Validate filter values against allowed record types and statuses.
4. Attempt deterministic exact ID lookup if applicable.
5. Execute full text search with mandatory filters in SQL.
6. Exclude stale chunks and sources that are deleted, inactive under default policy, or inaccessible.
7. Collapse duplicate chunks that point to the same canonical source where appropriate.
8. Return compact results with match reasons and source references.
9. Return an empty result list when no authorized matches exist.
10. Never reveal whether inaccessible records exist.
11. Never invoke an LLM to decide access or fabricate a result.
12. Never use embeddings or vector search in V2.

Suggested response:

```json
{
  "query": "database migration",
  "project_id": "project-uuid",
  "results": [],
  "has_more": false,
  "retrieval_mode": "full_text"
}
```

### 10.2 `get_memory_details(ids, project_id, actor)`

Purpose: fetch full details and evidence for selected results.

Required behavior:

1. Validate and bound the ID list.
2. Recheck authorization for every requested record.
3. Recheck canonical status, deletion, and freshness.
4. Return full content and source references for accessible records only.
5. Return explicit per ID outcomes for not found, stale, or inaccessible records without disclosing sensitive existence details.
6. Do not make a search chunk the authority for full content when the canonical source can be fetched.
7. Preserve the input order or document a stable ordering contract.
8. Do not automatically return every chunk or full source document for a result.

### 10.3 Error semantics

Follow existing V1 error patterns. At minimum distinguish invalid input, unauthorized request, project mismatch, record not found or inaccessible, stale index, database failure, and partial detail retrieval. Avoid exposing raw SQL errors, secrets, source content, or private record identifiers in user visible error messages.

### 10.4 Agent integration

Agents may call `search_memory` when they need prior evidence, but must continue to call `get_current_context` at task start. Search does not replace task checkpoints or current approved decisions. For current project truth, inspect the canonical V1 record or approved artifact instead of trusting a keyword hit alone.

Agents must not search across all projects by default. V2 is project scoped. Cross project learning is explicitly deferred to V4.

## 11. Source updates, stale chunks, and deletion safety

### 11.1 Source changes

When a searchable source changes, the system must stop returning chunks from the old source version as current. The implementation may mark chunks stale synchronously and then regenerate them. If regeneration fails, report an index freshness problem. Do not serve old content as though it represents the current source.

### 11.2 Status changes

When a decision is superseded, an item becomes inactive, a task changes status, or a source is otherwise made ineligible, retrieval must enforce the current canonical status. Updating only the copied status field on a chunk is insufficient.

### 11.3 Deletion

When a canonical record is deleted or marked deleted under the existing policy:

1. It becomes ineligible for search immediately.
2. `get_memory_details` refuses to return the deleted content.
3. Associated chunks are marked stale or removed according to the repository's deletion convention.
4. A later reindex cannot recreate the record from a stale chunk.
5. Historical source files remain preserved unless the owner separately authorizes their deletion under the relevant retention policy.

V2 does not implement the V4 hard purge workflow, but it must not leak deleted content through ordinary search.

## 12. Tests and evaluation

Tests are gates. Do not start V3 until all V2 gates pass and the Appendix E handoff is complete.

### 12.1 V1 regression suite

Run every V1 test, including decision persistence, task resumption, checkpoint concurrency, event idempotency, decision supersession, project isolation, and source preservation. Any regression blocks V2 release.

### 12.2 §28.2 exact identifier retrieval

Given a record with a known exact identifier, `search_memory` must return that record when the caller is authorized and the record is eligible. It must not return a different record due to token overlap. Include IDs containing punctuation and identifiers that PostgreSQL full text tokenization might split. Test exact lookup separately from keyword search.

### 12.3 §28.4 project boundary

Create two projects with similar or identical memory text. A caller authorized for Project A must not receive Project B records through exact lookup, full text search, pagination, or `get_memory_details`. Verify that an inaccessible ID does not disclose whether the record exists. Test default filters and explicit filters.

### 12.4 Import idempotency

For each migrated record type:

1. Run dry run and verify no target writes occur.
2. Import a known fixture and verify expected canonical records and provenance.
3. Run the same import again and verify no duplicate rows, events, or chunks.
4. Interrupt a multi record import after a committed batch, resume, and verify exactly one target per source identity.
5. Change a source record after the record type has been cut over and verify that the importer reports a conflict instead of overwriting PostgreSQL silently.
6. Include malformed JSON, invalid fields, missing IDs, duplicate IDs, and broken references.
7. Verify every input record is accounted for in the final report.

### 12.5 Cutover and no dual writers

For each record type being cut over, verify:

1. The PostgreSQL facade is the only canonical writer after cutover.
2. The legacy writer is disabled or redirected.
3. No runtime path independently writes the same logical record to JSONL and PostgreSQL.
4. A compatibility export, if retained, is one way only and cannot be read as canonical state.
5. The original JSONL file is preserved and its role is documented.

### 12.6 Index freshness

Create and index a source, then update it. Verify that old chunks are excluded and new chunks are searchable. Repeat the indexing operation and verify that it creates no duplicates. Delete or deactivate the source and verify its content is not returned.

### 12.7 Progressive disclosure

Verify that `search_memory` returns snippets and source refs, not full documents. Verify `get_memory_details` returns full details only for requested accessible IDs. Verify that a source reference is preserved even when the original file is unavailable, and the API marks it unavailable rather than inventing a replacement.

### 12.8 §28.4 project boundary with imported data

Import records from at least two fixture projects. Ensure that imported project ownership and scope are mapped correctly and that search cannot leak records across projects. This test is required even if project isolation already passes for native V1 rows.

### 12.9 Five real task evaluation: memory on versus memory off

Before adding keyword retrieval to agent workflows, choose five real tasks from the project's actual history. Include a mix of exact identifier lookup, finding a past decision, locating evidence, resuming an existing task, and finding a relevant prior project artifact. Do not fabricate benchmark tasks solely to make the feature look successful.

For each task, record:

1. The task description and expected correct evidence.
2. The canonical sources that prove the answer.
3. The baseline result with memory retrieval disabled. Agents may still use the ordinary repository tools and current context that are normally available; record exactly what was disabled.
4. The result with V2 memory retrieval enabled.
5. Whether the correct evidence was found.
6. Whether any irrelevant or inaccessible result was returned.
7. Number of retrieval calls and records opened.
8. Approximate extra prompt tokens, if measured by the current runtime.
9. End to end completion quality and time, if measurable.
10. A brief failure analysis.

Use the same model, task instructions, repository state, and available tools for both conditions. Avoid changing the task between runs. If possible, alternate run order to reduce order effects. A human reviewer checks correctness against canonical evidence.

V2 passes the evaluation when retrieval demonstrably helps at least the tasks that depend on historical evidence, does not create any authorization or project boundary failure, and does not materially degrade the remaining tasks. If it does not help, diagnose the indexing, query, filter, or agent integration problem before adding V3 complexity. Five tasks are an initial engineering gate, not a statistically definitive benchmark.

### 12.10 Security and injection checks

Store a source record containing text that asks the agent to ignore system instructions or reveal other projects. Verify that retrieval labels it as untrusted source content and that the agent does not treat it as executable instruction. Verify parameterized queries and ensure result snippets do not expose secrets or inaccessible paths.

## 13. Operational behavior

### 13.1 Logs

Import logs must include run ID, record type, source path, mapping version, source identity, outcome category, target ID when safe, and error category. Do not log full sensitive content. Search logs should include retrieval mode, number of candidates, filters applied, stale chunks excluded, and latency. V2 does not require the comprehensive retrieval learning log described for V3, but enough observability must exist to debug incorrect results.

### 13.2 Failure behavior

1. If PostgreSQL is unavailable, fail explicitly according to the existing runtime policy. Do not silently fall back to a legacy writer and create divergent state.
2. If the search index is stale, return only verified current candidates and report the indexing issue through the existing error or health mechanism.
3. If an import fails partway through, keep committed records and resume idempotently. Do not roll back an entire large import unless the transaction strategy specifically makes it safe and necessary.
4. If source parsing is ambiguous, skip that record with a clear error and require review.
5. If an exact ID is inaccessible, do not disclose its existence.

### 13.3 Performance

Use indexes and query plans to confirm that search applies project, scope, status, and freshness filters efficiently. Test with representative data sizes from the repository. Do not prematurely introduce a separate search service or cache. Bound result count and full detail fetches.

## 14. Implementation sequence and gates

Build in this order. Complete the exit criteria at each step before continuing.

### Step 1: Verify V1 and audit the repository

1. Read both parent specifications and the V1 handoff.
2. Run the full V1 test suite.
3. Inspect JSONL readers and writers.
4. Complete the source of truth matrix.
5. Identify the first safe record type for migration.

**Gate:** V1 passes and the selected record type has a known schema, owner, stable identity, and safe cutover plan.

### Step 2: Define importer mapping and dry run

1. Write the mapping document for the chosen record type.
2. Implement parse and validation logic.
3. Implement stable source identity and source hash.
4. Implement dry run output.
5. Add fixtures for valid, duplicate, malformed, and conflicting records.

**Gate:** Dry run accounts for every source record and performs no writes.

### Step 3: Implement idempotent import and verification

1. Implement atomic target writes plus durable import provenance.
2. Add bounded transactions and resume behavior.
3. Add structured reports.
4. Verify counts, identities, relationships, and samples.
5. Repeat the import and prove idempotency.

**Gate:** Import tests pass and verification output is reviewed.

### Step 4: Cut over the first record type

1. Document approval and rollback.
2. Switch reads and writes to the canonical facade.
3. Disable or redirect the old writer.
4. Verify there is no dual write path.
5. Preserve the legacy file and record its new role.

**Gate:** One canonical writer exists, and rollback does not enable two writers simultaneously.

### Step 5: Add `memory_items` and `memory_chunks`

1. Add the forward database migration.
2. Add constraints and indexes.
3. Implement deterministic chunk generation for selected source types.
4. Implement source version and stale chunk handling.
5. Implement PostgreSQL `search_vector` generation and GIN index.
6. Add tests for create, update, reindex, stale exclusion, and deletion eligibility.

**Gate:** No vector extension, embedding column, or embedding dependency exists.

### Step 6: Add search facade APIs

1. Implement exact ID lookup.
2. Implement keyword full text search.
3. Apply authorization, project, scope, status, and freshness filters in SQL.
4. Implement compact results and `has_more` or a documented cursor.
5. Implement `get_memory_details` with fresh authorization checks.
6. Add agent integration at the existing facade boundary.

**Gate:** Exact ID, project boundary, and progressive disclosure tests pass.

### Step 7: Migrate additional record types one at a time

Repeat Steps 2 through 4 for each approved record type. Do not batch unrelated schemas into one vague migration. After each cutover, update the source of truth matrix and rerun relevant tests.

**Gate:** Each type has its own import report, verification evidence, cutover record, and rollback procedure.

### Step 8: Run evaluation and complete handoff

1. Run all V1 regression tests.
2. Run all V2 importer, index, search, authorization, and deletion tests.
3. Run the five task memory on versus memory off evaluation.
4. Inspect the diff for V3 or V4 leakage.
5. Complete Appendix E handoff.

**Gate:** All required tests pass, results are recorded, and deferred work remains deferred.

## 15. Definition of done

V2 is done only when every applicable checkbox below is true.

### Predecessor and source audit

* [ ] V1 was verified and all V1 tests pass.
* [ ] Existing JSONL readers and writers were located in the actual repository.
* [ ] A source of truth matrix exists for every considered record type.
* [ ] Each migrated record type has a mapping specification and cutover plan.

### Migration

* [ ] Import is explicit, dry runnable, idempotent, and resumable.
* [ ] Stable source identities and hashes are recorded.
* [ ] Target writes and import markers are atomic.
* [ ] Invalid records are reported, not silently discarded.
* [ ] Verification checks counts, identities, references, and samples.
* [ ] Each migrated type has one canonical writer after cutover.
* [ ] Original JSONL files and other source artifacts are preserved.

### Storage and search

* [ ] `memory_items` exists with typed fields and source provenance.
* [ ] `memory_chunks` exists with `search_vector` and a GIN index.
* [ ] There are no embedding columns, vector indexes, or pgvector dependency.
* [ ] Indexing is deterministic and old source versions are excluded.
* [ ] Exact ID lookup is deterministic.
* [ ] Keyword search enforces project, scope, status, authorization, and freshness filters before results are returned.
* [ ] Search results are compact and include source references.
* [ ] Full details are fetched only for requested IDs and access is rechecked.
* [ ] Deleted or inaccessible records are not returned through stale chunks.

### Tests and evaluation

* [ ] V1 regression suite passes.
* [ ] §28.2 exact identifier retrieval passes.
* [ ] §28.4 project boundary passes for native and imported data.
* [ ] Import idempotency, interruption recovery, malformed record, and conflict tests pass.
* [ ] Index freshness, deletion eligibility, and progressive disclosure tests pass.
* [ ] Five real tasks were evaluated with memory on and memory off, and results were recorded.
* [ ] No critical authorization, source of truth, or stale content bug remains open.

### Scope control

* [ ] No embeddings, pgvector, semantic retrieval, or RRF was implemented.
* [ ] No automated lesson extraction, cross project learning, or consolidation was implemented.
* [ ] No second writable source of truth was introduced.
* [ ] Appendix E handoff is complete.

## 16. Deferred work for later versions

This section is a reminder of boundaries, not a work queue for this version.

1. **V3:** pgvector, pinned embedding model, selected section embeddings, hybrid retrieval using RRF, source change invalidation for embedding chunks, and retrieval logs as specified in `MEMORY.md` Phase 6.
2. **V4:** explicit task end lesson proposals and validation, authorized cross project lesson access, deduplication and consolidation, hard purge verification, and their acceptance tests.
3. **Not in any version unless separately approved:** a new graph database, independent vector database, custom memory model, autonomous permanent storage of every observation, or a memory platform separate from the Virtual Pod.

Do not add schema or abstractions in V2 solely to anticipate these features. Keep the V2 design extensible through the existing facade and source version contracts, but implement only the behavior required now.

## 17. Appendix E handoff template for V2

Complete this section after implementation. Replace every placeholder with an observed result. If something is not implemented, say so. Do not claim a test passed without its command and result.

# MEMV2 implementation handoff

## Implemented sections

* Repository audit:
* JSONL migration and cutover:
* `memory_items`:
* `memory_chunks` and full text indexing:
* `search_memory`:
* `get_memory_details`:
* Agent integration:
* Tests and evaluation:

## Existing code reused

* Existing memory facade and location:
* Existing PostgreSQL models and repositories:
* Existing migration framework:
* Existing JSONL readers/writers and how they were retired or redirected:
* Existing authorization checks:
* Existing logging or background job mechanisms reused:

## New code introduced

* Files added:
* Files modified:
* Migrations added:
* CLI commands or operational entry points added:
* New dependencies, if any, with rationale:

## Canonical source decisions

For each migrated record type, list:

| Record type | Canonical owner before | Canonical owner after | Cutover commit/time | Legacy file role | Legacy writer disabled or redirected | Rollback plan |
|---|---|---|---|---|---|---|
| Fill actual results | | | | | | |

* Remaining JSONL record types not migrated:
* Known historical gaps:
* Confirmation that no dual writers remain:

## Import results

For each import run, record:

| Record type | Source files | Source count | Inserted | Already imported | Reconciled | Skipped | Invalid | Failed | Verification status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Fill actual results | | | | | | | | | |

* Idempotency command and result:
* Interrupted import recovery test:
* Conflict handling test:
* Source preservation verification:

## Database and migrations

* Migration identifiers:
* Tables and indexes added:
* `search_vector` configuration:
* Chunking boundaries and maximum size:
* Source version and stale chunk behavior:
* Confirmation that there is no vector column, embedding generation, or pgvector dependency:
* Migration rollback or recovery procedure:

## API behavior

* `search_memory` input/output contract:
* Exact ID behavior:
* Mandatory SQL filters:
* Default result limit and hard maximum:
* `get_memory_details` behavior:
* Error semantics:
* Source reference format:
* Deletion and stale index behavior:

## Tests

| Test suite or command | Result | Evidence or output reference |
|---|---|---|
| Full V1 regression suite | | |
| §28.2 exact identifier retrieval | | |
| §28.4 project boundary | | |
| Import idempotency and resume | | |
| Import conflict and malformed record handling | | |
| Index freshness and deletion | | |
| Progressive disclosure | | |
| Security and injection checks | | |
| Five real task memory on/off evaluation | | |

## Evaluation findings

* Five tasks selected and why:
* Tasks improved by memory retrieval:
* Tasks unchanged or degraded:
* Incorrect or irrelevant results observed:
* Project boundary results:
* Approximate latency and context cost:
* Fixes made after evaluation:
* Remaining limitations:

## Deferred work, explicitly not implemented

* pgvector and semantic search: V3 only.
* Embeddings and model pinning: V3 only.
* RRF hybrid retrieval: V3 only.
* Automated lesson extraction and validation: V4 only.
* Cross project lessons: V4 only.
* Consolidation and hard purge workflow: V4 only.
* Any additional explicitly deferred work:

## Known gaps and blockers

* Gap:
* Impact:
* Why it remains:
* Required follow up version or owner:

## Final result

Choose one and explain:

* `PASS`: every V2 gate passes and V3 may be considered, but only if V2 evaluation demonstrates a concrete need for semantic search.
* `BLOCKED`: one or more mandatory gates fail. Fix V2 or its V1 dependency before proceeding.

* Final commit:
* Test commands and results:
* Confirmation that no dual writers remain:
* Confirmation that no V3 or V4 feature was built:
* Implementer and reviewer:
* Date:

## V2 operating rule

V2 makes the existing memory system searchable and migrates selected legacy data safely. PostgreSQL full text search is enough for this version. Exact identifiers must resolve deterministically, all results must respect project and status boundaries, and every result must point back to its source. Import one record type at a time, verify it, cut over one canonical writer, and preserve the original evidence. Do not add embeddings or learning behavior. V3 may begin only after V2 passes its tests, the five real task evaluation is documented, and this handoff is complete. Even then, V3 semantic search should be built only if V2 demonstrably misses real queries.
