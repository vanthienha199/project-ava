import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    dut.reset_n.value = 0
    dut.interrupts.value = 0
    dut.mask_reg.value = 0
    dut.current_isr_priority.value = 7
    dut.cpu_ack.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset_n.value = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_reset(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Check reset clears outputs
    dut.reset_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 0, "int_valid not cleared on reset"
    assert int(dut.irq_id.value) == 0, "irq_id not cleared on reset"
    assert int(dut.irq_ack.value) == 0, "irq_ack not cleared on reset"


@cocotb.test()
async def test_single_interrupt(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Assert IRQ3
    dut.interrupts.value = 0b00001000
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 1, "int_valid should be high for IRQ3"
    assert int(dut.irq_id.value) == 3, f"irq_id should be 3, got {int(dut.irq_id.value)}"

    # int_valid should clear next cycle (no new edges)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 0, "int_valid should be 1-cycle pulse"


@cocotb.test()
async def test_masked_interrupt(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Mask IRQ2, then assert it
    dut.mask_reg.value = 0b00000100
    dut.interrupts.value = 0b00000100
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 0, "Masked interrupt should not trigger"


@cocotb.test()
async def test_simultaneous_priority(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Assert IRQ2, IRQ5, IRQ7 simultaneously
    dut.interrupts.value = 0b10100100
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 1, "int_valid should be high"
    assert int(dut.irq_id.value) == 2, f"Lowest IRQ should win, got {int(dut.irq_id.value)}"


@cocotb.test()
async def test_edge_detection_no_retrigger(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Assert IRQ1
    dut.interrupts.value = 0b00000010
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 1, "First edge should trigger"

    # Hold IRQ1 high — should not retrigger
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 0, "Held interrupt should not retrigger"
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 0, "Still held, should not retrigger"


@cocotb.test()
async def test_edge_detection_release_reassert(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Assert IRQ4
    dut.interrupts.value = 0b00010000
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 1

    # Release
    dut.interrupts.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Reassert — should trigger again
    dut.interrupts.value = 0b00010000
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 1, "Re-asserted interrupt should trigger again"


@cocotb.test()
async def test_nested_interrupt_pending(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Currently running ISR at priority 5
    dut.current_isr_priority.value = 5

    # IRQ2 arrives (priority 2 < 5 → higher priority)
    dut.interrupts.value = 0b00000100
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 1
    assert int(dut.irq_id.value) == 2
    assert int(dut.nested_int_pending.value) == 1, "IRQ2 should nest over ISR priority 5"


@cocotb.test()
async def test_nested_interrupt_not_pending(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Currently running ISR at priority 1
    dut.current_isr_priority.value = 1

    # IRQ5 arrives (priority 5 > 1 → lower priority)
    dut.interrupts.value = 0b00100000
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 1
    assert int(dut.irq_id.value) == 5
    assert int(dut.nested_int_pending.value) == 0, "IRQ5 should not nest over ISR priority 1"


@cocotb.test()
async def test_cpu_ack_handshake(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Trigger IRQ6
    dut.interrupts.value = 0b01000000
    await RisingEdge(dut.clk)
    # Assert cpu_ack immediately so it is sampled on the same edge as int_valid
    dut.cpu_ack.value = 1
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 1, "int_valid should be high for IRQ6"
    assert int(dut.irq_id.value) == 6

    dut.cpu_ack.value = 0
    await RisingEdge(dut.clk)
    ack_val = int(dut.irq_ack.value)
    assert ack_val == (1 << 6), f"irq_ack should be one-hot for IRQ6, got {ack_val:#010b}"

    # irq_ack should clear next cycle
    await RisingEdge(dut.clk)
    assert int(dut.irq_ack.value) == 0, "irq_ack should clear after ack pulse"


@cocotb.test()
async def test_cpu_ack_without_valid(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # No interrupt pending, cpu_ack should not produce ack
    dut.cpu_ack.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.cpu_ack.value = 0
    assert int(dut.irq_ack.value) == 0, "No ack without int_valid"


@cocotb.test()
async def test_vector_address(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    for irq_num in range(8):
        # Release all interrupts first
        dut.interrupts.value = 0
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        # Assert single interrupt
        dut.interrupts.value = (1 << irq_num)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        if int(dut.int_valid.value) == 1:
            expected_addr = 0x1000 + (irq_num * 4)
            actual_addr = int(dut.vector_addr.value)
            assert actual_addr == expected_addr, (
                f"IRQ{irq_num}: vector_addr expected {expected_addr:#x}, got {actual_addr:#x}"
            )


@cocotb.test()
async def test_all_irqs_individually(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    for irq_num in range(8):
        await reset_dut(dut)

        dut.interrupts.value = (1 << irq_num)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        assert int(dut.int_valid.value) == 1, f"IRQ{irq_num} should trigger"
        assert int(dut.irq_id.value) == irq_num, f"irq_id should be {irq_num}"


@cocotb.test()
async def test_mask_then_unmask(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Mask IRQ0 and assert it
    dut.mask_reg.value = 0b00000001
    dut.interrupts.value = 0b00000001
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 0, "Masked IRQ0 should not trigger"

    # Unmask while interrupt still held — should trigger on rising edge of active
    dut.mask_reg.value = 0b00000000
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 1, "Unmasked IRQ0 should now trigger"
    assert int(dut.irq_id.value) == 0


@cocotb.test()
async def test_sequential_interrupts(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # IRQ3 first
    dut.interrupts.value = 0b00001000
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 1
    assert int(dut.irq_id.value) == 3

    # Add IRQ1 while IRQ3 still held — IRQ1 is new edge, higher priority
    dut.interrupts.value = 0b00001010
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.int_valid.value) == 1
    assert int(dut.irq_id.value) == 1, "IRQ1 should be detected as new edge"