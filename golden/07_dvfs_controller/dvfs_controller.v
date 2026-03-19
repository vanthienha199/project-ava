`timescale 1ns / 1ps

module dvfs_controller (
    input clk,
    input rst,
    input [7:0] workload,        // 0-255 workload intensity
    input [7:0] temperature,     // 0-255 temperature reading
    input [7:0] temp_threshold,  // thermal throttle threshold
    input [7:0] power_budget,    // max power allowed
    output reg [2:0] freq_sel,   // frequency select (0-7, higher=faster)
    output reg [2:0] voltage_sel,// voltage select (0-7, higher=more power)
    output reg throttled,        // 1 when thermally throttled
    output reg [7:0] power_est   // estimated power (proportional to V*f)
);

    // DVFS levels (freq_sel and voltage_sel are coupled)
    // Level 0: lowest power  → freq=0, volt=0, power~0
    // Level 7: highest power → freq=7, volt=7, power~49

    reg [2:0] target_level;
    reg [2:0] current_level;

    // Workload → target level mapping (simple thresholds)
    always @(*) begin
        if (workload < 32)
            target_level = 3'd0;
        else if (workload < 64)
            target_level = 3'd1;
        else if (workload < 96)
            target_level = 3'd2;
        else if (workload < 128)
            target_level = 3'd3;
        else if (workload < 160)
            target_level = 3'd4;
        else if (workload < 192)
            target_level = 3'd5;
        else if (workload < 224)
            target_level = 3'd6;
        else
            target_level = 3'd7;
    end

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            current_level <= 3'd0;
            freq_sel <= 3'd0;
            voltage_sel <= 3'd0;
            throttled <= 1'b0;
            power_est <= 8'd0;
        end else begin
            // Thermal throttling: if over threshold, clamp to level 2 max
            if (temperature >= temp_threshold) begin
                throttled <= 1'b1;
                if (current_level > 3'd2)
                    current_level <= current_level - 1;  // ramp down one step per cycle
                else
                    current_level <= current_level;       // hold at floor
            end else begin
                throttled <= 1'b0;
                // Power budget check: power ~ level * level (rough V*f model)
                if (target_level > current_level) begin
                    // Ramp up one step per cycle (safe voltage scaling)
                    if ((current_level + 1) * (current_level + 1) <= power_budget)
                        current_level <= current_level + 1;
                end else if (target_level < current_level) begin
                    // Ramp down one step per cycle
                    current_level <= current_level - 1;
                end
            end

            // Outputs follow current_level
            freq_sel <= current_level;
            voltage_sel <= current_level;
            power_est <= current_level * current_level;  // simplified V*f power model
        end
    end
endmodule
