// PWM (Pulse Width Modulation) generator
// Used in voltage regulators, motor control, LED dimming, power management
// Configurable period and duty cycle via registers
module pwm (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       enable,
    input  wire [7:0] period,      // PWM period (counter counts 0 to period-1)
    input  wire [7:0] duty,        // Duty cycle threshold (output high when counter < duty)
    output reg        pwm_out,
    output reg  [7:0] counter
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 8'd0;
            pwm_out <= 1'b0;
        end else if (!enable) begin
            counter <= 8'd0;
            pwm_out <= 1'b0;
        end else begin
            // Counter logic
            if (counter >= period - 1)
                counter <= 8'd0;
            else
                counter <= counter + 1;

            // PWM output: high when counter < duty
            if (counter < duty)
                pwm_out <= 1'b1;
            else
                pwm_out <= 1'b0;
        end
    end

endmodule
