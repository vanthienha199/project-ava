# Project Ava — Full Progress & Context for New Chat
**Last Updated:** March 19, 2026, 9:30 PM EST
**Author:** Ha Le (halevanthien@gmail.com)
**READ THIS FILE 100% BEFORE DOING ANYTHING**

---

## WHAT IS THIS PROJECT?

Project Ava (Automated Intelligent Verification with Agents) is a **working AI agent that automatically generates hardware verification testbenches**. Given a Verilog design file + natural language spec, the agent generates a cocotb (Python) testbench, runs Icarus Verilog simulation, and self-corrects until tests pass.

**It now has a full web platform** (like ThermalTrace) with Matrix theme, backed by Supabase, showing live benchmark data.

### CURRENT STATUS: WORKING AGENT + WEB PLATFORM — 11/11 DESIGNS, 103/103 TESTS

The agent is **fully built and functional**. It has been tested on 11 designs across 5 categories including power-aware RTL that no other AI tool can verify. Benchmark results from March 19, 2026:

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

### Design Categories
- **Combinational (2):** adder, ALU
- **Sequential (2):** counter, shift register
- **Power-aware (5):** ICG clock gating, frequency divider, power FSM, DVFS controller, PWM generator
- **Buffer/Memory (1):** FIFO
- **Protocol (1):** UART TX (8N1 serial)

### Who It Serves
1. **ACM Club Project** — Ha Le is on the Agent + Automation teams. Dylan is PM. AMD funds the project via Rex McCurry (AMD Orlando Site Lead). 16 students, 4 teams (Agents, Automation, FPGA Dev, Research). Semester goal: "one agent that can generate a verification test bench."
2. **Dr. Di Wu's Lab (Unary Lab, UCF)** — Ha Le's research advisor. Dr. Wu asked Ha Le to research agentic AI systems. This project IS that research.
3. **Personal Research / Breakthrough** — Must be something big companies (AMD etc.) would want to buy/license. Power-aware verification is the untouched gap — nobody else has built an AI agent for DVFS, clock gating, or power state machine verification.

### Target Users (decided March 19)
- **Primary (A):** Verification engineers at companies like AMD — CLI tool, assumes HDL knowledge, outputs coverage metrics
- **Secondary (D):** Researchers — metrics, benchmarks, reproducible results, comparison tables for papers

### The Unique Angle
Derek Martin (AMD engineer, ACM panel March 4) works on "features that turn stuff off to save power" — DVFS verification. Dr. Wu's Lit Silicon paper is about thermal imbalance causing DVFS throttling. **Project Ava connects both**: an AI verification agent specifically for power management RTL. Nobody else has done this.

**Important nuance (from critical review):** The Lit Silicon connection is **motivational, not technical**. Lit Silicon proves DVFS bugs matter (stragglers cost throughput). Project Ava prevents those bugs at design time. Don't claim "thermal-informed test generation" unless you actually build it — do claim "motivated by real-world DVFS failures documented in Lit Silicon."

---

## WHAT EXISTS RIGHT NOW (March 19, 2026)

### Project Structure
```
/Users/hale/projects/project-ava/
├── .git/                          ← GitHub: github.com/vanthienha199/project-ava (4 commits on main)
├── .gitignore
├── CLAUDE.md                      ← Instructions for Claude Code
├── PROGRESS.md                    ← THIS FILE
├── venv/                          ← Python 3.13 virtualenv with cocotb 2.0.1
├── src/
│   ├── __init__.py
│   ├── __main__.py                ← CLI entry point (python3 -m src benchmark, supports --backend)
│   ├── llm.py                     ← LLM wrapper (Claude CLI, Anthropic API, Ollama) — 300s timeout, 8192 max tokens
│   ├── generator.py               ← Prompt-based testbench generation + cocotb 2.0 auto-fixes
│   ├── simulator.py               ← Icarus Verilog runner with structured result parsing
│   ├── corrector.py               ← Error-feedback correction loop (error truncation at 2000 chars)
│   ├── agent.py                   ← Two-tier orchestrator (graceful timeout handling, forces reboot on LLM failure)
│   └── analyzer.py                ← Failure taxonomy (9 error categories)
├── prompts/
│   ├── v1_generate.txt            ← Generation prompt template (includes cocotb 2.0 rules)
│   └── v1_correct.txt             ← Correction prompt template
├── golden/                        ← Golden test suite (11 designs, all with config.json)
│   ├── 01_adder/                  ← 4-bit adder (combinational)
│   ├── 02_alu/                    ← 8-bit ALU (5 ops + zero flag)
│   ├── 03_icg/                    ← Integrated clock gating cell (POWER-AWARE)
│   ├── 04_counter/                ← 4-bit counter (sequential)
│   ├── 05_freq_divider/           ← Divide-by-2/4/8 (POWER-AWARE, DVFS component)
│   ├── 06_power_fsm/              ← Power state machine with thermal throttling (POWER-AWARE)
│   ├── 07_dvfs_controller/        ← Full DVFS controller (POWER-AWARE, the research gap)
│   ├── 08_shift_register/         ← 8-bit shift register with 4 modes (sequential)
│   ├── 09_fifo/                   ← Synchronous FIFO, 8-deep (buffer/memory)
│   ├── 10_pwm/                    ← PWM generator for voltage regulation (POWER-AWARE)
│   └── 11_uart_tx/                ← UART 8N1 transmitter (protocol)
├── docs/                          ← Web platform (5 pages, Matrix theme, Supabase-connected)
│   ├── index.html                 ← Dashboard — stats, benchmark table, charts (dynamic from Supabase)
│   ├── designs.html               ← Design browser — view Verilog source + specs, filter by category
│   ├── history.html               ← Run history — all runs, sortable, filterable
│   ├── analyze.html               ← Run analysis — deep dive into single run, iteration timeline, failures
│   └── live.html                  ← Live monitor — realtime agent status via Supabase subscriptions
├── scripts/
│   ├── setup_db.sql               ← Supabase schema (5 tables, RLS policies, indexes)
│   └── upload_results.py          ← Upload golden designs + run results to Supabase (retry logic)
├── runs/                          ← Auto-generated JSON run logs (gitignored)
├── research/
│   ├── RESEARCH_FINDINGS.md       ← cocotb 2.0 traps, CorrectBench algorithm, prompt rules
│   ├── cocotb_test/               ← Working adder test (reference)
│   ├── claude_gen_test/           ← Claude-generated ALU test (reference)
│   ├── icg_test/                  ← ICG proof-of-concept (hand-written + LLM-generated)
│   └── iiitb_cg/                  ← Cloned ICG repo (github.com/drvasanthi/iiitb_cg)
├── test_agent_icg.py              ← Single design test script
├── test_agent_all.py              ← Multi-design test script
├── test_new_designs.py            ← Power-aware designs test script
├── run_new_designs.py             ← Run 3 new designs only
├── test_simulator.py              ← Simulator module test
└── test_cli_benchmark.py          ← CLI benchmark test
```

### How to Run

```bash
# Activate venv (ALWAYS do this first)
source /Users/hale/projects/project-ava/venv/bin/activate

# Run benchmark on all 11 golden designs
python3 -m src benchmark

# Run with Anthropic API (has token tracking)
python3 -m src benchmark --backend anthropic_api

# Run on a single design directory
python3 -m src run --design-dir golden/07_dvfs_controller

# Upload results to Supabase (after benchmark)
python3 scripts/upload_results.py

# Upload only runs (skip designs)
python3 scripts/upload_results.py --runs-only
```

### Web Platform

```bash
# Preview locally
open /Users/hale/projects/project-ava/docs/index.html

# Deploy to Netlify: drag docs/ folder to app.netlify.com
```

**5 pages:** Dashboard, Designs, History, Analyze, Live
**Theme:** Matrix (ThermalTrace exact clone) — black bg, #00ff00 green, Share Tech Mono, matrix rain, scan animations
**Backend:** Supabase (free tier)
- URL: https://yvpmoyzggbcfaldhsbkl.supabase.co
- Anon key: in docs/*.html files
- Tables: designs, runs, iterations, failures, test_results
- Data: 11 designs + run results uploaded via scripts/upload_results.py

### Git (4 commits pushed to main)
```
f58248f — Initial release: agentic hardware verification framework
4e9671a — Add power state machine and DVFS controller to golden suite
dfa19c7 — Add failure analysis taxonomy to agent pipeline
52481ee — Update PROGRESS.md with complete session context
```

---

## ENVIRONMENT — VERIFIED WORKING

### This Mac (M4, 16GB, macOS Sequoia)
```
Python 3.13.12         — in venv (cocotb 2.0 needs ≤3.13, system has 3.14)
Icarus Verilog 13.0    — brew install icarus-verilog ✓
Verilator 5.046        — brew install verilator ✓
Ollama 0.18.1          — brew install ollama ✓ (service running)
DeepSeek-Coder 6.7B    — ollama pull deepseek-coder:6.7b ✓ (3.8GB)
cocotb 2.0.1           — in project venv ✓
Anthropic API          — $5 credits loaded, key in ~/.zshrc ✓
```

### LLM Backends (3 available)
```bash
# Claude CLI (free with Max plan, ~15-80s per call, no token tracking)
python3 -m src benchmark --backend claude_cli

# Anthropic API (paid, ~15-80s per call, has token tracking)
python3 -m src benchmark --backend anthropic_api --model claude-sonnet-4-20250514

# Ollama (free local, needs Alienware for 33B model)
python3 -m src benchmark --backend ollama --model deepseek-coder:6.7b
```

### Performance Discovery (This Session)
- **LLM is 99.1% of total runtime** — simulation is only 650ms avg
- **Correction calls are 2-5x slower** than generation (95s avg vs 28-40s)
- **Anthropic API is NOT faster than claude -p** — model inference dominates, not CLI overhead
- **First-pass success matters most** — designs that pass on iteration 1 finish in 14-41s; those needing corrections take 149-661s

### Virtual Environment
```bash
source /Users/hale/projects/project-ava/venv/bin/activate
```

### Other Hardware
- **Alienware 16 Area 51 (AA16250):** Intel Ultra 9 275HX, RTX 5070Ti/5080 (8-16GB VRAM), 32GB DDR5, 2TB SSD — from Dr. Wu's lab. Can run DeepSeek-Coder-33B locally via Ollama. **Not yet set up for SSH from Mac.**

---

## ARCHITECTURE — WHAT'S BUILT

### Agent Pipeline (Working)
```
Input: Verilog DUT file + natural language spec
                    ↓
┌─────────────────────────────────────────────┐
│  GENERATE (src/generator.py)                 │
│  Load prompt template → insert Verilog +     │
│  spec + cocotb 2.0 rules → call LLM →       │
│  strip markdown fences → auto-fix cocotb API │
└──────────────────┬──────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  SIMULATE (src/simulator.py)                 │
│  Write testbench to temp dir → make          │
│  SIM=icarus → parse output → structured      │
│  SimResult (pass/fail, test details, errors)  │
└──────────────────┬──────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  SELF-CORRECT (src/corrector.py + agent.py)  │
│  If FAIL: analyze errors → categorize →      │
│  feed to LLM corrector (max 3 attempts)      │
│  If timeout/error: gracefully force reboot   │
│  If still FAIL: reboot (regenerate fresh,    │
│  max 10 attempts)                            │
└──────────────────┬──────────────────────────┘
                    ↓
Output: Working testbench + SimResult + JSON run log
                    ↓
┌─────────────────────────────────────────────┐
│  UPLOAD (scripts/upload_results.py)          │
│  Push results to Supabase → web platform    │
│  displays live data                          │
└─────────────────────────────────────────────┘
```

### Key Modules

**src/llm.py** — LLM wrapper with 3 backends:
- `claude_cli`: calls `claude -p` via subprocess (free with Max plan, 300s timeout)
- `anthropic_api`: calls Anthropic API via urllib (needs ANTHROPIC_API_KEY, 300s timeout, 8192 max tokens)
- `ollama`: calls Ollama local API (free, localhost:11434)
- Returns: LLMResponse(text, model, tokens_in, tokens_out, latency_ms)

**src/generator.py** — Builds prompt from template, calls LLM, cleans output:
- Loads `prompts/v1_generate.txt` template
- Strips markdown code fences (LLMs wrap output in ```python```)
- Auto-fixes 8 known cocotb 2.0 API errors (units→unit, fork→start_soon, etc.)

**src/simulator.py** — Runs cocotb via Icarus Verilog:
- Creates temp directory, copies Verilog files, writes Makefile + test module
- Runs `make SIM=icarus`, parses output with regex
- Returns SimResult with individual test pass/fail, timing, and error extraction

**src/corrector.py** — Feeds errors back to LLM:
- Uses `prompts/v1_correct.txt` template
- Includes: Verilog source, spec, failed testbench code, error messages
- Error messages truncated to 2000 chars to avoid oversized prompts
- Same cocotb 2.0 auto-fixes as generator

**src/agent.py** — Two-tier orchestrator (CorrectBench algorithm):
- IC_MAX=3 corrections before reboot, IR_MAX=10 reboots before giving up
- **Graceful timeout handling**: if LLM times out during correction, forces reboot instead of crashing
- **Graceful generation failure**: if LLM times out during reboot generation, retries
- Records full history with failure analysis for every iteration
- Outputs JSON run log with all metrics

**src/analyzer.py** — Failure taxonomy (9 categories):
- SYNTAX, COCOTB_API, SIGNAL_ACCESS, TIMING, LOGIC, COMPILE, IMPORT, TIMEOUT, UNKNOWN
- Each failure tagged with whether the corrector can likely fix it

### Web Platform Architecture
```
[Frontend: 5 static HTML pages in docs/]
        ↕ reads/writes via Supabase JS client
[Supabase: PostgreSQL + REST API + Realtime]
        ↑ uploads via scripts/upload_results.py
[Agent: Runs locally on Mac, saves JSON to runs/]
```

**Supabase Tables:**
- `designs` — 11 golden designs with Verilog source + specs
- `runs` — Each agent execution (design, backend, pass/fail, iterations, latency, testbench code)
- `iterations` — Individual generate/correct/reboot steps within a run
- `failures` — Categorized failure analysis per iteration
- `test_results` — Individual test pass/fail per run

**Supabase Project:** https://yvpmoyzggbcfaldhsbkl.supabase.co (free tier, org: project-ava, account: annecgjackson@gmail.com)

### Critical cocotb 2.0 Discovery
LLMs generate cocotb 1.x API code that FAILS. The generator auto-fixes these patterns:
1. `units="ns"` → `unit="ns"` (MOST COMMON — LLMs always get this wrong even with rules in prompt)
2. `.value.integer` → `int(.value)`
3. `cocotb.fork()` → `cocotb.start_soon()`
4. `.kill()` → `.cancel()`
5. `raise TestFailure()` → `assert False`
6. `from cocotb.result import TestFailure` → removed
7. `from cocotb.binary import BinaryValue` → removed
8. `.value.binstr` → `str(.value)`

Also: signal named `in` (Python keyword) must use `getattr(dut, "in").value` — added as rule #11 in prompts.

---

## COMPETITIVE LANDSCAPE (March 2026)

### What Exists
| Tool | Best Result | Gap |
|---|---|---|
| AutoBench | 52% pass | No self-correction |
| CorrectBench | 70% pass | Only simple designs, unexplained 28% failure |
| ConfiBench | 72% pass | Still fails sequential |
| MAGE | 95.7% syntax | RTL generation only, not verification |
| UVM² | 87% coverage | Struggles timing/protocols |
| Cadence ChipStack | Commercial | Closed, $$$, announced Feb 2026 |
| Siemens Questa One | Commercial | Closed, $$$, announced GTC 2026 |
| ChipAgents | Startup ($74M) | Closed, multi-agent root cause analysis |

### What Nobody Can Do (Our Gap)
1. **Power-aware verification = ZERO AI tools exist** — Project Ava is FIRST
2. **Failure categorization** — CorrectBench doesn't explain why it fails, we do
3. **Open-source agent** — All commercial tools are closed/expensive
4. **cocotb 2.0 auto-fixes** — No other tool handles the API migration

### RealBench Reality Check
Best LLM (o1-preview): 13.3% pass on real IP modules, **0% on system-level**. We're at 100% on our golden suite but it's smaller/simpler designs.

### Full research details saved in:
- `/Users/hale/.claude/projects/-Users-hale/memory/project-ava-research.md`
- `/Users/hale/.claude/projects/-Users-hale/memory/project-ava-acm-amd.md`

---

## ACM MEETING & AMD PANEL CONTEXT

### Key People at AMD (from ACM panel March 4, 2026)
| Name | Role | Relevance |
|---|---|---|
| **Rex McCurry** | Site Lead, GPU Architect | Coordinates AMD-UCF. Wants "IP pipeline" (research). |
| **Derek Martin** | Hardware Architect | **"I work on features that turn stuff off to save power."** Direct DVFS customer. |
| **John G** | GPU Power Modeling | Recent UCF grad. Could validate power-aware tests. |
| **Michelle** | Verification (since 2008) | GPU verification → performance verification. |

### AMD's 4 Pillars at UCF
1. Talent pipeline (hiring)
2. Curriculum improvement
3. **IP pipeline (research)** ← Project Ava IS this
4. AI adoption ("AMD believes AI is a huge game changer")

### Key Quotes
- Rex: "Verification is 70-80% of VLSI cycle. If we don't get it right, costs us a lot of money."
- Rex: "We also want an IP pipeline. So that's the research."
- Industry standard: 1 designer : 3 verification engineers

### ACM Team Structure
- 4 teams × 4 people = 16 total
- Teams: Agents, Automation, FPGA Development, Research
- Dylan limited scope to functional verification "because it's our first time" — power-aware is the Phase 2 that impresses AMD

---

## WHAT TO BUILD NEXT (Priority Order)

### Done (Session 1 — March 19, 1:30 AM)
- [x] **Full agent pipeline** — generator, simulator, corrector, orchestrator, CLI
- [x] **7 golden designs** — adder, ALU, ICG, counter, freq_divider, power_fsm, DVFS controller
- [x] **Failure taxonomy** — 9-category analyzer module
- [x] **3 commits pushed** to GitHub

### Done (Session 2 — March 19 evening)
- [x] **Expanded golden suite to 11 designs** — Added shift register, FIFO, PWM, UART TX
- [x] **Anthropic API integration** — $5 credits loaded, `--backend anthropic_api` works
- [x] **Graceful error handling** — Agent survives LLM timeouts (forces reboot instead of crash)
- [x] **Error truncation** — Correction prompts capped at 2000 chars to avoid timeouts
- [x] **All designs have config.json** — Standardized golden suite
- [x] **Full web platform built** — 5 pages (Dashboard, Designs, History, Analyze, Live) with Matrix theme
- [x] **Supabase database** — 5 tables (designs, runs, iterations, failures, test_results) with RLS
- [x] **Upload script** — scripts/upload_results.py pushes agent results to Supabase (with retry logic)
- [x] **Data uploaded** — 11 designs + 9 full runs in Supabase (10_pwm + 11_uart_tx need re-upload)

### Immediate (Finish Web Platform)
- [ ] **Re-upload remaining data** — Run `python3 scripts/upload_results.py --runs-only` to get 10_pwm and 11_uart_tx
- [ ] **Deploy to Netlify** — Drag docs/ folder to app.netlify.com for public URL
- [ ] **Buy domain** — projectava.dev or similar ($12), point to Netlify

### Next (High Impact)
- [ ] **Alienware SSH setup** — Connect Mac → Alienware via SSH, install Ollama + DeepSeek-Coder-33B
- [ ] **Ollama benchmark** — Run all 11 designs with DeepSeek-Coder 6.7B and 33B. Compare pass rates to Claude. Paper result: "open-source LLM vs Claude on power-aware verification."
- [ ] **Analyzer module** — Auto-generate spec from Verilog DUT (parse ports, operations, clock/reset)

### Medium Term
- [ ] **More golden designs** — SPI master, I2C, watchdog timer, memory controller
- [ ] **Run database / learning** — Analyze Supabase data for patterns, improve prompts based on what fails
- [ ] **Parallel design execution** — Run multiple designs concurrently (asyncio) to cut benchmark time

### Research / Paper
- [ ] **Write up results** — Benchmark table, comparison to CorrectBench (72% vs our 100%), failure taxonomy, power-aware gap analysis
- [ ] **Present to Dr. Wu** — Working demo + research narrative
- [ ] **Present to AMD panel** — Live demo on unseen design

### Stretch
- [ ] **UPF integration** — Parse UPF files for power domain info
- [ ] **Cross-domain verification** — Clock × power × reset domain interactions

---

## IMPORTANT FINDINGS FROM THIS SESSION

### Proof of Concept Validated
1. **cocotb CAN verify power-aware designs with Icarus Verilog** — Proved with ICG clock gating cell (5/5 hand-written, 5/5 LLM-generated)
2. **Internal wires (cgclk, q_l, en) are visible via VPI** — No limitation
3. **LLM generates correct power-aware verification logic** — Only API syntax needs fixing
4. **Self-correction loop works** — 6 of 11 designs needed corrections and all recovered to 100%
5. **Shift register needed a full reboot** (7 iterations) — agent still persisted to success

### Performance Analysis (Session 2)
1. **LLM time is 99.1% of total** — simulation is ~650ms, negligible
2. **Correction calls are 2-5x slower than generation** — 95s avg vs 28-40s avg
3. **Anthropic API is same speed as claude -p** — model inference dominates, not CLI overhead
4. **Shift register was hardest** — 660s, 7 iterations, 6 corrections + 1 reboot
5. **UART TX can timeout** — protocol timing verification is genuinely hard for LLMs, but passes with retries

### Critical Limitations Identified
1. **Icarus Verilog has ZERO UPF support** — No power domains, isolation cells, retention. BUT clock gating, freq dividers, power FSMs, DVFS controllers are all plain Verilog and work fine.
2. **LLMs ALWAYS use `units="ns"` instead of `unit="ns"`** — Even with the rule in the prompt. The auto-fix catches this.
3. **Large correction prompts can timeout** — Power FSM and DVFS controller corrections take 50-120s each. UART TX corrections can exceed 300s.
4. **Python keyword `in`** — Signal named "in" requires `getattr(dut, "in")`. Rule #11 in prompts.
5. **Multi-LLM consensus** — No evidence this works for testbench generation. Dropped.
6. **Lit Silicon connection is motivational, not technical** — Can't directly convert thermal traces to test vectors.

### CorrectBench Failure Analysis (Why 28% Fail)
- Sequential circuits: 54.93% pass vs combinational 84.20%
- LLMs fail at: clock cycle timing, signal collection at right time points, driver formatting
- Validator only 88.85% accurate — 11% of validations are wrong
- **Our advantage:** failure taxonomy categorizes every error, enabling targeted improvement

---

## BUDGET
| Item | Cost | Status |
|---|---|---|
| Anthropic API credits | $5 loaded | ACTIVE — key in ~/.zshrc (NEVER commit to git) |
| Supabase | $0 | Free tier (annecgjackson@gmail.com account) |
| DeepSeek API | $0 | Free 5M tokens on signup |
| Domain (projectava.dev) | ~$12/yr | Not yet purchased |
| Hosting (Netlify) | $0 | Free tier |
| Alienware + Ollama | $0 | Free (from lab), needs SSH setup |
| **Total spent so far** | **$5** | Anthropic API credits |

---

## GIT AUTHOR RULES (CRITICAL)
- **ALWAYS:** `--author="Ha Le <halevanthien@gmail.com>"`
- **NEVER** add Co-Authored-By Claude
- **NEVER** mention Claude in any commit
- Author is ONLY Ha Le. No exceptions.

---

## KEY FILES TO READ

| File | What It Contains |
|---|---|
| This file (PROGRESS.md) | Full project context, what's built, what to build next |
| research/RESEARCH_FINDINGS.md | cocotb 2.0 API traps, CorrectBench algorithm, UVM² architecture, prompt rules |
| src/agent.py | Main orchestrator — the pipeline loop |
| src/llm.py | LLM wrapper (3 backends, 300s timeout) |
| src/generator.py | Prompt building + cocotb 2.0 auto-fixes |
| src/simulator.py | Icarus Verilog runner + result parsing |
| src/analyzer.py | Failure taxonomy (9 categories) |
| prompts/v1_generate.txt | Generation prompt template |
| prompts/v1_correct.txt | Correction prompt template |
| golden/07_dvfs_controller/ | The breakthrough design (DVFS controller) |
| docs/index.html | Web platform dashboard (Matrix theme, Supabase) |
| docs/designs.html | Design browser page |
| docs/history.html | Run history page |
| docs/analyze.html | Run analysis page |
| docs/live.html | Live agent monitor page |
| scripts/setup_db.sql | Supabase database schema |
| scripts/upload_results.py | Upload results to Supabase |
| CLAUDE.md | Claude Code instructions for this project |
| /Users/hale/.claude/projects/-Users-hale/memory/project-ava-research.md | Competitive landscape + gaps |
| /Users/hale/.claude/projects/-Users-hale/memory/project-ava-acm-amd.md | ACM meeting + AMD panel context |

---

## BEHAVIORAL NOTES FOR NEXT CHAT
- **Never use inline Python in shell commands** — always write to a file, then tell user to run `python3 filename.py`
- **Never ask "what do you want next"** — proceed with what's most optimal
- **The user wants a breakthrough product** — not just a school project. Think commercially.
- **cocotb 2.0 rules MUST be in every LLM prompt** — see prompts/v1_generate.txt
- **Signal `in` needs getattr()** — this bit us once, auto-fix rule #11
- **Supabase account** — annecgjackson@gmail.com (separate from main halevanthien@gmail.com, created because ThinkTank Research org had unpaid invoice blocking new projects)
- **ThermalTrace Supabase** — on vanthienha199 org (halevanthien@gmail.com), has $41.81 unpaid invoice
