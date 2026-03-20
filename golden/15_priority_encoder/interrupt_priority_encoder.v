// Interrupt Priority Encoder with Nested Interrupt Support
// Based on harishs1313 open-source design (GitHub)
`timescale 1ns/1ps

module interrupt_priority_encoder (
    input  wire        clk,
    input  wire        reset_n,
    input  wire [7:0]  interrupts,          // 8 interrupt request lines
    input  wire [7:0]  mask_reg,            // 1 = interrupt disabled
    input  wire [2:0]  current_isr_priority,// priority of running ISR
    input  wire        cpu_ack,             // CPU acknowledges interrupt
    output reg         int_valid,           // interrupt pending
    output reg  [2:0]  irq_id,             // highest-priority IRQ ID
    output reg  [7:0]  irq_ack,            // one-hot ack vector
    output wire        nested_int_pending,  // higher-priority IRQ waiting
    output wire [31:0] vector_addr          // ISR address = 0x1000 + irq_id*4
);

    reg [7:0] prev_irq;
    wire [7:0] active_irqs = interrupts & ~mask_reg;
    wire [7:0] edge_irqs  = active_irqs & ~prev_irq;

    // Fixed priority: IRQ0 = highest, IRQ7 = lowest
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            prev_irq  <= 8'b0;
            irq_id    <= 3'b000;
            int_valid <= 1'b0;
        end else begin
            prev_irq  <= active_irqs;
            int_valid <= 1'b0;

            casex (edge_irqs)
                8'bxxxxxxx1: begin irq_id <= 3'd0; int_valid <= 1'b1; end
                8'bxxxxxx10: begin irq_id <= 3'd1; int_valid <= 1'b1; end
                8'bxxxxx100: begin irq_id <= 3'd2; int_valid <= 1'b1; end
                8'bxxxx1000: begin irq_id <= 3'd3; int_valid <= 1'b1; end
                8'bxxx10000: begin irq_id <= 3'd4; int_valid <= 1'b1; end
                8'bxx100000: begin irq_id <= 3'd5; int_valid <= 1'b1; end
                8'bx1000000: begin irq_id <= 3'd6; int_valid <= 1'b1; end
                8'b10000000: begin irq_id <= 3'd7; int_valid <= 1'b1; end
                default:     begin int_valid <= 1'b0; end
            endcase
        end
    end

    // Nested interrupt: pending IRQ has higher priority (lower ID) than current ISR
    assign nested_int_pending = int_valid && (irq_id < current_isr_priority);

    // Vector address: base 0x1000, each entry 4 bytes apart
    assign vector_addr = 32'h00001000 + (irq_id * 4);

    // CPU acknowledgment generates one-hot ack pulse
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n)
            irq_ack <= 8'b0;
        else if (cpu_ack && int_valid)
            irq_ack <= (8'b1 << irq_id);
        else
            irq_ack <= 8'b0;
    end

endmodule
