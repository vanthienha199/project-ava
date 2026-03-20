# Project Ava — Full Progress & Context for New Chat
**Last Updated:** March 20, 2026, 12:45 PM EST
**Author:** Ha Le (halevanthien@gmail.com)
**READ THIS FILE 100% BEFORE DOING ANYTHING**

---

## WHAT IS THIS PROJECT?

Project Ava (Automated Intelligent Verification with Agents) is a **fully autonomous AI agent platform** for hardware verification. Users upload a Verilog design + natural language spec on the website, and the cloud-deployed agent automatically generates a cocotb testbench, simulates with Icarus Verilog, self-corrects until tests pass, and streams results live to the dashboard.

**It is now a real agentic AI application** — no terminal needed. The watcher runs 24/7 on Fly.io, picks up uploads from Supabase, and verifies designs autonomously using the Anthropic API.

### CURRENT STATUS: FULLY AUTONOMOUS CLOUD PLATFORM — 11/11 DESIGNS, 103/103 TESTS

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

**Total: 11/11 designs passed, 103/103 tests, 5 power-aware designs, 100% pass rate.**

### LLM Comparison (March 20, 2026)
| LLM | Backend | Adder | ALU | Pass Rate | Notes |
|---|---|---|---|---|---|
| **Claude (Sonnet)** | claude_cli / anthropic_api | PASS 6/6 | PASS 6/6 | **100%** (11/11) | All designs pass |
| **DeepSeek-Coder-33B** | Ollama (RTX 5090 via Vast.ai) | FAIL 0/0 | FAIL 0/4 | **0%** (0/2) | cocotb 2.0 trap kills it |

### Who It Serves
1. **ACM Club Project** — Ha Le is on the Agent + Automation teams. Dylan is PM. AMD funds via Rex McCurry. 16 students, 4 teams.
2. **Dr. Di Wu's Lab (Unary Lab, UCF)** — Agentic AI research.
3. **Personal Research / Breakthrough** — First AI tool for DVFS/power-aware verification. Companies like AMD would want this.

### The Unique Angle
Derek Martin (AMD engineer) works on DVFS verification. Dr. Wu's Lit Silicon paper is about DVFS throttling causing GPU stragglers. **Project Ava prevents DVFS bugs at design time.** Nobody else has done this.

---

## LIVE DEPLOYMENT (March 20, 2026)

### Public Website
- **URL:** https://astonishing-sorbet-80c3d2.netlify.app (rename to project-ava.netlify.app)
- **Host:** Netlify (free tier) — deploy by dragging `docs/` folder
- **6 pages:** Dashboard, Designs, Upload, History, Analyze, Live
- **Theme:** Matrix (ThermalTrace clone) — #000 bg, #00ff00 green, Share Tech Mono, matrix rain

### Supabase Database
- **URL:** https://yvpmoyzggbcfaldhsbkl.supabase.co
- **Account:** annecgjackson@gmail.com (free tier)
- **Tables:** designs, runs, iterations, failures, test_results
- **Realtime:** Enabled on runs, iterations, test_results (for Live page)
- **RLS:** Anonymous SELECT on all, INSERT on all, UPDATE on runs

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
- **Commits:** 10 on main
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
(next)  — Update PROGRESS.md with session 3 context
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
└─────────────────┘               └──────────────────┘           └──────────────────┘
```

---

## PROJECT STRUCTURE (March 20, 2026)

```
/Users/hale/projects/project-ava/
├── .git/                          ← GitHub: github.com/vanthienha199/project-ava (10 commits)
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
├── golden/                        ← Golden test suite (11 designs, all with config.json)
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
│   └── 11_uart_tx/                ← UART 8N1 transmitter (protocol)
├── docs/                          ← Web platform (6 pages, Matrix theme, Supabase)
│   ├── index.html                 ← Dashboard — stats, benchmark table, charts
│   ├── designs.html               ← Design browser — Verilog source + specs
│   ├── upload.html                ← Upload & Verify — paste Verilog + spec, submit
│   ├── history.html               ← Run history — sortable, filterable
│   ├── analyze.html               ← Run analysis — iteration timeline, failures
│   └── live.html                  ← Live monitor — realtime via Supabase subscriptions
├── scripts/
│   ├── setup_db.sql               ← Supabase schema (5 tables, RLS, indexes)
│   ├── enable_realtime.sql        ← Enable Supabase Realtime + UPDATE policy
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

# Run benchmark on all 11 golden designs
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
2. **100% pass rate** on golden suite (vs 52-72% for academic tools)
3. **Open-source agent** — all commercial tools are closed
4. **cocotb 2.0 auto-fixes** — no other tool handles the API migration
5. **Failure taxonomy** — 9-category analysis (CorrectBench can't explain failures)
6. **Fully autonomous web platform** — upload → verify → results (no other tool has this)
7. **LLM comparison data** — Claude 100% vs DeepSeek 0% proves commercial LLMs dominate

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

### Done (Session 3 — March 20, 2026)
- [x] **Fixed Supabase JS bug** — `const supabase` shadowed CDN global, renamed to `sb`
- [x] **Live reporter** — src/reporter.py pushes real-time status during agent runs
- [x] **Live page shows completed runs** — latest passing run displayed when idle
- [x] **Pipeline icons fixed** — replaced emojis with terminal-style glyphs
- [x] **DeepSeek-Coder-33B benchmark** — Vast.ai RTX 5090, 0/2 designs (Claude wins 100% vs 0%)
- [x] **Upload page** — paste Verilog + spec, submit for verification, 3 example designs
- [x] **Agent watcher** — src/watcher.py polls Supabase for pending uploads, runs agent
- [x] **Fly.io cloud deployment** — watcher runs 24/7 autonomously, no terminal needed
- [x] **Netlify deployment** — public URL live (astonishing-sorbet-80c3d2.netlify.app)
- [x] **Supabase Realtime enabled** — runs, iterations, test_results tables
- [x] **Full end-to-end test** — mux4to1 uploaded via web, watcher picked up, PASS 8/8
- [x] **test_adder_2 cloud test** — Fly.io watcher processed autonomously, PASS 10/10
- [x] **10 commits on GitHub**

### Next (High Priority)
- [ ] **Rename Netlify site** to project-ava.netlify.app
- [ ] **Buy domain** — projectava.dev (~$12/yr), point to Netlify
- [ ] **Handle duplicate design names** — Upload page should allow same name or auto-suffix
- [ ] **Clean up Supabase data** — Remove failed DeepSeek runs or mark them properly
- [ ] **More golden designs** — SPI master, I2C, watchdog timer

### Research / Paper
- [ ] **Write up results** — Claude 100% vs DeepSeek 0%, power-aware gap, failure taxonomy
- [ ] **Present to Dr. Wu** — Working demo: upload DVFS controller, watch it verify live
- [ ] **Present to AMD panel** — Live demo on unseen design

### Stretch
- [ ] **Auto-generate spec from Verilog** — Parse ports, operations, clock/reset
- [ ] **UPF integration** — Power domain info
- [ ] **Parallel design execution** — asyncio for faster benchmarks

---

## IMPORTANT FINDINGS

### Performance
- **LLM is 99.1% of total runtime** — simulation is ~650ms
- **Correction calls 2-5x slower** than generation
- **Anthropic API same speed as claude -p** — model inference dominates
- **DeepSeek-Coder-33B: 0% pass rate** — cocotb 2.0 API trap kills open-source LLMs

### Technical
- **cocotb 2.0 auto-fixes are essential** — 8 patterns LLMs always get wrong
- **Icarus Verilog has ZERO UPF support** — but clock gating, DVFS, power FSMs work as plain Verilog
- **Shift register was hardest** — 660s, 7 iterations, 1 reboot
- **Self-correction validated** — 6/11 designs needed corrections, all recovered to 100%

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
