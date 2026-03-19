# Project Ava — Full Progress & Context for New Chat
**Last Updated:** March 18, 2026
**Author:** Ha Le (halevanthien@gmail.com)
**READ THIS FILE 100% BEFORE DOING ANYTHING**

---

## WHAT IS THIS PROJECT?

Project Ava (Automated Intelligent Verification with Agents) is an **AI agent that automatically generates hardware verification testbenches**. Given a Verilog design file + natural language spec, the agent generates a cocotb (Python) testbench, runs simulation, and self-corrects until tests pass.

### Who It Serves
1. **ACM Club Project** — Ha Le is on the Agent + Automation teams. Dylan is PM. AMD funds the project via Rex McCurry (AMD Orlando Site Lead). 16 students, 4 teams. Semester goal: "one agent that can generate a verification test bench."
2. **Dr. Di Wu's Lab (Unary Lab, UCF)** — Ha Le's research advisor. Dr. Wu asked Ha Le to research agentic AI systems over spring break: "how such systems are built, what system components are needed, which parts on CPU vs GPU." This project IS that research — a real agentic AI system Ha Le is building and measuring.
3. **Personal Research** — No existing verification agent targets power-aware RTL (DVFS, clock gating). This is the gap. If Ha Le fills it, it's a real research contribution that impresses AMD.

### The Unique Angle (IMPORTANT)
Derek Martin (AMD engineer, spoke at ACM panel March 4) works on "features that turn stuff off to save power" — DVFS verification. Dr. Wu's Lit Silicon paper is about thermal imbalance causing DVFS throttling. **Ha Le connects both**: build a verification agent specifically for power management RTL. Nobody else has done this.

---

## ENVIRONMENT — VERIFIED WORKING (March 18, 2026)

### This Mac (M4, 16GB, macOS Sequoia)
```
Python 3.14.3          — system (too new for cocotb)
Python 3.13.12         — /opt/homebrew/opt/python@3.13/bin/python3.13
Icarus Verilog 13.0    — brew install icarus-verilog ✓
Verilator 5.046        — brew install verilator ✓
Ollama 0.18.1          — brew install ollama ✓ (service running)
DeepSeek-Coder 6.7B    — ollama pull deepseek-coder:6.7b ✓ (3.8GB)
cocotb 2.0.1           — in project venv (Python 3.13) ✓
Homebrew 5.1.0         — ✓
Docker                 — installed ✓
Git 2.39.5             — ✓
Node v18.20.8          — ✓
```

### Project Location & Repo
```
/Users/hale/projects/project-ava/
├── venv/                          ← Python 3.13 virtualenv with cocotb 2.0.1
├── research/
│   ├── RESEARCH_FINDINGS.md       ← ALL research findings (cocotb 2.0 traps, CorrectBench architecture, etc.)
│   ├── cocotb_test/               ← Working cocotb test (adder, 2/2 pass)
│   └── claude_gen_test/           ← Claude-generated ALU testbench (7/7 pass after fix)
│       ├── alu.v                  ← 8-bit ALU (add/sub/and/or/xor + zero flag)
│       ├── test_alu.py            ← Claude-generated cocotb testbench (FIXED for 2.0 API)
│       └── Makefile
├── PROGRESS.md                    ← THIS FILE
└── .git/                          ← GitHub: github.com/vanthienha199/project-ava
```

### Virtual Environment
```bash
# ALWAYS activate before running cocotb:
source /Users/hale/projects/project-ava/venv/bin/activate

# This venv uses Python 3.13 (cocotb 2.0 requires max 3.13, system has 3.14)
```

### GitHub Repo
- URL: https://github.com/vanthienha199/project-ava
- Public repo, created March 18, 2026
- No commits pushed yet (initial setup only)

### Other Hardware Available
- **Alienware 16 Area 51 (AA16250):** Intel Ultra 9 275HX, RTX 5070Ti/5080 (8-16GB VRAM), 32GB DDR5, 2TB SSD — from Dr. Wu's lab. Can run DeepSeek-Coder-33B locally via Ollama. Not yet set up for SSH from Mac.
- **AMD hpcfund.amd.com:** MI300X GPUs — access NOT granted yet (SSH rejected as of March 18). This is for lit_silicon work, NOT for Project Ava.

---

## LLM STRATEGY

### Primary: `claude -p` (Ha Le's Claude Max Plan)
```bash
echo "your prompt here" | claude -p
```
- FREE (included in Max subscription)
- Best quality for code generation
- ~3-5 sec per call
- **CRITICAL:** Claude does NOT know cocotb 2.0 API. Every prompt MUST include the 10 cocotb rules from RESEARCH_FINDINGS.md section 5.

### Backup: Ollama (Local, Free)
```bash
curl -s http://localhost:11434/api/generate -d '{"model":"deepseek-coder:6.7b","prompt":"...","stream":false}' | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"
```
- Free, unlimited, no rate limits
- Lower quality than Claude
- Good for rapid iteration during development

### Future: Alienware with DeepSeek-Coder-33B
- Much better quality than 6.7B
- Needs Alienware SSH setup first

---

## CRITICAL DISCOVERY: cocotb 2.0 API BREAKS ALL LLM-GENERATED CODE

**This is the single most important finding.** On March 18, we tested `claude -p` generating a cocotb testbench for an 8-bit ALU. Claude produced excellent logic but used cocotb 1.x API syntax. Result: **7/7 tests FAILED.**

After applying cocotb 2.0 fixes (replacing `.value.integer` with `int(.value)`, `units=` with `unit=`): **7/7 tests PASSED.**

**Conclusion:** The prompt template MUST include cocotb 2.0 rules or the agent will never work. See RESEARCH_FINDINGS.md section 1 for all 24 breaking changes, and section 5 for the 10 rules that must be in every prompt.

---

## ARCHITECTURE TO BUILD

### Agent Pipeline (Based on CorrectBench + UVM² Research)

```
Input: Verilog DUT file + natural language spec
                    ↓
┌─────────────────────────────────────────────┐
│  PHASE 1: ANALYZE                            │
│  Read DUT → identify ports, operations,      │
│  clock/reset, and generate test plan         │
└──────────────────┬──────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  PHASE 2: GENERATE                           │
│  LLM generates cocotb testbench + Makefile   │
│  (with cocotb 2.0 rules in prompt)           │
└──────────────────┬──────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  PHASE 3: SIMULATE                           │
│  make SIM=icarus → compile + run             │
│  Parse output: PASS/FAIL + error messages    │
└──────────────────┬──────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  PHASE 4: SELF-CORRECT (if FAIL)             │
│  Two-tier loop (from CorrectBench):          │
│  - Correction: feed errors to LLM, fix TB    │
│    (max 3 attempts)                          │
│  - Reboot: regenerate TB from scratch         │
│    (max 10 attempts)                         │
│  Corrector gets: error msg + TB code + spec   │
└──────────────────┬──────────────────────────┘
                    ↓
Output: Working testbench + simulation results + run log
```

### Key Design Principles (from research)
1. **LLM wrapper:** Abstract the LLM so we can swap claude -p / Ollama / DeepSeek API without changing agent code
2. **Prompts as files:** Store all prompts in `prompts/` directory with version numbers, never inline
3. **Log everything:** Every run saves: prompt sent, LLM response, generated testbench, simulation log, pass/fail, iterations, tokens, time
4. **Golden test suite:** 10-15 Verilog designs with known-good testbenches for regression testing
5. **Modular pipeline:** Each phase (Analyze, Generate, Simulate, Correct) is a separate module — can swap individually
6. **cocotb not UVM:** LLMs are much better at Python than SystemVerilog. Can add UVM later as a Generator module swap.

### Proposed Project Structure
```
project-ava/
├── venv/                          ← Python 3.13 + cocotb 2.0.1
├── src/
│   ├── agent.py                   ← Main orchestrator (the pipeline loop)
│   ├── analyzer.py                ← Phase 1: Parse DUT, generate test plan
│   ├── generator.py               ← Phase 2: LLM generates cocotb testbench
│   ├── simulator.py               ← Phase 3: Run icarus verilog, parse results
│   ├── corrector.py               ← Phase 4: Self-correction with error feedback
│   └── llm.py                     ← LLM wrapper (claude -p / ollama / API)
├── prompts/
│   ├── v1_analyze.txt             ← Prompt for DUT analysis
│   ├── v1_generate.txt            ← Prompt for testbench generation (includes cocotb 2.0 rules)
│   ├── v1_correct.txt             ← Prompt for error correction
│   └── CHANGELOG.md
├── golden/                        ← Golden test suite (DUT + known-good testbench pairs)
│   ├── 01_adder/
│   ├── 02_alu/
│   ├── 03_counter/
│   └── ...
├── runs/                          ← Auto-generated run logs (timestamped)
├── research/
│   ├── RESEARCH_FINDINGS.md       ← All pre-implementation research
│   ├── cocotb_test/               ← Working cocotb examples
│   └── claude_gen_test/           ← Claude generation test (ALU, 7/7 pass)
├── PROGRESS.md                    ← THIS FILE
├── CLAUDE.md                      ← Instructions for Claude Code
└── .gitignore
```

---

## GOLDEN TEST SUITE — DESIGNS TO USE

### Tier 1: Basic (build agent with these first)
| # | Design | Complexity | Status |
|---|---|---|---|
| 1 | 4-bit adder | Trivial (combinational) | cocotb test verified ✓ |
| 2 | 8-bit ALU | Easy (5 operations + zero flag) | Claude-generated test verified ✓ |
| 3 | 4-bit counter | Easy (sequential + clock) | Need to create |
| 4 | 8-bit shift register | Easy (sequential) | Need to create |

### Tier 2: Medium (prove agent handles real designs)
| # | Design | Source |
|---|---|---|
| 5 | FIFO buffer | Open source |
| 6 | UART transmitter | Open source |
| 7 | SPI master | Open source |

### Tier 3: Power-Aware (the AMD differentiator)
| # | Design | Source |
|---|---|---|
| 8 | Clock gating cell (ICG) | github.com/drvasanthi/iiitb_cg |
| 9 | Frequency divider | github.com/D3r3k23/clk_divider |
| 10 | Power state machine | Write ourselves |
| 11 | DVFS controller | Write ourselves (no open source exists — this is the research gap) |

---

## WHAT HAS BEEN DONE (March 18, 2026)

### Completed
- [x] Full research on existing tools: AutoBench, CorrectBench, ConfiBench, VerilogCoder, UVM², UVLLM
- [x] Full research on cocotb 2.0 breaking changes (24 changes documented)
- [x] Installed all tools: Icarus Verilog, Verilator, Ollama, cocotb
- [x] Created Python 3.13 venv (cocotb requires ≤3.13, system has 3.14)
- [x] Pulled DeepSeek-Coder 6.7B model in Ollama
- [x] Created GitHub repo: github.com/vanthienha199/project-ava
- [x] Tested end-to-end: claude -p → cocotb testbench → icarus simulation → PASS
- [x] Discovered and documented the critical cocotb 2.0 API trap
- [x] Identified golden test suite designs (4 tiers, 11 designs)
- [x] Documented CorrectBench algorithm (two-tier iteration: correct vs reboot)
- [x] Documented UVM² architecture (3-agent pipeline)
- [x] Confirmed `claude -p` works as free LLM via Max plan
- [x] Confirmed Ollama API works for local LLM calls
- [x] Saved all research in RESEARCH_FINDINGS.md

### NOT Done Yet (Next Chat Should Do These)
- [ ] **Create project structure** (src/, prompts/, golden/, runs/)
- [ ] **Build LLM wrapper** (llm.py — abstract claude -p vs ollama)
- [ ] **Build simulator module** (simulator.py — run make SIM=icarus, parse output)
- [ ] **Build generator module** (generator.py — prompt template + LLM call)
- [ ] **Build corrector module** (corrector.py — error feedback loop)
- [ ] **Build analyzer module** (analyzer.py — parse Verilog DUT)
- [ ] **Build main agent orchestrator** (agent.py — the full pipeline)
- [ ] **Create prompt templates** (v1_analyze.txt, v1_generate.txt, v1_correct.txt)
- [ ] **Create golden test suite** (Verilog designs for tiers 1-3)
- [ ] **Build logging system** (auto-save every run to runs/)
- [ ] **Build evaluation script** (run agent on all golden designs, report results)
- [ ] **Create CLAUDE.md** for the project
- [ ] **First commit + push to GitHub**
- [ ] **Set up Alienware for SSH + Ollama with DeepSeek-Coder-33B**

---

## CONTEXT: HA LE'S FULL SITUATION

### Dr. Wu's Lab (Unary Lab, UCF)
- **Primary task:** Run lit_silicon on AMD MI300X GPUs (waiting for access)
- **Spring break task:** Research agentic AI systems — Project Ava IS this research
- **Weekly meetings:** Wednesdays 2 PM, HEC356 (in-person) or Zoom
- **Connection:** Dr. Wu's Lit Silicon paper = thermal imbalance → DVFS throttling. Derek Martin at AMD = DVFS verification. Project Ava = agentic verification for DVFS. One project, three audiences.

### ACM Project Ava
- **PM:** Dylan (proposed project, AMD funded via Rex McCurry)
- **Ha Le's role:** Agent + Automation teams
- **Team size:** 16 people total, 4 teams
- **Semester goal:** One working verification agent
- **Spring break:** Agent team watching YouTube + reading GitHub on agents. Ha Le went deeper (read papers, set up tools, tested pipeline).
- **After break:** In-person meeting, hit the ground running

### Other Commitments
- Senior Design 2 (SafeFall) — Expo March 29, almost done
- Vooks (work) — Data investigation ongoing
- Only 3 credits this semester

### Budget
- Ha Le offered $100 for the project
- Likely needs $0-25 (Claude Max covers LLM, tools are free)
- DeepSeek API: $10-20 backup if needed (5M free tokens on signup)

---

## GIT AUTHOR RULES (CRITICAL)

- **ALWAYS:** `--author="Ha Le <halevanthien@gmail.com>"`
- **NEVER** add Co-Authored-By Claude
- **NEVER** mention Claude in any commit
- Author is ONLY Ha Le. No exceptions.

---

## HOW TO START BUILDING (Instructions for Next Chat)

1. Read this file 100%
2. Read `/Users/hale/projects/project-ava/research/RESEARCH_FINDINGS.md` 100%
3. Activate venv: `source /Users/hale/projects/project-ava/venv/bin/activate`
4. Start with the project structure + LLM wrapper + simulator module
5. Then build generator with prompt templates (MUST include cocotb 2.0 rules)
6. Then build corrector (two-tier: correct vs reboot)
7. Then build orchestrator
8. Test on golden suite tier 1 (adder, ALU, counter, shift register)
9. Expand to tier 2 and 3
10. Every step: log everything, version prompts, test against golden suite

---

## KEY FILES TO READ

| File | What It Contains |
|---|---|
| This file (PROGRESS.md) | Full project context, what's done, what to build next |
| research/RESEARCH_FINDINGS.md | cocotb 2.0 API traps, CorrectBench algorithm, UVM² architecture, golden suite designs, prompt rules |
| research/claude_gen_test/alu.v | Working 8-bit ALU design (reference DUT) |
| research/claude_gen_test/test_alu.py | Working Claude-generated cocotb testbench (FIXED for 2.0) |
| research/cocotb_test/test_adder.py | Simple working cocotb test (reference pattern) |
| /Users/hale/Desktop/Research/PROGRESS_LITSIL_CHOPPER.md | Dr. Wu's lab context (lit_silicon, chopper, AMD access) |
