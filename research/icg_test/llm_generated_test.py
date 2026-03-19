import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer


async def reset_signals(dut):
    getattr(dut, "in").value = 0
    dut.d0.value = 0
    dut.d1.value = 0


async def wait_clocks(dut, n):
    for _ in range(n):
        await RisingEdge(dut.clk)


@cocotb.test()
async def test_clock_gating_active(dut):
    """When in=0, cgclk should toggle and data should be sampled."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_signals(dut)
    getattr(dut, "in").value = 0

    # Wait for enable to propagate through DFFs
    await wait_clocks(dut, 5)

    # Check cgclk toggles by observing it over a few cycles
    saw_high = False
    saw_low = False
    for _ in range(20):
        await Timer(1, unit="ns")
        val = int(dut.cgclk.value)
        if val == 1:
            saw_high = True
        elif val == 0:
            saw_low = True
    assert saw_high and saw_low, "cgclk should toggle when in=0"


@cocotb.test()
async def test_clock_gating_disabled(dut):
    """When in=1, cgclk should stop toggling (stay low)."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_signals(dut)
    getattr(dut, "in").value = 1

    # Wait for the gating to propagate
    await wait_clocks(dut, 5)

    # After propagation, cgclk should remain low
    for _ in range(20):
        await Timer(1, unit="ns")
        val = int(dut.cgclk.value)
        assert val == 0, f"cgclk should stay low when in=1, got {val}"


@cocotb.test()
async def test_data_sampled_when_active(dut):
    """d0/d1 should be sampled into q0/q1 when clock is active (in=0)."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_signals(dut)
    getattr(dut, "in").value = 0

    await wait_clocks(dut, 5)

    # Drive data
    dut.d0.value = 1
    dut.d1.value = 1
    await wait_clocks(dut, 4)

    assert int(dut.q0.value) == 1, f"q0 should be 1, got {int(dut.q0.value)}"
    assert int(dut.q1.value) == 1, f"q1 should be 1, got {int(dut.q1.value)}"

    # Change data
    dut.d0.value = 0
    dut.d1.value = 0
    await wait_clocks(dut, 4)

    assert int(dut.q0.value) == 0, f"q0 should be 0, got {int(dut.q0.value)}"
    assert int(dut.q1.value) == 0, f"q1 should be 0, got {int(dut.q1.value)}"


@cocotb.test()
async def test_data_holds_when_gated(dut):
    """q0/q1 should hold their values when clock is gated (in=1)."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_signals(dut)
    getattr(dut, "in").value = 0

    await wait_clocks(dut, 5)

    # Set data while active
    dut.d0.value = 1
    dut.d1.value = 0
    await wait_clocks(dut, 4)

    q0_before = int(dut.q0.value)
    q1_before = int(dut.q1.value)

    # Gate the clock
    getattr(dut, "in").value = 1
    await wait_clocks(dut, 5)

    # Change input data while gated
    dut.d0.value = 0
    dut.d1.value = 1
    await wait_clocks(dut, 5)

    # Outputs should hold
    assert int(dut.q0.value) == q0_before, f"q0 should hold at {q0_before}, got {int(dut.q0.value)}"
    assert int(dut.q1.value) == q1_before, f"q1 should hold at {q1_before}, got {int(dut.q1.value)}"


@cocotb.test()
async def test_gate_ungate_transition(dut):
    """Data integrity across gate/ungate transitions."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_signals(dut)
    getattr(dut, "in").value = 0

    await wait_clocks(dut, 5)

    # Set initial data while active
    dut.d0.value = 1
    dut.d1.value = 1
    await wait_clocks(dut, 4)
    assert int(dut.q0.value) == 1
    assert int(dut.q1.value) == 1

    # Gate the clock
    getattr(dut, "in").value = 1
    await wait_clocks(dut, 5)

    # Change data while gated
    dut.d0.value = 0
    dut.d1.value = 0

    # Outputs should still hold old values
    await wait_clocks(dut, 5)
    assert int(dut.q0.value) == 1, "q0 should hold during gating"
    assert int(dut.q1.value) == 1, "q1 should hold during gating"

    # Ungate — new data should now be sampled
    getattr(dut, "in").value = 0
    await wait_clocks(dut, 5)

    assert int(dut.q0.value) == 0, f"q0 should update to 0 after ungating, got {int(dut.q0.value)}"
    assert int(dut.q1.value) == 0, f"q1 should update to 0 after ungating, got {int(dut.q1.value)}"
