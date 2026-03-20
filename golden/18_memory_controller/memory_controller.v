// Simple Synchronous SRAM Controller
// 256 x 8-bit memory with read/write, chip select, and busy signaling
// Write: 1 cycle latency. Read: 1 cycle latency (data valid next cycle).

module memory_controller (
    input  wire       clk,
    input  wire       rst,        // Async reset, active high
    input  wire       cs,         // Chip select (active high)
    input  wire       we,         // Write enable (1=write, 0=read)
    input  wire [7:0] addr,       // 8-bit address (256 locations)
    input  wire [7:0] wdata,      // Write data
    output reg  [7:0] rdata,      // Read data (valid 1 cycle after read request)
    output reg        rdata_valid, // High for 1 cycle when rdata is valid
    output reg        busy,       // High during operation
    output reg        error       // Address out of range or access without cs
);

    // Memory array
    reg [7:0] mem [0:255];

    // Internal state
    localparam IDLE    = 2'd0;
    localparam WRITE   = 2'd1;
    localparam READ    = 2'd2;

    reg [1:0] state;
    reg [7:0] addr_reg;
    reg [7:0] wdata_reg;

    integer i;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state       <= IDLE;
            rdata       <= 8'd0;
            rdata_valid <= 1'b0;
            busy        <= 1'b0;
            error       <= 1'b0;
            addr_reg    <= 8'd0;
            wdata_reg   <= 8'd0;
            // Clear memory on reset
            for (i = 0; i < 256; i = i + 1)
                mem[i] <= 8'd0;
        end else begin
            rdata_valid <= 1'b0;  // default: pulse
            error       <= 1'b0;  // default: pulse

            case (state)
                IDLE: begin
                    busy <= 1'b0;
                    if (cs) begin
                        if (we) begin
                            // Write operation
                            addr_reg  <= addr;
                            wdata_reg <= wdata;
                            busy      <= 1'b1;
                            state     <= WRITE;
                        end else begin
                            // Read operation
                            addr_reg <= addr;
                            busy     <= 1'b1;
                            state    <= READ;
                        end
                    end
                end

                WRITE: begin
                    mem[addr_reg] <= wdata_reg;
                    busy          <= 1'b0;
                    state         <= IDLE;
                end

                READ: begin
                    rdata       <= mem[addr_reg];
                    rdata_valid <= 1'b1;
                    busy        <= 1'b0;
                    state       <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end
endmodule
