// I2C Master Controller — Simplified single-byte transmit
// Generates SCL clock, drives SDA for start/stop/data/ack
// Protocol: START → 8-bit data (MSB first) → read ACK → STOP

module i2c_master (
    input  wire       clk,        // System clock
    input  wire       rst,        // Async reset, active high
    input  wire       start,      // Pulse to begin transaction
    input  wire [7:0] data_in,    // Byte to transmit
    output reg        scl,        // I2C clock line
    output reg        sda_out,    // I2C data line (master drives)
    input  wire       sda_in,     // I2C data line (slave drives during ACK)
    output reg        busy,       // Transaction in progress
    output reg        ack_received,// ACK bit from slave (0 = ACK, 1 = NACK)
    output reg        done        // Pulse when transaction complete
);

    // States
    localparam IDLE     = 4'd0;
    localparam START_1  = 4'd1;   // SDA high→low while SCL high
    localparam START_2  = 4'd2;   // SCL goes low
    localparam DATA_SCL_LOW  = 4'd3;   // Set SDA, SCL low
    localparam DATA_SCL_HIGH = 4'd4;   // SCL high (data sampled)
    localparam ACK_SCL_LOW   = 4'd5;   // Release SDA, SCL low
    localparam ACK_SCL_HIGH  = 4'd6;   // SCL high (read ACK)
    localparam STOP_1   = 4'd7;   // SDA low, SCL high
    localparam STOP_2   = 4'd8;   // SDA high (stop condition)

    reg [3:0] state;
    reg [7:0] shift_reg;
    reg [2:0] bit_cnt;            // 0-7, counts bits transmitted

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state        <= IDLE;
            scl          <= 1'b1;
            sda_out      <= 1'b1;
            busy         <= 1'b0;
            ack_received <= 1'b0;
            done         <= 1'b0;
            shift_reg    <= 8'd0;
            bit_cnt      <= 3'd0;
        end else begin
            done <= 1'b0;  // default: done is a pulse

            case (state)
                IDLE: begin
                    scl     <= 1'b1;
                    sda_out <= 1'b1;
                    if (start) begin
                        shift_reg <= data_in;
                        busy      <= 1'b1;
                        state     <= START_1;
                    end
                end

                START_1: begin
                    // Start condition: SDA goes low while SCL is high
                    sda_out <= 1'b0;
                    state   <= START_2;
                end

                START_2: begin
                    // SCL goes low, prepare first data bit
                    scl     <= 1'b0;
                    bit_cnt <= 3'd0;
                    state   <= DATA_SCL_LOW;
                end

                DATA_SCL_LOW: begin
                    // Drive data bit (MSB first), SCL stays low
                    scl     <= 1'b0;
                    sda_out <= shift_reg[7];
                    state   <= DATA_SCL_HIGH;
                end

                DATA_SCL_HIGH: begin
                    // SCL goes high — slave samples data
                    scl <= 1'b1;
                    if (bit_cnt == 3'd7) begin
                        state <= ACK_SCL_LOW;
                    end else begin
                        bit_cnt   <= bit_cnt + 1;
                        shift_reg <= {shift_reg[6:0], 1'b0};
                        state     <= DATA_SCL_LOW;
                    end
                end

                ACK_SCL_LOW: begin
                    // Release SDA for ACK, SCL low
                    scl     <= 1'b0;
                    sda_out <= 1'b1;  // Release line (open-drain)
                    state   <= ACK_SCL_HIGH;
                end

                ACK_SCL_HIGH: begin
                    // SCL high — read ACK from slave
                    scl          <= 1'b1;
                    ack_received <= sda_in;  // 0=ACK, 1=NACK
                    state        <= STOP_1;
                end

                STOP_1: begin
                    // SDA low while SCL goes high (prepare for stop)
                    scl     <= 1'b0;
                    sda_out <= 1'b0;
                    state   <= STOP_2;
                end

                STOP_2: begin
                    // Stop condition: SDA goes high while SCL is high
                    scl     <= 1'b1;
                    sda_out <= 1'b1;
                    busy    <= 1'b0;
                    done    <= 1'b1;
                    state   <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end
endmodule
