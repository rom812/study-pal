# How to Use the Prompt Structure System

## Overview
This system helps you convert natural language prompts into structured, token-efficient prompts for Cursor Code Agent.

## Two Ways to Use

### Method 1: Use the AI Assistant (Auto-Conversion)
**Simply write your prompt naturally, and I'll automatically convert it using the structure guide.**

Example:
- **You write**: "Add error handling to the tutor agent"
- **I'll convert it to**: Structured format with CONTEXT, INTENT, CONSTRAINTS, etc.
- **Then execute**: Based on the structured prompt

### Method 2: Use the Script (Manual Conversion)
**Use the Python script to convert prompts yourself before sending.**

#### Quick Start
```bash
# Interactive mode
python scripts/prompt_converter.py

# Command line mode
python scripts/prompt_converter.py "your natural prompt here"
```

#### Example Usage
```bash
$ python scripts/prompt_converter.py "Add error handling to tutor_agent.py"

## Structured Prompt

**CONTEXT:** Current state involves: tutor_agent.py

**INTENT:** Add: Add error handling to tutor_agent.py

**CONSTRAINTS:**
  - Maintain existing functionality
  - Follow existing code patterns
  - Ensure all tests pass

**ACCEPTANCE_CRITERIA:**
  - Functionality works as expected
  - No breaking changes
  - Tests pass

**PRIORITIES:**
  1. Add: Add error handling to tutor_agent.py
```

## Recommended Workflow

### For Simple Requests
Just write naturally - I'll handle the conversion automatically.

### For Complex Requests
1. Write your natural prompt
2. Review `PROMPT_STRUCTURE.md` for the structure
3. Refine your prompt with:
   - Specific file paths
   - Clear constraints
   - Acceptance criteria
   - Priorities

### For Best Results
Always include:
- ✅ File paths (e.g., `agents/tutor_agent.py`)
- ✅ Reference existing patterns (e.g., "like in scheduler_agent.py")
- ✅ Clear constraints (e.g., "maintain backward compatibility")
- ✅ Acceptance criteria (e.g., "all tests pass")
- ✅ Priorities (e.g., "focus on error handling first")

## Examples

### Example 1: Simple Feature Addition
**Natural Prompt:**
```
Add validation to the generate_quiz method in tutor_agent.py
```

**Structured Prompt (Auto-converted):**
```
CONTEXT: Current state involves: tutor_agent.py. The generate_quiz method 
currently returns unstructured data.

INTENT: Add validation to generate_quiz method to ensure all quiz outputs 
comply with QuizSchema from core/utils.py

CONSTRAINTS:
  - Use existing QuizSchema from core/utils.py
  - Maintain backward compatibility
  - Follow error handling pattern from scheduler_agent.py
  - Ensure all tests pass

ACCEPTANCE_CRITERIA:
  - generate_quiz returns validated QuizSchema instances
  - Invalid data raises ValidationError
  - Existing tests pass
  - New validation tests added

PRIORITIES:
  1. Implement Pydantic validation
  2. Add error handling
  3. Update tests
```

### Example 2: Bug Fix
**Natural Prompt:**
```
Fix the issue where the scheduler agent crashes when given invalid dates
```

**Structured Prompt (Auto-converted):**
```
CONTEXT: Current state involves: scheduler_agent.py. The agent crashes 
when processing invalid date inputs.

INTENT: Fix date validation in scheduler_agent.py to handle invalid dates 
gracefully without crashing

CONSTRAINTS:
  - Maintain existing API
  - Return user-friendly error messages
  - Follow error handling pattern from other agents
  - Don't break existing valid date processing

ACCEPTANCE_CRITERIA:
  - Invalid dates return error messages (no crashes)
  - Valid dates still work correctly
  - Error messages are user-friendly
  - Tests cover invalid date scenarios

PRIORITIES:
  1. Add date validation
  2. Add error handling
  3. Add tests for edge cases
```

## Tips for Maximum Token Efficiency

1. **Reference Files, Don't Paste Code**
   - Good: "In agents/tutor_agent.py, line 45..."
   - Bad: [pastes 50 lines of code]

2. **Reference Existing Patterns**
   - Good: "Follow the pattern from scheduler_agent.py lines 30-50"
   - Bad: "Handle errors properly"

3. **Be Specific About Constraints**
   - Good: "Maintain backward compatibility with current API"
   - Bad: "Don't break anything"

4. **Define Clear Success Criteria**
   - Good: "All tests in tests/test_tutor.py pass"
   - Bad: "It works"

5. **Batch Related Changes**
   - Good: "Refactor all agent classes to use BaseAgent pattern"
   - Bad: "Refactor tutor_agent, then scheduler_agent, then..."

## Quick Reference

- **Structure Guide**: See `PROMPT_STRUCTURE.md`
- **Converter Script**: `scripts/prompt_converter.py`
- **Usage Guide**: This file (`PROMPT_USAGE.md`)

## Need Help?

Just ask! I can:
- Convert your prompts automatically
- Help refine your prompts
- Explain the structure
- Provide examples for your specific use case

