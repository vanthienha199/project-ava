import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    """Assert active-low reset."""
    dut.rst_n.value = 0
    dut.mode.value = 0
    dut.serial_in.value = 0
    dut.parallel_in.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_reset(dut):
    """Verify reset clears data_out to 0."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await Timer(1, unit="ns")
    assert int(dut.data_out.value) == 0, f"data_out should be 0 after reset, got {int(dut.data_out.value)}"


@cocotb.test()
async def test_hold_mode(dut):
    """Mode=00 should hold current value."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Load a value first
    dut.mode.value = 0b11
    dut.parallel_in.value = 0xA5
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.data_out.value) == 0xA5

    # Hold
    dut.mode.value = 0b00
    for _ in range(5):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.data_out.value) == 0xA5, "Hold mode should keep value unchanged"


@cocotb.test()
async def test_shift_left(dut):
    """Mode=01 shifts left, serial_in enters at LSB."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Load 0x01
    dut.mode.value = 0b11
    dut.parallel_in.value = 0x01
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.data_out.value) == 0x01

    # Shift left with serial_in=0
    dut.mode.value = 0b01
    dut.serial_in.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.data_out.value) == 0x02, f"Expected 0x02, got {int(dut.data_out.value):#x}"

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.data_out.value) == 0x04


@cocotb.test()
async def test_shift_left_serial_in(dut):
    """Shift left with serial_in=1 fills LSB with 1."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.mode.value = 0b01
    dut.serial_in.value = 1
    # Shift 8 times to fill with 1s
    for _ in range(8):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.data_out.value) == 0xFF, f"Expected 0xFF, got {int(dut.data_out.value):#x}"


@cocotb.test()
async def test_shift_right(dut):
    """Mode=10 shifts right, serial_in enters at MSB."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Load 0x80
    dut.mode.value = 0b11
    dut.parallel_in.value = 0x80
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.data_out.value) == 0x80

    # Shift right with serial_in=0
    dut.mode.value = 0b10
    dut.serial_in.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.data_out.value) == 0x40, f"Expected 0x40, got {int(dut.data_out.value):#x}"

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.data_out.value) == 0x20


@cocotb.test()
async def test_shift_right_serial_in(dut):
    """Shift right with serial_in=1 fills MSB with 1."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.mode.value = 0b10
    dut.serial_in.value = 1
    for _ in range(8):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.data_out.value) == 0xFF


@cocotb.test()
async def test_parallel_load(dut):
    """Mode=11 loads parallel_in."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    for val in [0x00, 0xFF, 0xAA, 0x55, 0x42]:
        dut.mode.value = 0b11
        dut.parallel_in.value = val
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.data_out.value) == val, f"Expected {val:#x}, got {int(dut.data_out.value):#x}"


@cocotb.test()
async def test_serial_out_msb(dut):
    """serial_out_msb should reflect data_out[7]."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.mode.value = 0b11
    dut.parallel_in.value = 0x80  # MSB = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.serial_out_msb.value) == 1

    dut.parallel_in.value = 0x7F  # MSB = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.serial_out_msb.value) == 0


@cocotb.test()
async def test_serial_out_lsb(dut):
    """serial_out_lsb should reflect data_out[0]."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.mode.value = 0b11
    dut.parallel_in.value = 0x01  # LSB = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.serial_out_lsb.value) == 1

    dut.parallel_in.value = 0xFE  # LSB = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.serial_out_lsb.value) == 0


@cocotb.test()
async def test_shift_out_pattern(dut):
    """Load a pattern and shift it out, verify serial outputs."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    # Load 0b10110011
    dut.mode.value = 0b11
    dut.parallel_in.value = 0b10110011
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    # Shift left and collect MSB output
    dut.mode.value = 0b01
    dut.serial_in.value = 0
    bits = []
    for _ in range(8):
        await Timer(1, unit="ns")
        bits.append(int(dut.serial_out_msb.value))
        await RisingEdge(dut.clk)

    # First MSB out should be bit 7 of 0b10110011 = 1
    assert bits[0] == 1, f"First bit should be 1, got {bits[0]}"
