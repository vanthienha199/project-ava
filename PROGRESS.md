# Project Ava — Full Progress & Context for New Chat
**Last Updated:** March 20, 2026, 5:30 PM EST
**Author:** Ha Le (halevanthien@gmail.com)
**READ THIS FILE 100% BEFORE DOING ANYTHING**

---

## WHAT IS THIS PROJECT?

Project Ava (Automated Intelligent Verification with Agents) is a **fully autonomous AI agent platform** for hardware verification. Users upload a Verilog design + natural language spec on the website, and the cloud-deployed agent automatically generates a cocotb testbench, simulates with Icarus Verilog, self-corrects until tests pass, and streams results live to the dashboard.

**It is now a real agentic AI application** — no terminal needed. The watcher runs 24/7 on Fly.io, picks up uploads from Supabase, and verifies designs autonomously using the Anthropic API.

### CURRENT STATUS: 18/18 DESIGNS, 182/182 TESTS, 100% PASS RATE

| Design | Type | Tests | Iterations | Self-corrected? |
|---|---|---|---|---|
| 01_adder | Combinational | 6/6 | 1 | No |
| 02_alu | Combinational | 6/6 | 1 | No |
| 03_icg (clock gating) | **Power-aware** | 7/7 | 1 | No |
| 04_counter | Sequential | 6/6 | 2 | Yes (1 correction) |
| 05_freq_divider | **Power-aware (DVFS)** | 6/6 | 1 | No |
| 06_power_fsm | **Power-aware** | 20/20 | 4 | Yes (3 corrections) |
| 07_dvfs_controller | **Power-aware (DVFS)** | 11/11 | 4 | Yes (3 corrections) |
| 08_shift_register | Sequential | 9/9 | 7 | Yes (6 corrections + 1 reboot) |
| 09_fifo | Buffer/Memory | 11/11 | 2 | Yes (1 correction) |
| 10_pwm | **Power-aware** | 11/11 | 1 | No |
| 11_uart_tx | Protocol | 10/10 | 2 | Yes (1 correction) |
| 12_watchdog | Timer/Watchdog | 10/10 | 6 | Yes (5 corrections + 1 reboot) |
| 13_traffic_light | FSM/Controller | 9/9 | 5 | Yes (4 corrections + 1 reboot) |
| 14_spi_master | Protocol (SPI) | 11/11 | 1 | No (first-pass!) |
| 15_priority_encoder | Priority Logic | 14/14 | 2 | Yes (1 correction) |
| 16_i2c_master | Protocol (I2C) | 10/10 | 7 | Yes (6 corrections + 1 reboot) |
| 17_arbiter | Sequential (round-robin) | 11/11 | 5 | Yes (4 corrections + 1 reboot) |
| 18_memory_controller | Buffer/Memory (SRAM) | 14/14 | 2 | Yes (1 correction) |

**Total: 18/18 designs passed, 182/182 tests, 8 categories, 5 power-aware designs, 100% pass rate.**

Designs 12-15 are from **external open-source repos** (Efabless, nandland, fpga4student, harishs1313) — the agent had never seen them. This proves it works on unseen designs, not just pre-baked ones.

### LLM Comparison (March 20, 2026)
| LLM | Backend | Adder | ALU | Pass Rate | Notes |
|---|---|---|---|---|---|
| **Claude (Sonnet)** | claude_cli / anthropic_api | PASS 6/6 | PASS 6/6 | **100%** (18/18) | All designs pass |
| **DeepSeek-Coder-33B** | Ollama (RTX 5090 via Vast.ai) | FAIL 0/0 | FAIL 0/4 | **0%** (0/2) | cocotb 2.0 trap kills it |

### Who It Serves
1. **ACM Club Project** — Ha Le is on the Agent + Automation teams. Dylan is PM. AMD funds via Rex McCurry. 16 students, 4 teams.
2. **Dr. Di Wu's Lab (Unary Lab, UCF)** — Agentic AI research.
3. **Personal Research / Breakthrough** — First AI tool for DVFS/power-aware verification. Companies like AMD would want this.

### The Unique Angle
Derek Martin (AMD engineer) works on DVFS verification. Dr. Wu's Lit Silicon paper is about DVFS throttling causing GPU stragglers. **Project Ava prevents DVFS bugs at design time.** Nobody else has done this.

---

## DR. WU'S AGENTIC AI DIRECTION (CRITICAL CONTEXT)

Dr. Wu is an **AI systems/infrastructure researcher**, not an AI applications researcher. His interest in agentic AI:

> "You can look into agentic AI systems. How such systems are built, what system component are needed. Like which parts of the workload are on CPU, what are on GPU, how many GPU and CPU are needed."

He sent Ha Le this paper: **arXiv:2506.04301 — "The Cost of Dynamic Reasoning: Demystifying AI Agents and Test-Time Scaling from an AI Infrastructure Perspective"** (HPCA 2026). Key findings:
- Tool-augmented agents need **9.2x more LLM calls** per request than single-turn
- GPU idle **30-55% of the time** while CPU-bound tools execute
- Agentic inference uses **62-137x more GPU energy** per query than static inference
- **CPU is 50-90% of total latency** in agentic workflows (not GPU!)

**Decision (Session 4):** Keep Project Ava separate from infrastructure research. Ava is the verification tool. Infrastructure characterization of agentic workloads would be a separate project. Don't try to combine both — do each well.

### Key Papers for Dr. Wu (identified in session 4)
1. **arXiv:2506.04301** — "Cost of Dynamic Reasoning" (the one Dr. Wu sent — HPCA 2026)
2. **arXiv:2511.00739** — "A CPU-Centric Perspective on Agentic AI" (Georgia Tech + Intel)
3. **arXiv:2506.24045** — "Agent.xpu" — Heterogeneous SoC scheduling for agents
4. **arXiv:2509.20241** — "Energy Use of AI Inference" (Microsoft) — 13x energy with test-time scaling
5. **AMD blog:** "Agentic AI Brings New Attention to CPUs" — AMD sees CPU as the agentic bottleneck

### AMD Panel Context (March 4, 2026 ACM meeting)
- **Rex McCurry** — Site Lead, GPU Architect. Coordinates AMD-UCF. Wants "IP pipeline" (research).
- **Derek Martin** — Hardware Architect. "I work on features that turn stuff off to save power." Direct DVFS customer.
- **John G** — GPU Power Modeling. Recent UCF grad.
- **Michelle** — Verification since 2008. GPU verification → performance verification.
- Rex: "Verification is 70-80% of VLSI cycle. If we don't get it right, costs us a lot of money."
- Rex: "We also want an IP pipeline. So that's the research."
- AMD's 4 pillars at UCF: talent pipeline, curriculum, **IP pipeline (research)**, AI adoption

### Dr. Wu Communication Timeline
- Dr. Wu told Ha Le to research agentic AI systems
- Sent two papers: arXiv:2506.04301 (Cost of Dynamic Reasoning) + arXiv:2511.09861 (Lit Silicon)
- Ha Le built ThinkTank (GWAP for PRM training data) — Dr. Wu liked it, asked for 10-15min presentation
- Dr. Wu processing Ha Le's AMD machine access (th273073@ucf.edu, userid th273073)
- Plans to have Ha Le run lit_silicon on advanced AMD machines once access granted
- Dr. Wu's zoom: https://ucf.zoom.us/my/meeting.diwu
- Group meetings: Wednesday 2 PM, HEC356 (in-person) or Zoom

---

## LIVE DEPLOYMENT (March 20, 2026)

### Public Website
- **URL:** https://project-ava-ucf.netlify.app (renamed from astonishing-sorbet)
- **Host:** Netlify (free tier) — deploy by dragging `docs/` folder
- **6 pages:** Dashboard, Designs, Upload, History, Analyze, Live
- **Theme:** Matrix (ThermalTrace clone) — #000 bg, #00ff00 green, Share Tech Mono, matrix rain
- **New in session 4:** Testbench viewer on Live page (shows AI-generated code with COPY button)

### Supabase Database
- **URL:** https://yvpmoyzggbcfaldhsbkl.supabase.co
- **Account:** annecgjackson@gmail.com (free tier)
- **Tables:** designs, runs, iterations, failures, test_results
- **Realtime:** Enabled on runs, iterations, test_results (for Live page)
- **RLS:** Anonymous SELECT on all, INSERT on all, UPDATE on runs + designs

### Fly.io Cloud Watcher
- **App:** project-ava-watcher (https://fly.io/apps/project-ava-watcher)
- **Account:** halevanthien@gmail.com (GitHub login, credit card added)
- **Region:** iad (Ashburn, Virginia)
- **VM:** shared-cpu-1x, 512MB
- **Container:** Python 3.13 + Icarus Verilog + cocotb 2.0.1
- **Backend:** Anthropic API (ANTHROPIC_API_KEY set as Fly secret)
- **Behavior:** Polls Supabase every 5s for `backend='pending'` runs, processes them
- **Deploy:** `fly deploy` from project root
- **Logs:** `fly logs --app project-ava-watcher`
- **Cost:** Free tier (credit card required but not charged for small VM)

### GitHub
- **Repo:** github.com/vanthienha199/project-ava
- **Commits:** 12 on main (as of session 4)
```
f58248f — Initial release: agentic hardware verification framework
4e9671a — Add power state machine and DVFS controller to golden suite
dfa19c7 — Add failure analysis taxonomy to agent pipeline
52481ee — Update PROGRESS.md with complete session context
3dcc741 — Expand to 11 designs, add web platform and Supabase backend
7f225cf — Add live agent reporting and fix Supabase integration
0812011 — Show latest passing run on Live page when idle
70bf7ad — Add Upload page and agent watcher for interactive verification
a4e8da5 — Add Fly.io cloud deployment for autonomous watcher
ac8d001 — Update PROGRESS.md with session 3 context and add test file
e834cfd — Expand to 15 designs with external sources, add testbench viewer
(next)  — Update PROGRESS.md with session 4 context
```

---

## FULL AUTONOMOUS FLOW (How It Works End-to-End)

```
User (Browser)                     Supabase Cloud                  Fly.io (Watcher)
┌─────────────────┐               ┌──────────────────┐           ┌──────────────────┐
│ 1. Upload page   │               │                  │           │                  │
│    Paste Verilog │──INSERT───────▶ designs table     │           │                  │
│    + spec        │──INSERT───────▶ runs (pending)    │           │                  │
│                  │               │                  │           │                  │
│ 2. Live page     │               │         ◀────────────POLL────│ watcher.py       │
│    (watching)    │               │                  │──────────▶│ finds pending    │
│                  │               │                  │           │                  │
│                  │               │                  │           │ 3. Downloads     │
│                  │               │                  │           │    Verilog + spec │
│                  │               │                  │           │                  │
│                  │               │                  │           │ 4. Calls Claude  │
│                  │               │                  │           │    (Anthropic API)│
│                  │               │                  │           │                  │
│                  │               │                  │           │ 5. Generates     │
│                  │               │                  │           │    cocotb test   │
│                  │               │                  │           │                  │
│                  │               │                  │           │ 6. Runs iverilog │
│                  │               │                  │           │    simulation    │
│                  │               │                  │           │                  │
│                  │               │                  │           │ 7. Self-corrects │
│                  │               │                  │           │    (up to 3+10)  │
│                  │               │                  │           │                  │
│                  │◀──REALTIME────│         ◀────────────PATCH───│ 8. Updates run   │
│ Live page shows  │  (WebSocket)  │ runs (passed)    │           │    with results  │
│ results!         │               │ test_results     │           │                  │
│                  │               │                  │           │                  │
│ 3. Testbench     │               │                  │           │                  │
│    viewer shows  │               │                  │           │                  │
│    generated code│               │                  │           │                  │
└─────────────────┘               └──────────────────┘           └──────────────────┘
```

---

## PROJECT STRUCTURE (March 20, 2026)

```
/Users/hale/projects/project-ava/
├── .git/                          ← GitHub: github.com/vanthienha199/project-ava (12 commits)
├── .gitignore
├── .dockerignore                  ← Auto-generated from .gitignore for Fly.io
├── CLAUDE.md                      ← Instructions for Claude Code
├── PROGRESS.md                    ← THIS FILE
├── Dockerfile                     ← Fly.io container (Python 3.13 + iverilog + cocotb)
├── fly.toml                       ← Fly.io app config (project-ava-watcher)
├── venv/                          ← Python 3.13 virtualenv (local only)
├── src/
│   ├── __init__.py
│   ├── __main__.py                ← CLI (python3 -m src benchmark, --backend, --ollama-url)
│   ├── llm.py                     ← LLM wrapper (3 backends, 300s timeout, 8192 max tokens)
│   ├── generator.py               ← Prompt-based generation + cocotb 2.0 auto-fixes
│   ├── simulator.py               ← Icarus Verilog runner + structured result parsing
│   ├── corrector.py               ← Error-feedback correction (2000 char truncation)
│   ├── agent.py                   ← Two-tier orchestrator + live reporter integration
│   ├── analyzer.py                ← Failure taxonomy (9 categories)
│   ├── reporter.py                ← Live status reporter (pushes to Supabase during runs)
│   └── watcher.py                 ← Polls Supabase for pending uploads, runs agent
├── prompts/
│   ├── v1_generate.txt            ← Generation prompt (includes cocotb 2.0 rules)
│   └── v1_correct.txt             ← Correction prompt
├── golden/                        ← Golden test suite (18 designs)
│   ├── 01_adder/                  ← 4-bit adder (combinational)
│   ├── 02_alu/                    ← 8-bit ALU (5 ops + zero flag)
│   ├── 03_icg/                    ← Integrated clock gating cell (POWER-AWARE)
│   ├── 04_counter/                ← 4-bit counter (sequential)
│   ├── 05_freq_divider/           ← Divide-by-2/4/8 (POWER-AWARE, DVFS)
│   ├── 06_power_fsm/              ← Power state machine (POWER-AWARE)
│   ├── 07_dvfs_controller/        ← Full DVFS controller (POWER-AWARE, the gap)
│   ├── 08_shift_register/         ← 8-bit shift register (sequential)
│   ├── 09_fifo/                   ← Synchronous FIFO (buffer/memory)
│   ├── 10_pwm/                    ← PWM generator (POWER-AWARE)
│   ├── 11_uart_tx/                ← UART 8N1 transmitter (protocol)
│   ├── 12_watchdog/               ← 32-bit watchdog timer (from Efabless EF_WDT32)
│   ├── 13_traffic_light/          ← Highway/farm road FSM (from fpga4student)
│   ├── 14_spi_master/             ← SPI Mode 0 master (from nandland, MIT license)
│   ├── 15_priority_encoder/       ← 8-input interrupt priority encoder (from harishs1313)
│   ├── 16_i2c_master/            ← I2C single-byte master (protocol, session 5)
│   ├── 17_arbiter/               ← 4-port round-robin arbiter (sequential, session 5)
│   └── 18_memory_controller/     ← 256x8 synchronous SRAM controller (buffer/memory, session 5)
├── docs/                          ← Web platform (6 pages, Matrix theme, Supabase)
│   ├── index.html                 ← Dashboard — stats, benchmark table, charts
│   ├── designs.html               ← Design browser — Verilog source + specs
│   ├── upload.html                ← Upload & Verify — handles duplicate names (upsert)
│   ├── history.html               ← Run history — sortable, filterable
│   ├── analyze.html               ← Run analysis — iteration timeline, failures
│   └── live.html                  ← Live monitor + testbench viewer + copy button
├── scripts/
│   ├── setup_db.sql               ← Supabase schema (5 tables, RLS, indexes)
│   ├── enable_realtime.sql        ← Enable Realtime + UPDATE policies (runs + designs)
│   └── upload_results.py          ← Bulk upload golden designs + run results
├── runs/                          ← Auto-generated JSON run logs (gitignored)
├── research/
│   ├── RESEARCH_FINDINGS.md       ← cocotb 2.0 traps, CorrectBench, prompt rules
│   └── (reference dirs)
└── test_upload_flow.v             ← Test file for upload flow (mux4to1)
```

---

## HOW TO RUN

### Local Development
```bash
# Activate venv
source /Users/hale/projects/project-ava/venv/bin/activate

# Run benchmark on all 15 golden designs
python3 -m src benchmark

# Run with Anthropic API
python3 -m src benchmark --backend anthropic_api

# Run single design
python3 -m src run --design-dir golden/07_dvfs_controller

# Run with remote Ollama (e.g., Vast.ai SSH tunnel)
python3 -m src run --design-dir golden/01_adder --backend ollama --model deepseek-coder:33b --ollama-url http://localhost:11435

# Upload results to Supabase
python3 scripts/upload_results.py

# Start local watcher (picks up uploads from website)
python3 -m src.watcher

# Preview website locally
python3 -m http.server 8080 --directory docs
```

### Deploy Website
```bash
# Drag docs/ folder to app.netlify.com (manual deploy)
```

### Deploy Watcher to Fly.io
```bash
fly deploy                                              # rebuild + deploy
fly logs --app project-ava-watcher                      # check logs
fly status --app project-ava-watcher                    # check machine status
fly secrets set ANTHROPIC_API_KEY=<key>                 # set API key
fly machine start <id> --app project-ava-watcher        # start if stopped
```

---

## KEY MODULES

**src/llm.py** — LLM wrapper with 3 backends:
- `claude_cli`: calls `claude -p` via subprocess (300s timeout)
- `anthropic_api`: calls Anthropic API via urllib (300s timeout, 8192 max tokens)
- `ollama`: calls Ollama API (supports `base_url` for remote servers)

**src/generator.py** — Prompt builder + cocotb 2.0 auto-fixes (8 patterns)

**src/simulator.py** — Icarus Verilog runner + structured SimResult parsing

**src/corrector.py** — Error-feedback to LLM (error truncation at 2000 chars)

**src/agent.py** — Two-tier orchestrator:
- IC_MAX=3 corrections, IR_MAX=10 reboots
- Graceful timeout handling (forces reboot on LLM failure)
- Integrates with LiveReporter for real-time status

**src/reporter.py** — Pushes live status to Supabase during agent execution:
- `start_run()` → INSERT pending row
- `update_iteration()` → PATCH with progress
- `complete_run()` → PATCH with final results
- `report_test_result()` → INSERT individual test results
- Never crashes the agent (all errors caught)

**src/watcher.py** — Polls Supabase for pending uploads:
- Finds runs with `backend='pending'`
- Downloads Verilog + spec from designs table
- Creates temp dir, runs agent, updates results
- Runs continuously with 5s poll interval
- Used locally (`python3 -m src.watcher`) or on Fly.io

**src/__main__.py** — CLI entry point:
- `python3 -m src run --design-dir <dir>` — single design
- `python3 -m src benchmark` — all golden designs
- Reads spec from `spec.txt` OR `config.json` (session 4 fix)
- Supports `--backend`, `--model`, `--ollama-url`

**src/analyzer.py** — 9-category failure taxonomy:
- SYNTAX, COCOTB_API, SIGNAL_ACCESS, TIMING, LOGIC, COMPILE, IMPORT, TIMEOUT, UNKNOWN

---

## ENVIRONMENT

### This Mac (M4, 16GB, macOS Sequoia)
```
Python 3.13.12         — in venv
Icarus Verilog 13.0    — brew
cocotb 2.0.1           — pip in venv
Ollama 0.18.1          — brew (DeepSeek-Coder 6.7B local)
Docker 28.1.1          — for Fly.io builds
Fly CLI                — brew install flyctl
Anthropic API          — $5 credits, key in ~/.zshrc
```

### Vast.ai (Used for DeepSeek-Coder-33B benchmark)
- 1x RTX 5090, 32GB VRAM, $0.43/hr
- SSH: `ssh -p 55813 root@47.186.29.91`
- Ollama installed with deepseek-coder:33b pulled
- SSH tunnel: `ssh -N -L 11435:localhost:11434 -p 55813 root@47.186.29.91`
- **Instance should be destroyed when not in use** to save money

### Alienware 16 Area 51 (Dr. Wu's lab)
- Intel Ultra 9 275HX, RTX 5080 (16GB), 32GB DDR5
- Ubuntu Linux, user: `demo`, WiFi IP: 192.168.1.171
- SSH blocked: `AllowGroups` in sshd_config restricts to `cecs computers admins`, `support`, `remote`
- **Needs Priyank Pathak** to run `usermod -aG remote demo` as root
- Ollama NOT installed (no sudo)

### AMD Machine Access (pending)
- Dr. Wu submitted Ha Le's info to AMD
- Name: Ha Le, Email: th273073@ucf.edu, userid: th273073
- GitHub: vanthienha199, SSH key: RSA (submitted)
- Estimated ~1 week for access
- Plan: Run lit_silicon on advanced AMD GPUs once access granted

---

## COMPETITIVE LANDSCAPE (March 2026)

| Tool | Best Result | Gap |
|---|---|---|
| AutoBench | 52% pass | No self-correction |
| CorrectBench | 70% pass | Only simple designs, unexplained 28% failure |
| ConfiBench | 72% pass | Still fails sequential |
| MAGE | 95.7% syntax | RTL generation only, not verification |
| Cadence ChipStack | Commercial | Closed, $$$ |
| ChipAgents | Startup ($74M) | Closed, multi-agent |

**Project Ava advantages:**
1. **Power-aware verification = FIRST** — no other AI tool does DVFS/ICG/power FSM
2. **100% pass rate** on 15-design golden suite (vs 52-72% for academic tools)
3. **External designs proven** — 4 designs from open-source repos, never seen before, all pass
4. **Open-source agent** — all commercial tools are closed
5. **cocotb 2.0 auto-fixes** — no other tool handles the API migration
6. **Failure taxonomy** — 9-category analysis (CorrectBench can't explain failures)
7. **Fully autonomous web platform** — upload → verify → results (no other tool has this)
8. **LLM comparison data** — Claude 100% vs DeepSeek 0% proves commercial LLMs dominate
9. **Testbench viewer** — users can see exactly what the AI generated

---

## WHAT TO BUILD NEXT (Priority Order)

### Done (Session 1 — March 19, 1:30 AM)
- [x] Full agent pipeline — generator, simulator, corrector, orchestrator, CLI
- [x] 7 golden designs — adder, ALU, ICG, counter, freq_divider, power_fsm, DVFS controller
- [x] Failure taxonomy — 9-category analyzer module
- [x] 3 commits pushed to GitHub

### Done (Session 2 — March 19 evening)
- [x] Expanded golden suite to 11 designs (shift register, FIFO, PWM, UART TX)
- [x] Anthropic API integration ($5 credits, --backend anthropic_api)
- [x] Graceful timeout handling (forces reboot on LLM failure)
- [x] Error truncation (2000 char cap in corrector)
- [x] Full web platform (5 pages, Matrix theme, Supabase backend)
- [x] Supabase database (5 tables, RLS, indexes, data uploaded)

### Done (Session 3 — March 20 morning)
- [x] Fixed Supabase JS bug — `const supabase` shadowed CDN global, renamed to `sb`
- [x] Live reporter — src/reporter.py pushes real-time status during agent runs
- [x] Live page shows completed runs — latest passing run displayed when idle
- [x] Pipeline icons fixed — replaced emojis with terminal-style glyphs
- [x] DeepSeek-Coder-33B benchmark — Vast.ai RTX 5090, 0/2 designs (Claude 100% vs 0%)
- [x] Upload page — paste Verilog + spec, submit for verification, 3 example designs
- [x] Agent watcher — src/watcher.py polls Supabase for pending uploads, runs agent
- [x] Fly.io cloud deployment — watcher runs 24/7 autonomously, no terminal needed
- [x] Netlify deployment — public URL live
- [x] Supabase Realtime enabled — runs, iterations, test_results tables
- [x] Full end-to-end test — mux4to1 uploaded via web, watcher picked up, PASS 8/8
- [x] test_adder_2 cloud test — Fly.io watcher processed autonomously, PASS 10/10

### Done (Session 4 — March 20 afternoon)
- [x] **Full agentic AI investigation** — read all Dr. Wu Slack messages, ACM panel transcript, analyzed his research direction
- [x] **Research paper analysis** — arXiv:2506.04301 "Cost of Dynamic Reasoning" (HPCA 2026) + 5 more papers on agentic AI infrastructure
- [x] **Decision: keep Ava separate from infrastructure research** — Ava is verification tool, infrastructure characterization is separate project
- [x] **Fixed duplicate design name crash** — Upload page now upserts (updates existing design instead of erroring)
- [x] **Testbench viewer on Live page** — shows AI-generated cocotb code with COPY button and line count
- [x] **VIEW CODE links** on recent run cards — click to see any run's generated testbench
- [x] **4 new external designs added** — watchdog (Efabless), traffic light FSM (fpga4student), SPI master (nandland), priority encoder (harishs1313)
- [x] **All 4 pass: 15/15 designs, 147/147 tests, 100%** — SPI master passed first-try!
- [x] **__main__.py updated** — reads spec from config.json when spec.txt doesn't exist
- [x] **UPDATE RLS policy on designs table** — enables upload page upsert
- [x] **Netlify renamed** — project-ava-ucf.netlify.app (project-ava was taken)
- [x] **Results uploaded to Supabase** — all 15 designs + runs in database
- [x] **Fly.io redeployed** — watcher has latest code
- [x] **Pushed to GitHub** — 12 commits on main
- [x] **Memory files updated** — project-ava.md + MEMORY.md index

### Done (Session 5 — March 20, 2026 evening)
- [x] **3 new golden designs** — I2C master (10/10), round-robin arbiter (11/11), SRAM memory controller (14/14)
- [x] **SHA-256 core** (secworks, 929 lines, BSD-2, ASIC-proven in 40nm) — 9/9 tests with NIST FIPS 180-4 vectors
- [x] **19/19 designs, 191/191 tests, 100% pass rate**
- [x] **Mutation testing engine** — first open-source Verilog mutation tester for cocotb
- [x] **Mutation testing on all 19 designs** — 546 mutants, 389 killed, 71.2% overall score
- [x] **4 designs at 100% mutation score** — adder, ALU, ICG, SHA-256
- [x] **SHA-256: 96 mutants, 100% killed** — strongest testbench in the suite
- [x] **Toggle coverage analyzer** — VCD parsing for signal toggle coverage
- [x] **API backend switched to official anthropic SDK** — proper timeout handling
- [x] **Testbenches for all 19 designs** saved in runs/
- [x] **API retry with backoff** — SDK handles 429/529 automatically
- [x] **Results uploaded to Supabase** — all 19 designs in database
- [x] **17 commits pushed to GitHub**

### Next (High Priority)
- [ ] **Buy domain** — projectava.dev (~$12/yr), point to Netlify
- [ ] **Present to Dr. Wu** — Live demo: upload DVFS controller, watch agent verify, show testbench
- [ ] **Clean up Supabase data** — Remove or properly mark DeepSeek benchmark failures

### Research / Paper
- [ ] **Write up results** — 19/19 (100%), 71.2% mutation score, power-aware gap, Claude vs DeepSeek
- [ ] **Present to AMD panel** — Live demo on unseen design + mutation score data
- [ ] **Read agentic AI infrastructure papers** — for Dr. Wu's research direction (separate from Ava)

### Stretch
- [ ] **Auto-generate spec from Verilog** — Parse ports, operations, clock/reset
- [ ] **UPF integration** — Power domain info
- [ ] **Parallel design execution** — asyncio for faster benchmarks
- [ ] **Coverage metrics** — toggle, branch, FSM coverage (what verification engineers care about)

---

## IMPORTANT FINDINGS

### Performance
- **LLM is 99.1% of total runtime** — simulation is ~650ms
- **Correction calls 2-5x slower** than generation
- **Anthropic API same speed as claude -p** — model inference dominates
- **DeepSeek-Coder-33B: 0% pass rate** — cocotb 2.0 API trap kills open-source LLMs
- **SPI master passed first-try** — 11 tests, 52s (protocol designs can be easy if spec is clear)
- **Watchdog and traffic light needed reboots** — timer/FSM designs are harder for LLMs

### Technical
- **cocotb 2.0 auto-fixes are essential** — 8 patterns LLMs always get wrong
- **Icarus Verilog has ZERO UPF support** — but clock gating, DVFS, power FSMs work as plain Verilog
- **Shift register was hardest** — 660s, 7 iterations, 1 reboot
- **Self-correction validated** — 13/18 designs needed corrections, all recovered to 100%
- **External designs work** — 4 designs from GitHub repos the agent never saw, all pass

---

## BUDGET
| Item | Cost | Status |
|---|---|---|
| Anthropic API credits | $5 loaded | ACTIVE — key in ~/.zshrc + Fly.io secret |
| Supabase | $0 | Free tier (annecgjackson@gmail.com) |
| Netlify | $0 | Free tier (halevanthien@gmail.com) |
| Fly.io | $0 | Free tier (halevanthien@gmail.com, card added) |
| Vast.ai | ~$0.50 spent | RTX 5090 $0.43/hr — DESTROY WHEN NOT IN USE |
| Domain | ~$12/yr | Not yet purchased |
| **Total spent** | **~$5.50** | |

---

## GIT AUTHOR RULES (CRITICAL)
- **ALWAYS:** `--author="Ha Le <halevanthien@gmail.com>"`
- **NEVER** add Co-Authored-By Claude
- **NEVER** mention Claude in any commit

---

## BEHAVIORAL NOTES FOR NEXT CHAT
- **Never use inline Python in shell commands** — always write to a file
- **Never ask "what do you want next"** — proceed with what's most optimal
- **This is a breakthrough product** — not a school project. Think commercially.
- **cocotb 2.0 rules MUST be in every LLM prompt**
- **Supabase account:** annecgjackson@gmail.com (NOT halevanthien — that has unpaid invoice)
- **Fly.io account:** halevanthien@gmail.com (GitHub login)
- **Netlify account:** halevanthien@gmail.com
- **Dr. Wu wants agentic AI SYSTEMS research** — how workloads stress hardware (CPU/GPU/memory). Keep this separate from Ava's verification tool purpose.
- **AMD machine access pending** — ~1 week, for running lit_silicon on AMD GPUs
