import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_zero_plus_zero(dut):
    """Test 0 + 0 = 0"""
    dut.a.value = 0
    dut.b.value = 0
    await Timer(2, unit="ns")
    assert int(dut.sum.value) == 0, f"Expected 0, got {int(dut.sum.value)}"


@cocotb.test()
async def test_one_plus_one(dut):
    """Test 1 + 1 = 2"""
    dut.a.value = 1
    dut.b.value = 1
    await Timer(2, unit="ns")
    assert int(dut.sum.value) == 2, f"Expected 2, got {int(dut.sum.value)}"


@cocotb.test()
async def test_max_plus_max(dut):
    """Test 15 + 15 = 30"""
    dut.a.value = 15
    dut.b.value = 15
    await Timer(2, unit="ns")
    assert int(dut.sum.value) == 30, f"Expected 30, got {int(dut.sum.value)}"


@cocotb.test()
async def test_carry(dut):
    """Test 15 + 1 = 16 (carry out)"""
    dut.a.value = 15
    dut.b.value = 1
    await Timer(2, unit="ns")
    assert int(dut.sum.value) == 16, f"Expected 16, got {int(dut.sum.value)}"


@cocotb.test()
async def test_asymmetric(dut):
    """Test 3 + 12 = 15"""
    dut.a.value = 3
    dut.b.value = 12
    await Timer(2, unit="ns")
    assert int(dut.sum.value) == 15, f"Expected 15, got {int(dut.sum.value)}"


@cocotb.test()
async def test_all_combinations(dut):
    """Exhaustive test of all 256 input combinations"""
    for a in range(16):
        for b in range(16):
            dut.a.value = a
            dut.b.value = b
            await Timer(2, unit="ns")
            expected = a + b
            result = int(dut.sum.value)
            assert result == expected, f"{a} + {b}: expected {expected}, got {result}"
