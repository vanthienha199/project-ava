import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

IDLE = 0
LOW_POWER = 1
ACTIVE = 2
BOOST = 3


async def reset_dut(dut):
    """Assert reset and release."""
    dut.rst.value = 1
    dut.request.value = 0
    dut.thermal_warning.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_reset_state(dut):
    """After reset, FSM should be in IDLE with all outputs deasserted."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == IDLE, f"Expected IDLE, got {int(dut.state.value)}"
    assert int(dut.clk_enable.value) == 0
    assert int(dut.voltage_sel.value) == 0
    assert int(dut.boost_active.value) == 0


@cocotb.test()
async def test_idle_to_active(dut):
    """Request=10 from IDLE should go to ACTIVE."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.request.value = 0b10
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == ACTIVE


@cocotb.test()
async def test_idle_to_low_power(dut):
    """Request=01 from IDLE should go to LOW_POWER."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.request.value = 0b01
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == LOW_POWER
    # Outputs update one cycle after state transition
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.clk_enable.value) == 1
    assert int(dut.voltage_sel.value) == 0b01


@cocotb.test()
async def test_idle_boost_goes_through_active(dut):
    """Request=11 from IDLE goes to ACTIVE (must go through ACTIVE to reach BOOST)."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.request.value = 0b11
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == ACTIVE, "IDLE+boost request should go to ACTIVE first"


@cocotb.test()
async def test_active_to_boost(dut):
    """From ACTIVE, request=11 with no thermal warning goes to BOOST."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.request.value = 0b10
    await RisingEdge(dut.clk)  # -> ACTIVE
    await Timer(1, unit="ns")
    assert int(dut.state.value) == ACTIVE

    dut.request.value = 0b11
    dut.thermal_warning.value = 0
    await RisingEdge(dut.clk)  # -> BOOST
    await Timer(1, unit="ns")
    assert int(dut.state.value) == BOOST
    # Outputs update one cycle after state transition
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.boost_active.value) == 1
    assert int(dut.voltage_sel.value) == 0b11


@cocotb.test()
async def test_active_thermal_throttle(dut):
    """Thermal warning in ACTIVE should force to LOW_POWER."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.request.value = 0b10
    await RisingEdge(dut.clk)  # -> ACTIVE
    await Timer(1, unit="ns")
    assert int(dut.state.value) == ACTIVE

    dut.thermal_warning.value = 1
    dut.request.value = 0b10  # keep active request but thermal overrides
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == LOW_POWER, "Thermal should force LOW_POWER"


@cocotb.test()
async def test_boost_thermal_exits(dut):
    """Thermal warning in BOOST should drop to ACTIVE."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Go to ACTIVE then BOOST
    dut.request.value = 0b10
    await RisingEdge(dut.clk)
    dut.request.value = 0b11
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == BOOST

    dut.thermal_warning.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == ACTIVE, "Thermal in BOOST should go to ACTIVE"


@cocotb.test()
async def test_boost_non_boost_request_drops(dut):
    """Non-boost request in BOOST drops to ACTIVE."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.request.value = 0b10
    await RisingEdge(dut.clk)
    dut.request.value = 0b11
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == BOOST

    dut.request.value = 0b10  # non-boost
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == ACTIVE


@cocotb.test()
async def test_low_power_to_active(dut):
    """From LOW_POWER, request=10 goes to ACTIVE."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.request.value = 0b01
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == LOW_POWER

    dut.request.value = 0b10
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == ACTIVE


@cocotb.test()
async def test_low_power_to_idle(dut):
    """From LOW_POWER, request=00 goes to IDLE."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.request.value = 0b01
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == LOW_POWER

    dut.request.value = 0b00
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == IDLE


@cocotb.test()
async def test_active_outputs(dut):
    """Verify ACTIVE state outputs: clk_enable=1, voltage_sel=10, boost_active=0."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.request.value = 0b10
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == ACTIVE
    # Outputs update one cycle after state transition
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.clk_enable.value) == 1
    assert int(dut.voltage_sel.value) == 0b10
    assert int(dut.boost_active.value) == 0


@cocotb.test()
async def test_active_blocks_boost_on_thermal(dut):
    """From ACTIVE, boost request with thermal warning should NOT go to BOOST."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.request.value = 0b10
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.state.value) == ACTIVE

    dut.request.value = 0b11
    dut.thermal_warning.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    # thermal_warning overrides: goes to LOW_POWER, not BOOST
    assert int(dut.state.value) == LOW_POWER
