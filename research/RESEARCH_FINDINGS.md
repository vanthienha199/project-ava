# Pre-Implementation Research Findings
**Date:** March 18, 2026
**Purpose:** Everything discovered before writing the agent, so we don't make avoidable mistakes

---

## 1. cocotb 2.0 API Traps (CRITICAL — Must Be in Every Prompt)

These are breaking changes that LLMs (including Claude) DON'T know about. Every generated testbench will fail without these rules.

### Signal Reading
```python
# WRONG (1.x style — Claude generates this by default)
val = dut.signal.value.integer
val = dut.signal.value.signed_integer

# CORRECT (2.0)
val = dut.signal.value.to_unsigned()    # for LogicArray (multi-bit)
val = int(dut.signal.value)             # quick cast works for most cases
val = dut.signal.value.to_signed()      # for signed interpretation
```

### Single-bit signals return `Logic`, not `int`
```python
# WRONG — crashes with "Logic has no attribute integer"
assert dut.zero.value.integer == 1

# CORRECT
assert int(dut.zero.value) == 1
assert dut.zero.value == 1              # equality comparison works
```

### Timer syntax
```python
# WRONG (deprecated)
await Timer(1, units="ns")

# CORRECT
await Timer(1, unit="ns")
```

### fork() removed
```python
# WRONG (removed in 2.0)
cocotb.fork(my_coroutine())

# CORRECT
cocotb.start_soon(my_coroutine())
```

### Task management
```python
# WRONG
task.kill()
await task.join()

# CORRECT
task.cancel()
await task
```

### No arithmetic on LogicArray
```python
# WRONG
result = dut.a.value + dut.b.value

# CORRECT
result = int(dut.a.value) + int(dut.b.value)
```

### Value construction
```python
# WRONG (BinaryValue removed)
from cocotb.binary import BinaryValue
val = BinaryValue(10, 4)

# CORRECT
from cocotb.types import LogicArray
val = LogicArray.from_unsigned(10, 4)
```

### Test result
```python
# WRONG (removed)
raise TestFailure("msg")
raise TestSuccess("msg")

# CORRECT
assert condition, "msg"        # for failure
cocotb.pass_test("msg")        # for explicit pass
```

### Bit indexing is REVERSED by default
```python
# 2.0 default: descending range (VHDL-style)
val = LogicArray(0b1010, 4)   # Range(3, 'downto', 0)
val[3] == 1  # MSB at highest index
val[0] == 0  # LSB at lowest index
```

### Slice assignment must match width
```python
# WRONG — raises ValueError
val = LogicArray(0, 4)
val[:] = "00001111"   # 8 bits into 4-bit array

# CORRECT
val[:] = "1111"       # exact width match
```

---

## 2. CorrectBench Architecture (What to Steal)

### The Algorithm (Pseudocode)
```
Input: DUT Specification
Output: Working Testbench

IC = 0  (correction counter)
IR = 0  (reboot counter)

TB = Generator(SPEC)           # Initial generation

While not done:
    is_correct, bugs = Validator(TB)

    If NOT correct AND IC < 3:
        IC += 1
        TB = Corrector(TB, bugs)    # Fix with bug info

    Else if NOT correct AND IR < 10:
        IR += 1
        IC = 0                       # Reset correction counter
        TB = Generator(SPEC)         # Start fresh

    Else:
        done = True

Return TB
```

### Key Design Decisions
- **Two iteration types:** Correction (fix existing) vs Reboot (start fresh). Max 3 fixes before giving up and regenerating.
- **Validator uses 20 imperfect RTL designs** as cross-checkers (clever but complex — we can simplify by using actual simulation)
- **Corrector gets 3 questions:** Why did it fail? Where is the bug? How to fix it?
- **Pass ratio: 70.13%** (vs 52.18% for AutoBench, 33.33% for raw LLM)

### What We Should Adopt
1. Two-tier iteration (correct vs reboot) — YES
2. Pass bug info to corrector — YES
3. 20 imperfect RTLs for validation — NO (too complex, we have real simulation)
4. Max 3 corrections, max 10 reboots — good starting defaults

---

## 3. UVM² Architecture (State of the Art)

### Three Agents
1. **AgentA (Analysis):** Reads spec → identifies functional points → creates test plan
2. **AgentG (Generation):** Creates UVM testbench from test plan (templates + LLM hybrid)
3. **AgentO (Optimization):** Iteratively improves coverage based on simulation feedback

### Key Results
- 87% code coverage, 89% functional coverage
- 38x faster than human engineers
- Uses DeepSeek-v3 as primary LLM
- Struggles with: complex timing, protocol handshakes, driver/monitor (~80%)

### What We Should Adopt
1. Separate analysis → generation → optimization phases — YES
2. Coverage-driven feedback loop — YES (long term)
3. Template + LLM hybrid for structural code — YES (Makefiles, boilerplate)
4. DeepSeek-v3 as LLM — NO (we use claude -p, which is better)

---

## 4. Golden Test Suite — Target Designs

### Tier 1: Basic (validate agent works)
| # | Design | Source | Why |
|---|---|---|---|
| 1 | 4-bit adder | Write ourselves | Simplest possible |
| 2 | 8-bit ALU (add/sub/and/or/xor) | Already created | Tests multiple ops |
| 3 | 4-bit counter | Write ourselves | Tests sequential logic + clock |
| 4 | 8-bit shift register | Write ourselves | Tests shift operations |

### Tier 2: Medium (real-world useful)
| # | Design | Source | Why |
|---|---|---|---|
| 5 | FIFO buffer | Open source | Industry-standard design |
| 6 | UART transmitter | Open source | Protocol verification |
| 7 | SPI master | Open source | Multi-signal protocol |

### Tier 3: Power-Aware (the AMD angle)
| # | Design | Source | Why |
|---|---|---|---|
| 8 | Clock gating cell (ICG) | github.com/drvasanthi/iiitb_cg | Basic power management |
| 9 | Frequency divider | github.com/D3r3k23/clk_divider | DVFS component |
| 10 | Power state machine | Write ourselves | FSM with power modes |

### Tier 4: Complex (stretch goals)
| # | Design | Source | Why |
|---|---|---|---|
| 11 | DVFS controller | Write ourselves | Full DVFS with freq + voltage |
| 12 | DDR3 memory controller | github.com/AngeloJacobo/UberDDR3 | Complex protocol |

---

## 5. Prompt Template Requirements

Based on the cocotb 2.0 research, every prompt to the LLM MUST include:

```
RULES FOR COCOTB 2.0 (CRITICAL):
1. Use int(dut.signal.value) to read signal values, NEVER .value.integer
2. Single-bit signals return Logic type, use int() to convert
3. Use Timer(N, unit="ns"), NOT units="ns"
4. Use cocotb.start_soon(), NOT cocotb.fork()
5. Use task.cancel(), NOT task.kill()
6. Use assert for failures, NOT raise TestFailure()
7. No arithmetic on LogicArray — convert to int() first
8. Do NOT import BinaryValue — use LogicArray if needed
9. Do NOT use .value.binstr — use str(value) instead
10. Slice assignments must match exact width
```

---

## 6. Architecture Decision: cocotb vs UVM

**Decision: cocotb (Python testbenches)**

| Factor | cocotb | UVM |
|---|---|---|
| LLM generation quality | HIGH (LLMs excellent at Python) | LOW (LLMs hallucinate UVM classes) |
| cocotb 2.0 API traps | Manageable (10 rules above) | UVM has hundreds of patterns to get wrong |
| Time to first working agent | 1-2 weeks | 4-8 weeks |
| Industry adoption | Growing, especially FPGA | Dominant in ASIC |
| Open source simulator support | Icarus Verilog, Verilator | Verilator (partial UVM), commercial only for full |
| Our LLM (Claude) strength | Excellent Python | Good but hallucinates UVM specifics |

Can always add UVM generation later as a separate Generator module.

---

## 7. Verified Working Pipeline (Tested Today)

```
[claude -p]  →  generates cocotb Python testbench
     ↓
[write to file]  →  test_design.py + Makefile
     ↓
[make SIM=icarus]  →  iverilog compiles + vvp simulates
     ↓
[parse output]  →  PASS/FAIL + error messages
     ↓
[if FAIL: feed errors back to claude -p]  →  corrected testbench
     ↓
[repeat until PASS or max iterations]
```

**Tested end-to-end on March 18, 2026:**
- Icarus Verilog 13.0: compiles and simulates ✓
- Ollama DeepSeek-Coder 6.7B: generates testbenches ✓
- claude -p: generates high-quality testbenches (but with cocotb 2.0 API errors) ✓
- cocotb 2.0.1 in Python 3.13 venv: runs testbenches ✓
- Self-correction hypothesis confirmed: Claude's logic was correct, only API syntax needed fixing ✓

---

## Sources
- [CorrectBench Paper](https://arxiv.org/abs/2411.08510)
- [UVM² Paper](https://arxiv.org/abs/2504.19959)
- [cocotb 2.0 Migration Guide](https://docs.cocotb.org/en/stable/upgrade-2.0.html)
- [cocotb Examples](https://docs.cocotb.org/en/stable/examples.html)
- [IIITB Clock Gating](https://github.com/drvasanthi/iiitb_cg)
- [Clock Divider](https://github.com/D3r3k23/clk_divider)
- [Frequency Divider](https://github.com/DantuNandiniDevi/iiitb_freqdiv)
- [UVM Testbench for Frequency Divider](https://github.com/Vivek-Dave/UVM_TestBench_For_Frequency_Divider)
- [Architect in the Loop](https://arxiv.org/html/2512.00016)
- [AI Agents for UVM Generation](https://semiengineering.com/ai-agents-for-uvm-generation-challenges-and-opportunities/)
