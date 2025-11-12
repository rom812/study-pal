"""Create a simple test PDF for RAG testing."""

from pathlib import Path

# Create a simple text-based PDF content
pdf_content = """Chapter 1: Derivatives

A derivative represents the rate of change of a function with respect to a variable.
The derivative of f(x) = x^2 is f'(x) = 2x.

The chain rule is a formula for computing the derivative of a composition of functions.
If y = f(g(x)), then dy/dx = f'(g(x)) * g'(x).

Chapter 2: Integrals

An integral represents the area under a curve.
The integral is the inverse operation of differentiation.
The fundamental theorem of calculus connects derivatives and integrals.

Integration by parts: ∫u dv = uv - ∫v du

Chapter 3: Limits

A limit describes the value that a function approaches as the input approaches some value.
Limits are fundamental to calculus and are used to define derivatives and integrals.
"""

# Save as text file (we'll use it directly for testing)
output_path = Path(__file__).parent / "calculus_sample.txt"
output_path.write_text(pdf_content)
print(f"Created test file: {output_path}")
