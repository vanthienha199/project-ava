`timescale 1ns / 1ps

module power_fsm (
    input clk,
    input rst,
    input [1:0] request,     // 00=idle, 01=low_power, 10=active, 11=boost
    input thermal_warning,    // high temperature alert
    output reg [1:0] state,   // current power state
    output reg clk_enable,    // clock gating control
    output reg [1:0] voltage_sel, // voltage level select
    output reg boost_active   // boost mode indicator
);

    // Power states
    localparam IDLE      = 2'b00;
    localparam LOW_POWER = 2'b01;
    localparam ACTIVE    = 2'b10;
    localparam BOOST     = 2'b11;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= IDLE;
            clk_enable <= 1'b0;
            voltage_sel <= 2'b00;
            boost_active <= 1'b0;
        end else begin
            case (state)
                IDLE: begin
                    clk_enable <= 1'b0;
                    voltage_sel <= 2'b00;
                    boost_active <= 1'b0;
                    if (request == 2'b10)
                        state <= ACTIVE;
                    else if (request == 2'b01)
                        state <= LOW_POWER;
                    else if (request == 2'b11)
                        state <= ACTIVE;  // must go through ACTIVE to reach BOOST
                end

                LOW_POWER: begin
                    clk_enable <= 1'b1;
                    voltage_sel <= 2'b01;  // lowest voltage
                    boost_active <= 1'b0;
                    if (request == 2'b10)
                        state <= ACTIVE;
                    else if (request == 2'b00)
                        state <= IDLE;
                    else if (request == 2'b11)
                        state <= ACTIVE;
                end

                ACTIVE: begin
                    clk_enable <= 1'b1;
                    voltage_sel <= 2'b10;  // nominal voltage
                    boost_active <= 1'b0;
                    if (request == 2'b11 && !thermal_warning)
                        state <= BOOST;
                    else if (request == 2'b01)
                        state <= LOW_POWER;
                    else if (request == 2'b00)
                        state <= IDLE;
                    else if (thermal_warning)
                        state <= LOW_POWER;  // thermal throttle
                end

                BOOST: begin
                    clk_enable <= 1'b1;
                    voltage_sel <= 2'b11;  // highest voltage
                    boost_active <= 1'b1;
                    if (thermal_warning)
                        state <= ACTIVE;    // thermal forces exit boost
                    else if (request != 2'b11)
                        state <= ACTIVE;    // any non-boost request drops to active
                end
            endcase
        end
    end
endmodule
