// Synchronous FIFO buffer — 8-bit data, 8 entries deep
// Standard FIFO with full, empty, and count signals
module fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH = 8
) (
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire                  wr_en,
    input  wire                  rd_en,
    input  wire [DATA_WIDTH-1:0] wr_data,
    output reg  [DATA_WIDTH-1:0] rd_data,
    output wire                  full,
    output wire                  empty,
    output reg  [$clog2(DEPTH):0] count
);

    // Memory array
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // Pointers
    reg [$clog2(DEPTH)-1:0] wr_ptr;
    reg [$clog2(DEPTH)-1:0] rd_ptr;

    assign full  = (count == DEPTH);
    assign empty = (count == 0);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr  <= 0;
            rd_ptr  <= 0;
            count   <= 0;
            rd_data <= 0;
        end else begin
            case ({wr_en && !full, rd_en && !empty})
                2'b10: begin  // Write only
                    mem[wr_ptr] <= wr_data;
                    wr_ptr <= wr_ptr + 1;
                    count  <= count + 1;
                end
                2'b01: begin  // Read only
                    rd_data <= mem[rd_ptr];
                    rd_ptr  <= rd_ptr + 1;
                    count   <= count - 1;
                end
                2'b11: begin  // Simultaneous read and write
                    mem[wr_ptr] <= wr_data;
                    rd_data <= mem[rd_ptr];
                    wr_ptr <= wr_ptr + 1;
                    rd_ptr <= rd_ptr + 1;
                    // count stays the same
                end
                default: ;  // No operation
            endcase
        end
    end

endmodule
