# Project Ava

AI agent that generates cocotb testbenches for Verilog designs, runs simulation with Icarus Verilog, and self-corrects until tests pass.

Upload a Verilog file and a plain-English spec on the website — the agent handles the rest.

**Live:** [projectava.dev](https://projectava.dev)

---

## How It Works

1. You provide a Verilog design and a natural language spec
2. The agent calls an LLM to generate a cocotb testbench
3. Icarus Verilog compiles and simulates
4. If tests fail, the agent feeds errors back to the LLM and retries (up to 3 corrections + 10 reboots)
5. Results stream live to the web dashboard

The cloud watcher runs on Fly.io and polls Supabase for new uploads, so no terminal is needed.

---

## Current Benchmark

19 designs tested, covering combinational logic, sequential circuits, protocols (SPI, I2C, UART), FSMs, and power-aware designs (DVFS, clock gating, power state machines).

| # | Design | Type | Tests | Mutation Score |
|---|--------|------|-------|----------------|
| 01 | adder | Combinational | 6/6 | 100.0% |
| 02 | alu | Combinational | 6/6 | 100.0% |
| 03 | icg | Clock gating | 7/7 | 100.0% |
| 04 | counter | Sequential | 6/6 | 80.0% |
| 05 | freq_divider | DVFS | 6/6 | 61.5% |
| 06 | power_fsm | Power-aware | 20/20 | 60.4% |
| 07 | dvfs_controller | DVFS | 11/11 | 37.5% |
| 08 | shift_register | Sequential | 9/9 | 50.0% |
| 09 | fifo | Buffer/Memory | 11/11 | 68.4% |
| 10 | pwm | PWM | 11/11 | 58.8% |
| 11 | uart_tx | Protocol | 10/10 | 69.6% |
| 12 | watchdog | Timer | 10/10 | 70.0% |
| 13 | traffic_light | FSM | 9/9 | 71.4% |
| 14 | spi_master | Protocol (SPI) | 11/11 | 66.7% |
| 15 | priority_encoder | Priority logic | 14/14 | 66.7% |
| 16 | i2c_master | Protocol (I2C) | 10/10 | 73.9% |
| 17 | arbiter | Round-robin | 11/11 | 56.0% |
| 18 | memory_controller | SRAM | 14/14 | 60.0% |
| 19 | sha256 | Crypto (929 lines) | 9/9 | 100.0% |

All 19 designs pass. 13 of them needed self-correction to get there.

The SHA-256 core is from [secworks](https://github.com/secworks/sha256) (BSD-2-Clause, ASIC-proven) and is tested against NIST FIPS 180-4 vectors.

Designs 12-15 come from external open-source repos the agent had never seen before.

---

## Mutation Testing

The repo includes a mutation testing engine (`src/mutator.py`) that injects small bugs into Verilog source and checks whether the testbench catches them. This measures how thorough the generated tests actually are.

7 mutation categories: relational operators, logical operators, arithmetic, constant bit flips, conditional negation, stuck-at-zero, and bitwise vs logical confusion.

Across all 19 designs: **546 mutants generated, 389 killed, 71.2% overall mutation score.**

Many surviving mutants are equivalent (e.g., replacing `<= 1'b0` with `<= 0` — same thing in Verilog), so the effective score is higher.

---

## Quick Start

### Prerequisites

- Python 3.13+
- Icarus Verilog (`brew install icarus-verilog` or `apt install iverilog`)
- Anthropic API key or Claude CLI

### Install

```bash
git clone https://github.com/vanthienha199/project-ava.git
cd project-ava
python3 -m venv venv
source venv/bin/activate
pip install cocotb anthropic vcdvcd
```

### Run

```bash
# Verify a single design
python3 -m src run --design-dir golden/01_adder

# With Anthropic API
export ANTHROPIC_API_KEY=your-key
python3 -m src run --design-dir golden/07_dvfs_controller --backend anthropic_api

# Full benchmark
python3 -m src benchmark

# Mutation testing (no API needed, runs locally)
python3 -m src.mutation_runner --design-dir golden/01_adder --testbench runs/01_adder_tb.py
```

---

## Project Structure

```
src/
├── __main__.py          # CLI
├── llm.py               # LLM backends (Claude CLI, Anthropic API, Ollama)
├── generator.py          # Testbench generation + cocotb 2.0 auto-fixes
├── simulator.py          # Icarus Verilog runner
├── corrector.py          # Error-feedback correction
├── agent.py              # Self-correcting orchestrator
├── mutator.py            # Verilog mutation engine
├── mutation_runner.py    # Mutation test runner
├── coverage.py           # Toggle coverage analyzer (VCD)
├── reporter.py           # Live status push to Supabase
├── watcher.py            # Cloud watcher for web uploads
└── analyzer.py           # Failure categorization

golden/                   # 19 Verilog designs with specs
docs/                     # Web dashboard (hosted on Netlify)
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Claude Sonnet via Anthropic API |
| Simulator | Icarus Verilog + cocotb 2.0 |
| Database | Supabase (PostgreSQL + Realtime) |
| Website | Static HTML/JS on Netlify |
| Cloud Watcher | Fly.io |
| Coverage | vcdvcd |

---

## License

MIT

---

## Author

**Ha Le** — University of Central Florida

[projectava.dev](https://projectava.dev)
