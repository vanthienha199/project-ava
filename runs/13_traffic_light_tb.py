import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

GREEN  = 0b001
YELLOW = 0b010
RED    = 0b100

async def reset_dut(dut):
    dut.rst.value = 1
    dut.sensor.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

@cocotb.test()
async def test_reset(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.rst.value = 1
    dut.sensor.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.highway_light.value) == GREEN, "After reset highway should be GREEN"
    assert int(dut.farm_light.value) == RED, "After reset farm should be RED"

@cocotb.test()
async def test_highway_stays_green_no_sensor(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    for i in range(20):
        await RisingEdge(dut.clk)
        assert int(dut.highway_light.value) == GREEN, f"Cycle {i}: highway should stay GREEN without sensor"
        assert int(dut.farm_light.value) == RED, f"Cycle {i}: farm should stay RED without sensor"

@cocotb.test()
async def test_sensor_before_min_time_no_transition(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    dut.sensor.value = 1
    for i in range(5):
        await RisingEdge(dut.clk)
        assert int(dut.highway_light.value) == GREEN, f"Cycle {i}: should not transition before min time"
    dut.sensor.value = 0

@cocotb.test()
async def test_sensor_triggers_after_min_time(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    # Wait 7 cycles with no sensor (count goes 0..6)
    for _ in range(7):
        await RisingEdge(dut.clk)
    assert int(dut.highway_light.value) == GREEN, "Should still be GREEN after 7 cycles without sensor"
    # Now assert sensor — at next rising edge count>=6 && sensor, so transition
    dut.sensor.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # one more for state to register
    assert int(dut.highway_light.value) == YELLOW, "Highway should be YELLOW after sensor triggers transition"
    assert int(dut.farm_light.value) == RED, "Farm should still be RED during highway yellow"

@cocotb.test()
async def test_full_cycle(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # S_HWY_GREEN: wait minimum 7 cycles then assert sensor
    for _ in range(7):
        await RisingEdge(dut.clk)
    dut.sensor.value = 1
    await RisingEdge(dut.clk)  # transition happens here (count=7>=6 && sensor)
    dut.sensor.value = 0
    await RisingEdge(dut.clk)  # now in S_HWY_YELLOW, count=0 after this edge? Let's check

    # S_HWY_YELLOW: should last 3 cycles
    assert int(dut.highway_light.value) == YELLOW, "Should be in HWY_YELLOW"
    assert int(dut.farm_light.value) == RED
    yellow_count = 0
    for _ in range(3):
        if int(dut.highway_light.value) == YELLOW:
            yellow_count += 1
        await RisingEdge(dut.clk)

    # S_FARM_GREEN: should last 5 cycles
    assert int(dut.highway_light.value) == RED, "Highway should be RED during farm green"
    assert int(dut.farm_light.value) == GREEN, "Farm should be GREEN"
    farm_green_count = 0
    for _ in range(5):
        if int(dut.farm_light.value) == GREEN:
            farm_green_count += 1
        await RisingEdge(dut.clk)
    assert farm_green_count == 5, f"Farm green lasted {farm_green_count} cycles, expected 5"

    # S_FARM_YELLOW: should last 3 cycles
    assert int(dut.highway_light.value) == RED, "Highway should be RED during farm yellow"
    assert int(dut.farm_light.value) == YELLOW, "Farm should be YELLOW"
    farm_yellow_count = 0
    for _ in range(3):
        if int(dut.farm_light.value) == YELLOW:
            farm_yellow_count += 1
        await RisingEdge(dut.clk)
    assert farm_yellow_count == 3, f"Farm yellow lasted {farm_yellow_count} cycles, expected 3"

    # Back to S_HWY_GREEN
    assert int(dut.highway_light.value) == GREEN, "Should return to HWY_GREEN"
    assert int(dut.farm_light.value) == RED

@cocotb.test()
async def test_light_encodings(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # HWY_GREEN state
    assert int(dut.highway_light.value) == 0b001, "GREEN encoding should be 3'b001"
    assert int(dut.farm_light.value) == 0b100, "RED encoding should be 3'b100"

    # Trigger transition to HWY_YELLOW
    for _ in range(7):
        await RisingEdge(dut.clk)
    dut.sensor.value = 1
    await RisingEdge(dut.clk)
    dut.sensor.value = 0
    await RisingEdge(dut.clk)

    assert int(dut.highway_light.value) == 0b010, "YELLOW encoding should be 3'b010"

@cocotb.test()
async def test_sensor_exact_min_boundary(dut):
    """Sensor high exactly when count reaches 6 (minimum time)."""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Let count run to 6 (7 cycles: count 0,1,2,3,4,5,6)
    for _ in range(6):
        await RisingEdge(dut.clk)
    # count is now 6, assert sensor right before the clock edge
    dut.sensor.value = 1
    await RisingEdge(dut.clk)  # count>=6 && sensor => transition
    dut.sensor.value = 0
    await RisingEdge(dut.clk)
    assert int(dut.highway_light.value) == YELLOW, "Should transition at exact min boundary"

@cocotb.test()
async def test_multiple_full_cycles(dut):
    """Run through two complete cycles to verify repeatability."""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    for cycle in range(2):
        # HWY_GREEN: wait min time then sensor
        for _ in range(7):
            await RisingEdge(dut.clk)
        dut.sensor.value = 1
        await RisingEdge(dut.clk)
        dut.sensor.value = 0
        await RisingEdge(dut.clk)

        # HWY_YELLOW: 3 cycles
        assert int(dut.highway_light.value) == YELLOW, f"Cycle {cycle}: expected HWY_YELLOW"
        for _ in range(3):
            await RisingEdge(dut.clk)

        # FARM_GREEN: 5 cycles
        assert int(dut.farm_light.value) == GREEN, f"Cycle {cycle}: expected FARM_GREEN"
        for _ in range(5):
            await RisingEdge(dut.clk)

        # FARM_YELLOW: 3 cycles
        assert int(dut.farm_light.value) == YELLOW, f"Cycle {cycle}: expected FARM_YELLOW"
        for _ in range(3):
            await RisingEdge(dut.clk)

        # Back to HWY_GREEN
        assert int(dut.highway_light.value) == GREEN, f"Cycle {cycle}: expected return to HWY_GREEN"

@cocotb.test()
async def test_reset_mid_cycle(dut):
    """Reset in the middle of a state should return to HWY_GREEN."""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Get to HWY_YELLOW
    for _ in range(7):
        await RisingEdge(dut.clk)
    dut.sensor.value = 1
    await RisingEdge(dut.clk)
    dut.sensor.value = 0
    await RisingEdge(dut.clk)
    assert int(dut.highway_light.value) == YELLOW

    # Reset mid-yellow
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.highway_light.value) == GREEN, "Reset should return to HWY_GREEN"
    assert int(dut.farm_light.value) == RED, "Reset should set farm to RED"
    dut.rst.value = 0