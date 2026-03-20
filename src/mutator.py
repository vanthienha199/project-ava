"""
Mutation testing engine for Verilog designs.
Generates mutants by applying small syntactic changes to RTL source code,
then checks whether the test suite detects the injected bug.

This is the first open-source mutation testing engine for cocotb.
Commercial equivalent: Synopsys Certitude (~$200K/year).

Mutation Score = (Killed Mutants / Total Non-Equivalent Mutants) x 100%

Usage:
    from src.mutator import MutationEngine
    engine = MutationEngine()
    mutants = engine.generate_mutants(verilog_source)
    # Returns list of Mutant(source, category, line, description)
"""

import re
from dataclasses import dataclass


@dataclass
class Mutant:
    source: str           # Mutated Verilog source
    category: str         # Mutation category (e.g., "relational_op")
    line_num: int          # Line number where mutation was applied
    original: str          # Original line content
    mutated: str           # Mutated line content
    description: str       # Human-readable description


# Lines matching these patterns are structural — skip them for mutation
SKIP_PATTERNS = [
    r'^\s*$',                           # Empty lines
    r'^\s*//',                          # Comments
    r'^\s*/\*',                         # Block comment start
    r'^\s*\*',                          # Block comment body
    r'^\s*module\b',                    # Module declaration
    r'^\s*endmodule\b',                 # Module end
    r'^\s*input\b',                     # Input declaration
    r'^\s*output\b',                    # Output declaration
    r'^\s*inout\b',                     # Inout declaration
    r'^\s*wire\b',                      # Wire declaration
    r'^\s*reg\b',                       # Reg declaration
    r'^\s*integer\b',                   # Integer declaration
    r'^\s*parameter\b',                 # Parameter
    r'^\s*localparam\b',                # Localparam
    r'^\s*`',                           # Preprocessor directives
    r'^\s*\);',                         # Port list close
    r'^\s*\)',                          # Closing paren
    r'^\s*end\b',                       # End keyword alone
    r'^\s*begin\b',                     # Begin keyword alone
    r'^\s*else\s*$',                    # Bare else
    r'^\s*default\s*:',                 # Default case (removing would cause synth error)
    r'^\s*case\s*\(',                   # Case statement header
    r'^\s*endcase\b',                   # Endcase
    r'^\s*always\b',                    # Always block header
    r'^\s*assign\b.*=\s*\{',           # Concatenation assigns (complex)
    r'^\s*for\s*\(',                    # For loop header
    r'^\s*initial\b',                   # Initial block
    r'^\s*\$',                          # System tasks
]


class MutationEngine:
    """Generates Verilog mutants using regex-based mutation operators."""

    def __init__(self):
        self.operators = self._build_operators()

    def _build_operators(self):
        """Define mutation operators by category."""
        return {
            # Tier 1: High-value mutations (most likely to expose real bugs)
            "relational_op": [
                # == → != (equality flip — catches missing/wrong comparisons)
                (r'(?<![=!<>])={2}(?!=)', '!=', "== -> !="),
                # != → == (inequality flip)
                (r'!=', '==', "!= -> =="),
                # >= → > (off-by-one boundary)
                (r'>=', '>', ">= -> >"),
                # <= that is comparison (not NBA) → <
                # Only match <= when preceded by comparison context
                (r'(?<=\s)<=(?=\s*\d)', '<', "<= -> < (comparison)"),
                # > → >= (off-by-one boundary)
                (r'(?<![=\-])>(?!=)', '>=', "> -> >="),
                # < → <= (off-by-one boundary) — avoid matching <=
                (r'(?<![=<])(?<!<)<(?!=)(?!<)', '<=', "< -> <="),
            ],

            "logical_op": [
                # && → || (AND to OR — guard condition bugs)
                (r'&&', '||', "&& -> ||"),
                # || → && (OR to AND)
                (r'\|\|', '&&', "|| -> &&"),
            ],

            "arithmetic_op": [
                # + → - (addition to subtraction)
                (r'(?<![+])\+(?![+=])', '-', "+ -> -"),
                # - → + (subtraction to addition) — avoid ->
                (r'(?<![->])-(?![->])', '+', "- -> +"),
            ],

            "constant_bit": [
                # 1'b0 → 1'b1 (bit flip)
                (r"1'b0", "1'b1", "1'b0 -> 1'b1"),
                # 1'b1 → 1'b0 (bit flip)
                (r"1'b1", "1'b0", "1'b1 -> 1'b0"),
            ],

            "conditional_negation": [
                # if (signal) → if (!signal) — polarity bugs
                (r'if\s*\(\s*([a-zA-Z_]\w*)\s*\)', r'if (!\1)', "if(x) -> if(!x)"),
                # if (!signal) → if (signal) — remove negation
                (r'if\s*\(\s*!([a-zA-Z_]\w*)\s*\)', r'if (\1)', "if(!x) -> if(x)"),
            ],

            # Tier 2: Medium-value mutations
            "stuck_at": [
                # Replace RHS of assignment with 0
                # Pattern: <= <expr>; → <= 0;  (for single-bit or narrow signals)
                # This is handled specially in generate_mutants
            ],

            "bitwise_vs_logical": [
                # & → && (bitwise AND to logical AND)
                (r'(?<![&])&(?![&{])', '&&', "& -> &&"),
                # | → || (bitwise OR to logical OR)
                (r'(?<![|])\|(?![|{])', '||', "| -> ||"),
            ],
        }

    def _is_structural_line(self, line):
        """Check if a line is structural (should not be mutated)."""
        for pattern in SKIP_PATTERNS:
            if re.match(pattern, line):
                return True
        return False

    def _is_nba_assignment(self, line, match_pos):
        """Check if <= at match_pos is a non-blocking assignment, not comparison."""
        # In Verilog, <= is NBA when it appears as: signal <= expr;
        # It's comparison when it appears in: if (a <= b)
        before = line[:match_pos].strip()
        # If the line contains 'if' or 'else if' or is inside a condition, it's comparison
        if re.search(r'\b(if|else\s+if|while|case)\b', before):
            return False
        # If there's a signal name right before <=, it's NBA
        if re.search(r'[a-zA-Z_]\w*\s*$', before):
            return True
        return False

    def generate_mutants(self, verilog_source: str) -> list:
        """
        Generate all mutants from a Verilog source file.

        Returns:
            List of Mutant objects, each with a single mutation applied.
        """
        mutants = []
        lines = verilog_source.split('\n')

        for i, line in enumerate(lines):
            if self._is_structural_line(line):
                continue

            # Apply each operator category
            for category, ops in self.operators.items():
                if category == "stuck_at":
                    # Handle stuck-at separately
                    stuck_mutants = self._generate_stuck_at(lines, i, line)
                    mutants.extend(stuck_mutants)
                    continue

                for pattern, replacement, desc in ops:
                    # Special handling for <= comparison vs NBA
                    if desc == "<= -> < (comparison)":
                        # Only apply if it's actually a comparison
                        match = re.search(pattern, line)
                        if match and self._is_nba_assignment(line, match.start()):
                            continue

                    # Check if pattern matches
                    if re.search(pattern, line):
                        new_line = re.sub(pattern, replacement, line, count=1)
                        if new_line != line:  # Ensure mutation actually changed something
                            mutated_lines = lines.copy()
                            mutated_lines[i] = new_line
                            mutants.append(Mutant(
                                source='\n'.join(mutated_lines),
                                category=category,
                                line_num=i + 1,
                                original=line.strip(),
                                mutated=new_line.strip(),
                                description=f"Line {i+1}: {desc}",
                            ))

        return mutants

    def _generate_stuck_at(self, lines, line_idx, line):
        """Generate stuck-at-0 mutants for NBA assignments."""
        mutants = []

        # Match: signal <= expression;
        match = re.match(r'^(\s*\w+(?:\[\S+\])?\s*<=\s*)(.+?)\s*;', line)
        if match and not re.search(r'\b(if|else|case|for)\b', line):
            prefix = match.group(1)
            # Stuck at zero
            new_line = f"{prefix}0;"
            if new_line.strip() != line.strip():
                mutated_lines = lines.copy()
                mutated_lines[line_idx] = new_line
                mutants.append(Mutant(
                    source='\n'.join(mutated_lines),
                    category="stuck_at_zero",
                    line_num=line_idx + 1,
                    original=line.strip(),
                    mutated=new_line.strip(),
                    description=f"Line {line_idx+1}: stuck-at-zero",
                ))

        return mutants

    def summary(self, mutants: list) -> dict:
        """Summarize mutants by category."""
        cats = {}
        for m in mutants:
            cats[m.category] = cats.get(m.category, 0) + 1
        return cats


@dataclass
class MutationResult:
    """Result of running tests against a single mutant."""
    mutant: Mutant
    killed: bool              # True if tests detected the mutation
    survived: bool            # True if tests passed despite mutation
    error: bool = False       # True if mutant caused compilation error
    compile_error: bool = False  # True if iverilog failed to compile
    tests_passed: int = 0
    tests_total: int = 0
    error_message: str = ""


@dataclass
class MutationReport:
    """Full mutation testing report for a design."""
    design_name: str
    total_mutants: int
    killed: int
    survived: int
    errors: int               # Compile errors (equivalent to killed)
    mutation_score: float     # killed / (total - compile_errors) * 100
    results: list             # List of MutationResult
    summary_by_category: dict  # {category: {total, killed, survived}}

    def to_dict(self) -> dict:
        return {
            "design_name": self.design_name,
            "total_mutants": self.total_mutants,
            "killed": self.killed,
            "survived": self.survived,
            "errors": self.errors,
            "mutation_score": round(self.mutation_score, 1),
            "by_category": self.summary_by_category,
            "survived_details": [
                {
                    "line": r.mutant.line_num,
                    "category": r.mutant.category,
                    "original": r.mutant.original,
                    "mutated": r.mutant.mutated,
                    "description": r.mutant.description,
                }
                for r in self.results if r.survived
            ],
        }
