// Watchdog Timer — 32-bit countdown with kick (reload) and timeout
// Based on Efabless EF_WDT32 open-source IP (Apache 2.0)
// https://github.com/efabless/EF_WDT32
module watchdog_timer (
    input  wire        clk,
    input  wire        rst_n,      // active-low async reset
    input  wire        enable,     // enable countdown
    input  wire        kick,       // pulse to reload counter (pet the dog)
    input  wire [31:0] load_val,   // timeout reload value
    output reg  [31:0] count,      // current counter value
    output wire        timeout     // high when counter hits zero while enabled
);

    assign timeout = enable & (count == 32'd0);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 32'h0;
        end else if (!enable) begin
            count <= load_val;       // hold at load value when disabled
        end else if (kick) begin
            count <= load_val;       // reload on kick
        end else if (timeout) begin
            count <= load_val;       // auto-reload on timeout
        end else begin
            count <= count - 32'd1;  // countdown
        end
    end

endmodule
