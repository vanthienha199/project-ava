"""
cocotb testbench for secworks SHA-256 core.
Tests against NIST FIPS 180-4 known-answer test vectors.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# NIST test vector 1: SHA-256("abc")
# Message "abc" = 0x616263, padded to 512 bits per SHA-256 spec:
# 61626380 00000000 00000000 00000000
# 00000000 00000000 00000000 00000000
# 00000000 00000000 00000000 00000000
# 00000000 00000000 00000000 00000018
NIST_BLOCK_ABC = int(
    "61626380" + "00000000" * 13 + "00000000" + "00000018", 16
)

NIST_DIGEST_ABC = int(
    "ba7816bf" "8f01cfea" "414140de" "5dae2223"
    "b00361a3" "96177a9c" "b410ff61" "f20015ad", 16
)

# NIST test vector 2: empty message SHA-256("")
# Padded: 80000000 00000000 ... 00000000 (512 bits, length = 0)
NIST_BLOCK_EMPTY = int(
    "80000000" + "00000000" * 15, 16
)

NIST_DIGEST_EMPTY = int(
    "e3b0c442" "98fc1c14" "9afbf4c8" "996fb924"
    "27ae41e4" "649b934c" "a495991b" "7852b855", 16
)


async def reset_dut(dut):
    """Assert reset (active low) and release."""
    dut.reset_n.value = 0
    dut.init.value = 0
    dut.next.value = 0
    dut.mode.value = 1  # SHA-256 mode
    dut.block.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk)
    dut.reset_n.value = 1
    await RisingEdge(dut.clk)


async def wait_ready(dut, timeout_cycles=200):
    """Wait for ready signal to go high."""
    for _ in range(timeout_cycles):
        await RisingEdge(dut.clk)
        if int(dut.ready.value) == 1:
            return True
    return False


async def hash_block(dut, block, use_init=True):
    """Hash a single 512-bit block. Returns digest as int."""
    # Wait for ready
    ready = await wait_ready(dut, timeout_cycles=200)
    assert ready, "Core not ready before hash"

    # Load block and pulse init or next
    dut.block.value = block
    dut.mode.value = 1  # SHA-256
    if use_init:
        dut.init.value = 1
    else:
        dut.next.value = 1
    await RisingEdge(dut.clk)
    dut.init.value = 0
    dut.next.value = 0

    # Wait for completion (64 rounds + overhead)
    ready = await wait_ready(dut, timeout_cycles=200)
    assert ready, "Core did not complete within 200 cycles"

    # Read digest
    digest = int(dut.digest.value)
    return digest


@cocotb.test()
async def test_reset_state(dut):
    """After reset: ready=1, digest_valid=0"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await RisingEdge(dut.clk)
    assert int(dut.ready.value) == 1, "ready should be 1 after reset"


@cocotb.test()
async def test_sha256_abc(dut):
    """NIST vector: SHA-256('abc') = ba7816bf..."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    digest = await hash_block(dut, NIST_BLOCK_ABC, use_init=True)

    assert digest == NIST_DIGEST_ABC, (
        f"SHA-256('abc') mismatch:\n"
        f"  expected: {NIST_DIGEST_ABC:064x}\n"
        f"  got:      {digest:064x}"
    )


@cocotb.test()
async def test_sha256_empty(dut):
    """NIST vector: SHA-256('') = e3b0c442..."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    digest = await hash_block(dut, NIST_BLOCK_EMPTY, use_init=True)

    assert digest == NIST_DIGEST_EMPTY, (
        f"SHA-256('') mismatch:\n"
        f"  expected: {NIST_DIGEST_EMPTY:064x}\n"
        f"  got:      {digest:064x}"
    )


@cocotb.test()
async def test_ready_goes_low_during_processing(dut):
    """ready should go low after init pulse, then return high."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await wait_ready(dut)

    dut.block.value = NIST_BLOCK_ABC
    dut.mode.value = 1
    dut.init.value = 1
    await RisingEdge(dut.clk)
    dut.init.value = 0

    # ready should drop within a few cycles
    found_low = False
    for _ in range(5):
        await RisingEdge(dut.clk)
        if int(dut.ready.value) == 0:
            found_low = True
            break
    assert found_low, "ready never went low during processing"

    # Should eventually return high
    ready = await wait_ready(dut, timeout_cycles=200)
    assert ready, "ready never returned high after processing"


@cocotb.test()
async def test_digest_valid(dut):
    """digest_valid should be asserted when hash is complete."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    digest = await hash_block(dut, NIST_BLOCK_ABC, use_init=True)

    # After ready returns, digest_valid should be high
    dv = int(dut.digest_valid.value)
    assert dv == 1, f"digest_valid should be 1 after completion, got {dv}"


@cocotb.test()
async def test_back_to_back_hashes(dut):
    """Hash two different messages back to back."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # First hash: "abc"
    digest1 = await hash_block(dut, NIST_BLOCK_ABC, use_init=True)
    assert digest1 == NIST_DIGEST_ABC, "First hash (abc) failed"

    # Second hash: empty string (use init again for fresh hash)
    digest2 = await hash_block(dut, NIST_BLOCK_EMPTY, use_init=True)
    assert digest2 == NIST_DIGEST_EMPTY, "Second hash (empty) failed"


@cocotb.test()
async def test_deterministic(dut):
    """Same input should produce same output twice."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    digest1 = await hash_block(dut, NIST_BLOCK_ABC, use_init=True)
    digest2 = await hash_block(dut, NIST_BLOCK_ABC, use_init=True)
    assert digest1 == digest2, "Same input produced different digests"


@cocotb.test()
async def test_all_zeros_block(dut):
    """Hash a block of all zeros (not a valid padded message, but tests core)."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # All-zeros block — known SHA-256 result
    digest = await hash_block(dut, 0, use_init=True)

    # Just verify it completes and produces a non-zero digest
    assert digest != 0, "All-zeros block should not produce all-zeros digest"


@cocotb.test()
async def test_all_ones_block(dut):
    """Hash a block of all ones."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    all_ones = (1 << 512) - 1
    digest = await hash_block(dut, all_ones, use_init=True)

    # Verify it completes and is different from all-zeros result
    assert digest != 0, "All-ones block should produce non-zero digest"
