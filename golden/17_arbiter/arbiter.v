// Round-Robin Arbiter — 4 requestors
// Fair scheduling: rotates priority after each grant
// Single-cycle grant when request is present

module arbiter (
    input  wire       clk,
    input  wire       rst,        // Async reset, active high
    input  wire [3:0] req,        // Request lines (one-hot or multiple)
    output reg  [3:0] grant,      // Grant lines (one-hot, at most 1 bit set)
    output reg        valid       // High when a grant is active
);

    reg [1:0] priority_ptr;       // Points to highest-priority requestor

    // Combinational: find next grant based on round-robin priority
    reg [3:0] grant_next;
    reg       valid_next;

    always @(*) begin
        grant_next = 4'b0000;
        valid_next = 1'b0;

        // Check requestors starting from priority_ptr, wrapping around
        case (priority_ptr)
            2'd0: begin
                if      (req[0]) begin grant_next = 4'b0001; valid_next = 1'b1; end
                else if (req[1]) begin grant_next = 4'b0010; valid_next = 1'b1; end
                else if (req[2]) begin grant_next = 4'b0100; valid_next = 1'b1; end
                else if (req[3]) begin grant_next = 4'b1000; valid_next = 1'b1; end
            end
            2'd1: begin
                if      (req[1]) begin grant_next = 4'b0010; valid_next = 1'b1; end
                else if (req[2]) begin grant_next = 4'b0100; valid_next = 1'b1; end
                else if (req[3]) begin grant_next = 4'b1000; valid_next = 1'b1; end
                else if (req[0]) begin grant_next = 4'b0001; valid_next = 1'b1; end
            end
            2'd2: begin
                if      (req[2]) begin grant_next = 4'b0100; valid_next = 1'b1; end
                else if (req[3]) begin grant_next = 4'b1000; valid_next = 1'b1; end
                else if (req[0]) begin grant_next = 4'b0001; valid_next = 1'b1; end
                else if (req[1]) begin grant_next = 4'b0010; valid_next = 1'b1; end
            end
            2'd3: begin
                if      (req[3]) begin grant_next = 4'b1000; valid_next = 1'b1; end
                else if (req[0]) begin grant_next = 4'b0001; valid_next = 1'b1; end
                else if (req[1]) begin grant_next = 4'b0010; valid_next = 1'b1; end
                else if (req[2]) begin grant_next = 4'b0100; valid_next = 1'b1; end
            end
        endcase
    end

    // Sequential: register grant and update priority pointer
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            grant        <= 4'b0000;
            valid        <= 1'b0;
            priority_ptr <= 2'd0;
        end else begin
            grant <= grant_next;
            valid <= valid_next;

            // Rotate priority: after granting requestor N, next priority starts at N+1
            if (valid_next) begin
                case (grant_next)
                    4'b0001: priority_ptr <= 2'd1;
                    4'b0010: priority_ptr <= 2'd2;
                    4'b0100: priority_ptr <= 2'd3;
                    4'b1000: priority_ptr <= 2'd0;
                    default: priority_ptr <= priority_ptr;
                endcase
            end
        end
    end
endmodule
