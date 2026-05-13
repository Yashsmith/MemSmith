# Product Requirements Document: MemSmith v3

**Project:** MemSmith  
**Version:** 3.0 (The SQLite Pivot)  
**Author:** Yashsmith Shah  
**Date:** May 13, 2026  
**Status:** Active Development  

---

## Preface: What Changed and Why

The v2 PRD made one critical mistake: it tried to compete with Redis on Redis's terms. It claimed `<5ms` latency as a win when Redis ships `<1ms` in C. It framed MemSmith as "production-grade infrastructure" when the actual underserved user is a developer who shouldn't have to think about infrastructure at all.

This PRD corrects that. MemSmith v3 is not a Redis replacement. It is the **SQLite of multi-agent state** — zero-infra, embedded, Python-native, and so easy to start that the getting-started experience is the product. The technical work is identical. The framing and API surface are completely different.

---

## 1. The One-Line Pitch

> **MemSmith: Shared state for multi-agent AI systems. No server. No config. Just `pip install`.**

---

## 2. The Exact User

Before anything else, this section defines the specific human MemSmith is built for. Every feature decision traces back to this person.

**Primary User: "Hackathon Arjun"**

- Final-year CS student or 1–2 year junior dev
- Building a multi-agent pipeline (CrewAI, OpenAI Agents SDK, LangGraph, or raw API calls)
- Project: hackathon, portfolio piece, tutorial, or internal demo
- Pain: two agents overwriting each other's state, or a 40-minute run crashes and everything is lost
- Won't do: install Docker, configure Redis, read 3 pages of infra docs for a side project
- Will do: `pip install memsmith` if the README solves their exact problem in the first scroll

**Secondary User: "Tutorial Priya"**

- Developer advocate, blogger, or technical writer building a multi-agent tutorial
- Needs a state layer she can demo without 15 lines of setup boilerplate
- Will embed MemSmith in every tutorial she writes if the API reads like English
- Her tutorials become the distribution channel. Every code block in every tutorial is a free advertisement.

**Who MemSmith is NOT for (yet):**

- Production SaaS companies with DevOps teams (they have Redis and should use it)
- Teams with >10 concurrent agents in production (they need Redis Cluster, full stop)
- Anyone with a managed infra budget (Mem0, Zep, LangGraph Platform exist for them)

---

## 3. The Problem (Stated From Arjun's Perspective)

Arjun is building a research pipeline: a Researcher agent that finds papers and a Writer agent that synthesizes them. He has three problems he's Googling right now:

**Problem 1: Race Conditions**
The Writer starts before the Researcher finishes. He passes state through function arguments, but the moment he has 3+ agents, this falls apart. He's seen people suggest Redis but he's not going to install Redis for a prototype.

**Problem 2: Crash Volatility**
His pipeline runs for 40 minutes. It crashes at minute 38 — a rate limit error, a network blip, anything. Everything is gone. He restarts from zero.

**Problem 3: Invisible Failures**
When something goes wrong, he has no idea which agent wrote what and when. He prints `state` to the terminal like a caveman. He cannot tell if Agent A read stale state or if Agent B wrote twice.

Redis solves all three. But Redis requires 20 minutes of setup Arjun doesn't want to spend. **MemSmith solves all three in 2 minutes.**

---

## 4. The Solution

MemSmith is a **Python-native, embedded, agent-aware state engine.** It runs in the same process as your agents (or as a lightweight background process for multi-process setups). It has no server to configure, no Docker image to pull, no external dependency to manage.

The primary interface is a **Python SDK** — not an HTTP API. HTTP endpoints exist for multi-process and multi-machine setups, but the default experience is importing a library.

### The Three Pillars

**1. Zero Infrastructure**
`pip install memsmith`. That's it. `memsmith.session()` starts an in-memory state store in the current process. There is no step 2.

**2. Agent-Native API**
The API is designed around agents, not around keys. Instead of `SET namespace:key value`, you write `session.agent("researcher").push("papers", data)`. Instead of writing a polling loop, you write `session.agent("writer").wait_for("researcher", "papers")`. The semantics of your agent system are visible in the code.

**3. Debuggability as a First-Class Feature**
`memsmith watch` opens a live TUI showing every agent's state in real-time. `memsmith dump` produces a human-readable, timestamped replay of every state transition in the session. This is the feature Arjun actually needs and nobody has built cleanly. It makes MemSmith the tool you reach for the moment something goes wrong.

---

## 5. API Design (The Core of Everything)

The API is the product. It needs to read like English and make Redis feel verbose by comparison.

### 5.1 In-Process Mode (Primary)

```python
import memsmith

# Start a session — zero config, zero infra
session = memsmith.session("research_pipeline")

# In your Researcher agent
async def researcher_agent(session):
    papers = await fetch_papers()
    session.agent("researcher").push("papers", papers)
    session.agent("researcher").push("status", "done")

# In your Writer agent  
async def writer_agent(session):
    # Blocks until researcher pushes "papers" — no polling, no sleep()
    papers = await session.agent("writer").wait_for("researcher", key="papers")
    draft = await write_draft(papers)
    session.agent("writer").push("draft", draft)

# Broadcast to all agents
session.broadcast("pipeline_complete", payload={"total_papers": 47})

# Human-readable checkpoint — writes a snapshot to disk
session.checkpoint("after_research_phase")

# On crash recovery — resume from last checkpoint
session = memsmith.resume("research_pipeline")
```

### 5.2 Multi-Process Mode (Secondary)

When agents run in separate processes or machines, MemSmith runs as a lightweight background process:

```bash
memsmith serve --port 7117  # starts in <100ms
```

```python
# Each agent process connects to the same session
session = memsmith.connect("research_pipeline", host="localhost:7117")

# API is identical to in-process mode
session.agent("researcher").push("papers", papers)
```

### 5.3 The Lock API

```python
# Acquire a lock — agent-aware, not key-aware
async with session.agent("writer").lock("draft_section_1", timeout_ms=5000):
    # only one agent writes at a time
    session.agent("writer").push("draft_section_1", content)

# Non-blocking check
lock = session.agent("editor").try_lock("draft_section_1")
if lock.held_by:
    print(f"Section locked by {lock.held_by}, waiting...")
```

### 5.4 The Debuggability API

```python
# Get full history for a session
history = session.history()
# Returns: [{timestamp, agent, operation, key, value_preview}, ...]

# Export a human-readable replay
session.export("pipeline_replay.json")

# From CLI
# memsmith dump research_pipeline
# memsmith watch research_pipeline   (live TUI)
```

### 5.5 What the API Deliberately Does NOT Have

- No raw `GET /key` and `SET /key` at the primary surface. Those exist internally but are not the API Arjun uses.
- No configuration files. No YAML. No environment variables required.
- No concept of "namespaces" that the user has to manage. The `session` and `agent` context handles that.

---

## 6. The Killer Feature: `memsmith watch`

This single feature is why someone posts the GIF on Twitter.

`memsmith watch` is a terminal UI (built with Textual or Rich) that shows:

```
┌─────────────────────────────── MemSmith Watch ───────────────────────────────┐
│  Session: research_pipeline          Runtime: 00:02:34          Agents: 3    │
├──────────────────┬──────────────────┬──────────────────┬──────────────────── │
│   researcher     │    writer        │    editor        │    BROADCAST        │
├──────────────────┼──────────────────┼──────────────────┼──────────────────── │
│ ✅ papers [47]   │ ⏳ wait_for...   │                  │                     │
│ ✅ status: done  │                  │                  │                     │
│                  │ ✅ draft [3.2kb] │ 🔒 lock: draft   │                     │
│                  │                  │ ✅ edits [12]    │                     │
│                  │                  │                  │ 📢 pipeline_done    │
└──────────────────┴──────────────────┴──────────────────┴──────────────────── │

  [ q: quit   p: pause   d: dump   c: clear ]
```

Each column is an agent. Each row is a state event. Colors:
- 🟢 Green: successful write
- 🔵 Blue: successful read
- 🟡 Yellow: lock acquired
- 🔴 Red: lock conflict / timeout
- 📢 Broadcast events shown in right column

**Why this matters:** Every other debuggability tool for agents is a logging library that produces walls of text. This is visual, real-time, and structured. Arjun sees exactly which agent did what and when. He screencaps it. He posts it. That's the distribution flywheel.

---

## 7. Technical Architecture

The architecture from v2 is preserved. The implementation changes are minimal. The framing changes completely.

### 7.1 Core Engine

```
memsmith/
├── core/
│   ├── session.py          # Session object — primary user entrypoint
│   ├── agent_context.py    # Agent-scoped API (push, wait_for, lock)
│   ├── shard_store.py      # Sharded in-memory dict (16 shards, asyncio.Lock per shard)
│   ├── wal.py              # Async Write-Ahead Log — background thread, append-only
│   ├── checkpoint.py       # Snapshot serialization using msgspec + msgpack
│   └── recovery.py         # Resume from checkpoint or WAL replay
├── server/
│   ├── app.py              # FastAPI app — only used in multi-process mode
│   ├── routes.py           # HTTP endpoints (internal, not primary API)
│   └── ws.py               # WebSocket endpoint for `memsmith watch` remote mode
├── cli/
│   ├── main.py             # Click CLI
│   ├── watch.py            # Textual TUI for live state visualization
│   └── dump.py             # Human-readable session replay export
└── integrations/
    ├── langchain.py        # MemSmithCheckpointer for LangGraph
    ├── crewai.py           # MemSmithMemory for CrewAI
    └── openai_sdk.py       # MemSmithStore for OpenAI Agents SDK
```

### 7.2 Sharded Store (Unchanged from v2, renamed for clarity)

16 asyncio.Lock-partitioned shards. Agent A writing to shard 3 does not block Agent B writing to shard 11. Hash function: `shard_id = hash(key) % 16`.

```python
class ShardStore:
    def __init__(self, num_shards: int = 16):
        self._shards: list[dict] = [{} for _ in range(num_shards)]
        self._locks: list[asyncio.Lock] = [asyncio.Lock() for _ in range(num_shards)]
    
    def _shard(self, key: str) -> int:
        return hash(key) % len(self._shards)
    
    async def set(self, key: str, value: Any) -> None:
        shard = self._shard(key)
        async with self._locks[shard]:
            self._shards[shard][key] = value
            await self._wal.append(op="SET", key=key, value=value)
```

### 7.3 Serialization

msgspec with Msgpack encoding. Binary wire format, C-speed serialization. For checkpoints written to disk, human-readable JSON is also produced alongside binary so `memsmith dump` doesn't require deserialization.

```python
import msgspec

encoder = msgspec.msgpack.Encoder()
decoder = msgspec.msgpack.Decoder()

# Encode
binary = encoder.encode({"agent": "researcher", "key": "papers", "value": [...]})

# Decode  
data = decoder.decode(binary)
```

### 7.4 Write-Ahead Log

A background thread (not the main event loop) handles all disk writes. The main thread enqueues log entries into an `asyncio.Queue`. The WAL thread drains the queue and appends to an append-only binary file. On startup, MemSmith replays unprocessed WAL entries before accepting new connections.

```python
class WAL:
    def __init__(self, path: str):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._path = path
        self._encoder = msgspec.msgpack.Encoder()
    
    async def append(self, op: str, key: str, value: Any) -> None:
        # Non-blocking — enqueue and return immediately
        entry = WALEntry(
            timestamp=time.time_ns(),
            op=op, key=key, value=value
        )
        await self._queue.put(entry)
    
    async def _flush_worker(self):
        # Runs in background — drains queue and writes to disk
        async with aiofiles.open(self._path, "ab") as f:
            while True:
                entry = await self._queue.get()
                await f.write(self._encoder.encode(entry))
```

### 7.5 `wait_for` Implementation

This is the most important API primitive. It uses an asyncio.Event internally, not polling.

```python
async def wait_for(self, source_agent: str, key: str, timeout_ms: int = 30000) -> Any:
    full_key = f"{source_agent}:{key}"
    event = self._session._get_or_create_event(full_key)
    
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout_ms / 1000)
    except asyncio.TimeoutError:
        raise MemSmithTimeoutError(
            f"Timed out waiting for agent '{source_agent}' to push '{key}'"
        )
    
    return self._session.store.get(full_key)
```

When `researcher.push("papers", data)` is called, it sets the asyncio.Event for `"researcher:papers"`, and any agent awaiting that event is immediately unblocked. Zero polling. Zero sleep loops.

### 7.6 The Server Mode (FastAPI + uvloop)

Only activated when `memsmith serve` is run. Uses FastAPI + Uvicorn + uvloop. HTTP endpoints mirror the Python SDK. WebSocket endpoint powers the remote `memsmith watch` mode.

```python
# uvloop is a one-line config change
import uvloop
uvloop.install()  # replaces default asyncio event loop globally
```

---

## 8. Functional Requirements

| ID | Feature | Description | Priority | Phase |
|---|---|---|---|---|
| F-01 | `session()` in-process | Zero-config session start, no network call | P0 | 1 |
| F-02 | `agent().push()` | Write state scoped to an agent identity | P0 | 1 |
| F-03 | `agent().get()` | Read state scoped to an agent | P0 | 1 |
| F-04 | `agent().wait_for()` | Event-based blocking wait, no polling | P0 | 1 |
| F-05 | `agent().lock()` | Async context manager for atomic write sections | P0 | 1 |
| F-06 | Async WAL | Background append-only log, non-blocking | P0 | 2 |
| F-07 | `session.checkpoint()` | Explicit snapshot to disk (msgpack + JSON) | P0 | 2 |
| F-08 | `memsmith resume()` | Recover session state from last checkpoint | P0 | 2 |
| F-09 | `memsmith watch` TUI | Live per-agent state visualization in terminal | P1 | 3 |
| F-10 | `memsmith dump` | Human-readable timestamped session replay | P1 | 3 |
| F-11 | `memsmith serve` | Multi-process HTTP + WebSocket server mode | P1 | 3 |
| F-12 | `session.broadcast()` | Fan-out event to all agents in session | P1 | 3 |
| F-13 | Semantic TTL | Auto-expire state keys after inactivity | P2 | 4 |
| F-14 | LangGraph integration | `MemSmithCheckpointer` drop-in for LangGraph | P2 | 4 |
| F-15 | CrewAI integration | `MemSmithMemory` drop-in for CrewAI | P2 | 4 |

---

## 9. Non-Functional Requirements

**Installation:** `pip install memsmith`. Zero system dependencies. No Docker. No native libraries that break on Windows. Tested on macOS (Apple Silicon + Intel), Linux, Windows.

**Startup time:** `memsmith.session()` must be ready in under 100ms. No network calls on startup.

**Latency:** Core read/write in-process: under 1ms (we're in the same Python process). Server mode: under 5ms on localhost. These are honest numbers, not marketing numbers.

**Crash recovery:** After a hard kill (`kill -9`), the next `memsmith.resume()` must restore all state up to the last WAL-flushed entry. Target: under 500ms recovery time for sessions under 100MB.

**Python compatibility:** 3.11+. No support for older versions — msgspec and uvloop both require modern Python.

**Windows compatibility:** In-process mode must work fully on Windows. Server mode (uvloop) is Linux/macOS only — this must be clearly documented, not silently broken.

---

## 10. Observability — The "memsmith watch" TUI Spec

This is the first thing in every demo. It must look impressive on a 13" MacBook screen.

### Layout

```
┌─────────────────────────────── MemSmith Watch ───────────────────────────────┐
│  Session: {name}   Runtime: {HH:MM:SS}   Agents: {n}   Events: {total}      │
├──────────────────────────────────────────────────────────────────────────────┤
│  [researcher]          [writer]            [editor]         [BROADCAST]      │
│  ─────────────         ──────────          ──────────       ─────────────    │
│  ✅ papers (47)        ⏳ waiting...                                          │
│  ✅ status: done       ✅ draft (3.2kb)    🔒 acquiring...                   │
│                                            ✅ edits (12)    📢 task_done     │
├──────────────────────────────────────────────────────────────────────────────┤
│  [ q: quit ]  [ p: pause ]  [ d: dump ]  [ c: clear ]  [ f: filter agent ]  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Event Color Coding

| Color | Meaning |
|---|---|
| 🟢 Green | Successful write (push) |
| 🔵 Blue | Successful read (get) |
| 🟡 Yellow | Lock acquired |
| 🔴 Red | Lock conflict or timeout |
| ⏳ Spinner | Blocking wait_for in progress |
| 📢 White | Broadcast event |

### `memsmith dump` Output Format

```
MemSmith Session Dump: research_pipeline
Generated: 2026-05-13 14:32:01 IST
─────────────────────────────────────────
[00:00.000] SESSION START
[00:00.012] researcher → PUSH papers (47 items, 8.3kb)
[00:00.013] writer     → WAIT_FOR researcher:papers
[00:01.247] researcher → PUSH status "done"
[00:01.248] writer     ← UNBLOCKED (wait_for resolved)
[00:01.302] writer     → PUSH draft (3.2kb)
[00:01.303] editor     → LOCK_ACQUIRE draft_section_1
[00:01.305] editor     → PUSH edits (12 items)
[00:01.306] editor     → LOCK_RELEASE draft_section_1
[00:01.307] SESSION     → BROADCAST pipeline_complete
[00:01.309] CHECKPOINT  → Saved to .memsmith/research_pipeline_001.snap
─────────────────────────────────────────
Total events: 9  |  Duration: 1.309s  |  Peak memory: 12.1kb
```

This output is the thing people post on Reddit. It makes invisible state visible. It is the actual product value, not the technical implementation.

---

## 11. Integration Layer (Phase 4)

These adapters make MemSmith a drop-in for existing frameworks. They are the distribution multiplier — every LangGraph tutorial that uses `MemSmithCheckpointer` is a MemSmith advertisement.

### LangGraph Checkpointer

```python
from memsmith.integrations import MemSmithCheckpointer
from langgraph.graph import StateGraph

checkpointer = MemSmithCheckpointer(session_id="my_graph_run")
graph = StateGraph(...).compile(checkpointer=checkpointer)
# That's it. LangGraph now persists state through MemSmith.
```

### CrewAI Memory

```python
from memsmith.integrations import MemSmithMemory
from crewai import Crew

crew = Crew(
    agents=[researcher, writer],
    memory=MemSmithMemory(session_id="crew_run_001")
)
```

---

## 12. Roadmap

### Phase 1 — The Core Engine (Weeks 1–2)
**Goal:** `pip install memsmith` and a two-agent demo works end-to-end.

- Sharded in-memory store (16 shards, asyncio.Lock)
- `session()`, `agent().push()`, `agent().get()`
- `agent().wait_for()` using asyncio.Event (no polling)
- `agent().lock()` context manager
- msgspec + Msgpack serialization
- Session scoping and agent identity

**Exit criterion:** This exact code runs without error:
```python
import asyncio
import memsmith

async def main():
    session = memsmith.session("demo")
    session.agent("a").push("msg", "hello from A")
    result = await session.agent("b").wait_for("a", "msg")
    print(result)  # "hello from A"

asyncio.run(main())
```

### Phase 2 — Reliability (Weeks 3–4)
**Goal:** A crashed run can be resumed. Arjun never loses 40 minutes of work again.

- Async WAL with background flush thread
- `session.checkpoint()` — explicit binary + JSON snapshot
- `memsmith.resume()` — WAL replay on startup
- Crash simulation test suite (kill -9 mid-run, verify recovery)

**Exit criterion:** Kill the process mid-run with `kill -9`, resume, verify all state up to last WAL flush is intact.

### Phase 3 — Observability + Server Mode (Week 5)
**Goal:** `memsmith watch` works. This is the demo people share.

- `memsmith watch` TUI (Textual library)
- `memsmith dump` — timestamped session replay export
- `memsmith serve` — FastAPI + uvloop multi-process server
- WebSocket endpoint for remote `watch` mode
- `session.broadcast()` fan-out

**Exit criterion:** Record a GIF of `memsmith watch` showing two agents sharing state in real-time. This GIF is the README hero asset.

### Phase 4 — Open Source Launch + Integrations (Week 6)
**Goal:** MemSmith is discoverable and immediately usable within existing agent frameworks.

- `MemSmithCheckpointer` for LangGraph
- `MemSmithMemory` for CrewAI
- "Good First Issue" guide — at least 5 labeled issues ready for contributors
- README with the GIF, one-command install, and the two-agent demo that runs in 60 seconds
- PyPI release

**Exit criterion:** A developer who has never heard of MemSmith can clone the repo, run the demo, and understand the value in under 3 minutes.

---

## 13. README Strategy

The README is a sales page. It must answer these questions in order, without scrolling:

1. **What is this?** (one sentence)
2. **What problem does it solve?** (the race condition / crash loss scenario, in 3 lines)
3. **How do I install it?** (`pip install memsmith`)
4. **What does it look like?** (the `memsmith watch` GIF)
5. **Show me the code** (the two-agent demo, under 15 lines)
6. **How is this different from Redis?** (answered in one table: Redis needs a server, MemSmith doesn't)

---

## 14. Positioning: The Single Comparison Table

This table goes in the README and ends the "why not just Redis" conversation.

| | MemSmith | Redis | Mem0 | LangGraph State |
|---|---|---|---|---|
| Setup | `pip install` | Install + configure server | API key + account | Part of LangGraph |
| Infra required | None | Redis server | Cloud account | None |
| agent-native API | ✅ | ❌ | ✅ | Partial |
| `wait_for` primitive | ✅ | ❌ (manual pub/sub) | ❌ | ❌ |
| Live state TUI | ✅ | ❌ | ❌ | ❌ |
| Human-readable dump | ✅ | ❌ | ❌ | Partial |
| Works offline | ✅ | ✅ | ❌ | ✅ |
| Best for | Local dev | Production | Production | LangGraph apps |

**The message:** MemSmith doesn't beat Redis in production. It replaces the friction of setting up Redis during development. When you go to production, use Redis. Use MemSmith now.

---

## 15. Success Metrics (6-Month Targets)

| Metric | Target | Why |
|---|---|---|
| GitHub Stars | 1,500 | Proxy for "people found this useful enough to bookmark" |
| PyPI weekly downloads | 3,000 | Proxy for actual usage, not just interest |
| Integrations in tutorials | 10+ | Distribution — tutorials are permanent advertising |
| Contributors | 15+ | Viability signal for open source health |
| Issues opened | 50+ | Community engagement, not just passive users |

The watch metric is **PyPI downloads**, not stars. Stars are vanity. Downloads mean Arjun actually ran `pip install memsmith` and used it for something.

---

## 16. What This Project Proves (For Yashsmith's Resume)

This section is honest and intentional. Building MemSmith in 6 weeks as a solo engineer demonstrates:

- **Concurrency:** Sharded asyncio state with partitioned locking
- **Persistence:** WAL implementation with crash recovery semantics  
- **Systems thinking:** Understanding why Redis exists and building something orthogonal to it, not competing with it
- **API design:** Python-native SDK that reads like English while hiding complexity
- **OSS execution:** End-to-end from idea → PyPI → community

The "SQLite of agent state" framing is also a better story in an interview than "I built a Redis clone." It shows you understand market positioning and user empathy, not just code.

---

*MemSmith v3 PRD — End of Document*