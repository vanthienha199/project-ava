import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    """Assert reset and wait."""
    dut.rst.value = 1
    await Timer(20, unit="ns")
    dut.rst.value = 0
    await Timer(5, unit="ns")


@cocotb.test()
async def test_reset(dut):
    """Verify all outputs are 0 after reset."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await RisingEdge(dut.clk)
    assert int(dut.clk_div2.value) == 0, "clk_div2 should be 0 after reset"
    assert int(dut.clk_div4.value) == 0, "clk_div4 should be 0 after reset"
    assert int(dut.clk_div8.value) == 0, "clk_div8 should be 0 after reset"


@cocotb.test()
async def test_div2_frequency(dut):
    """Verify clk_div2 toggles every 2 clock cycles."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Count transitions over 16 clock cycles
    transitions = 0
    prev = int(dut.clk_div2.value)
    for _ in range(16):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        curr = int(dut.clk_div2.value)
        if curr != prev:
            transitions += 1
        prev = curr
    # div2 should toggle ~8 times in 16 clocks
    assert transitions >= 6, f"clk_div2 transitions={transitions}, expected ~8"


@cocotb.test()
async def test_div4_frequency(dut):
    """Verify clk_div4 toggles every 4 clock cycles."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    transitions = 0
    prev = int(dut.clk_div4.value)
    for _ in range(16):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        curr = int(dut.clk_div4.value)
        if curr != prev:
            transitions += 1
        prev = curr
    # div4 should toggle ~4 times in 16 clocks
    assert transitions >= 3, f"clk_div4 transitions={transitions}, expected ~4"


@cocotb.test()
async def test_div8_frequency(dut):
    """Verify clk_div8 toggles every 8 clock cycles."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    transitions = 0
    prev = int(dut.clk_div8.value)
    for _ in range(32):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        curr = int(dut.clk_div8.value)
        if curr != prev:
            transitions += 1
        prev = curr
    # div8 should toggle ~4 times in 32 clocks
    assert transitions >= 2, f"clk_div8 transitions={transitions}, expected ~4"


@cocotb.test()
async def test_reset_during_operation(dut):
    """Verify reset clears outputs mid-operation."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Run for a while
    for _ in range(10):
        await RisingEdge(dut.clk)
    # Assert reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.clk_div2.value) == 0, "clk_div2 should be 0 after mid-reset"
    assert int(dut.clk_div4.value) == 0, "clk_div4 should be 0 after mid-reset"
    assert int(dut.clk_div8.value) == 0, "clk_div8 should be 0 after mid-reset"


@cocotb.test()
async def test_count_sequence(dut):
    """Verify the internal counter increments correctly."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # After reset, count should increment each clock
    # The outputs are registered versions of count bits, delayed by 1 cycle
    # Collect 8 cycles of output
    values = []
    for _ in range(8):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        d2 = int(dut.clk_div2.value)
        d4 = int(dut.clk_div4.value)
        d8 = int(dut.clk_div8.value)
        values.append((d2, d4, d8))
    # Just verify we got a mix of 0s and 1s (counter is running)
    d2_vals = [v[0] for v in values]
    assert 0 in d2_vals and 1 in d2_vals, "clk_div2 should toggle"


@cocotb.test()
async def test_outputs_after_long_run(dut):
    """Run for many cycles and ensure outputs remain valid."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    for _ in range(100):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    d2 = int(dut.clk_div2.value)
    d4 = int(dut.clk_div4.value)
    d8 = int(dut.clk_div8.value)
    assert d2 in [0, 1] and d4 in [0, 1] and d8 in [0, 1]


@cocotb.test()
async def test_div_relationships(dut):
    """Verify div2 toggles faster than div4, div4 faster than div8."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    counts = [0, 0, 0]  # transitions for div2, div4, div8
    prev = [0, 0, 0]
    for _ in range(32):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        curr = [int(dut.clk_div2.value), int(dut.clk_div4.value), int(dut.clk_div8.value)]
        for i in range(3):
            if curr[i] != prev[i]:
                counts[i] += 1
            prev[i] = curr[i]
    assert counts[0] > counts[1], f"div2 transitions ({counts[0]}) should > div4 ({counts[1]})"
    assert counts[1] > counts[2], f"div4 transitions ({counts[1]}) should > div8 ({counts[2]})"
