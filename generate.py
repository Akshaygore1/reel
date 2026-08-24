#!/usr/bin/env python3
"""
Master System Design Reel Generator — 100% Python Engine.
Branded for @buildebugship (Vibrant Red) with crystal-clear procedural sound effects.

Usage:
  python3 generate.py --list                 # List all flagship reel presets
  python3 generate.py --preset autoscaling   # Build a specific flagship reel
  python3 generate.py --preset all           # Build all flagship reels
  python3 generate.py --prompt "Consistent Hashing" # Single-prompt AI reel
  python3 generate.py --hd                   # Export in 1080x1920 HD resolution
  python3 generate.py --clean                # Clean temporary caches and frame folders
"""
import os, sys, time, shutil, argparse, subprocess, re
from engine.build_gallery import build_gallery_html
from reel.rendering import create_run, render_legacy_preset, render_run
from reel.runs import (DEFAULT_DURATION, MAX_DURATION, MIN_DURATION, clean_work,
                       validate_duration)

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "output")
AUDIO_DIR = os.path.join(WORKSPACE_DIR, "audio")
TMP_FRAMES_DIR = os.path.join(WORKSPACE_DIR, ".tmp_frames")
FPS = 30
def normalize_duration(duration):
    """Apply the shared 15–30 second reel policy without silently clamping."""
    return validate_duration(duration)

PRESETS = {
    "ci_cd": {
        "id": "ci_cd",
        "title": "CI/CD Pipeline (Continuous Integration & Canary Delivery)",
        "script": "engine/generators/ci_cd.py",
        "audio": "audio/ci_cd.wav",
        "output_video": "video_ci_cd.mp4",
        "duration": 20.0,
        "caption": """CI/CD explained: why shipping code manually at 2 AM is high-risk roulette.

In modern engineering, you don't SSH into production servers to pull code or restart containers manually.

Continuous Integration (CI):
Every commit automatically triggers static linting, AST type checks, container builds, and 400+ unit/integration test suites in isolated runners. If one test breaks or a CVE vulnerability is found, the CI gate halts the pipeline immediately—blocking bad code before it ever touches production.

Continuous Delivery (CD):
Once tests pass, an immutable signed artifact (Docker image) is stored. CD engages an automated Canary / Blue-Green rollout:
1. Route 10% traffic to Green pods.
2. Monitor 200 OK pings and latency.
3. Automatically promote to 100% traffic with zero downtime and instant rollback capabilities.

How does your team handle deployment pipelines—GitHub Actions, GitLab CI, or ArgoCD?
Follow @buildebugship for DevOps internals and backend architecture explained visually.

#cicd #devops #systemdesign #cloud #softwareengineering #kubernetes #docker #backend"""
    },
    "mcp_explained": {
        "id": "mcp_explained",
        "title": "MCP Explained (Custom Adapters vs One Open Protocol)",
        "script": "engine/generators/mcp_explained.py",
        "audio": "audio/mcp_explained.wav",
        "output_video": "video_mcp_explained.mp4",
        "duration": 18.0,
        "audio_theme": "mcp_protocol",
        "caption": """MCP explained with a real example: how an AI assistant connects to live tools without a custom integration for every API.

Imagine a travel assistant answering: “Should I pack an umbrella for Mumbai?” The model can reason, but its training data cannot tell it the live forecast.

Without a shared protocol, the app must rebuild authentication, schemas, discovery, retries, and error handling for every data source.

Model Context Protocol (MCP) standardizes that connection. The AI host runs an MCP client, discovers capabilities exposed by an MCP server, calls a tool such as:

get_forecast(city=\"Mumbai\")

The weather server executes the real API call and returns structured context: 22°C with rain. The model can now use that result in its answer.

MCP does not make the model omniscient, and the server still needs permissions and security controls. It gives AI applications a consistent way to discover and use tools, resources, and prompts.

What would you connect to an AI assistant first—GitHub, your database, or internal docs?
Follow @buildebugship for AI architecture and backend systems explained visually.

#mcp #modelcontextprotocol #aiagents #systemdesign #backend #llm #developer"""
    },
    "sql_injection": {
        "id": "sql_injection",
        "title": "SQL Injection (String Concatenation vs Prepared Statement)",
        "script": "engine/generators/sql_injection.py",
        "audio": "audio/sql_injection.wav",
        "output_video": "video_sql_injection.mp4",
        "caption": """SQL Injection explained: how one rogue quote bypasses authentication entirely.

When you concatenate raw user strings into SQL queries:
$sql = "SELECT * FROM users WHERE user = '" + input + "'";

Entering: admin' OR 1=1 --
turns the WHERE clause into: WHERE user = 'admin' OR 1=1 (which is always TRUE). The rest of the query is commented out with --.

The database ignores the password and dumps all user records.

The fix: Prepared Statements (Parameterized Queries). Input is parameterized as pure data, never parsed as executable SQL code.

Are you using parameterized queries across all your microservices?
Follow @buildebugship for cybersecurity architecture and backend internals explained visually.

#security #sqlinjection #cybersecurity #backend #webdev #database #systemdesign"""
    },
    "database_failover": {
        "id": "database_failover",
        "title": "Database Failover (Primary to Synchronous Replica)",
        "script": "engine/generators/database_failover.py",
        "audio": "audio/database_failover.wav",
        "output_video": "video_database_failover.mp4",
        "caption": """Database failover explained: what happens when your primary database suddenly dies?

In this setup, every write lands on the Primary and its WAL record is streamed to a synchronous Replica. A commit is acknowledged only after both nodes persist it, keeping the standby ready with an RPO of 0 seconds.

Then the Primary stops answering heartbeats.

After 3 missed health checks, the failover controller:
1. Fences the old Primary so it cannot rejoin as a second writer.
2. Confirms the Replica has replayed the latest WAL position.
3. Promotes the Replica to the new Primary.
4. Flips the database proxy to the new write endpoint.

Writes recover in 2.8 seconds with zero committed transactions lost in this synchronous-replication scenario.

The tradeoff: synchronous replication adds write latency across availability zones. Asynchronous replication is faster, but the newest writes can be lost during failover.

When did you last test an actual database failover—not just document it?
Follow @buildebugship for database internals and system design explained visually.

#database #postgresql #systemdesign #highavailability #backend #devops #distributedsystems #sre"""
    },
    "kafka_partitions": {
        "id": "kafka_partitions",
        "title": "Kafka Partitions (Commit Log Conveyors & Consumer Groups)",
        "script": "engine/generators/kafka_partitions.py",
        "audio": "audio/kafka_partitions.wav",
        "output_video": "video_kafka_partitions.mp4",
        "caption": """Kafka Partitions explained: how to process 1.2M events/sec without queue bottlenecks.

A single message queue forces workers to read sequentially. When traffic surges 10x, consumer lag explodes to 50,000+ unread messages and head-of-line blocking stalls your system.

Kafka solves this by sharding topics into independent, ordered commit log partitions (P-0, P-1, P-2).

With a Kafka Consumer Group:
1. Messages are distributed by key hash across partitions.
2. Each consumer instance locks exclusively onto one partition.
3. Workers stream events in parallel with zero locking contention and strict per-key ordering.

Consumer lag drops to 0 and throughput surges to 1.2M events/sec.

How many partitions do you allocate per topic in production?
Follow @buildebugship for distributed systems and event-driven architecture explained visually.

#kafka #systemdesign #distributedsystems #backend #microservices #eventdriven #devops"""
    },
    "redis_pubsub_vs_kafka": {
        "id": "redis_pubsub_vs_kafka",
        "title": "Redis Pub/Sub vs Kafka (Ephemeral Fan-Out vs Durable Log)",
        "script": "engine/generators/redis_pubsub_vs_kafka.py",
        "audio": "audio/redis_pubsub_vs_kafka.wav",
        "output_video": "video_redis_pubsub_vs_kafka.mp4",
        "caption": """Redis Pub/Sub vs Kafka: fast live fan-out versus a durable, replayable event log.

When every consumer is online, both systems can deliver an event immediately.

Redis Pub/Sub broadcasts each message only to subscribers that are connected at that moment. It does not persist messages, track consumer offsets, or replay missed events. If a subscriber disconnects when event #1042 is published, that subscriber never receives it.

Kafka appends event #1042 to a partitioned log. The consumer's committed offset remains at #1041, so Kafka records a lag of one while the consumer is offline. When it reconnects, it resumes from offset #1042 and processes the retained event.

Choose Redis Pub/Sub for transient live signals where occasional loss is acceptable: presence, live UI updates, or disposable notifications.

Choose Kafka when events must survive restarts, be replayed, feed multiple independent consumer groups, or power durable workflows such as orders, payments, audit pipelines, and CDC.

Redis Pub/Sub is a broadcast channel. Kafka is a retained event log. They solve different problems.

Which one is carrying your production events today?
Follow @buildebugship for backend architecture and distributed systems explained visually.

#redis #kafka #pubsub #eventdriven #systemdesign #backend #distributedsystems #microservices"""
    },
    "redis_vs_db": {
        "id": "redis_vs_db",
        "title": "Redis vs PostgreSQL (RAM Silicon vs Magnetic Platter)",
        "script": "engine/generators/redis_vs_db.py",
        "audio": "audio/redis_vs_db.wav",
        "output_video": "video_redis_vs_db.mp4",
        "caption": """Redis vs Database Disk: why in-memory lookups are 375x faster.

Reading from a traditional database requires spinning magnetic platters and mechanical seek arms. That 45ms disk I/O penalty creates an API bottleneck under load.

Redis stores key-value pairs directly in electrical DRAM transistors. No disk heads. No seek times. 0.12ms response latency.

Use the Cache-Aside pattern: check Redis first, fall back to Postgres only on a cache miss.

What is your cache hit ratio in production?
Follow @buildebugship for database performance and system design explained visually.

#redis #postgresql #systemdesign #database #backend #devops #caching"""
    },
    "autoscaling": {
        "id": "autoscaling",
        "title": "Autoscaling (Pachinko Drops & Motorized Crane Scaler)",
        "script": "engine/generators/autoscaling.py",
        "audio": "audio/autoscaling.wav",
        "output_video": "video_autoscaling.mp4",
        "caption": """Autoscaling explained: how cloud infrastructure spins up servers before traffic crashes them.

When traffic surges 10x during a flash sale, 2 instances hit 98% CPU and start dropping packets.

The Horizontal Pod Autoscaler (HPA) triggers an overhead crane, rolling in 2 new server pods in parallel.

Traffic immediately splits across 4 instances, load drops to 34% CPU, and your service achieves 100% uptime.

What is your CPU scaling threshold set to in production?
Follow @buildebugship for cloud architecture and distributed systems explained visually.

#kubernetes #aws #cloudarchitecture #systemdesign #devops #backend"""
    },
    "cron_jobs": {
        "id": "cron_jobs",
        "title": "Cron Jobs (5 Mechanical Sliding Gates & Midnight Alignment)",
        "script": "engine/generators/cron_jobs.py",
        "audio": "audio/cron_jobs.wav",
        "output_video": "video_cron_jobs.mp4",
        "caption": """Cron jobs explained: what * * * * * actually does under the hood.

A cron expression is 5 mechanical sliding gates: Minute, Hour, Day of Month, Month, and Day of Week.

Every 60 seconds, the clock daemon advances. When all 5 gates align at midnight (0 0 * * *), the trapdoor clicks open and fires your job trigger.

Simple, deterministic, and running the backbone of Linux infrastructure for 45 years.

What is your most critical cron job?
Follow @buildebugship for backend systems and Linux architecture explained visually.

#linux #devops #cron #backend #softwareengineering #sysadmin"""
    },
    "vpn_tunnel": {
        "id": "vpn_tunnel",
        "title": "VPN Explained (Airport Runway & Encapsulated Transit Tunnel)",
        "script": "engine/generators/vpn_tunnel.py",
        "audio": "audio/vpn_tunnel.wav",
        "output_video": "video_vpn_tunnel.mp4",
        "caption": """VPN explained: what your WiFi can actually see vs what it can't.

HTTPS hides what you send, NOT where you send it.

Every request has a destination IP on the outside, and your WiFi router and ISP read it to forward packets. That's why your network logs paypal.com and github.com even when SSL encrypted.

A VPN wraps the whole request inside a second outer packet addressed to the VPN server. Everything on your local path sees only the VPN server IP.

Save this for the next time someone asks how a VPN actually works.
Follow @buildebugship for cybersecurity and networking explained visually.

#vpn #networking #cybersecurity #systemdesign #privacy #devops"""
    },
    "cold_starts": {
        "id": "cold_starts",
        "title": "Serverless Cold Starts (1,180ms Penalty vs 40ms Warm Call)",
        "script": "engine/generators/cold_starts.py",
        "audio": "audio/cold_starts.wav",
        "output_video": "video_cold_starts.mp4",
        "caption": """Serverless cold starts explained: why the same function takes 1,180ms then 40ms.

Your serverless function is not running until someone invokes it.

When traffic grows past what is already warm, the cloud platform has to provision a new microVM: download code, boot the runtime, and run global init(). That is the cold start.

Once warm, subsequent requests execute in 40ms directly in memory.

Have you optimized your Lambda cold starts with provisioned concurrency?
Follow @buildebugship for serverless and cloud architecture explained visually.

#serverless #aws #lambda #cloud #systemdesign #devops #backend"""
    },
    "database_indexing": {
        "id": "database_indexing",
        "title": "Database Indexing (Sequential Scan Gate vs B+Tree Seek Orb)",
        "script": "engine/generators/database_indexing.py",
        "audio": "audio/database_indexing.wav",
        "output_video": "video_database_indexing.mp4",
        "caption": """Database Indexing explained: why the same query takes 850ms and then 0.12ms.

Without an index, your database runs a sequential scan: it reads all 10,000,000 rows of the users table and compares every email against your WHERE clause. 8.4 million row reads and 850ms of disk I/O later, the query times out.

Add one index:

CREATE INDEX idx_users_email ON users (email);

The database now maintains a sorted B+Tree over the email column. The root page routes the seek, one internal page narrows the range, and the leaf page holds the pointer straight to your rowid.

Result: 3 page reads instead of 10 million. O(log n) lookups at 0.12ms.

Rule of thumb: index every column used in WHERE, JOIN, and ORDER BY clauses. The tradeoff: each additional index slows down INSERTs and UPDATEs.

Which column is missing an index in your production database right now?
Follow @buildebugship for database internals and system design explained visually.

#database #postgresql #sql #backend #systemdesign #webdev #performance"""
    },
    "streaming_vs_direct": {
        "id": "streaming_vs_direct",
        "title": "Streaming Response vs Direct (SSE & Chunked Transfer vs Blocking HTTP)",
        "script": "engine/generators/streaming_vs_direct.py",
        "audio": "audio/streaming_vs_direct.wav",
        "output_video": "video_streaming_vs_direct.mp4",
        "caption": """Streaming Responses (SSE) vs Direct HTTP: why waiting 10s destroys UX.

When you ask ChatGPT a question, two very different architectures can deliver the answer:

1. Direct Response (Buffered HTTP):
The LLM server holds the entire generation in memory until all 500 tokens are complete. The user stares at a frozen loading spinner for 8 to 10 seconds. Then—BOOM—all the text dumps at once. By that time, 68% of users have already bounced.

2. Streaming Response (Server-Sent Events / Chunked Transfer):
The GPU tokenizer flushes each token delta (data: {"delta": ...}) the millisecond it is computed. The client UI paints words continuously with a live blinking cursor in 38ms Time-To-First-Byte (TTFB).

Perceived speed feels instantaneous, and users can start reading immediately while the model continues generating in the background.

Are you streaming LLM completions and large API payloads in production?
Follow @buildebugship for AI architecture and system design internals explained visually.

#streaming #sse #chatgpt #ai #apis #backend #webdev #systemdesign #softwareengineering"""
    },
    "websockets_vs_polling": {
        "id": "websockets_vs_polling",
        "title": "WebSockets vs Polling (HTTP Poll Flood vs Full-Duplex Push Pipe)",
        "script": "engine/generators/websockets_vs_polling.py",
        "audio": "audio/websockets_vs_polling.wav",
        "output_video": "video_websockets_vs_polling.mp4",
        "caption": """WebSockets vs Polling explained: why "anything new?" spam melts your server at scale.

With HTTP polling, the client re-fetches /feed every 5 seconds — whether anything changed or not. At 100 clients it's harmless: 2 of 3 polls come back empty but staleness stays under 5s.

Then traffic grows ×10. 4,700 clients hammer the same endpoint and 92% of polls return empty 204s. 8,640 wasted responses burn the server's CPU, polls queue behind each other, and users stare at a feed that's 8+ seconds stale. Scaling up just buys bigger bins for the waste.

The WebSocket fix: one HTTP handshake (GET /ws → 101 Switching Protocols) upgrades the connection into a persistent full-duplex pipe. The server PUSHES each event the moment it happens — 23ms delivery, zero empty responses, one TCP connection per client.

The tradeoff: WebSockets need stateful servers, heartbeat/reconnect logic, and break simple HTTP caching. Polling is still fine for rare, small, non-interactive updates.

What's your real-time transport — polling, long-polling, SSE, or WebSockets?
Follow @buildebugship for network and system design internals explained visually.

#websockets #polling #backend #systemdesign #realtime #webdev #javascript #networking"""
    },
    "sql_vs_nosql": {
        "id": "sql_vs_nosql",
        "title": "SQL vs NoSQL (Merge-Join Monolith vs Sharded Document Store)",
        "script": "engine/generators/sql_vs_nosql.py",
        "audio": "audio/sql_vs_nosql.wav",
        "output_video": "video_sql_vs_nosql.mp4",
        "caption": """SQL vs NoSQL explained: why the JOIN decides whether you scale up or scale out.

In SQL (PostgreSQL), orders live in their own table. Every user read is a JOIN: users joined to orders, executed on ONE node. At 12k req/s that's fine — 0.4ms.

Then traffic spikes ×10. 412 queries pile onto the same single JOIN queue, P99 latency hits 850ms, and timeouts roll in. You can scale UP (4× the CPU) but a JOIN cannot be split across machines — the data has to live together to be joined.

The NoSQL answer (MongoDB / DynamoDB): denormalize. Embed the orders array inside the user document. One document = one read, zero JOINs. No JOIN means the data can SHARD: hash(user_id) routes each read to exactly 1 of 3 nodes. 0.12ms reads at 150k req/s.

The tradeoff: NoSQL gives up cross-document JOINs and strong cross-row ACID transactions. That's why most companies run BOTH — SQL for money and relations, NoSQL for scale-out reads.

What do you reach for first — Postgres or Mongo?
Follow @buildebugship for database internals and system design explained visually.

#sql #nosql #mongodb #postgresql #systemdesign #database #backend #webdev"""
    },
    "chatgpt_streaming": {
        "id": "chatgpt_streaming",
        "title": "How ChatGPT Streams Responses (Server-Sent Events & Token Generation)",
        "script": "engine/generators/chatgpt_streaming.py",
        "audio": "audio/chatgpt_streaming.wav",
        "output_video": "video_chatgpt_streaming.mp4",
        "caption": """How ChatGPT streams responses in real-time under the hood.

ChatGPT doesn't write full sentences at once. Its Transformer model generates answers autoregressively: predicting ONE token at a time.

If ChatGPT waited for all 500 tokens before sending the response, you would stare at a frozen loading spinner for 15 seconds.

Instead, the client sends:
POST /v1/chat/completions { "stream": true }

The server responds with:
Content-Type: text/event-stream
Transfer-Encoding: chunked

As the GPU calculates each token, the server immediately flushes:
data: {"delta": {"content": "word"}}

The client reads the stream chunk and paints words onto your screen in 38ms. When complete, the server sends data: [DONE].

Are you using Server-Sent Events (SSE) or WebSockets in your AI apps?
Follow @buildebugship for AI architecture and system design explained visually.

#chatgpt #openai #ai #systemdesign #backend #sse #webdev #softwareengineering"""
    },
    "cdn_edge": {
        "id": "cdn_edge",
        "title": "CDN Edge (Central Origin 320ms vs Global Edge PoPs 8ms)",
        "script": "engine/generators/cdn_edge.py",
        "audio": "audio/cdn_edge.wav",
        "output_video": "video_cdn_edge.mp4",
        "caption": """CDN vs Central Origin explained: why your global users experience 320ms ping and how Edge PoPs drop it to 8ms.

Without a Content Delivery Network (CDN), every player and browser across Tokyo, London, and Sydney must send HTTP requests across 12,000 km of undersea fiber cables directly to a single US-East origin server.

Under peak traffic:
1. Cross-ocean Round-Trip Time (RTT) averages 320ms - 350ms.
2. The single origin server CPU spikes to 98% under heavy media streaming load.
3. Packet loss surges and global users suffer severe buffering.

The CDN solution:
Deploy a worldwide network of Edge Points of Presence (PoPs) powered by Anycast DNS geo-routing.

When a user in Tokyo requests a 4K video or game texture:
1. Anycast automatically routes the request to the closest Edge PoP in Tokyo (< 15km away).
2. NVMe SSD & RAM edge caches serve static assets instantly with a 98.4% Cache Hit Ratio.
3. Response latency plummets from 320ms to 8ms.
4. Origin server load drops by 98%, protecting your core database and APIs.

Which CDN provider powers your production infrastructure: Cloudflare, AWS CloudFront, Fastly, or Akamai?
Follow @buildebugship for distributed systems, networking, and backend architecture explained visually.

#cdn #systemdesign #networking #backend #webdev #cloud #devops #performance #softwareengineering"""
    },
    "authn_vs_authz": {
        "id": "authn_vs_authz",
        "title": "AuthN vs AuthZ (Authentication vs Authorization Pinball)",
        "script": "engine/generators/authn_vs_authz.py",
        "audio": "audio/authn_vs_authz.wav",
        "output_video": "video_authn_vs_authz.mp4",
        "caption": """Authentication (AuthN) vs Authorization (AuthZ) explained: why passing AuthN doesn't mean you have access.

Think of your API like an arcade pinball machine with two distinct security chambers:

1. Authentication (AuthN) = "WHO ARE YOU?"
The plunger launches your request into the top chamber. JWT signature verification, OAuth2 tokens, and FIDO2 Passkeys bounce against the bumpers to verify identity.
Result: 200 OK — Identity confirmed (User ID #42).

2. Authorization (AuthZ) = "WHAT ARE YOU ALLOWED TO DO?"
User #42 attempts to hit the Admin gate to DELETE /database.
Even though AuthN passed 200 OK, the RBAC policy filter checks roles & scopes. User #42 only has ROLE: VIEWER.
Result: 403 FORBIDDEN! The security flipper blocks access.

3. RBAC Resolution:
The policy engine routes Viewer through the READ lane — correct scope, correct access. 200 OK.

The Golden Rule:
• AuthN verifies Identity (401 if invalid token/signature).
• AuthZ verifies Permissions (403 if role lacks the required scope).
Always enforce both layers with RBAC or ABAC in production!

How do you handle AuthZ in your microservices — Casbin, OPA/Rego, Keycloak, or custom middleware?
Follow @buildebugship for cybersecurity architecture and backend internals explained visually.

#security #authn #authz #cybersecurity #backend #jwt #oauth #rbac #systemdesign"""
    },
    "react_under_hood": {
        "id": "react_under_hood",
        "title": "React Under the Hood (Fiber Tree & Concurrent Scheduler vs Real DOM)",
        "script": "engine/generators/react_under_hood.py",
        "audio": "audio/react_under_hood.wav",
        "output_video": "video_react_under_hood.mp4",
        "caption": """React under the hood explained: why setState rebuilds a virtual tree — not the DOM.

Every time state changes, React re-runs the component in memory. It builds a new virtual tree of Fiber nodes, diffs it against the previous one, and commits ONLY the nodes whose output actually changed to the real DOM.

That's why one setState in <Card/> costs a 16ms frame and the browser stays at 60fps.

The problem: when state changes at the ROOT, React 18 and below re-render the entire subtree in one synchronous pass. 10,000 fibers block the main thread for 120ms — the browser can't paint a single frame, and the UI janks.

The React 18 fix: Concurrent Mode. The Fiber scheduler time-slices that giant render into 5ms chunks, yields back to the browser between slices so it can paint, and only commits the 1 real DOM mutation at the end. Interruptible, urgent-safe, 16.6ms frames at 60fps.

Are you splitting expensive renders with useMemo, memo, or relying on concurrent scheduling?
Follow @buildebugship for frontend internals and system design explained visually.

#react #react18 #frontend #javascript #webdev #systemdesign #performance #concurrency"""
    },
    "captcha_explained": {
        "id": "captcha_explained",
        "title": "How CAPTCHA Works (Human vs Bot Interaction Risk Simulator)",
        "script": "engine/generators/captcha_explained.py",
        "audio": "audio/captcha_explained.wav",
        "output_video": "video_captcha_explained.mp4",
        "caption": """How CAPTCHA works: why clicking “I’m not a robot” is only the beginning.

A checkbox alone cannot prove that someone is human—a bot can click it too. Modern CAPTCHA systems treat the interaction as one input to a broader, server-side risk decision.

In this simulation:
1. A human cursor pauses, changes direction, and clicks with varied timing.
2. A bot jumps directly to the target in 8ms and repeats the same action.
3. The risk engine combines interaction behavior with browser, network, and request context.

Low-risk traffic receives a signed pass token. Uncertain traffic gets an extra image or interaction challenge. Clearly abusive traffic can be blocked or rate-limited.

The exact signals and thresholds vary by CAPTCHA provider, and the numbers shown here are illustrative. CAPTCHA raises the cost of automation—it does not prove humanity from one click.

What signal would expose a bot fastest: timing, repetition, or request context?
Follow @buildebugship for cybersecurity and backend systems explained visually.

#captcha #cybersecurity #websecurity #backend #systemdesign #automation #webdev #security"""
    },
    "garbage_collection": {
        "id": "garbage_collection",
        "title": "Garbage Collection (Root Tracing, Sweep Gate & Compactor Piston)",
        "script": "engine/generators/garbage_collection.py",
        "audio": "audio/garbage_collection.wav",
        "output_video": "video_garbage_collection.mp4",
        "caption": """Garbage Collection explained: how a managed runtime turns a 96% full heap back into reusable memory.

Your code allocates objects into a managed heap. When the last reference to an object disappears, the bytes do not vanish immediately — the object becomes unreachable and waits for the collector.

In this 64MB heap, allocation pressure reaches 96% and triggers a 180ms stop-the-world full collection.

The tracing collector starts from GC roots such as stack frames, static fields, and native handles. It marks every object reachable through the reference graph, sweeps everything unmarked, then compacts survivors to remove fragmentation.

Result: about 37MB reclaimed, heap usage falls to 38%, and allocation resumes after a 12ms optimized pause.

Important: GC reclaims managed memory, not external resources such as files, sockets, or database connections. Close those explicitly. Collector tuning also trades pause time against throughput and memory overhead.

Which runtime collector do you use in production — G1, ZGC, Go GC, or V8 Orinoco?
Follow @buildebugship for runtime internals and system design explained visually.

#garbagecollection #jvm #golang #javascript #backend #performance #systemdesign #memory"""
    },
    "garbage_collection_simple": {
        "id": "garbage_collection_simple",
        "title": "Garbage Collection — Simple (Heap Jar & GC Broom)",
        "script": "engine/generators/garbage_collection_simple.py",
        "audio": "audio/garbage_collection_simple.wav",
        "audio_theme": "memory_gc",
        "output_video": "video_garbage_collection_simple.mp4",
        "caption": """Garbage Collection, explained simply.

Your app creates objects and stores them in memory. As long as the app still has a reference to an object, that object stays alive.

When the reference disappears, the object becomes garbage. It is no longer useful, but it still occupies memory until the garbage collector runs.

The garbage collector keeps the objects your app can still reach and removes the rest. That frees memory automatically so the app can continue creating new objects.

Simple rule:
A reference means KEEP IT.
No reference means CLEAN IT.

Garbage collection manages memory, but you should still close files, sockets, and database connections yourself.

Which language taught you garbage collection first?
Follow @buildebugship for programming concepts explained visually.

#garbagecollection #programming #java #javascript #golang #dotnet #backend #memory"""
    }
}

# Flagship scripts predate SceneV2, so their synchronized plans live beside the
# registry entry. Each cue corresponds to an apparatus action visible in its beat.
PRESET_AUDIO_PLANS = {
    "ci_cd": ("compute", ((.12, "processing", .55), (.35, "alarm", .80), (.66, "latch", .65), (.84, "success", .75))),
    "mcp_explained": ("protocol", ((.10, "packet", .55), (.38, "latch", .70), (.64, "processing", .60), (.88, "success", .75))),
    "sql_injection": ("security", ((.14, "tick", .45), (.34, "alarm", .90), (.68, "latch", .70), (.86, "success", .75))),
    "database_failover": ("storage", ((.12, "packet", .50), (.36, "alarm", .85), (.65, "latch", .80), (.84, "success", .70))),
    "kafka_partitions": ("storage", ((.10, "queue", .55), (.38, "alarm", .75), (.64, "sweep", .65), (.82, "success", .70))),
    "redis_pubsub_vs_kafka": ("storage", ((.12, "packet", .55), (.37, "queue", .80), (.65, "latch", .65), (.86, "success", .70))),
    "redis_vs_db": ("storage", ((.11, "tick", .50), (.36, "queue", .75), (.66, "sweep", .65), (.84, "success", .70))),
    "autoscaling": ("mechanical", ((.12, "packet", .50), (.35, "alarm", .85), (.64, "latch", .75), (.83, "success", .70))),
    "cron_jobs": ("mechanical", ((.14, "tick", .60), (.37, "queue", .65), (.64, "latch", .85), (.82, "success", .65))),
    "vpn_tunnel": ("security", ((.10, "packet", .55), (.36, "alarm", .75), (.64, "sweep", .70), (.86, "success", .65))),
    "cold_starts": ("compute", ((.12, "packet", .50), (.35, "processing", .85), (.65, "impact", .65), (.84, "success", .70))),
    "database_indexing": ("storage", ((.10, "queue", .50), (.36, "alarm", .75), (.64, "sweep", .70), (.83, "success", .75))),
    "streaming_vs_direct": ("network", ((.12, "packet", .55), (.36, "queue", .80), (.63, "packet", .70), (.85, "success", .65))),
    "websockets_vs_polling": ("network", ((.10, "packet", .50), (.37, "queue", .85), (.64, "latch", .65), (.84, "success", .70))),
    "sql_vs_nosql": ("storage", ((.12, "processing", .50), (.35, "queue", .85), (.66, "sweep", .70), (.85, "success", .70))),
    "chatgpt_streaming": ("compute", ((.11, "processing", .55), (.36, "impact", .80), (.64, "packet", .70), (.86, "success", .65))),
    "cdn_edge": ("network", ((.10, "packet", .55), (.36, "queue", .80), (.64, "sweep", .70), (.84, "success", .70))),
    "authn_vs_authz": ("security", ((.12, "latch", .50), (.35, "alarm", .85), (.65, "latch", .75), (.84, "success", .70))),
    "react_under_hood": ("compute", ((.11, "processing", .55), (.37, "queue", .80), (.64, "sweep", .65), (.85, "success", .70))),
    "captcha_explained": ("security", ((.12, "tick", .50), (.36, "alarm", .80), (.66, "latch", .70), (.84, "success", .70))),
    "garbage_collection": ("compute", ((.10, "processing", .50), (.37, "queue", .80), (.64, "sweep", .75), (.84, "impact", .60))),
    "garbage_collection_simple": ("compute", ((.12, "blip", .50), (.36, "queue", .75), (.64, "sweep", .75), (.85, "success", .65))),
}
for _key, (_profile, _events) in PRESET_AUDIO_PLANS.items():
    PRESETS[_key]["audio_plan"] = {
        "profile": _profile,
        "events": [{"at": at, "kind": kind, "intensity": intensity} for at, kind, intensity in _events],
    }

def render_frames_with_script(script_path, temp_dir):
    """Executes generator script directly to produce frames into temp_dir"""
    os.makedirs(temp_dir, exist_ok=True)
    env = os.environ.copy()
    env["TMP_FRAMES_DIR"] = temp_dir
    abs_script = os.path.join(WORKSPACE_DIR, script_path)
    cmd = [sys.executable, abs_script, temp_dir]
    subprocess.run(cmd, check=True, env=env, stdout=subprocess.DEVNULL)

def compile_video(frames_dir, audio_path, output_mp4, duration=DEFAULT_DURATION, hd=False, uhd=False):
    """Assembles frames + audio into high-compatibility H.264 MP4 (with optional HD/UHD scaling)"""
    os.makedirs(os.path.dirname(output_mp4), exist_ok=True)

    # Check whether frames are named f_0000.png or frame_0000.png
    if os.path.exists(os.path.join(frames_dir, "f_0000.png")):
        input_pattern = f"{frames_dir}/f_%04d.png"
    else:
        input_pattern = f"{frames_dir}/frame_%04d.png"

    duration = normalize_duration(duration)
    frame_count = len([name for name in os.listdir(frames_dir) if name.endswith(".png")])
    source_duration = frame_count / FPS
    timing_scale = duration / source_duration

    filters = []
    if abs(timing_scale - 1.0) > 0.0001:
        filters += [f"setpts={timing_scale:.8f}*PTS", f"fps={FPS}"]
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", input_pattern,
        "-i", audio_path,
    ]
    if uhd:
        filters.append("scale=2160:3840:flags=lanczos")
    elif hd:
        filters.append("scale=1080:1920:flags=lanczos")
    if filters:
        cmd += ["-vf", ",".join(filters)]
    cmd += [
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-crf", "16" if uhd else ("17" if hd else "18"),
        "-preset", "slow" if uhd else "fast",
        "-movflags", "+faststart",
        output_mp4
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def build_preset(preset_key, hd=False, force_audio=True, uhd=False, duration=None):
    """Compatibility adapter: render an existing preset into a unique run kit."""
    if preset_key not in PRESETS:
        print(f"❌ Preset '{preset_key}' not found. Run with --list to see options.")
        return False

    preset = PRESETS[preset_key]
    resolution = "2160p" if uhd else ("1080p" if hd else "720p")
    selected_duration = normalize_duration(duration if duration is not None else preset.get("duration"))
    print(f"🎬 Generating {preset['title']} as a unique {resolution} run...")
    destination = render_legacy_preset(preset_key, preset, selected_duration, resolution)
    build_gallery_html()
    print(f"✅ Run kit: {destination}")
    return destination

def generate_from_prompt(prompt_text, hd=False, uhd=False, duration=None):
    """
    Generates a system design reel from any topic prompt:
    - Smart routing: maps to flagship bespoke apparatus when relevant
    - Dynamic blueprint: generates tailored blueprint diagram for new topics
    """
    clean_p = prompt_text.strip().lower().replace("-", " ")
    
    # Check for flagship topic match
    if clean_p == "mcp" or "model context protocol" in clean_p:
        print(f"🎯 Matched flagship reel: MCP Explained")
        return build_preset("mcp_explained", hd=hd, uhd=uhd, duration=duration)
    if "auto" in clean_p and "scal" in clean_p:
        print(f"🎯 Matched flagship reel: Autoscaling")
        return build_preset("autoscaling", hd=hd, uhd=uhd, duration=duration)
    if "kafka" in clean_p and ("redis" in clean_p or "pub/sub" in clean_p or "pubsub" in clean_p or ("pub" in clean_p and "sub" in clean_p)):
        print(f"🎯 Matched flagship reel: Redis Pub/Sub vs Kafka")
        return build_preset("redis_pubsub_vs_kafka", hd=hd, uhd=uhd, duration=duration)
    if "redis" in clean_p or "ram vs" in clean_p or "in memory" in clean_p:
        print(f"🎯 Matched flagship reel: Redis vs Database Disk")
        return build_preset("redis_vs_db", hd=hd, uhd=uhd, duration=duration)
    if "sql" in clean_p and "inject" in clean_p:
        print(f"🎯 Matched flagship reel: SQL Injection")
        return build_preset("sql_injection", hd=hd, uhd=uhd, duration=duration)
    if "failover" in clean_p or ("primary" in clean_p and ("replica" in clean_p or "database" in clean_p)):
        print(f"🎯 Matched flagship reel: Database Failover")
        return build_preset("database_failover", hd=hd, uhd=uhd, duration=duration)
    if "nosql" in clean_p or ("sql" in clean_p and " vs " in clean_p):
        print(f"🎯 Matched flagship reel: SQL vs NoSQL")
        return build_preset("sql_vs_nosql", hd=hd, uhd=uhd, duration=duration)
    if "websocket" in clean_p or "polling" in clean_p:
        print(f"🎯 Matched flagship reel: WebSockets vs Polling")
        return build_preset("websockets_vs_polling", hd=hd, uhd=uhd, duration=duration)
    if "index" in clean_p:
        print(f"🎯 Matched flagship reel: Database Indexing")
        return build_preset("database_indexing", hd=hd, uhd=uhd, duration=duration)
    if "cron" in clean_p:
        print(f"🎯 Matched flagship reel: Cron Jobs")
        return build_preset("cron_jobs", hd=hd, uhd=uhd, duration=duration)
    if "vpn" in clean_p or "tunnel" in clean_p or "wifi" in clean_p:
        print(f"🎯 Matched flagship reel: VPN Explained")
        return build_preset("vpn_tunnel", hd=hd, uhd=uhd, duration=duration)
    if "cold" in clean_p or "serverless" in clean_p or "lambda" in clean_p:
        print(f"🎯 Matched flagship reel: Serverless Cold Starts")
        return build_preset("cold_starts", hd=hd, uhd=uhd, duration=duration)
    if "chatgpt" in clean_p or "gpt" in clean_p or "openai" in clean_p:
        print(f"🎯 Matched flagship reel: How ChatGPT Streams Responses")
        return build_preset("chatgpt_streaming", hd=hd, uhd=uhd, duration=duration)
    if "stream" in clean_p or "sse" in clean_p or "chunked" in clean_p or "direct" in clean_p:
        print(f"🎯 Matched flagship reel: Streaming Response vs Direct")
        return build_preset("streaming_vs_direct", hd=hd, uhd=uhd, duration=duration)
    if "cdn" in clean_p or "edge" in clean_p or "content delivery" in clean_p:
        print(f"🎯 Matched flagship reel: CDN Edge")
        return build_preset("cdn_edge", hd=hd, uhd=uhd, duration=duration)
    if "auth" in clean_p or "pinball" in clean_p or "jwt" in clean_p or "rbac" in clean_p:
        print(f"🎯 Matched flagship reel: AuthN vs AuthZ Pinball")
        return build_preset("authn_vs_authz", hd=hd, uhd=uhd, duration=duration)
    if "react" in clean_p or ("virtual dom" in clean_p) or "reconcile" in clean_p:
        print(f"🎯 Matched flagship reel: React Under the Hood")
        return build_preset("react_under_hood", hd=hd, uhd=uhd, duration=duration)
    if "captcha" in clean_p or "not a robot" in clean_p:
        print(f"🎯 Matched flagship reel: How CAPTCHA Works")
        return build_preset("captcha_explained", hd=hd, uhd=uhd, duration=duration)
    if "ci/cd" in clean_p or "ci cd" in clean_p or "cicd" in clean_p or "continuous integration" in clean_p or "continuous delivery" in clean_p or "pipeline" in clean_p:
        print(f"🎯 Matched flagship reel: CI/CD Pipeline")
        return build_preset("ci_cd", hd=hd, uhd=uhd, duration=duration)
    if "garbage" in clean_p or "garbage collector" in clean_p or clean_p in ("gc", "memory gc"):
        print(f"🎯 Matched flagship reel: Garbage Collection — Simple")
        return build_preset("garbage_collection_simple", hd=hd, uhd=uhd, duration=duration)

    # --prompt is the explicitly requested quick path. It still uses the safe
    # SceneV2/run-kit pipeline, but agents should scaffold and author bespoke scenes.
    resolution = "2160p" if uhd else ("1080p" if hd else "720p")
    brief = create_run(prompt_text, normalize_duration(duration), resolution, mode="quick")
    print(f"✨ Quick SceneV2 run: {brief['run_id']}")
    destination = render_run(brief["run_id"])
    build_gallery_html()
    return destination

def clean_directory():
    """Purges ignored run workspaces; published runs are never pruned."""
    count = clean_work()
    print(f"✨ Removed {count} work directories; published runs were preserved.")

def main():
    parser = argparse.ArgumentParser(description="Master System Design Reels Generator (100% Python)")
    parser.add_argument("--list", action="store_true", help="List all core reel presets")
    parser.add_argument("--preset", type=str, help="Preset key (sql_injection, redis_vs_db, autoscaling, cron_jobs, vpn_tunnel, cold_starts, all)")
    parser.add_argument("--prompt", type=str, help="Generate a reel from any topic prompt")
    parser.add_argument("--hd", action="store_true", help="Render in 1080x1920 HD publication resolution")
    parser.add_argument("--uhd", action="store_true", help="Render in 2160x3840 Ultra HD publication resolution")
    parser.add_argument("--duration", type=float, help=f"Reel duration in seconds ({MIN_DURATION:g}–{MAX_DURATION:g}; default {DEFAULT_DURATION:g})")
    parser.add_argument("--clean", action="store_true", help="Clean all temporary cache and frame folders")
    parser.add_argument("--serve", nargs="?", const=8000, type=int, help="Start the interactive video gallery server (default port 8000)")

    args = parser.parse_args()

    if args.serve:
        from reel.cli import main as reel_main
        reel_main(["serve", "--port", str(args.serve)])
        return

    if args.list:
        print("\n📋 Available Core System Design Reel Presets:")
        print("───────────────────────────────────────────────────────────────────")
        for k, v in PRESETS.items():
            print(f"  • {k:18} : {v['title']}")
        print("───────────────────────────────────────────────────────────────────")
        print("Usage: python3 generate.py --preset <name>  (or --preset all)\n")
        return

    if args.clean:
        clean_directory()
        return

    if args.prompt:
        generate_from_prompt(args.prompt, hd=args.hd, uhd=args.uhd, duration=args.duration)
        return

    if args.preset:
        if args.preset.lower() == "all":
            for k in PRESETS.keys():
                build_preset(k, hd=args.hd, uhd=args.uhd, duration=args.duration)
        else:
            build_preset(args.preset, hd=args.hd, uhd=args.uhd, duration=args.duration)
        return

    parser.print_help()

if __name__ == "__main__":
    main()
