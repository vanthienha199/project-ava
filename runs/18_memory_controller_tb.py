import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    dut.rst.value = 1
    dut.cs.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.wdata.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


async def write_mem(dut, addr, data):
    dut.cs.value = 1
    dut.we.value = 1
    dut.addr.value = addr
    dut.wdata.value = data
    await RisingEdge(dut.clk)
    dut.cs.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)


async def read_mem(dut, addr):
    dut.cs.value = 1
    dut.we.value = 0
    dut.addr.value = addr
    await RisingEdge(dut.clk)
    dut.cs.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")  # let NBA phase commit before sampling
    rdata = int(dut.rdata.value)
    rdata_valid = int(dut.rdata_valid.value)
    return rdata, rdata_valid


@cocotb.test()
async def test_reset(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    assert int(dut.rdata.value) == 0, "rdata should be 0 after reset"
    assert int(dut.rdata_valid.value) == 0, "rdata_valid should be 0 after reset"
    assert int(dut.busy.value) == 0, "busy should be 0 after reset"
    assert int(dut.error.value) == 0, "error should be 0 after reset"


@cocotb.test()
async def test_write_then_read(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    await write_mem(dut, 0x10, 0xAB)

    rdata, rdata_valid = await read_mem(dut, 0x10)
    assert rdata == 0xAB, f"Expected 0xAB, got {hex(rdata)}"
    assert rdata_valid == 1, "rdata_valid should be 1 after read"


@cocotb.test()
async def test_multiple_writes_readback(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    test_data = {0x00: 0x11, 0x01: 0x22, 0x7F: 0x55, 0xFE: 0xAA, 0xFF: 0xFF}
    for addr, data in test_data.items():
        await write_mem(dut, addr, data)

    for addr, expected in test_data.items():
        rdata, rdata_valid = await read_mem(dut, addr)
        assert rdata == expected, f"addr {hex(addr)}: expected {hex(expected)}, got {hex(rdata)}"
        assert rdata_valid == 1, f"rdata_valid should be 1 for addr {hex(addr)}"


@cocotb.test()
async def test_read_unwritten_address(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    rdata, rdata_valid = await read_mem(dut, 0x42)
    assert rdata == 0x00, f"Unwritten address should return 0x00, got {hex(rdata)}"
    assert rdata_valid == 1, "rdata_valid should still pulse"


@cocotb.test()
async def test_cs_low_no_operation(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    dut.cs.value = 0
    dut.we.value = 1
    dut.addr.value = 0x20
    dut.wdata.value = 0xDE
    for _ in range(4):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.busy.value) == 0, "busy should stay 0 when cs=0"

    dut.we.value = 0
    for _ in range(4):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.busy.value) == 0, "busy should stay 0 when cs=0"


@cocotb.test()
async def test_back_to_back_writes_then_reads(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    await write_mem(dut, 0x00, 0xCA)
    await write_mem(dut, 0x01, 0xFE)

    rdata0, rv0 = await read_mem(dut, 0x00)
    rdata1, rv1 = await read_mem(dut, 0x01)

    assert rdata0 == 0xCA, f"addr 0x00: expected 0xCA, got {hex(rdata0)}"
    assert rv0 == 1
    assert rdata1 == 0xFE, f"addr 0x01: expected 0xFE, got {hex(rdata1)}"
    assert rv1 == 1


@cocotb.test()
async def test_boundary_addresses(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    await write_mem(dut, 0x00, 0x01)
    await write_mem(dut, 0xFF, 0xFE)

    rdata_low, rv_low = await read_mem(dut, 0x00)
    rdata_high, rv_high = await read_mem(dut, 0xFF)

    assert rdata_low == 0x01, f"addr 0x00: expected 0x01, got {hex(rdata_low)}"
    assert rv_low == 1
    assert rdata_high == 0xFE, f"addr 0xFF: expected 0xFE, got {hex(rdata_high)}"
    assert rv_high == 1


@cocotb.test()
async def test_overwrite(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    await write_mem(dut, 0x05, 0x11)
    await write_mem(dut, 0x05, 0x22)

    rdata, rdata_valid = await read_mem(dut, 0x05)
    assert rdata == 0x22, f"Expected 0x22 after overwrite, got {hex(rdata)}"
    assert rdata_valid == 1


@cocotb.test()
async def test_busy_signal_write(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    assert int(dut.busy.value) == 0, "busy should be 0 before operation"

    dut.cs.value = 1
    dut.we.value = 1
    dut.addr.value = 0x30
    dut.wdata.value = 0x77
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.busy.value) == 1, "busy should be 1 during write operation"

    dut.cs.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.busy.value) == 0, "busy should be 0 after write completes"


@cocotb.test()
async def test_busy_signal_read(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    assert int(dut.busy.value) == 0, "busy should be 0 before operation"

    dut.cs.value = 1
    dut.we.value = 0
    dut.addr.value = 0x40
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.busy.value) == 1, "busy should be 1 during read operation"

    dut.cs.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.busy.value) == 0, "busy should be 0 after read completes"


@cocotb.test()
async def test_rdata_valid_pulse(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    await write_mem(dut, 0x50, 0x99)

    dut.cs.value = 1
    dut.we.value = 0
    dut.addr.value = 0x50
    await RisingEdge(dut.clk)
    dut.cs.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.rdata_valid.value) == 1, "rdata_valid should be 1 the cycle after read"

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.rdata_valid.value) == 0, "rdata_valid should pulse for only 1 cycle"


@cocotb.test()
async def test_memory_cleared_after_reset(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    await write_mem(dut, 0x10, 0xFF)
    await write_mem(dut, 0x20, 0xAA)

    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    rdata1, rv1 = await read_mem(dut, 0x10)
    rdata2, rv2 = await read_mem(dut, 0x20)

    assert rdata1 == 0x00, f"Memory at 0x10 should be 0 after reset, got {hex(rdata1)}"
    assert rdata2 == 0x00, f"Memory at 0x20 should be 0 after reset, got {hex(rdata2)}"


@cocotb.test()
async def test_rdata_valid_not_asserted_on_write(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    dut.cs.value = 1
    dut.we.value = 1
    dut.addr.value = 0x60
    dut.wdata.value = 0x55
    await RisingEdge(dut.clk)
    dut.cs.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.rdata_valid.value) == 0, "rdata_valid should not assert during write"
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.rdata_valid.value) == 0, "rdata_valid should remain 0 after write"


@cocotb.test()
async def test_sequential_read_write_interleaved(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    pairs = [(0x01, 0xA1), (0x02, 0xB2), (0x03, 0xC3), (0x04, 0xD4)]
    for addr, data in pairs:
        await write_mem(dut, addr, data)

    for addr, expected in pairs:
        rdata, rv = await read_mem(dut, addr)
        assert rdata == expected, f"addr {hex(addr)}: expected {hex(expected)}, got {hex(rdata)}"
        assert rv == 1