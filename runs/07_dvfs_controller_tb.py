import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


async def reset_dut(dut):
    dut.rst.value = 1
    dut.workload.value = 0
    dut.temperature.value = 0
    dut.temp_threshold.value = 80
    dut.power_budget.value = 255
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_reset(dut):
    """After reset: all outputs zero"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    assert int(dut.freq_sel.value) == 0
    assert int(dut.voltage_sel.value) == 0
    assert int(dut.throttled.value) == 0
    assert int(dut.power_est.value) == 0


@cocotb.test()
async def test_ramp_up_high_workload(dut):
    """High workload ramps level up over multiple cycles"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.workload.value = 250  # target_level = 7
    dut.power_budget.value = 255  # no power limit
    # Ramp up needs time: current_level increments by 1 each cycle,
    # then freq_sel follows one cycle later (registered output)
    for _ in range(20):
        await RisingEdge(dut.clk)
    level = int(dut.freq_sel.value)
    assert level == 7, f"Expected level 7 after ramp-up, got {level}"


@cocotb.test()
async def test_low_workload_stays_low(dut):
    """Low workload keeps level at 0"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.workload.value = 10  # target_level = 0
    for _ in range(5):
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.freq_sel.value) == 0


@cocotb.test()
async def test_thermal_throttle(dut):
    """Temperature above threshold triggers throttle"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # First ramp up
    dut.workload.value = 250
    dut.power_budget.value = 255
    for _ in range(15):
        await RisingEdge(dut.clk)
    # Now apply thermal throttle
    dut.temperature.value = 90
    dut.temp_threshold.value = 80
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.throttled.value) == 1


@cocotb.test()
async def test_throttle_ramps_down(dut):
    """Throttling ramps down to level 2 max"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.workload.value = 250
    dut.power_budget.value = 255
    for _ in range(15):
        await RisingEdge(dut.clk)
    level_before = int(dut.freq_sel.value)
    # Apply throttle
    dut.temperature.value = 90
    dut.temp_threshold.value = 80
    for _ in range(20):
        await RisingEdge(dut.clk)
    level_after = int(dut.freq_sel.value)
    assert level_after <= 2, f"Throttled level should be <= 2, got {level_after}"
    assert level_after < level_before, "Level should decrease under throttling"


@cocotb.test()
async def test_power_budget_limits_ramp(dut):
    """Power budget limits how high the level can go"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.workload.value = 250  # target = 7
    dut.power_budget.value = 9  # allows up to level 3 (3*3=9)
    for _ in range(15):
        await RisingEdge(dut.clk)
    level = int(dut.freq_sel.value)
    assert level <= 3, f"Power budget 9 should limit to level 3, got {level}"


@cocotb.test()
async def test_power_estimate(dut):
    """Power estimate = level * level"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.workload.value = 250
    dut.power_budget.value = 255
    for _ in range(15):
        await RisingEdge(dut.clk)
    level = int(dut.freq_sel.value)
    power = int(dut.power_est.value)
    assert power == level * level, f"Power should be {level}^2={level*level}, got {power}"


@cocotb.test()
async def test_freq_voltage_coupled(dut):
    """freq_sel and voltage_sel always match"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.workload.value = 200
    dut.power_budget.value = 255
    for _ in range(10):
        await RisingEdge(dut.clk)
        f = int(dut.freq_sel.value)
        v = int(dut.voltage_sel.value)
        assert f == v, f"freq_sel={f} != voltage_sel={v}"


@cocotb.test()
async def test_throttle_clears(dut):
    """Throttle clears when temperature drops below threshold"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.temperature.value = 90
    dut.temp_threshold.value = 80
    dut.workload.value = 100
    for _ in range(5):
        await RisingEdge(dut.clk)
    assert int(dut.throttled.value) == 1
    # Cool down
    dut.temperature.value = 50
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.throttled.value) == 0


@cocotb.test()
async def test_ramp_down(dut):
    """Reducing workload ramps level down"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.workload.value = 250
    dut.power_budget.value = 255
    for _ in range(15):
        await RisingEdge(dut.clk)
    high_level = int(dut.freq_sel.value)
    # Now reduce workload
    dut.workload.value = 10  # target = 0
    for _ in range(15):
        await RisingEdge(dut.clk)
    low_level = int(dut.freq_sel.value)
    assert low_level < high_level, f"Level should decrease: {high_level} -> {low_level}"
    assert low_level == 0, f"Should ramp to 0, got {low_level}"
