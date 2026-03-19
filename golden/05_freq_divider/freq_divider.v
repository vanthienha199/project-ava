`timescale 1ns / 1ps

module freq_divider (
    input clk,
    input rst,
    output reg clk_div2,
    output reg clk_div4,
    output reg clk_div8
);
    reg [2:0] count;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            count <= 3'b000;
            clk_div2 <= 1'b0;
            clk_div4 <= 1'b0;
            clk_div8 <= 1'b0;
        end else begin
            count <= count + 1;
            clk_div2 <= count[0];
            clk_div4 <= count[1];
            clk_div8 <= count[2];
        end
    end
endmodule
