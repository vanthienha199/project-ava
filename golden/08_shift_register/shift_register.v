// 8-bit shift register with parallel load, serial in/out, and direction control
// Supports: shift left, shift right, parallel load, hold
module shift_register (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [1:0] mode,       // 00=hold, 01=shift left, 10=shift right, 11=parallel load
    input  wire       serial_in,
    input  wire [7:0] parallel_in,
    output reg  [7:0] data_out,
    output wire       serial_out_msb,
    output wire       serial_out_lsb
);

    assign serial_out_msb = data_out[7];
    assign serial_out_lsb = data_out[0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= 8'b0;
        end else begin
            case (mode)
                2'b00: data_out <= data_out;                        // Hold
                2'b01: data_out <= {data_out[6:0], serial_in};      // Shift left
                2'b10: data_out <= {serial_in, data_out[7:1]};      // Shift right
                2'b11: data_out <= parallel_in;                     // Parallel load
            endcase
        end
    end

endmodule
