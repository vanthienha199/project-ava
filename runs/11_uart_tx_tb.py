import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLKS_PER_BIT = 4


async def reset_dut(dut):
    """Assert active-low reset."""
    dut.rst_n.value = 0
    dut.tx_start.value = 0
    dut.tx_data.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def send_byte(dut, data):
    """Initiate transmission of a byte."""
    dut.tx_data.value = data
    dut.tx_start.value = 1
    await RisingEdge(dut.clk)
    dut.tx_start.value = 0


async def wait_tx_done(dut, timeout=200):
    """Wait for tx_done to pulse."""
    for _ in range(timeout):
        await RisingEdge(dut.clk)
        if int(dut.tx_done.value) == 1:
            return True
    return False


async def capture_frame(dut):
    """Capture a full UART frame (start + 8 data + stop) by sampling mid-bit."""
    bits = []
    # Wait for start bit (tx_out goes low)
    for _ in range(200):
        await RisingEdge(dut.clk)
        if int(dut.tx_out.value) == 0:
            break

    # Sample mid-bit for start bit (we're at the beginning, skip to mid)
    for _ in range(CLKS_PER_BIT // 2):
        await RisingEdge(dut.clk)
    start_bit = int(dut.tx_out.value)
    assert start_bit == 0, f"Start bit should be 0, got {start_bit}"

    # Skip rest of start bit
    for _ in range(CLKS_PER_BIT - CLKS_PER_BIT // 2):
        await RisingEdge(dut.clk)

    # Sample 8 data bits at mid-bit
    for _ in range(8):
        for _ in range(CLKS_PER_BIT // 2):
            await RisingEdge(dut.clk)
        bits.append(int(dut.tx_out.value))
        for _ in range(CLKS_PER_BIT - CLKS_PER_BIT // 2):
            await RisingEdge(dut.clk)

    # Sample stop bit at mid-bit
    for _ in range(CLKS_PER_BIT // 2):
        await RisingEdge(dut.clk)
    stop_bit = int(dut.tx_out.value)

    return bits, stop_bit


@cocotb.test()
async def test_reset_idle(dut):
    """After reset, tx_out=1 (idle), tx_busy=0, tx_done=0."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await Timer(1, unit="ns")
    assert int(dut.tx_out.value) == 1, "tx_out should idle high"
    assert int(dut.tx_busy.value) == 0, "tx_busy should be 0 in idle"
    assert int(dut.tx_done.value) == 0, "tx_done should be 0 in idle"


@cocotb.test()
async def test_tx_busy_during_transmission(dut):
    """tx_busy should go high during transmission."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_byte(dut, 0x55)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.tx_busy.value) == 1, "tx_busy should be 1 during transmission"


@cocotb.test()
async def test_tx_done_pulses(dut):
    """tx_done should pulse for 1 clock after transmission completes."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_byte(dut, 0x00)
    done = await wait_tx_done(dut)
    assert done, "tx_done should pulse after transmission"
    # Next cycle, tx_done should be 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.tx_done.value) == 0, "tx_done should be 0 after pulse"


@cocotb.test()
async def test_start_bit(dut):
    """Verify start bit is 0."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_byte(dut, 0xAA)
    # Wait for tx_out to go low (start bit)
    for _ in range(10):
        await RisingEdge(dut.clk)
        if int(dut.tx_out.value) == 0:
            break
    assert int(dut.tx_out.value) == 0, "Start bit should be 0"


@cocotb.test()
async def test_transmit_0x00(dut):
    """Transmit 0x00 and verify all data bits are 0."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_byte(dut, 0x00)
    bits, stop = await capture_frame(dut)
    data = sum(b << i for i, b in enumerate(bits))
    assert data == 0x00, f"Expected 0x00, got {data:#x}"
    assert stop == 1, "Stop bit should be 1"


@cocotb.test()
async def test_transmit_0xFF(dut):
    """Transmit 0xFF and verify all data bits are 1."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_byte(dut, 0xFF)
    bits, stop = await capture_frame(dut)
    data = sum(b << i for i, b in enumerate(bits))
    assert data == 0xFF, f"Expected 0xFF, got {data:#x}"
    assert stop == 1, "Stop bit should be 1"


@cocotb.test()
async def test_transmit_0x55(dut):
    """Transmit 0x55 (alternating bits: 01010101)."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_byte(dut, 0x55)
    bits, stop = await capture_frame(dut)
    data = sum(b << i for i, b in enumerate(bits))
    assert data == 0x55, f"Expected 0x55, got {data:#x}"
    assert stop == 1


@cocotb.test()
async def test_transmit_0xA3(dut):
    """Transmit 0xA3 and verify correct bit pattern."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_byte(dut, 0xA3)
    bits, stop = await capture_frame(dut)
    data = sum(b << i for i, b in enumerate(bits))
    assert data == 0xA3, f"Expected 0xA3, got {data:#x}"
    assert stop == 1


@cocotb.test()
async def test_back_to_back_transmit(dut):
    """Send two bytes back to back and verify both complete."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # First byte
    await send_byte(dut, 0x12)
    done = await wait_tx_done(dut)
    assert done, "First transmission should complete"

    await RisingEdge(dut.clk)
    # Second byte
    await send_byte(dut, 0x34)
    done = await wait_tx_done(dut)
    assert done, "Second transmission should complete"


@cocotb.test()
async def test_idle_returns_after_tx(dut):
    """After transmission, line should return to idle (high)."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_byte(dut, 0x42)
    await wait_tx_done(dut)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.tx_out.value) == 1, "tx_out should be idle high after transmission"
    assert int(dut.tx_busy.value) == 0, "tx_busy should be 0 after transmission"


@cocotb.test()
async def test_stop_bit(dut):
    """Verify stop bit is 1."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_byte(dut, 0x42)
    bits, stop = await capture_frame(dut)
    assert stop == 1, "Stop bit should be 1"
