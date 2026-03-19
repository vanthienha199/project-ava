import cocotb
from cocotb.triggers import Timer
import random

@cocotb.test()
async def test_adder_basic(dut):
    """Test basic addition"""
    dut.a.value = 3
    dut.b.value = 5
    await Timer(1, units="ns")
    assert dut.sum.value == 8, f"Expected 8, got {dut.sum.value}"

@cocotb.test()
async def test_adder_random(dut):
    """Test with random values"""
    for _ in range(20):
        a = random.randint(0, 15)
        b = random.randint(0, 15)
        dut.a.value = a
        dut.b.value = b
        await Timer(1, units="ns")
        assert dut.sum.value == a + b, f"{a}+{b}: expected {a+b}, got {dut.sum.value}"
