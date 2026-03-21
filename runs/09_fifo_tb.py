import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    """Assert active-low reset."""
    dut.rst_n.value = 0
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_reset(dut):
    """Verify reset clears FIFO: empty=1, full=0, count=0."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await Timer(1, unit="ns")
    assert int(dut.empty.value) == 1, "FIFO should be empty after reset"
    assert int(dut.full.value) == 0, "FIFO should not be full after reset"
    assert int(dut.count.value) == 0, "Count should be 0 after reset"


@cocotb.test()
async def test_write_single(dut):
    """Write a single item and verify count and empty flag."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.wr_en.value = 1
    dut.wr_data.value = 0x42
    await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 1, f"Count should be 1, got {int(dut.count.value)}"
    assert int(dut.empty.value) == 0, "FIFO should not be empty"


@cocotb.test()
async def test_write_read_single(dut):
    """Write then read a single item, verify data integrity."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Write
    dut.wr_en.value = 1
    dut.wr_data.value = 0xAB
    await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    await RisingEdge(dut.clk)
    # Read
    dut.rd_en.value = 1
    await RisingEdge(dut.clk)
    dut.rd_en.value = 0
    await Timer(1, unit="ns")
    assert int(dut.rd_data.value) == 0xAB, f"Expected 0xAB, got {int(dut.rd_data.value):#x}"
    assert int(dut.count.value) == 0


@cocotb.test()
async def test_fifo_full(dut):
    """Fill FIFO to capacity (8 items) and verify full flag."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.wr_en.value = 1
    for i in range(8):
        dut.wr_data.value = i
        await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    await Timer(1, unit="ns")
    assert int(dut.full.value) == 1, "FIFO should be full after 8 writes"
    assert int(dut.count.value) == 8, f"Count should be 8, got {int(dut.count.value)}"


@cocotb.test()
async def test_write_when_full_ignored(dut):
    """Writing when full should not change count."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.wr_en.value = 1
    for i in range(8):
        dut.wr_data.value = i
        await RisingEdge(dut.clk)
    # Now full, try one more write
    dut.wr_data.value = 0xFF
    await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 8, "Count should remain 8 when writing to full FIFO"


@cocotb.test()
async def test_read_when_empty_ignored(dut):
    """Reading when empty should not change count."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.rd_en.value = 1
    await RisingEdge(dut.clk)
    dut.rd_en.value = 0
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 0, "Count should remain 0 when reading empty FIFO"


@cocotb.test()
async def test_fifo_order(dut):
    """Verify FIFO maintains first-in-first-out order."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Write 4 items
    values = [0x10, 0x20, 0x30, 0x40]
    dut.wr_en.value = 1
    for v in values:
        dut.wr_data.value = v
        await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    await RisingEdge(dut.clk)

    # Read them back
    read_values = []
    dut.rd_en.value = 1
    for _ in range(4):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        read_values.append(int(dut.rd_data.value))
    dut.rd_en.value = 0

    assert read_values == values, f"FIFO order mismatch: {read_values} vs {values}"


@cocotb.test()
async def test_simultaneous_read_write(dut):
    """Simultaneous read and write should keep count stable."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Write 4 items first
    dut.wr_en.value = 1
    for i in range(4):
        dut.wr_data.value = i
        await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    count_before = int(dut.count.value)
    assert count_before == 4

    # Simultaneous read and write
    dut.wr_en.value = 1
    dut.rd_en.value = 1
    dut.wr_data.value = 0xFF
    await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    await Timer(1, unit="ns")
    count_after = int(dut.count.value)
    assert count_after == count_before, f"Count changed during simultaneous R/W: {count_before} -> {count_after}"


@cocotb.test()
async def test_fill_and_drain(dut):
    """Fill FIFO completely then drain it, verify empty at end."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Fill
    dut.wr_en.value = 1
    for i in range(8):
        dut.wr_data.value = i * 10
        await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    await Timer(1, unit="ns")
    assert int(dut.full.value) == 1

    # Drain
    dut.rd_en.value = 1
    for _ in range(8):
        await RisingEdge(dut.clk)
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.empty.value) == 1, "FIFO should be empty after draining"
    assert int(dut.count.value) == 0


@cocotb.test()
async def test_count_tracking(dut):
    """Verify count tracks accurately through writes and reads."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Write 3
    dut.wr_en.value = 1
    for i in range(3):
        dut.wr_data.value = i
        await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 3

    # Read 1
    dut.rd_en.value = 1
    await RisingEdge(dut.clk)
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 2

    # Write 2 more
    dut.wr_en.value = 1
    for i in range(2):
        dut.wr_data.value = 100 + i
        await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 4
