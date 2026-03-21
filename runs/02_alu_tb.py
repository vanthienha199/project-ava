import cocotb
from cocotb.triggers import Timer


async def apply_and_check(dut, a, b, op, expected, op_name):
    """Helper: apply inputs, wait, check result."""
    dut.a.value = a
    dut.b.value = b
    dut.op.value = op
    await Timer(2, unit="ns")
    result = int(dut.result.value)
    assert result == expected, (
        f"{op_name}: a={a}, b={b}, expected={expected}, got={result}"
    )


@cocotb.test()
async def test_add(dut):
    """Test addition operation (op=000)."""
    await apply_and_check(dut, 10, 20, 0b000, 30, "ADD")
    await apply_and_check(dut, 0, 0, 0b000, 0, "ADD")
    await apply_and_check(dut, 255, 1, 0b000, 0, "ADD overflow")  # 8-bit wraps
    await apply_and_check(dut, 100, 155, 0b000, 255, "ADD")
    await apply_and_check(dut, 128, 128, 0b000, 0, "ADD overflow 128+128")


@cocotb.test()
async def test_sub(dut):
    """Test subtraction operation (op=001)."""
    await apply_and_check(dut, 20, 10, 0b001, 10, "SUB")
    await apply_and_check(dut, 50, 50, 0b001, 0, "SUB equal")
    await apply_and_check(dut, 0, 1, 0b001, 255, "SUB underflow")  # wraps to 255
    await apply_and_check(dut, 200, 100, 0b001, 100, "SUB")


@cocotb.test()
async def test_and(dut):
    """Test bitwise AND operation (op=010)."""
    await apply_and_check(dut, 0xFF, 0x0F, 0b010, 0x0F, "AND")
    await apply_and_check(dut, 0xAA, 0x55, 0b010, 0x00, "AND complementary")
    await apply_and_check(dut, 0xFF, 0xFF, 0b010, 0xFF, "AND all ones")
    await apply_and_check(dut, 0x00, 0xFF, 0b010, 0x00, "AND with zero")


@cocotb.test()
async def test_or(dut):
    """Test bitwise OR operation (op=011)."""
    await apply_and_check(dut, 0xF0, 0x0F, 0b011, 0xFF, "OR")
    await apply_and_check(dut, 0x00, 0x00, 0b011, 0x00, "OR zeros")
    await apply_and_check(dut, 0xAA, 0x55, 0b011, 0xFF, "OR complementary")
    await apply_and_check(dut, 0x12, 0x34, 0b011, 0x36, "OR")


@cocotb.test()
async def test_xor(dut):
    """Test bitwise XOR operation (op=100)."""
    await apply_and_check(dut, 0xFF, 0xFF, 0b100, 0x00, "XOR same")
    await apply_and_check(dut, 0xAA, 0x55, 0b100, 0xFF, "XOR complementary")
    await apply_and_check(dut, 0x00, 0x00, 0b100, 0x00, "XOR zeros")
    await apply_and_check(dut, 0x0F, 0xF0, 0b100, 0xFF, "XOR nibbles")


@cocotb.test()
async def test_default_ops(dut):
    """Test default case: op=101,110,111 should output 0."""
    for op in [0b101, 0b110, 0b111]:
        dut.a.value = 42
        dut.b.value = 99
        dut.op.value = op
        await Timer(2, unit="ns")
        result = int(dut.result.value)
        assert result == 0, f"Default op={op}: expected 0, got {result}"


@cocotb.test()
async def test_zero_flag(dut):
    """Test zero flag output."""
    # Result is zero
    dut.a.value = 0
    dut.b.value = 0
    dut.op.value = 0b000
    await Timer(2, unit="ns")
    assert int(dut.zero.value) == 1, "Zero flag should be 1 when result is 0"

    # Result is non-zero
    dut.a.value = 5
    dut.b.value = 3
    dut.op.value = 0b000
    await Timer(2, unit="ns")
    assert int(dut.zero.value) == 0, "Zero flag should be 0 when result is non-zero"

    # SUB to zero
    dut.a.value = 100
    dut.b.value = 100
    dut.op.value = 0b001
    await Timer(2, unit="ns")
    assert int(dut.zero.value) == 1, "Zero flag should be 1 for equal SUB"


@cocotb.test()
async def test_boundary_values(dut):
    """Test boundary values: 0x00 and 0xFF."""
    await apply_and_check(dut, 0, 0, 0b000, 0, "ADD 0+0")
    await apply_and_check(dut, 255, 0, 0b000, 255, "ADD 255+0")
    await apply_and_check(dut, 255, 255, 0b001, 0, "SUB 255-255")
    await apply_and_check(dut, 1, 1, 0b100, 0, "XOR 1^1")
