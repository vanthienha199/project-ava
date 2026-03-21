import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def clock_edge(dut):
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_reset(dut):
    """Reset sets count to 0."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst.value = 0
    dut.enable.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 1
    await Timer(5, unit="ns")
    assert int(dut.count.value) == 0, f"Expected 0 after reset, got {int(dut.count.value)}"
    dut.rst.value = 0


@cocotb.test()
async def test_increment_when_enabled(dut):
    """Count increments on each rising edge when enable is high."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst.value = 1
    dut.enable.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    dut.enable.value = 1
    for expected in range(1, 8):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.count.value) == expected, (
            f"Expected {expected}, got {int(dut.count.value)}"
        )


@cocotb.test()
async def test_hold_when_disabled(dut):
    """Count holds when enable is low."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst.value = 1
    dut.enable.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    dut.enable.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 1
    dut.enable.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.count.value) == 1, (
            f"Count should hold at 1, got {int(dut.count.value)}"
        )


@cocotb.test()
async def test_wraparound(dut):
    """Count wraps from 15 to 0."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst.value = 1
    dut.enable.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    dut.enable.value = 1
    for _ in range(15):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 15, (
        f"Expected 15 before wrap, got {int(dut.count.value)}"
    )
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 0, (
        f"Expected 0 after wrap, got {int(dut.count.value)}"
    )


@cocotb.test()
async def test_reset_overrides_enable(dut):
    """Async reset overrides enable and clears count mid-count."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst.value = 1
    dut.enable.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    dut.enable.value = 1
    for _ in range(5):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 5, (
        f"Expected count=5 before reset, got {int(dut.count.value)}"
    )
    dut.rst.value = 1
    await Timer(3, unit="ns")
    assert int(dut.count.value) == 0, (
        f"Async reset should clear count immediately, got {int(dut.count.value)}"
    )
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 1, (
        f"Expected count to resume from 0 after reset release, got {int(dut.count.value)}"
    )