// SPI Master — Mode 0 (CPOL=0, CPHA=0), 8-bit, MSB-first
// Simplified from nandland/spi-master (MIT License)
// https://github.com/nandland/spi-master
module spi_master #(
    parameter CLKS_PER_HALF_BIT = 2  // sclk = clk / (2 * CLKS_PER_HALF_BIT)
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       tx_start,      // pulse to begin transaction
    input  wire [7:0] tx_data,       // byte to send on MOSI
    output reg  [7:0] rx_data,       // byte received on MISO
    output reg        rx_valid,      // pulses 1 cycle when rx_data valid
    output reg        tx_ready,      // high when idle, ready for tx_start
    output reg        sclk,          // SPI clock (idle low, Mode 0)
    output reg        mosi,          // master out, slave in
    input  wire       miso           // master in, slave out
);

    localparam IDLE = 2'b00;
    localparam LEAD = 2'b01;  // leading (rising) edge phase
    localparam TRAIL= 2'b10;  // trailing (falling) edge phase
    localparam DONE = 2'b11;

    reg [1:0] state;
    reg [$clog2(CLKS_PER_HALF_BIT)-1:0] clk_count;
    reg [2:0] bit_index;
    reg [7:0] tx_shift;
    reg [7:0] rx_shift;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= IDLE;
            sclk      <= 1'b0;
            mosi      <= 1'b0;
            tx_ready  <= 1'b1;
            rx_valid  <= 1'b0;
            rx_data   <= 8'h00;
            clk_count <= 0;
            bit_index <= 3'd7;
            tx_shift  <= 8'h00;
            rx_shift  <= 8'h00;
        end else begin
            rx_valid <= 1'b0;

            case (state)
                IDLE: begin
                    sclk     <= 1'b0;
                    tx_ready <= 1'b1;
                    if (tx_start) begin
                        tx_shift  <= tx_data;
                        bit_index <= 3'd7;
                        tx_ready  <= 1'b0;
                        mosi      <= tx_data[7]; // drive MSB immediately
                        state     <= LEAD;
                        clk_count <= 0;
                    end
                end

                LEAD: begin  // wait, then raise sclk (rising edge = sample MISO)
                    tx_ready <= 1'b0;
                    if (clk_count == CLKS_PER_HALF_BIT - 1) begin
                        sclk      <= 1'b1;
                        rx_shift  <= {rx_shift[6:0], miso}; // sample MISO
                        clk_count <= 0;
                        state     <= TRAIL;
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                TRAIL: begin  // wait, then lower sclk (falling edge = shift MOSI)
                    if (clk_count == CLKS_PER_HALF_BIT - 1) begin
                        sclk      <= 1'b0;
                        clk_count <= 0;
                        if (bit_index == 0) begin
                            state <= DONE;
                        end else begin
                            bit_index <= bit_index - 1;
                            mosi      <= tx_shift[bit_index - 1];
                            state     <= LEAD;
                        end
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                DONE: begin
                    rx_data  <= rx_shift;
                    rx_valid <= 1'b1;
                    state    <= IDLE;
                end
            endcase
        end
    end

endmodule
