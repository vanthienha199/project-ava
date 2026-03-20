// UART Transmitter — 8N1 format (8 data bits, no parity, 1 stop bit)
// Baud rate set by CLKS_PER_BIT parameter (default 4 for fast simulation)
module uart_tx #(
    parameter CLKS_PER_BIT = 4
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       tx_start,    // Pulse high to begin transmission
    input  wire [7:0] tx_data,     // Data byte to transmit
    output reg        tx_out,      // Serial output line (idle high)
    output reg        tx_busy,     // High while transmitting
    output reg        tx_done      // Pulses high for 1 clock when transmission complete
);

    // States
    localparam IDLE  = 2'b00;
    localparam START = 2'b01;
    localparam DATA  = 2'b10;
    localparam STOP  = 2'b11;

    reg [1:0] state;
    reg [$clog2(CLKS_PER_BIT)-1:0] clk_count;
    reg [2:0] bit_index;
    reg [7:0] tx_shift;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= IDLE;
            tx_out    <= 1'b1;    // Idle high
            tx_busy   <= 1'b0;
            tx_done   <= 1'b0;
            clk_count <= 0;
            bit_index <= 0;
            tx_shift  <= 0;
        end else begin
            tx_done <= 1'b0;  // Default: not done

            case (state)
                IDLE: begin
                    tx_out  <= 1'b1;
                    tx_busy <= 1'b0;
                    if (tx_start) begin
                        state     <= START;
                        tx_shift  <= tx_data;
                        tx_busy   <= 1'b1;
                        clk_count <= 0;
                    end
                end

                START: begin
                    tx_out <= 1'b0;  // Start bit = 0
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 1;
                    end else begin
                        clk_count <= 0;
                        bit_index <= 0;
                        state     <= DATA;
                    end
                end

                DATA: begin
                    tx_out <= tx_shift[bit_index];  // LSB first
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 1;
                    end else begin
                        clk_count <= 0;
                        if (bit_index < 7) begin
                            bit_index <= bit_index + 1;
                        end else begin
                            state <= STOP;
                        end
                    end
                end

                STOP: begin
                    tx_out <= 1'b1;  // Stop bit = 1
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 1;
                    end else begin
                        tx_done <= 1'b1;
                        tx_busy <= 1'b0;
                        state   <= IDLE;
                    end
                end
            endcase
        end
    end

endmodule
