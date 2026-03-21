import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ClockCycles


async def reset_dut(dut):
    dut.rst_n.value = 0
    dut.enable.value = 0
    dut.kick.value = 0
    dut.load_val.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_reset_state(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.rst_n.value = 0
    dut.enable.value = 0
    dut.kick.value = 0
    dut.load_val.value = 100
    await ClockCycles(dut.clk, 3)
    assert int(dut.count.value) == 0, f"After reset, count should be 0, got {int(dut.count.value)}"
    assert int(dut.timeout.value) == 0, "timeout should be low during reset (enable=0)"


@cocotb.test()
async def test_disabled_holds_load_val(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    dut.enable.value = 0
    dut.load_val.value = 500
    await ClockCycles(dut.clk, 2)
    assert int(dut.count.value) == 500, f"Disabled: count should be load_val=500, got {int(dut.count.value)}"
    dut.load_val.value = 1000
    await ClockCycles(dut.clk, 2)
    assert int(dut.count.value) == 1000, f"Disabled: count should track load_val=1000, got {int(dut.count.value)}"
    assert int(dut.timeout.value) == 0, "timeout should be low when disabled"


@cocotb.test()
async def test_countdown(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    load = 10
    dut.load_val.value = load
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    dut.enable.value = 1
    await RisingEdge(dut.clk)
    for expected in range(load - 1, load - 5, -1):
        await RisingEdge(dut.clk)
        val = int(dut.count.value)
        assert val == expected, f"Countdown: expected {expected}, got {val}"


@cocotb.test()
async def test_kick_reloads(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    load = 20
    dut.load_val.value = load
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    dut.enable.value = 1
    await ClockCycles(dut.clk, 5)
    count_before_kick = int(dut.count.value)
    assert count_before_kick < load, "Counter should have decremented"
    dut.kick.value = 1
    await RisingEdge(dut.clk)
    dut.kick.value = 0
    await RisingEdge(dut.clk)
    assert int(dut.count.value) == load, f"After kick, count should be reloaded to load={load}, got {int(dut.count.value)}"
    await RisingEdge(dut.clk)
    assert int(dut.count.value) == load - 1, f"One cycle after reload, count should be load-1={load-1}, got {int(dut.count.value)}"


@cocotb.test()
async def test_timeout_fires(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    load = 5
    dut.load_val.value = load
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    dut.enable.value = 1
    for _ in range(load + 2):
        await RisingEdge(dut.clk)
    seen_timeout = False
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    dut.load_val.value = 3
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    dut.enable.value = 1
    for _ in range(4):
        await RisingEdge(dut.clk)
        if int(dut.timeout.value) == 1:
            seen_timeout = True
            break
    assert seen_timeout, "timeout should fire when count reaches 0 and enable is high"


@cocotb.test()
async def test_auto_reload_after_timeout(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    load = 3
    dut.load_val.value = load
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    dut.enable.value = 1
    for _ in range(load + 1):
        await RisingEdge(dut.clk)
    timeout_seen = False
    for _ in range(load + 1):
        if int(dut.count.value) == 0 and int(dut.timeout.value) == 1:
            timeout_seen = True
            await RisingEdge(dut.clk)
            reloaded = int(dut.count.value)
            assert reloaded == load - 1 or reloaded == load, \
                f"After timeout, count should auto-reload to load_val={load} (or load-1), got {reloaded}"
            break
        await RisingEdge(dut.clk)
    if not timeout_seen:
        dut.enable.value = 0
        await ClockCycles(dut.clk, 2)
        dut.enable.value = 1
        for _ in range(load + 2):
            if int(dut.count.value) == 0 and int(dut.timeout.value) == 1:
                timeout_seen = True
                await RisingEdge(dut.clk)
                reloaded = int(dut.count.value)
                assert reloaded == load - 1 or reloaded == load, \
                    f"After timeout auto-reload, expected ~{load}, got {reloaded}"
                break
            await RisingEdge(dut.clk)
    assert timeout_seen, "Should have observed timeout and auto-reload"


@cocotb.test()
async def test_kick_during_countdown(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    load = 50
    dut.load_val.value = load
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    dut.enable.value = 1
    await ClockCycles(dut.clk, 10)
    mid_count = int(dut.count.value)
    assert mid_count < load, f"Should have decremented from {load}, got {mid_count}"
    dut.kick.value = 1
    await RisingEdge(dut.clk)
    dut.kick.value = 0
    await RisingEdge(dut.clk)
    assert int(dut.count.value) == load, f"After kick mid-countdown, count should reload to {load}, got {int(dut.count.value)}"
    await RisingEdge(dut.clk)
    assert int(dut.count.value) == load - 1, f"One cycle after kick reload, expected {load-1}, got {int(dut.count.value)}"


@cocotb.test()
async def test_reset_during_countdown(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    dut.load_val.value = 100
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    dut.enable.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    assert int(dut.count.value) == 0, f"Reset should clear count to 0, got {int(dut.count.value)}"
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_timeout_not_asserted_when_disabled(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    dut.load_val.value = 0
    dut.enable.value = 0
    await ClockCycles(dut.clk, 3)
    assert int(dut.timeout.value) == 0, "timeout must not assert when enable is low, even if count is 0"


@cocotb.test()
async def test_full_countdown_cycle(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    load = 4
    dut.load_val.value = load
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    assert int(dut.count.value) == load
    dut.enable.value = 1
    await RisingEdge(dut.clk)
    counts = []
    for _ in range(load + 2):
        await RisingEdge(dut.clk)
        counts.append(int(dut.count.value))
    assert counts[0] == load - 1, f"First tick: expected {load-1}, got {counts[0]}"
    assert counts[1] == load - 2, f"Second tick: expected {load-2}, got {counts[1]}"
    assert 0 in counts, f"Counter should reach 0 within {load+2} cycles, saw {counts}"