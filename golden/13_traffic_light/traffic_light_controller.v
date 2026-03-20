// Traffic Light Controller — Highway/Farm Road intersection with sensor
// Based on open-source designs from Devipriya1921 and fpga4student.com
module traffic_light_controller (
    input  wire       clk,
    input  wire       rst,            // active-high synchronous reset
    input  wire       sensor,         // vehicle detected on farm road
    output reg  [2:0] highway_light,  // {red, yellow, green}
    output reg  [2:0] farm_light      // {red, yellow, green}
);

    // Light encoding: 3'b001 = green, 3'b010 = yellow, 3'b100 = red
    localparam GREEN  = 3'b001;
    localparam YELLOW = 3'b010;
    localparam RED    = 3'b100;

    // States
    localparam S_HWY_GREEN  = 2'b00;  // Highway green, farm red
    localparam S_HWY_YELLOW = 2'b01;  // Highway yellow, farm red
    localparam S_FARM_GREEN = 2'b10;  // Highway red, farm green
    localparam S_FARM_YELLOW= 2'b11;  // Highway red, farm yellow

    // Timing (in clock cycles): green=7, yellow=3, farm_green=5
    localparam T_HWY_GREEN  = 4'd7;
    localparam T_YELLOW     = 4'd3;
    localparam T_FARM_GREEN = 4'd5;

    reg [1:0] state;
    reg [3:0] count;

    // State machine + counter
    always @(posedge clk) begin
        if (rst) begin
            state <= S_HWY_GREEN;
            count <= 4'd0;
        end else begin
            case (state)
                S_HWY_GREEN: begin
                    if (count >= T_HWY_GREEN - 1 && sensor) begin
                        state <= S_HWY_YELLOW;
                        count <= 4'd0;
                    end else begin
                        count <= count + 4'd1;
                    end
                end
                S_HWY_YELLOW: begin
                    if (count >= T_YELLOW - 1) begin
                        state <= S_FARM_GREEN;
                        count <= 4'd0;
                    end else begin
                        count <= count + 4'd1;
                    end
                end
                S_FARM_GREEN: begin
                    if (count >= T_FARM_GREEN - 1) begin
                        state <= S_FARM_YELLOW;
                        count <= 4'd0;
                    end else begin
                        count <= count + 4'd1;
                    end
                end
                S_FARM_YELLOW: begin
                    if (count >= T_YELLOW - 1) begin
                        state <= S_HWY_GREEN;
                        count <= 4'd0;
                    end else begin
                        count <= count + 4'd1;
                    end
                end
            endcase
        end
    end

    // Output logic
    always @(*) begin
        case (state)
            S_HWY_GREEN:   begin highway_light = GREEN;  farm_light = RED;    end
            S_HWY_YELLOW:  begin highway_light = YELLOW; farm_light = RED;    end
            S_FARM_GREEN:  begin highway_light = RED;    farm_light = GREEN;  end
            S_FARM_YELLOW: begin highway_light = RED;    farm_light = YELLOW; end
            default:       begin highway_light = RED;    farm_light = RED;    end
        endcase
    end

endmodule
