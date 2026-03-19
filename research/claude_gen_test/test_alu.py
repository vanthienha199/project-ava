import cocotb
from cocotb.triggers import Timer


async def drive_and_check(dut, a, b, op, expected_result, desc=""):
    dut.a.value = a
    dut.b.value = b
    dut.op.value = op
    await Timer(1, unit="ns")
    result = int(dut.result.value)
    zero = int(dut.zero.value)
    expected_result_8bit = expected_result & 0xFF
    expected_zero = 1 if expected_result_8bit == 0 else 0
    assert result == expected_result_8bit, f"{desc}: expected result {expected_result_8bit}, got {result}"
    assert zero == expected_zero, f"{desc}: expected zero={expected_zero}, got {zero}"


@cocotb.test()
async def test_add(dut):
    await drive_and_check(dut, 10, 20, 0b000, 30, "add basic")
    await drive_and_check(dut, 0, 0, 0b000, 0, "add zeros")
    await drive_and_check(dut, 255, 0, 0b000, 255, "add 255+0")
    await drive_and_check(dut, 0, 255, 0b000, 255, "add 0+255")
    await drive_and_check(dut, 255, 1, 0b000, 0, "add overflow 255+1")
    await drive_and_check(dut, 255, 255, 0b000, 254, "add overflow 255+255")
    await drive_and_check(dut, 128, 128, 0b000, 0, "add overflow 128+128")


@cocotb.test()
async def test_sub(dut):
    await drive_and_check(dut, 20, 10, 0b001, 10, "sub basic")
    await drive_and_check(dut, 0, 0, 0b001, 0, "sub zeros")
    await drive_and_check(dut, 255, 255, 0b001, 0, "sub equal")
    await drive_and_check(dut, 0, 1, 0b001, 255, "sub underflow 0-1")
    await drive_and_check(dut, 1, 255, 0b001, 2, "sub underflow 1-255")
    await drive_and_check(dut, 255, 0, 0b001, 255, "sub 255-0")


@cocotb.test()
async def test_and(dut):
    await drive_and_check(dut, 0xFF, 0x0F, 0b010, 0x0F, "and mask")
    await drive_and_check(dut, 0xAA, 0x55, 0b010, 0x00, "and complementary")
    await drive_and_check(dut, 0, 0, 0b010, 0, "and zeros")
    await drive_and_check(dut, 255, 255, 0b010, 255, "and ones")
    await drive_and_check(dut, 0, 255, 0b010, 0, "and 0 & 255")


@cocotb.test()
async def test_or(dut):
    await drive_and_check(dut, 0xF0, 0x0F, 0b011, 0xFF, "or complementary")
    await drive_and_check(dut, 0, 0, 0b011, 0, "or zeros")
    await drive_and_check(dut, 255, 0, 0b011, 255, "or 255|0")
    await drive_and_check(dut, 0, 255, 0b011, 255, "or 0|255")
    await drive_and_check(dut, 0xAA, 0x55, 0b011, 0xFF, "or AA|55")


@cocotb.test()
async def test_xor(dut):
    await drive_and_check(dut, 0xFF, 0xFF, 0b100, 0x00, "xor same")
    await drive_and_check(dut, 0xAA, 0x55, 0b100, 0xFF, "xor complementary")
    await drive_and_check(dut, 0, 0, 0b100, 0, "xor zeros")
    await drive_and_check(dut, 255, 0, 0b100, 255, "xor 255^0")
    await drive_and_check(dut, 0, 255, 0b100, 255, "xor 0^255")


@cocotb.test()
async def test_default_op(dut):
    await drive_and_check(dut, 100, 200, 0b101, 0, "default op 101")
    await drive_and_check(dut, 100, 200, 0b110, 0, "default op 110")
    await drive_and_check(dut, 100, 200, 0b111, 0, "default op 111")


@cocotb.test()
async def test_zero_flag(dut):
    dut.a.value = 5
    dut.b.value = 5
    dut.op.value = 0b001
    await Timer(1, unit="ns")
    assert int(dut.zero.value) == 1, "zero flag should be 1 when result is 0"

    dut.a.value = 5
    dut.b.value = 3
    dut.op.value = 0b001
    await Timer(1, unit="ns")
    assert int(dut.zero.value) == 0, "zero flag should be 0 when result is non-zero"

    dut.a.value = 0
    dut.b.value = 0
    dut.op.value = 0b000
    await Timer(1, unit="ns")
    assert int(dut.zero.value) == 1, "zero flag should be 1 for 0+0"

    dut.a.value = 0xAA
    dut.b.value = 0x55
    dut.op.value = 0b010
    await Timer(1, unit="ns")
    assert int(dut.zero.value) == 1, "zero flag should be 1 for AA & 55"
