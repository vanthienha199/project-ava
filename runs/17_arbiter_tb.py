import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    dut.rst.value = 1
    dut.req.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_reset_state(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.req.value = 0
    await reset_dut(dut)
    assert int(dut.grant.value) == 0, f"grant should be 0 after reset, got {int(dut.grant.value)}"
    assert int(dut.valid.value) == 0, f"valid should be 0 after reset, got {int(dut.valid.value)}"


@cocotb.test()
async def test_single_request_req0(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    dut.req.value = 0b0001
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b0001, f"expected grant=0001, got {int(dut.grant.value)}"
    assert int(dut.valid.value) == 1, f"expected valid=1, got {int(dut.valid.value)}"


@cocotb.test()
async def test_single_request_req2(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    # priority_ptr starts at 0, so req[2] should be granted
    dut.req.value = 0b0100
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b0100, f"expected grant=0100, got {int(dut.grant.value)}"
    assert int(dut.valid.value) == 1, f"expected valid=1"


@cocotb.test()
async def test_no_request(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    dut.req.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0, f"expected grant=0 when no req"
    assert int(dut.valid.value) == 0, f"expected valid=0 when no req"


@cocotb.test()
async def test_simultaneous_req0_req2_priority0(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    # priority_ptr=0, req[0] and req[2] both asserted
    dut.req.value = 0b0101
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b0001, f"expected req[0] granted first, got {int(dut.grant.value)}"
    assert int(dut.valid.value) == 1
    # next cycle priority_ptr=1, req[2] should win
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b0100, f"expected req[2] granted second, got {int(dut.grant.value)}"
    assert int(dut.valid.value) == 1


@cocotb.test()
async def test_all_four_round_robin(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    dut.req.value = 0b1111
    expected_grants = [0b0001, 0b0010, 0b0100, 0b1000, 0b0001, 0b0010]
    for i, expected in enumerate(expected_grants):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        got = int(dut.grant.value)
        assert got == expected, f"cycle {i}: expected grant={bin(expected)}, got {bin(got)}"
        assert int(dut.valid.value) == 1, f"cycle {i}: expected valid=1"


@cocotb.test()
async def test_priority_holds_with_no_req(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    # Grant req[1] to advance priority_ptr to 2
    dut.req.value = 0b0010
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b0010
    # Remove all requests for several cycles
    dut.req.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.grant.value) == 0
        assert int(dut.valid.value) == 0
    # Now assert req[0] and req[2]: priority_ptr=2, so req[2] should win
    dut.req.value = 0b0101
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b0100, f"expected req[2] (ptr=2), got {int(dut.grant.value)}"


@cocotb.test()
async def test_fairness_after_req3(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    # Advance to priority_ptr=3 by granting 0,1,2
    dut.req.value = 0b1111
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b0001  # ptr=0 grants req[0]
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b0010  # ptr=1 grants req[1]
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b0100  # ptr=2 grants req[2]
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b1000  # ptr=3 grants req[3]
    # Now ptr=0; req[3] and req[0] both asserted — req[0] should win
    dut.req.value = 0b1001
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b0001, f"req[0] should win after ptr resets to 0, got {int(dut.grant.value)}"


@cocotb.test()
async def test_grant_is_one_hot(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    dut.req.value = 0b1111
    for _ in range(16):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        g = int(dut.grant.value)
        if int(dut.valid.value):
            assert g != 0 and (g & (g - 1)) == 0, f"grant {bin(g)} is not one-hot"


@cocotb.test()
async def test_back_to_back_rotation(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    # req[0] and req[2] only
    dut.req.value = 0b0101
    grants = []
    for _ in range(6):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        grants.append(int(dut.grant.value))
    # Should alternate 0001, 0100, 0001, 0100, ...
    assert grants[0] == 0b0001, f"expected 0001 first, got {bin(grants[0])}"
    assert grants[1] == 0b0100, f"expected 0100 second, got {bin(grants[1])}"
    assert grants[2] == 0b0001, f"expected 0001 third, got {bin(grants[2])}"
    assert grants[3] == 0b0100, f"expected 0100 fourth, got {bin(grants[3])}"


@cocotb.test()
async def test_async_reset_mid_operation(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    dut.req.value = 0b1111
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    # Assert reset asynchronously
    dut.rst.value = 1
    await Timer(3, unit="ns")
    assert int(dut.grant.value) == 0, f"async reset: grant should be 0, got {int(dut.grant.value)}"
    assert int(dut.valid.value) == 0, f"async reset: valid should be 0"
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    # After de-reset with all requests, ptr=0 so req[0] wins
    await Timer(1, unit="ns")
    assert int(dut.grant.value) == 0b0001, f"after reset release, expected req[0], got {int(dut.grant.value)}"