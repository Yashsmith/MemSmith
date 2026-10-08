# Memory System

## A Dynamic, Adaptive Memory Architecture for Intelligent Systems

> **Memory is not where information lives. Memory is how information
> changes over time.**

------------------------------------------------------------------------

# 1. Purpose

This document defines a conceptual and technical model for building a
general-purpose memory system for intelligent systems.

The objective is **not** to define a coding agent, multi-agent
architecture, RAG system, or a particular implementation.

The objective is to answer a more fundamental question:

> **What should memory mean for an intelligent system?**

The system should be capable of:

-   forming memories from experiences
-   distinguishing different kinds of memories
-   assigning memories different scopes
-   retrieving memories according to context
-   reinforcing useful memories
-   allowing unimportant memories to fade
-   consolidating repeated experiences into higher-level knowledge
-   representing relationships between memories
-   handling contradictory knowledge
-   preserving provenance
-   archiving low-accessibility memories without necessarily deleting
    them
-   reactivating old memories when they become relevant again
-   generalizing project-specific knowledge into broader knowledge when
    justified
-   maintaining a history of how memories changed over time

The central idea is:

> **A memory system should not optimize for remembering everything. It
> should optimize for remembering the right things, at the right level
> of detail, at the right time.**

------------------------------------------------------------------------

# 2. The Fundamental Idea

A conventional storage system thinks about information like this:

``` text
information
     ↓
storage
     ↓
retrieval
```

A richer memory system looks like:

``` text
                    EXPERIENCE
                        ↓
                    FORMATION
                        ↓
                  CLASSIFICATION
                        ↓
                     SCORING
                        ↓
                    STORAGE
                        ↓
                    RETRIEVAL
                        ↓
                      USE
                        ↓
                    OUTCOME
                   /       \
             SUCCESS       FAILURE
                ↓             ↓
          REINFORCEMENT     PENALTY
                ↓             ↓
          CONSOLIDATION     DECAY
                ↓
            GENERALIZATION
                ↓
          LONG-TERM MEMORY
                ↓
              ARCHIVE
                ↓
           REACTIVATION
                ↓
             RETRIEVAL
```

Memory is therefore not merely a storage layer.

It is a **dynamic lifecycle**.

------------------------------------------------------------------------

# 3. The Core Thesis

The system should treat memory as a combination of:

``` text
Memory
=
content
+
type
+
scope
+
lifecycle
+
accessibility
+
strength
+
confidence
+
importance
+
provenance
+
relationships
+
evidence
+
history
```

A memory is therefore not simply:

``` json
{
  "text": "Use PostgreSQL"
}
```

It is closer to:

``` json
{
  "content": "Use PostgreSQL for this project's structured state",
  "type": "decision",
  "scope": "project",
  "lifecycle": "passive",
  "strength": 0.81,
  "confidence": 0.94,
  "importance": 0.76,
  "accessibility": 0.72,
  "applicability": 0.34,
  "provenance": [],
  "relationships": [],
  "successful_uses": 5,
  "failed_uses": 0
}
```

The distinction between these dimensions is critical.

------------------------------------------------------------------------

# 4. Memory Is Multidimensional

One of the most important architectural decisions is:

> **Do not collapse memory into a single "importance" score.**

A memory has multiple independent properties.

For example:

``` text
Memory:
"Use architecture X for Project A"

Type:
Decision

Scope:
Project A

Lifecycle:
Persistent

Strength:
0.91

Confidence:
0.96

Importance:
0.88

Applicability:
0.21

Accessibility:
0.72
```

This means:

-   the memory is strongly established
-   the system is highly confident it is correct
-   it is important
-   but it is only applicable to Project A

Another memory might be:

``` text
"Use progressive disclosure when context becomes large."

Strength:
0.83

Confidence:
0.91

Applicability:
0.94

Scope:
Global
```

These memories should behave very differently even if their numerical
strength is similar.

------------------------------------------------------------------------

# 5. The Six Core Dimensions

A useful model is to represent memory using six major dimensions.

## 5.1 Type

**What kind of information is this?**

Examples:

-   episodic
-   semantic
-   procedural
-   decision
-   preference
-   observation
-   lesson
-   associative

## 5.2 Scope

**Where does this memory apply?**

Examples:

``` text
Task
Meeting
Session
Agent
Project
Team
Organization
Global
```

## 5.3 Lifecycle

**Where is this memory in its lifecycle?**

Examples:

``` text
Working
Active
Consolidating
Persistent
Archived
```

## 5.4 Accessibility

**How easy should it be to retrieve right now?**

This is dynamic.

A memory can exist permanently while becoming difficult to retrieve.

## 5.5 Strength

**How strongly has the memory been reinforced by useful experience?**

Strength changes based on successful and unsuccessful use.

## 5.6 Confidence

**How likely is the memory to be correct?**

Confidence depends on:

-   evidence
-   source quality
-   independent confirmation
-   contradictions
-   human validation
-   temporal validity

------------------------------------------------------------------------

# 6. Memory Type

Memory lifecycle answers:

> "How established is this memory?"

Memory type answers:

> "What does this memory represent?"

These should remain separate.

------------------------------------------------------------------------

# 7. Working Memory

Working memory represents the system's immediate cognitive state.

It contains what is necessary **right now**.

Examples:

``` text
Current objective
Current task
Current conversation
Immediate reasoning
Temporary hypothesis
Intermediate output
Current relevant memories
Current tool result
Current error
```

Working memory should be aggressively bounded.

It should **not** contain everything the system knows.

The principle is:

> **Working memory is about immediate usefulness, not durability.**

------------------------------------------------------------------------

# 8. Episodic Memory

Episodic memory represents experiences and events.

It answers:

> **What happened?**

Example:

``` text
During the architecture meeting on October 8,
the team rejected Approach A because it introduced
unnecessary operational complexity.
```

Potential metadata:

``` text
timestamp
participants
context
event
source
location/session
decisions
related memories
```

Episodic memory is generally closer to the original experience.

------------------------------------------------------------------------

# 9. Semantic Memory

Semantic memory represents extracted knowledge.

It answers:

> **What do we know?**

Example:

``` text
Approach A introduces unnecessary operational complexity.
```

This may have been derived from:

``` text
Meeting 1
Meeting 2
Experiment 1
Incident 3
```

The individual experiences can remain as provenance while the semantic
memory becomes the easier-to-retrieve abstraction.

------------------------------------------------------------------------

# 10. Procedural Memory

Procedural memory represents how something is done.

It answers:

> **How do we do this?**

Example:

``` text
When debugging service X:

1. Check connection pool metrics.
2. Inspect service logs.
3. Check deployment configuration.
4. Compare against previous incidents.
```

Repeated successful procedures are strong candidates for durable memory.

------------------------------------------------------------------------

# 11. Associative Memory

Associative memory represents relationships between memories.

Example:

``` text
Requirement
     ↓
Architecture Decision
     ↓
Implementation
     ↓
Observed Result
     ↓
Lesson
```

Associative memory can be represented as a graph.

The graph is not merely a visualization.

It can become part of retrieval and reasoning.

------------------------------------------------------------------------

# 12. Other Useful Memory Types

Additional types may include:

### Observation

Something directly observed.

``` text
CPU utilization exceeded 90%.
```

### Decision

A deliberate choice.

``` text
The team selected PostgreSQL.
```

### Preference

A persistent preference.

``` text
Prefer visual explanations.
```

### Lesson

A generalized experience-derived principle.

``` text
Adding unnecessary orchestration layers increases operational complexity.
```

### Hypothesis

An unvalidated belief.

``` text
The latency issue may be caused by connection pooling.
```

### Constraint

A rule or limitation.

``` text
This service cannot access external networks.
```

These types should remain extensible.

------------------------------------------------------------------------

# 13. Memory Lifecycle

The lifecycle represents how memory changes over time.

A conceptual lifecycle:

``` text
NEW
 ↓
WORKING
 ↓
ACTIVE
 ↓
CONSOLIDATING
 ↓
PERSISTENT
 ↓
ARCHIVED
```

But this is **not a one-way pipeline**.

Memory can move backward.

``` text
ARCHIVED
    ↓
relevant retrieval
    ↓
REACTIVATION
    ↓
ACTIVE
```

Likewise:

``` text
PERSISTENT
    ↓
contradicted / stale
    ↓
ACTIVE
    ↓
ARCHIVED
```

The system therefore behaves more like a state machine than a pipeline.

------------------------------------------------------------------------

# 14. The Four-Level Mental Model

The system can use four intuitive memory levels:

``` text
┌────────────────────┐
│      WORKING       │
│ Immediate cognition│
└─────────┬──────────┘
          ↓
┌────────────────────┐
│       ACTIVE       │
│ Recent / relevant  │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│      PASSIVE       │
│ Consolidated       │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│   SUPER-PASSIVE    │
│ Durable knowledge  │
└────────────────────┘
```

These names are useful as a conceptual model.

They are **not intended as standardized neuroscience terminology**.

A technical implementation may map them to:

``` text
Working Memory
Active / Session Memory
Persistent / Long-Term Memory
Deep / Archival / Durable Memory
```

------------------------------------------------------------------------

# 15. Working Memory vs Active Memory

This distinction is important.

### Working Memory

> What is needed **right now**.

Examples:

``` text
current tool call
current hypothesis
current task
current reasoning
```

### Active Memory

> What is currently relevant or recently useful.

Examples:

``` text
today's decisions
recent meeting context
recent project state
recently successful strategies
```

Therefore:

``` text
Working = immediate cognitive state

Active = currently accessible experience/knowledge
```

------------------------------------------------------------------------

# 16. Passive Memory

Passive memory represents information that has survived enough
experience to become relatively durable.

Examples:

``` text
Important project decisions
Repeated patterns
Established preferences
Lessons
Stable facts
Validated procedures
```

Passive memory does not need to be retrieved every time.

It remains available for relevant situations.

------------------------------------------------------------------------

# 17. Super-Passive Memory

Super-passive memory represents durable, repeatedly validated knowledge.

Examples:

``` text
General engineering principles
Cross-project lessons
Stable user preferences
Highly validated procedures
Organizational knowledge
Core system knowledge
```

A memory should require substantial evidence before reaching this level.

A single observation should almost never become super-passive.

------------------------------------------------------------------------

# 18. Long-Term Memory Is Not the Same as Super-Passive

Long-term is fundamentally a **retention concept**.

Super-passive is a conceptual **durability / consolidation level**.

A memory can be:

``` text
Long-term
+
project scoped
```

without being globally applicable.

Therefore:

``` text
long-term ≠ global
```

and:

``` text
old ≠ important
```

------------------------------------------------------------------------

# 19. Memory Geography

A useful way to think about memory is that it has **geography**.

Memory has:

-   scope
-   proximity
-   depth
-   accessibility
-   relationships
-   lifetime

For example:

``` text
                 GLOBAL
                   │
              ORGANIZATION
                   │
                 TEAM
                   │
                PROJECT
                   │
                SESSION
                   │
                MEETING
                   │
                  TASK
```

A query should not necessarily search this entire universe.

It should start near the current context and expand outward when
necessary.

------------------------------------------------------------------------

# 20. Memory Scope

Possible scopes:

``` text
TASK
MEETING
SESSION
AGENT
PROJECT
TEAM
ORGANIZATION
GLOBAL
```

Examples:

``` text
Session-scoped:
"What happened during this conversation?"

Project-scoped:
"Why did Project A choose PostgreSQL?"

Team-scoped:
"How does Team X deploy services?"

Organization-scoped:
"What deployment practices have repeatedly worked?"

Global:
"What general engineering principle applies?"
```

Scope should be explicit.

------------------------------------------------------------------------

# 21. Scope Is Separate From Lifecycle

A memory can be:

``` text
Project
+
Semantic
+
Persistent
```

or:

``` text
Session
+
Episodic
+
Active
```

or:

``` text
Organization
+
Procedural
+
Persistent
```

This is why a flat four-tier memory architecture is insufficient.

Memory should be multidimensional.

------------------------------------------------------------------------

# 22. Memory Across Projects

Some knowledge should survive individual projects.

Example:

``` text
Project A
    ↓
Repeated lesson
    ↓
Candidate organizational memory
    ↓
Project B
```

But this promotion must be conservative.

A project-specific workaround should not become a global rule simply
because it was successful once.

A useful rule:

> **Promotion of scope requires evidence of transferability, not merely
> evidence of success.**

------------------------------------------------------------------------

# 23. Cross-Functional Memory

Memory should also connect different domains.

For example:

``` text
Product Requirement
        ↓
Architecture Decision
        ↓
Backend Implementation
        ↓
Database Change
        ↓
Observed Performance
        ↓
Engineering Lesson
```

This allows memory to cross:

-   product
-   frontend
-   backend
-   database
-   infrastructure
-   research
-   operations

The resulting knowledge is more valuable than isolated departmental
memories.

------------------------------------------------------------------------

# 24. Memory Formation

Not everything should become memory.

A formation pipeline could be:

``` text
Experience
    ↓
Observation
    ↓
Candidate extraction
    ↓
Classification
    ↓
Importance assessment
    ↓
Scope determination
    ↓
Deduplication
    ↓
Evidence attachment
    ↓
Memory creation
```

Potential questions:

``` text
Is this worth remembering?

Is this new?

Is it already known?

Is it temporary?

Is it a fact, event, decision, procedure, or lesson?

What scope does it belong to?

How reliable is the source?
```

------------------------------------------------------------------------

# 25. Memory Formation Should Be Selective

A major failure mode would be:

``` text
every interaction
      ↓
memory
```

This creates:

-   memory explosion
-   retrieval noise
-   redundant memories
-   context bloat
-   incorrect reinforcement
-   graph clutter

Instead:

``` text
experience
    ↓
candidate
    ↓
importance/relevance filter
    ↓
memory OR discard
```

Some information should never become persistent memory.

------------------------------------------------------------------------

# 26. Memory Scoring

Memory should use multiple signals.

Possible dimensions:

``` text
relevance
recency
importance
confidence
provenance quality
successful usage
failed usage
scope match
applicability
freshness
relationship strength
contradiction status
```

Do not collapse all of these into one permanent score.

Instead maintain the dimensions independently and calculate
task-specific retrieval scores.

------------------------------------------------------------------------

# 27. Retrieval Score

For a specific query, a conceptual score could be:

``` text
Retrieval Score =

    semantic relevance
  + contextual relevance
  + scope match
  + memory strength
  + confidence
  + graph relevance
  + successful-use history
  + recency
  + applicability

  - contradiction penalty
  - staleness penalty
  - context cost
```

The weights should depend on the task.

For example, a debugging task may prioritize:

``` text
recent
+
project
+
procedural
+
successful history
```

A strategic question may prioritize:

``` text
persistent
+
high confidence
+
cross-project
+
high applicability
```

------------------------------------------------------------------------

# 28. Retrieval Is Not Reinforcement

This distinction is essential.

Bad model:

``` text
retrieved
   ↓
stronger
   ↓
retrieved more
   ↓
stronger
```

This creates feedback loops.

Instead:

``` text
retrieved
   ↓
used
   ↓
outcome
   ↓
evaluation
   ↓
reinforcement
```

Retrieval gives the system an opportunity to learn.

Successful application provides evidence.

------------------------------------------------------------------------

# 29. Reinforcement

A memory can become stronger through:

-   successful use
-   explicit human confirmation
-   independent supporting evidence
-   repeated usefulness
-   cross-context validation
-   successful prediction
-   successful procedure execution

A conceptual model:

``` text
Δstrength =

    successful_use
  + explicit_validation
  + supporting_evidence
  + repeated_relevance
  + independent_confirmation

  - failed_application
  - contradiction
  - staleness
```

This is conceptual rather than a final mathematical specification.

------------------------------------------------------------------------

# 30. The Most Important Reinforcement Principle

> **Repeated successful recall is stronger evidence than repeated recall
> alone.**

Suppose a bad retrieval system retrieves the same memory 100 times.

That does not mean the memory is important.

But if a memory is:

``` text
retrieved
→ applied
→ successful

retrieved
→ applied
→ successful

retrieved
→ applied
→ successful
```

then there is evidence that the memory is genuinely useful.

This distinction should be built into the architecture.

------------------------------------------------------------------------

# 31. Memory Decay

Good memory requires forgetting.

But forgetting should not necessarily mean deletion.

A useful conceptual model:

``` text
high relevance
    ↓
high accessibility

low relevance
    ↓
lower accessibility

long inactivity
    ↓
archive
```

Decay can affect:

-   retrieval priority
-   accessibility
-   freshness
-   ranking
-   context inclusion

It does not necessarily destroy the underlying record.

------------------------------------------------------------------------

# 32. Memory Should Lose Resolution Before Meaning

This is a particularly important idea.

Imagine:

### Initial memory

``` text
On October 8 at 14:31,
the user rejected architecture X,
after discussing three specific concerns
for 11 minutes.
```

Later:

``` text
Architecture X was rejected because
it introduced unnecessary complexity.
```

Later:

``` text
Avoid unnecessarily complex orchestration.
```

The system has progressively transformed:

``` text
detailed event
      ↓
gist
      ↓
pattern
      ↓
principle
```

This is memory compression and consolidation.

------------------------------------------------------------------------

# 33. Memory Decay vs Memory Compression

These are different.

### Decay

Reduces accessibility.

``` text
memory still exists
but becomes harder to retrieve
```

### Compression

Reduces representational detail.

``` text
large experience
      ↓
smaller useful representation
```

A memory can therefore become:

``` text
less detailed
+
still highly accessible
```

or:

``` text
detailed
+
very low accessibility
```

These are different states.

------------------------------------------------------------------------

# 34. Archival Memory

Archive should mean:

> **Low accessibility, not deletion.**

Example:

``` text
ACTIVE
  ↓
inactivity
  ↓
PERSISTENT
  ↓
long inactivity
  ↓
ARCHIVE
```

The original evidence can remain accessible through explicit lookup.

The normal retrieval system simply gives it a low priority.

------------------------------------------------------------------------

# 35. "Distance" Instead of Delete

A useful conceptual principle:

> **Memory should have distance, not necessarily a delete button.**

A memory can become distant.

``` text
ACTIVE
  ↓
LESS ACCESSIBLE
  ↓
ARCHIVED
```

But it can return.

``` text
ARCHIVED
  ↓
new relevant context
  ↓
RETRIEVED
  ↓
REACTIVATED
```

This creates reversible forgetting.

------------------------------------------------------------------------

# 36. Reactivation

An old memory should be able to return when context makes it relevant
again.

Example:

``` text
Old memory
    ↓
new query resembles old context
    ↓
retrieval
    ↓
successful application
    ↓
reactivation
    ↓
increased accessibility
```

The system does not have to permanently promote it.

Temporary reactivation can be enough.

------------------------------------------------------------------------

# 37. Memory Consolidation

Consolidation transforms multiple experiences into durable knowledge.

Example:

``` text
Experience A
Experience B
Experience C
Experience D
       ↓
common pattern
       ↓
consolidated memory
```

Instead of repeatedly retrieving four experiences:

``` text
A + B + C + D
```

the system can retrieve:

``` text
Pattern P
```

while retaining the ability to inspect:

``` text
P
 ↓
A
B
C
D
```

------------------------------------------------------------------------

# 38. Memory Synthesis

Synthesis is related to consolidation but slightly different.

### Retrieval

Finds existing knowledge.

### Consolidation

Compresses or stabilizes existing knowledge.

### Synthesis

Creates a new abstraction from multiple memories.

Example:

``` text
Observation A
Observation B
Observation C
Observation D

       ↓

new pattern
```

That new pattern did not previously exist as a memory.

------------------------------------------------------------------------

# 39. Memory Generalization

Generalization is the process of determining whether a memory applies
beyond its original scope.

Example:

``` text
Project A
    ↓
successful lesson
    ↓
Project B
    ↓
same lesson works
    ↓
Project C
    ↓
same lesson works
```

The system can form:

``` text
cross-project memory
```

Potentially:

``` text
organization-level memory
```

Generalization should require evidence.

------------------------------------------------------------------------

# 40. Generalization Should Be Conservative

Do not do this:

``` text
Worked once in Project A
        ↓
GLOBAL RULE
```

Instead:

``` text
Worked in A
    ↓
candidate

Worked in B
    ↓
stronger candidate

Worked in C
    ↓
cross-project pattern

validated
    ↓
organizational memory
```

This protects against overgeneralization.

------------------------------------------------------------------------

# 41. Memory Contradictions

Persistent memory introduces an unavoidable problem:

> Two memories may disagree.

Example:

``` text
Memory A:
"Use Redis."

Memory B:
"Use Valkey."
```

The system should not blindly overwrite A.

The relationship may be:

``` text
B
│
└── SUPERSEDES → A
```

But another situation could be:

``` text
A:
Redis is preferred for Project A.

B:
Valkey is preferred for Project B.
```

These are not contradictory.

They have different scopes.

Therefore contradiction detection must consider:

``` text
content
scope
time
context
source
confidence
validity
```

------------------------------------------------------------------------

# 42. Temporal Validity

Memories may need:

``` text
valid_from
valid_until
```

Example:

``` text
Memory A
valid: Jan → Jun

Memory B
valid: Jul → present
```

This allows the system to preserve historical truth.

The old memory can remain correct for its historical period even if it
is no longer current.

------------------------------------------------------------------------

# 43. Supersession

When one memory replaces another:

``` text
Old Memory
     │
     └── SUPERSEDED_BY
                     ↓
                 New Memory
```

The old memory remains in provenance.

Normal retrieval should prefer the new memory.

Historical retrieval can still access the old one.

------------------------------------------------------------------------

# 44. Provenance

Every important memory should answer:

> **Why do we believe this?**

A memory should be traceable to:

``` text
source
 ↓
event
 ↓
observation
 ↓
extraction
 ↓
memory
```

Possible sources:

-   conversation
-   meeting
-   document
-   experiment
-   tool result
-   code change
-   benchmark
-   user feedback
-   agent observation
-   external data

------------------------------------------------------------------------

# 45. Evidence vs Memory

This distinction is fundamental.

### Evidence

What actually happened.

### Memory

What the system retained or inferred from what happened.

Therefore:

``` text
Evidence
   ↓
Observation
   ↓
Memory
   ↓
Consolidated Memory
   ↓
Generalized Knowledge
```

The system should retain enough lineage to move backwards.

------------------------------------------------------------------------

# 46. Memory Lineage

A consolidated memory should be able to answer:

> **Where did I come from?**

Example:

``` text
GLOBAL LESSON
     │
     ├── Project A lesson
     │      ├── incident 1
     │      └── incident 2
     │
     ├── Project B lesson
     │      └── benchmark 3
     │
     └── Project C lesson
            └── incident 4
```

This is memory lineage.

------------------------------------------------------------------------

# 47. Memory Graph

Memory should be modeled as a graph.

``` text
                  Requirement
                       │
                       │ derived from
                       ▼
                    Decision
                    /      \
          implemented by   supersedes
                /             \
             Change          Old Decision
                │
                ▼
             Outcome
                │
                ▼
              Lesson
```

Possible relationship types:

``` text
RELATED_TO
DERIVED_FROM
CAUSED_BY
CAUSED
SUPPORTS
CONTRADICTS
SUPERSEDES
GENERALIZES
SPECIALIZES
IMPLEMENTED_BY
DEPENDS_ON
CONFIRMED_BY
INVALIDATED_BY
USED_WITH
SUCCESSFUL_WITH
FAILED_WITH
```

------------------------------------------------------------------------

# 48. Edges Are First-Class Memory

The system should remember not only:

``` text
A
B
C
```

but:

``` text
A → B
B → C
A → C
```

The relationship itself can contain:

``` text
strength
confidence
activation_count
successful_activation_count
last_activated
provenance
```

This allows the graph to learn.

------------------------------------------------------------------------

# 49. Associative Retrieval

When memory A is activated:

``` text
A
```

related memories can receive activation:

``` text
A = 1.0

B = 0.7
C = 0.4
D = 0.2
```

A conceptual propagation function:

``` text
activation(B)
=
activation(A)
× edge_strength(A,B)
× distance_decay
```

This creates associative recall.

The system can therefore retrieve memories because they are connected,
not only because they are semantically similar.

------------------------------------------------------------------------

# 50. Edge Reinforcement

Repeatedly useful relationships become stronger.

Initially:

``` text
A ───── B
```

After repeated successful associations:

``` text
A ═════ B
```

Eventually:

``` text
A █████ B
```

The visualization can reflect this.

But the graph's edge strength should also affect retrieval.

------------------------------------------------------------------------

# 51. Memory Visualization

The memory system should have a visual representation because memory is
fundamentally relational.

The primary UI can be a **Memory Canvas**.

``` text
┌──────────────────────────────────────────────────────────┐
│                    MEMORY CANVAS                         │
│                                                          │
│                  ●───────●                               │
│                 / \       \                              │
│                ●   ●──────●                              │
│                 \         /                              │
│                  ●───────●                               │
│                                                          │
│              MEMORY GRAPH                                │
└──────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 52. Visual Encoding

The graph should communicate memory properties visually.

Possible mappings:

``` text
Node size
→ importance / strength

Node brightness
→ accessibility

Node opacity
→ decay

Border
→ confidence

Pulse
→ recent retrieval

Halo
→ active use

Edge thickness
→ relationship strength

Edge brightness
→ recent activation
```

The visualization should not merely be decorative.

It should expose the memory system's internal dynamics.

------------------------------------------------------------------------

# 53. Retrieval Pulse

When a memory is retrieved:

``` text
query
 ↓
memory selected
 ↓
node pulses
 ↓
connected edges illuminate
 ↓
related memories activate
 ↓
timeline receives event
```

The user can literally see:

> **What did the system remember?**

------------------------------------------------------------------------

# 54. Memory Strengthening Animation

If a memory is successfully used:

``` text
before:

    ○────○


after:

    ◉════○
```

The node becomes slightly larger.

The relationship becomes slightly stronger.

The UI receives a `memory.reinforced` event.

This makes learning visible.

------------------------------------------------------------------------

# 55. Decay Visualization

When a memory becomes less accessible:

``` text
ACTIVE:

    ◉════◉


DECAYING:

    ○────·


ARCHIVED:

    ···
```

The system visually communicates:

> "This still exists, but it is becoming distant."

------------------------------------------------------------------------

# 56. Memory Kanban

The graph should coexist with a Kanban-like lifecycle view.

``` text
┌────────────┬────────────┬────────────┬────────────────┐
│  WORKING   │   ACTIVE   │  PASSIVE   │ SUPER-PASSIVE  │
├────────────┼────────────┼────────────┼────────────────┤
│ Current    │ Recent     │ Lessons    │ Core principles│
│ context    │ decisions  │ Patterns   │ Durable rules  │
│            │            │ Decisions  │ Global memory  │
└────────────┴────────────┴────────────┴────────────────┘
```

The Kanban is not a second storage model.

It is another view of the same underlying memory graph.

------------------------------------------------------------------------

# 57. Memory Card

A memory card could display:

``` text
┌───────────────────────────────┐
│ Architecture X is preferred   │
│ for high-concurrency service  │
│                               │
│ Semantic / Lesson             │
│ Project: Alpha                │
│                               │
│ Strength       ████████░░ 0.81│
│ Confidence     █████████░ 0.93│
│ Accessibility  ██████░░░░ 0.64│
│                               │
│ Used successfully: 7          │
│ Failed: 1                     │
│                               │
│ Last used: 3 days ago         │
└───────────────────────────────┘
```

------------------------------------------------------------------------

# 58. Memory Transition Explanation

Every transition should be explainable.

Example:

``` text
ACTIVE → PASSIVE

Reason:
- retrieved 9 times
- successfully used 7 times
- referenced across 4 sessions
- confidence = 0.92
- no significant contradictions
```

Or:

``` text
PASSIVE → ACTIVE

Reason:
- current context strongly matches memory
- retrieved during current task
- high contextual relevance
```

Or:

``` text
ACTIVE → ARCHIVED

Reason:
- no meaningful use for 120 days
- low importance
- low current relevance
```

The system should never silently mutate memory.

------------------------------------------------------------------------

# 59. Memory Timeline

Every memory should have a timeline.

Example:

``` text
Oct 1
  │
  ├── Created
  │
Oct 2
  │
  ├── Retrieved
  │
Oct 4
  │
  ├── Successfully used
  │
Oct 7
  │
  ├── Retrieved again
  │
Oct 12
  │
  ├── Relationship strengthened
  │
Oct 15
  │
  ├── Promoted
  │
Nov 3
  │
  ├── Successfully reused
  │
Dec 1
  │
  └── Generalized
```

This makes the evolution of a memory inspectable.

------------------------------------------------------------------------

# 60. Memory State Machine

A more precise lifecycle:

``` text
                    ┌──────────────┐
                    │    NEW       │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │   WORKING    │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │    ACTIVE    │◄──────────┐
                    └──────┬───────┘           │
                           ↓                   │
                    ┌──────────────┐           │
                    │ CONSOLIDATING│           │
                    └──────┬───────┘           │
                           ↓                   │
                    ┌──────────────┐           │
                    │  PERSISTENT  │───────────┘
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │   ARCHIVED   │
                    └──────┬───────┘
                           │
                       relevance
                           │
                           └──────────────→ REACTIVATED
```

------------------------------------------------------------------------

# 61. Promotion

Promotion should depend on multiple signals.

### WORKING → ACTIVE

When:

``` text
useful
AND
relevant beyond immediate operation
```

### ACTIVE → PASSIVE

When:

``` text
repeatedly useful
OR
high importance
OR
explicitly validated
OR
strong supporting evidence
```

### PASSIVE → SUPER-PASSIVE

When:

``` text
repeatedly validated
AND
stable
AND
high confidence
AND
broad applicability
AND
few contradictions
```

Time alone should not promote a memory.

------------------------------------------------------------------------

# 62. Demotion

Memories can also move downward.

Possible reasons:

-   stale
-   unused
-   superseded
-   contradicted
-   low relevance
-   failed application
-   scope changed
-   confidence decreased

Example:

``` text
SUPER-PASSIVE
      ↓
PASSIVE
      ↓
ACTIVE
      ↓
ARCHIVED
```

The system is therefore adaptive in both directions.

------------------------------------------------------------------------

# 63. Promotion of Scope

Lifecycle and scope should evolve independently.

Example:

``` text
Project Memory
    ↓
validated in another project
    ↓
Cross-Project Memory
    ↓
validated repeatedly
    ↓
Organization Memory
```

This should be a separate process from:

``` text
Active → Passive
```

A memory can become more durable without becoming more global.

------------------------------------------------------------------------

# 64. Consolidation Engine

A background consolidation process can periodically analyze memories.

Conceptually:

``` text
recent memories
      ↓
duplicate detection
      ↓
similarity clustering
      ↓
pattern detection
      ↓
contradiction detection
      ↓
relationship extraction
      ↓
memory synthesis
      ↓
compression
      ↓
promotion / demotion
```

This should not necessarily happen synchronously during every
interaction.

------------------------------------------------------------------------

# 65. Memory "Dreaming"

A future extension could allow the memory system to perform offline
replay.

During low activity:

``` text
recent experiences
      ↓
replay
      ↓
compare
      ↓
cluster
      ↓
discover relationships
      ↓
discover patterns
      ↓
generate candidate memories
      ↓
validate
      ↓
consolidate
```

This is analogous to the conceptual idea of "dreaming":

> using previously collected experiences to discover higher-order
> patterns.

It should remain a metaphor rather than a claim of biological
equivalence.

------------------------------------------------------------------------

# 66. Candidate Memories

Newly inferred memories should not immediately become trusted knowledge.

Use states such as:

``` text
CANDIDATE
VALIDATING
ESTABLISHED
CONSOLIDATED
SUPERSEDED
ARCHIVED
```

Example:

``` text
Pattern discovered
      ↓
Candidate
      ↓
more evidence
      ↓
Validated
      ↓
Established
      ↓
repeated success
      ↓
Consolidated
```

This protects against hallucinated or weakly supported memories.

------------------------------------------------------------------------

# 67. Human Validation

Important memories can be explicitly validated.

Example:

``` text
Memory:

"Architecture B is preferred for this workload."

Confidence: 0.81

[Confirm]
[Reject]
[Modify]
```

A human confirmation becomes provenance:

``` text
validated_by = human
validated_at = timestamp
validation_source = explicit_confirmation
```

Human-approved decisions can receive stronger trust, while still
remaining versioned and traceable.

------------------------------------------------------------------------

# 68. Confidence vs Strength

These should never be treated as the same thing.

### Strength

> How strongly is this memory represented/reinforced?

### Confidence

> How likely is this memory to be correct?

Example:

``` text
Strength = 0.94
Confidence = 0.51
```

This could mean:

> The system remembers this very strongly but is uncertain whether it is
> actually true.

Conversely:

``` text
Strength = 0.45
Confidence = 0.98
```

could mean:

> The system is highly confident in the fact but rarely needs it.

------------------------------------------------------------------------

# 69. Importance vs Relevance

These are also different.

### Importance

How valuable is the information generally?

### Relevance

How useful is it for the current context?

Example:

``` text
Global security policy:

importance = 0.98
current relevance = 0.05
```

It is extremely important but irrelevant to the current question.

Another memory:

``` text
Current debugging error:

importance = 0.42
current relevance = 0.99
```

It is not globally important, but it is extremely relevant right now.

------------------------------------------------------------------------

# 70. Applicability

Applicability describes how broadly a memory can transfer.

Example:

``` text
Project-specific workaround:

strength = 0.91
confidence = 0.94
applicability = 0.18
```

versus:

``` text
General engineering principle:

strength = 0.82
confidence = 0.91
applicability = 0.93
```

This prevents local hacks from becoming global knowledge.

------------------------------------------------------------------------

# 71. Retrieval Architecture

A retrieval system can operate in stages:

``` text
                 QUERY
                   │
                   ↓
          Context understanding
                   │
                   ↓
            Scope selection
                   │
                   ↓
          Candidate retrieval
             /     |      \
          Vector  Graph  Metadata
             \     |      /
              \    |     /
                Ranking
                   │
                   ↓
          Contradiction check
                   │
                   ↓
            Deduplication
                   │
                   ↓
          Context compression
                   │
                   ↓
            Budget control
                   │
                   ↓
            Memory context
```

------------------------------------------------------------------------

# 72. Context Locality

Memory should not indiscriminately search everything.

Given:

``` text
Current Task
```

the system can search outward:

``` text
Task
 ↓
Meeting
 ↓
Session
 ↓
Project
 ↓
Team
 ↓
Organization
 ↓
Global
```

Only expand outward when necessary.

This gives memory a concept of **locality**.

------------------------------------------------------------------------

# 73. Progressive Disclosure

Retrieved memory should be available in layers.

### Level 1 --- Summary

``` text
Architecture X was rejected due to complexity.
```

### Level 2 --- Context

``` text
Rejected during architecture review.
Three concerns were raised.
```

### Level 3 --- Evidence

``` text
Decision record
Benchmark
Discussion
```

### Level 4 --- Raw history

``` text
Full transcript
Logs
Tool calls
```

The system should start shallow and go deeper only when needed.

------------------------------------------------------------------------

# 74. Memory Compression

A large experience may evolve into:

``` text
Full conversation
       ↓
Important events
       ↓
Decisions
       ↓
Facts
       ↓
Patterns
       ↓
Semantic memory
       ↓
Durable principle
```

The original experience should remain available through provenance.

Therefore:

``` text
compressed memory
+
source memory
```

is preferable to forcing every retrieval to operate over raw history.

------------------------------------------------------------------------

# 75. Context Budget

Memory retrieval should explicitly consider token cost.

Example:

``` text
Context Budget = 8,000 tokens

System instructions       1,500
Current task               1,500
Working memory             1,500
Relevant memories          2,000
Evidence                   1,000
Reserve                      500
```

The memory system should optimize for:

``` text
information value / token cost
```

rather than simply returning top-K memories.

------------------------------------------------------------------------

# 76. Memory Retrieval Should Explain Itself

Every retrieval can include:

``` text
memory
why_retrieved
confidence
scope
strength
evidence
related_memories
warnings
```

Example:

``` json
{
  "memory": "Use approach B for high concurrency",
  "why_retrieved": "Current workload matches 4 previous successful cases",
  "confidence": 0.93,
  "strength": 0.86,
  "scope": "project",
  "evidence_count": 8,
  "warnings": [
    "Failed under low-memory configuration"
  ]
}
```

------------------------------------------------------------------------

# 77. Retrieval Is Not Proof

This is another core rule.

A memory being retrieved does not mean it is true.

A memory being frequently retrieved does not mean it is important.

A memory being strong does not mean it is globally applicable.

A memory being old does not mean it is permanent.

Therefore:

``` text
retrieval
≠
truth
```

and:

``` text
frequency
≠
importance
```

and:

``` text
strength
≠
confidence
```

------------------------------------------------------------------------

# 78. Contradiction Resolution

When conflicting memories are found, consider:

``` text
scope
time
confidence
provenance
source quality
validity
specificity
human validation
```

Possible outcomes:

``` text
CONTRADICTS
SUPERSEDES
EXCEPTION_TO
CONTEXTUAL_VARIANT
TEMPORAL_VARIANT
```

The system should preserve both sides when both are historically valid.

------------------------------------------------------------------------

# 79. Memory Metadata

A conceptual memory object:

``` text
Memory
├── id
├── content
├── summary
│
├── type
├── scope
├── lifecycle_state
│
├── strength
├── confidence
├── importance
├── relevance
├── accessibility
├── applicability
│
├── created_at
├── updated_at
├── last_accessed_at
├── last_reinforced_at
├── valid_from
├── valid_until
│
├── access_count
├── successful_use_count
├── failed_use_count
│
├── provenance
├── evidence
├── relationships
│
├── parent_memory
├── derived_from
├── supersedes
├── superseded_by
├── contradictions
│
└── embedding / retrieval metadata
```

This is conceptual rather than a final database schema.

------------------------------------------------------------------------

# 80. Memory Events

The system should preserve memory history.

Example events:

``` text
CREATED
RETRIEVED
USED
SUCCESS
FAILURE
REINFORCED
DECAYED
PROMOTED
DEMOTED
MERGED
SPLIT
CONSOLIDATED
GENERALIZED
CONTRADICTED
SUPERSEDED
REACTIVATED
ARCHIVED
RESTORED
```

A memory should therefore have both:

``` text
current state
```

and:

``` text
historical event stream
```

------------------------------------------------------------------------

# 81. Example Memory Event

``` json
{
  "event": "memory.reinforced",
  "memory_id": "mem_123",
  "timestamp": "2026-10-08T14:00:00Z",

  "previous_strength": 0.71,
  "new_strength": 0.78,

  "reason": "successful_application",

  "context_id": "ctx_456",
  "evidence_id": "obs_982"
}
```

This makes memory changes auditable.

------------------------------------------------------------------------

# 82. Graph Event

Likewise:

``` json
{
  "event": "memory.edge_strengthened",

  "source": "mem_A",
  "target": "mem_B",

  "relationship": "SUCCESSFUL_WITH",

  "previous_strength": 0.44,
  "new_strength": 0.57,

  "reason": "successful_joint_retrieval"
}
```

------------------------------------------------------------------------

# 83. Storage Architecture

A practical implementation can separate storage concerns.

``` text
                    MEMORY SERVICE
                         │
         ┌───────────────┼────────────────┐
         │               │                │
         ▼               ▼                ▼
    PostgreSQL       Vector Index      Graph Layer
         │               │                │
    state/events      semantic         relations
    metadata         retrieval         traversal
         │
         ▼
    Object Storage / Git
         │
    raw evidence
    transcripts
    documents
    artifacts
```

PostgreSQL can hold:

-   memory metadata
-   lifecycle state
-   events
-   scores
-   provenance references
-   permissions

Vector storage can handle semantic retrieval.

Graph storage can handle relationship traversal when graph scale
justifies it.

Object storage or Git can hold large source artifacts.

------------------------------------------------------------------------

# 84. Example Relational Model

``` sql
CREATE TABLE memories (
    id UUID PRIMARY KEY,

    content TEXT NOT NULL,
    summary TEXT,

    type TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL,

    scope_type TEXT NOT NULL,
    scope_id UUID,

    strength FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    importance FLOAT NOT NULL,
    relevance FLOAT NOT NULL,
    accessibility FLOAT NOT NULL,
    applicability FLOAT NOT NULL,

    decay_rate FLOAT NOT NULL,

    retrieval_count INT DEFAULT 0,
    successful_use_count INT DEFAULT 0,
    failed_use_count INT DEFAULT 0,

    created_at TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP,
    last_reinforced_at TIMESTAMP,

    valid_from TIMESTAMP,
    valid_until TIMESTAMP,

    metadata JSONB
);
```

------------------------------------------------------------------------

# 85. Relationship Model

``` sql
CREATE TABLE memory_edges (
    id UUID PRIMARY KEY,

    source_memory_id UUID NOT NULL,
    target_memory_id UUID NOT NULL,

    relationship_type TEXT NOT NULL,

    strength FLOAT NOT NULL,
    confidence FLOAT NOT NULL,

    activation_count INT DEFAULT 0,
    successful_activation_count INT DEFAULT 0,

    created_at TIMESTAMP NOT NULL,
    last_activated_at TIMESTAMP,

    metadata JSONB
);
```

------------------------------------------------------------------------

# 86. Memory Event Model

``` sql
CREATE TABLE memory_events (
    id UUID PRIMARY KEY,

    memory_id UUID NOT NULL,

    event_type TEXT NOT NULL,

    timestamp TIMESTAMP NOT NULL,

    previous_state JSONB,
    new_state JSONB,

    reason TEXT,

    evidence_id UUID,

    metadata JSONB
);
```

This creates a complete memory history.

------------------------------------------------------------------------

# 87. A Memory Is More Like a Living Object

The conceptual object is:

``` text
                    ┌──────────────────┐
                    │      MEMORY      │
                    ├──────────────────┤
                    │ Content          │
                    │ Type             │
                    │ Scope            │
                    │ Lifecycle        │
                    │ Strength         │
                    │ Confidence       │
                    │ Accessibility    │
                    │ Importance       │
                    │ Applicability    │
                    │ Provenance       │
                    │ Evidence         │
                    │ Relationships    │
                    │ History          │
                    └──────────────────┘
```

It changes continuously.

------------------------------------------------------------------------

# 88. Example: Human-Like Memory Evolution

Consider meeting someone called Alex.

### First encounter

``` text
"I met Alex today."
```

Episodic memory.

### Second encounter

``` text
"Alex works in design."
```

Semantic memory.

### Repeated interactions

``` text
"Alex prefers visual explanations."
```

Stable semantic/preference memory.

### Repeated successful communication

``` text
"When explaining something to Alex,
use visual examples."
```

Procedural memory.

### Years without interaction

``` text
Accessibility ↓
```

The memory becomes distant.

### Working together again

``` text
old memory
    ↓
retrieved
    ↓
reactivated
```

The memory becomes active again.

This single example demonstrates:

``` text
episodic
semantic
preference
procedural
consolidation
decay
archive
reactivation
```

------------------------------------------------------------------------

# 89. Example: Preference Evolution

Initial experience:

``` text
"I tried cold brew."
```

Experience:

``` text
"I didn't like it."
```

Decision:

``` text
"I won't order cold brew."
```

Stable preference:

``` text
"Don't recommend cold brew."
```

The system transformed:

``` text
experience
    ↓
observation
    ↓
decision
    ↓
preference
    ↓
procedural recommendation rule
```

Memory is therefore not static.

It **changes representation as understanding improves**.

------------------------------------------------------------------------

# 90. Example: Engineering Lesson

Initial experience:

``` text
Incident:
Connection pool exhausted.
```

Investigation:

``` text
Pool size was too small.
```

Fix:

``` text
Increase pool size.
```

Successful outcome:

``` text
Incident resolved.
```

Second incident:

``` text
Same pattern occurs.
```

The memory becomes stronger.

After multiple projects:

``` text
High-concurrency systems require
connection pool sizing based on expected concurrency.
```

Now the system has transformed:

``` text
event
 ↓
fact
 ↓
pattern
 ↓
lesson
 ↓
general principle
```

------------------------------------------------------------------------

# 91. The Memory System as a Learning Loop

The complete learning loop is:

``` text
                 EXPERIENCE
                     ↓
                 OBSERVATION
                     ↓
                   MEMORY
                     ↓
                 RETRIEVAL
                     ↓
                    USE
                     ↓
                  OUTCOME
                /         \
           SUCCESS        FAILURE
              ↓              ↓
        REINFORCEMENT      PENALTY
              ↓              ↓
          STRENGTH ↑      CONFIDENCE ↓
              ↓
        CONSOLIDATION
              ↓
         GENERALIZATION
              ↓
       DURABLE KNOWLEDGE
```

This is the central technical mechanism.

------------------------------------------------------------------------

# 92. The Memory System as a Graph

At the same time:

``` text
                    EXPERIENCE
                         │
                         ▼
                    EPISODIC A
                    /         \
             supports          causes
                  /               \
                 ▼                 ▼
            SEMANTIC B          EVENT C
                 │                 │
             generalizes        derived from
                 │                 │
                 ▼                 ▼
             LESSON D          DECISION E
                 │
             used with
                 │
                 ▼
             PROCEDURE F
```

The lifecycle and graph operate together.

------------------------------------------------------------------------

# 93. The Memory System as a Geography

At another level:

``` text
                         GLOBAL
                           │
                     ORGANIZATION
                           │
                         TEAM
                           │
                        PROJECT
                           │
                        SESSION
                           │
                         MEETING
                           │
                          TASK
```

The same memory system therefore has:

``` text
TIME
+
TYPE
+
SPACE/SCOPE
+
RELATIONSHIPS
```

This is why memory is better modeled as a multidimensional system.

------------------------------------------------------------------------

# 94. Three Major Conceptual Directions

## Direction 1 --- Memory Is Not Storage

Core thesis:

> **Memory is a lifecycle, not merely a storage mechanism.**

Focus:

``` text
formation
retrieval
reinforcement
decay
consolidation
archival
reactivation
```

Potential statement:

> Memory is not where information lives. Memory is how information
> changes over time.

------------------------------------------------------------------------

## Direction 2 --- Memory Has Geography

Core thesis:

> **Memory exists in a space of scope, proximity, depth and
> relationships.**

Memory has:

``` text
location
scope
lifetime
type
relationships
accessibility
```

Example:

``` text
Current
  ↓
Session
  ↓
Project
  ↓
Organization
  ↓
Global
  ↓
Archive
```

Potential statement:

> Memory has topology.

------------------------------------------------------------------------

## Direction 3 --- Memory Should Forget

Core thesis:

> **Useful memory requires selective forgetting.**

The objective is not:

``` text
maximum retention
```

It is:

``` text
maximum useful retention
```

Important distinctions:

``` text
forgetting ≠ deletion

archive ≠ deletion

low accessibility ≠ absence

old ≠ unimportant

frequent ≠ important
```

Potential statement:

> A memory does not necessarily need to disappear. It can simply become
> distant.

------------------------------------------------------------------------

# 95. The Strongest Hybrid Model

The strongest conceptual model combines all three:

> **Memory is a dynamic lifecycle that exists across different scopes
> and relationships, and forgetting is part of that lifecycle.**

``` text
                       EXPERIENCE
                           ↓
                       FORMATION
                           ↓
                        WORKING
                           ↓
                         ACTIVE
                           ↓
                     CONSOLIDATION
                           ↓
                       PERSISTENT
                           ↓
                         DECAY
                           ↓
                        ARCHIVE
                           │
                           │
                      relevance
                           │
                           ▼
                      REACTIVATION
                           │
                           ▼
                         ACTIVE
```

Meanwhile, every memory exists within:

``` text
TYPE
SCOPE
GRAPH
PROVENANCE
EVIDENCE
```

------------------------------------------------------------------------

# 96. Important Conceptual Distinctions

These should become explicit design principles.

``` text
Retrieval ≠ Truth

Frequency ≠ Importance

Strength ≠ Confidence

Importance ≠ Relevance

Long-term ≠ Global

Old ≠ Permanent

Archive ≠ Delete

Decay ≠ Destruction

Memory ≠ Evidence

Consolidation ≠ Summarization

Synthesis ≠ Retrieval

Scope ≠ Lifecycle

Association ≠ Similarity
```

These distinctions prevent the system from collapsing into a simplistic
vector database.

------------------------------------------------------------------------

# 97. Open Questions

The architecture should intentionally leave several areas open for
experimentation.

## Formation

-   What qualifies as a memory?
-   Does every interaction create a candidate?
-   What should be discarded immediately?
-   How much should an LLM participate in extraction?

## Classification

-   Can a memory have multiple types?
-   Can an episodic memory become semantic?
-   Can one memory represent both an event and a lesson?

## Consolidation

-   When should memories merge?
-   How should repeated experiences be clustered?
-   When does a pattern become a reliable lesson?
-   How should consolidation preserve provenance?

## Reinforcement

-   How much should successful use increase strength?
-   How should failure affect confidence?
-   How should human confirmation be weighted?

## Decay

-   What determines decay rate?
-   Should different memory types decay differently?
-   Should decay affect confidence or only accessibility?
-   How reversible should decay be?

## Retrieval

-   Should retrieval activate related memories?
-   How far should graph traversal go?
-   How should scope constrain retrieval?
-   How should token cost affect ranking?

## Generalization

-   How many independent contexts are required?
-   When can project knowledge become organizational knowledge?
-   How do we detect false generalization?

## Contradictions

-   Is this a contradiction or contextual exception?
-   Which memory is newer?
-   Which source is more trustworthy?
-   Should both memories remain?

## Archival

-   When does a memory become archival?
-   Should archival memories remain searchable?
-   How should explicit historical search behave?

------------------------------------------------------------------------

# 98. Initial Technical Principles

Before implementing anything, the system should preserve these
principles.

### Principle 1

**Memory is a lifecycle, not a table.**

### Principle 2

**Memory type and memory lifecycle are different dimensions.**

### Principle 3

**Scope and lifecycle are different dimensions.**

### Principle 4

**Strength and confidence are different dimensions.**

### Principle 5

**Retrieval should not automatically reinforce memory.**

### Principle 6

**Successful use should be stronger reinforcement than retrieval
frequency.**

### Principle 7

**Forgetting should primarily affect accessibility before destroying
information.**

### Principle 8

**Every durable memory should have provenance.**

### Principle 9

**Contradictions should be represented, not silently overwritten.**

### Principle 10

**Project-specific memories should not automatically become global
knowledge.**

### Principle 11

**Consolidated memories should retain lineage to their evidence.**

### Principle 12

**Memory retrieval should be context-budget aware.**

### Principle 13

**Graph relationships should be first-class objects.**

### Principle 14

**Memory should be observable and explainable.**

### Principle 15

**The UI should represent the same underlying memory state rather than
maintaining a separate visualization model.**

------------------------------------------------------------------------

# 99. Minimal Conceptual Architecture

At the highest level:

``` text
                         MEMORY SYSTEM
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
     FORMATION            RETRIEVAL          CONSOLIDATION
          │                   │                   │
          ▼                   ▼                   ▼
     CLASSIFICATION       RANKING             SYNTHESIS
          │                   │                   │
          ▼                   ▼                   ▼
       SCORING             CONTEXT             GENERALIZATION
          │                ASSEMBLY                │
          └───────────────────┼───────────────────┘
                              │
                              ▼
                       MEMORY GRAPH
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
              EVENTS       EVIDENCE      HISTORY
```

------------------------------------------------------------------------

# 100. The Ideal End State

The final system should feel less like:

``` text
Vector Database
+
Metadata
+
RAG
```

and more like:

``` text
                    ┌─────────────────────┐
                    │   MEMORY UNIVERSE   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
           LIFECYCLE          GRAPH            SCOPE
              │                │                │
              │                │                │
      Working → Active       A → B          Task → Global
              │                │                │
          Consolidate       B → C             │
              │                │                │
          Persistent        C → D             │
              │                │                │
            Decay              │               │
              │                │                │
           Archive             │               │
              │                │               │
        Reactivation ──────────┴───────────────┘
```

The system continuously answers:

``` text
What happened?

What do I know?

How do I do this?

What is related?

Why do I believe this?

Where does this apply?

How important is it?

How confident am I?

Has this been useful?

Has it failed?

Should I remember it?

Should I forget it?

Should I make it more durable?

Should I generalize it?

Could an old memory be useful again?
```

------------------------------------------------------------------------

# 101. Final Mental Model

The entire concept can be reduced to one system:

``` text
                         EXPERIENCE
                              │
                              ▼
                         FORMATION
                              │
                              ▼
                         WORKING
                              │
                              ▼
                          ACTIVE
                              │
                     ┌────────┴────────┐
                     │                 │
                SUCCESSFUL          UNUSED
                     │                 │
                     ▼                 ▼
                REINFORCEMENT        DECAY
                     │                 │
                     ▼                 ▼
                CONSOLIDATION       ARCHIVE
                     │                 │
                     ▼                 │
                 PERSISTENT            │
                     │                 │
                     ▼                 │
                GENERALIZATION         │
                     │                 │
                     ▼                 │
                 DEEP MEMORY           │
                     │                 │
                     └───────┬─────────┘
                             │
                       RELEVANT AGAIN
                             │
                             ▼
                         REACTIVATE
                             │
                             ▼
                           ACTIVE
```

And around every memory:

``` text
                 ┌──────────────────┐
                 │      MEMORY      │
                 ├──────────────────┤
                 │ Content          │
                 │ Type             │
                 │ Scope            │
                 │ Lifecycle        │
                 │ Strength         │
                 │ Confidence       │
                 │ Accessibility    │
                 │ Importance       │
                 │ Applicability    │
                 │ Provenance       │
                 │ Evidence         │
                 │ Relationships    │
                 │ History          │
                 └──────────────────┘
```

The memory graph connects these objects.

The lifecycle changes them.

Retrieval activates them.

Successful use reinforces them.

Failure challenges them.

Consolidation compresses them.

Generalization broadens them.

Decay makes them distant.

Archival preserves them without keeping them constantly accessible.

Reactivation brings them back.

------------------------------------------------------------------------

# 102. The Central Idea

The system should ultimately be built around this principle:

> **A good memory system does not remember everything. It learns what
> deserves to remain accessible.**

And a deeper formulation:

> **Memory is the controlled transformation of experience into
> increasingly durable, increasingly abstract, and selectively
> accessible knowledge.**

The goal is therefore not:

``` text
STORE EVERYTHING
```

but:

``` text
EXPERIENCE
    ↓
UNDERSTAND
    ↓
REMEMBER
    ↓
USE
    ↓
LEARN
    ↓
REINFORCE
    ↓
CONSOLIDATE
    ↓
GENERALIZE
    ↓
FORGET WHAT NO LONGER MATTERS
    ↓
REACTIVATE WHAT MATTERS AGAIN
```

That is the conceptual foundation of the memory system.
