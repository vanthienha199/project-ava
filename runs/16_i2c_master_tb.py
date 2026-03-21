import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
import random

@cocotb.test()
async def test_reset_state(dut):
    """Test reset state"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Apply reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_in.value = 0
    dut.sda_in.value = 1
    
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    
    # Check reset state
    assert int(dut.scl.value) == 1, f"SCL should be 1 after reset, got {int(dut.scl.value)}"
    assert int(dut.sda_out.value) == 1, f"SDA_OUT should be 1 after reset, got {int(dut.sda_out.value)}"
    assert int(dut.busy.value) == 0, f"BUSY should be 0 after reset, got {int(dut.busy.value)}"
    assert int(dut.done.value) == 0, f"DONE should be 0 after reset, got {int(dut.done.value)}"
    assert int(dut.ack_received.value) == 0, f"ACK_RECEIVED should be 0 after reset, got {int(dut.ack_received.value)}"
    
    # Release reset
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    
    # Should still be in idle state
    assert int(dut.scl.value) == 1
    assert int(dut.sda_out.value) == 1
    assert int(dut.busy.value) == 0

@cocotb.test()
async def test_transmit_a5_with_ack(dut):
    """Test transmitting 0xA5 (10100101) with ACK response"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_in.value = 0
    dut.sda_in.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Start transaction
    dut.data_in.value = 0xA5
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    # Should be busy now
    await Timer(1, unit="ns")
    assert int(dut.busy.value) == 1, "Should be busy after start"
    
    # Wait for start condition - SDA should go low while SCL is high
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.scl.value) == 1 and int(dut.sda_out.value) == 0, "Start condition: SDA low while SCL high"
    
    # SCL should go low next
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.scl.value) == 0, "SCL should go low after start condition"
    
    # Track data bits - 0xA5 = 10100101
    expected_bits = [1, 0, 1, 0, 0, 1, 0, 1]  # MSB first
    
    for i, expected_bit in enumerate(expected_bits):
        # Data setup phase (SCL low)
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.scl.value) == 0, f"SCL should be low during data setup for bit {i}"
        assert int(dut.sda_out.value) == expected_bit, f"Bit {i}: expected {expected_bit}, got {int(dut.sda_out.value)}"
        
        # Data sample phase (SCL high)
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.scl.value) == 1, f"SCL should be high during data sample for bit {i}"
        assert int(dut.sda_out.value) == expected_bit, f"Bit {i}: data should remain stable during SCL high"
    
    # ACK phase - SCL low, SDA released
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.scl.value) == 0, "SCL should be low during ACK setup"
    assert int(dut.sda_out.value) == 1, "SDA should be released (high) during ACK setup"
    
    # ACK sample - SCL high, provide ACK
    dut.sda_in.value = 0  # Provide ACK
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.scl.value) == 1, "SCL should be high during ACK sample"
    
    # Stop condition setup
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.scl.value) == 0, "SCL should go low for stop setup"
    assert int(dut.sda_out.value) == 0, "SDA should be low for stop setup"
    
    # Stop condition - SDA high while SCL high
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.scl.value) == 1, "SCL should be high for stop condition"
    assert int(dut.sda_out.value) == 1, "SDA should go high for stop condition"
    assert int(dut.done.value) == 1, "DONE should pulse high"
    assert int(dut.busy.value) == 0, "BUSY should go low"
    assert int(dut.ack_received.value) == 0, "ACK_RECEIVED should be 0 (ACK)"
    
    # Next cycle - done should be low
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.done.value) == 0, "DONE should be a single cycle pulse"

@cocotb.test()
async def test_transmit_ff_with_nack(dut):
    """Test transmitting 0xFF with NACK response"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_in.value = 0
    dut.sda_in.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Start transaction
    dut.data_in.value = 0xFF
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    # Skip to data phase
    await RisingEdge(dut.clk)  # START_1
    await RisingEdge(dut.clk)  # START_2
    
    # Check all data bits are 1
    for i in range(8):
        await RisingEdge(dut.clk)  # DATA_SCL_LOW
        await Timer(1, unit="ns")
        assert int(dut.sda_out.value) == 1, f"Bit {i} should be 1 for 0xFF"
        await RisingEdge(dut.clk)  # DATA_SCL_HIGH
    
    # ACK phase
    await RisingEdge(dut.clk)  # ACK_SCL_LOW
    dut.sda_in.value = 1  # Provide NACK
    await RisingEdge(dut.clk)  # ACK_SCL_HIGH
    
    # Skip to completion
    await RisingEdge(dut.clk)  # STOP_1
    await RisingEdge(dut.clk)  # STOP_2
    await Timer(1, unit="ns")
    
    assert int(dut.ack_received.value) == 1, "ACK_RECEIVED should be 1 (NACK)"
    assert int(dut.done.value) == 1, "DONE should pulse high"

@cocotb.test()
async def test_transmit_00(dut):
    """Test transmitting 0x00 - all data bits should be 0"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_in.value = 0
    dut.sda_in.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Start transaction
    dut.data_in.value = 0x00
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    # Skip to data phase
    await RisingEdge(dut.clk)  # START_1
    await RisingEdge(dut.clk)  # START_2
    
    # Check all data bits are 0
    for i in range(8):
        await RisingEdge(dut.clk)  # DATA_SCL_LOW
        await Timer(1, unit="ns")
        assert int(dut.sda_out.value) == 0, f"Bit {i} should be 0 for 0x00"
        await RisingEdge(dut.clk)  # DATA_SCL_HIGH

@cocotb.test()
async def test_busy_flag_timing(dut):
    """Test busy flag is high during transaction and low after done"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_in.value = 0
    dut.sda_in.value = 0  # ACK
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Initially not busy
    assert int(dut.busy.value) == 0, "Should not be busy initially"
    
    # Start transaction
    dut.data_in.value = 0x55
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    # Should be busy throughout transaction
    done_found = False
    for cycle in range(25):  # More than enough cycles for complete transaction
        await Timer(1, unit="ns")
        if int(dut.done.value) == 1:
            assert int(dut.busy.value) == 0, "BUSY should be low when DONE is high"
            done_found = True
            break
        else:
            assert int(dut.busy.value) == 1, f"Should be busy during transaction (cycle {cycle})"
        await RisingEdge(dut.clk)
    
    assert done_found, "Transaction should have completed"
    
    # After done, should not be busy
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.busy.value) == 0, "Should not be busy after transaction"

@cocotb.test()
async def test_done_pulse_width(dut):
    """Test done pulse is exactly 1 cycle wide"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_in.value = 0
    dut.sda_in.value = 0  # ACK
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Start transaction
    dut.data_in.value = 0x33
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    # Wait for done
    done_seen = False
    for cycle in range(25):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if int(dut.done.value) == 1:
            assert not done_seen, "DONE should only pulse once"
            done_seen = True
            # Check next cycle
            await RisingEdge(dut.clk)
            await Timer(1, unit="ns")
            assert int(dut.done.value) == 0, "DONE should be low after 1 cycle"
            break
    
    assert done_seen, "DONE pulse should have occurred"

@cocotb.test()
async def test_start_condition_timing(dut):
    """Test start condition: sda_out falls while scl is high"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_in.value = 0
    dut.sda_in.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Initially both should be high
    assert int(dut.scl.value) == 1 and int(dut.sda_out.value) == 1, "Both SCL and SDA should be high initially"
    
    # Start transaction
    dut.data_in.value = 0x12
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    # First cycle after start - should be in START_1 state
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.scl.value) == 1, "SCL should still be high during start condition"
    assert int(dut.sda_out.value) == 0, "SDA should go low during start condition"

@cocotb.test()
async def test_stop_condition_timing(dut):
    """Test stop condition: sda_out rises while scl is high"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_in.value = 0
    dut.sda_in.value = 0  # ACK
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Start transaction
    dut.data_in.value = 0x99
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    # Wait for stop condition
    for cycle in range(25):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if int(dut.done.value) == 1:
            # This should be the stop condition
            assert int(dut.scl.value) == 1, "SCL should be high during stop condition"
            assert int(dut.sda_out.value) == 1, "SDA should be high during stop condition"
            break

@cocotb.test()
async def test_back_to_back_transactions(dut):
    """Test back-to-back transactions: start new one immediately after done"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_in.value = 0
    dut.sda_in.value = 0  # ACK
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # First transaction
    dut.data_in.value = 0xAA
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    # Wait for first transaction to complete
    for cycle in range(25):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if int(dut.done.value) == 1:
            assert int(dut.busy.value) == 0, "Should not be busy when done"
            # Start second transaction immediately
            dut.data_in.value = 0x55
            dut.start.value = 1
            break
    
    # Next cycle
    await RisingEdge(dut.clk)
    dut.start.value = 0
    await Timer(1, unit="ns")
    assert int(dut.busy.value) == 1, "Should be busy for second transaction"
    assert int(dut.done.value) == 0, "DONE should be low after pulse"
    
    # Wait for second transaction to complete
    for cycle in range(25):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if int(dut.done.value) == 1:
            assert int(dut.busy.value) == 0, "Should not be busy when second transaction done"
            break

@cocotb.test()
async def test_random_data_patterns(dut):
    """Test various random data patterns"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    test_values = [0x00, 0xFF, 0xAA, 0x55, 0x0F, 0xF0, 0x3C, 0xC3]
    
    for test_val in test_values:
        # Reset
        dut.rst.value = 1
        dut.start.value = 0
        dut.data_in.value = 0
        dut.sda_in.value = 0  # ACK
        await RisingEdge(dut.clk)
        dut.rst.value = 0
        await RisingEdge(dut.clk)
        
        # Start transaction
        dut.data_in.value = test_val
        dut.start.value = 1
        await RisingEdge(dut.clk)
        dut.start.value = 0
        
        # Skip to data phase and verify bits
        await RisingEdge(dut.clk)  # START_1
        await RisingEdge(dut.clk)  # START_2
        
        expected_bits = [(test_val >> (7-i)) & 1 for i in range(8)]
        
        for i, expected_bit in enumerate(expected_bits):
            await RisingEdge(dut.clk)  # DATA_SCL_LOW
            await Timer(1, unit="ns")
            actual_bit = int(dut.sda_out.value)
            assert actual_bit == expected_bit, f"Value 0x{test_val:02X}, bit {i}: expected {expected_bit}, got {actual_bit}"
            await RisingEdge(dut.clk)  # DATA_SCL_HIGH
        
        # Wait for completion
        for cycle in range(10):
            await RisingEdge(dut.clk)
            if int(dut.done.value) == 1:
                break