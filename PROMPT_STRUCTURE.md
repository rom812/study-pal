# Ultimate Prompt Structure for Cursor Code Agent

## Overview
This document defines the optimal prompt structure to maximize token efficiency and get the best results from Cursor's code agent. Follow this structure to ensure clear, actionable, and cost-effective prompts.

---

## Core Prompt Structure

### Template
```
[CONTEXT] + [INTENT] + [CONSTRAINTS] + [ACCEPTANCE_CRITERIA] + [PRIORITIES]
```

### Components Breakdown

#### 1. CONTEXT (What)
**Purpose**: Provide background about what needs to be done
**Format**: 
- State the current situation
- Reference specific files/components if relevant
- Include relevant code snippets or file paths

**Example**:
```
In the tutor_agent.py file, the generate_quiz method currently returns 
unstructured text. The RAG pipeline in core/rag_pipeline.py has been 
updated to support structured outputs.
```

#### 2. INTENT (Why/What)
**Purpose**: Clearly state what you want to achieve
**Format**:
- Use action verbs (create, modify, refactor, add, remove, fix)
- Be specific about the desired outcome
- Include the target location if applicable

**Example**:
```
Refactor the generate_quiz method to return a Pydantic model that matches 
the QuizSchema defined in core/utils.py, ensuring all quiz questions 
include validation and metadata.
```

#### 3. CONSTRAINTS (How)
**Purpose**: Specify limitations, requirements, or patterns to follow
**Format**:
- List technical constraints
- Reference existing patterns in the codebase
- Specify dependencies or integrations
- Include performance requirements if relevant

**Example**:
```
- Use the existing Pydantic models from core/utils.py
- Maintain backward compatibility with the current API
- Follow the error handling pattern used in scheduler_agent.py
- Ensure all quiz outputs validate against QuizSchema
- Use async/await pattern consistent with other agents
```

#### 4. ACCEPTANCE_CRITERIA (Done When)
**Purpose**: Define what "done" looks like
**Format**:
- List specific, testable outcomes
- Include edge cases to handle
- Specify validation requirements

**Example**:
```
- generate_quiz returns a QuizSchema instance
- All quiz questions have required fields (question, options, correct_answer)
- Invalid inputs raise ValidationError with clear messages
- Existing tests in tests/test_tutor.py pass
- New unit tests cover Pydantic validation
```

#### 5. PRIORITIES (Order)
**Purpose**: Specify what to focus on first
**Format**:
- Order tasks if multiple changes needed
- Highlight critical paths
- Note what can be deferred

**Example**:
```
Priority 1: Implement Pydantic model return type
Priority 2: Add validation for quiz generation
Priority 3: Update existing tests
Priority 4: Add new test cases for edge cases
```

---

## Prompt Patterns by Task Type

### Pattern 1: Feature Addition
```
CONTEXT: [Current state of relevant code]
INTENT: Add [feature] to [component] that [does something]
CONSTRAINTS:
  - [Technical constraint 1]
  - [Pattern to follow]
  - [Integration requirement]
ACCEPTANCE_CRITERIA:
  - [Testable outcome 1]
  - [Testable outcome 2]
PRIORITIES:
  - [Focus area 1]
  - [Focus area 2]
```

### Pattern 2: Bug Fix
```
CONTEXT: [Issue description] in [file/component]
INTENT: Fix [specific bug] that causes [problem]
CONSTRAINTS:
  - [What not to break]
  - [Performance requirement]
ACCEPTANCE_CRITERIA:
  - [Bug is resolved]
  - [No regressions]
  - [Tests pass]
PRIORITIES:
  - [Critical fix]
  - [Edge cases]
```

### Pattern 3: Refactoring
```
CONTEXT: [Current implementation] in [file]
INTENT: Refactor [component] to [improve aspect] while [maintaining behavior]
CONSTRAINTS:
  - [Maintain API compatibility]
  - [Follow pattern from X]
  - [Performance target]
ACCEPTANCE_CRITERIA:
  - [All tests pass]
  - [Code quality improved]
  - [No breaking changes]
PRIORITIES:
  - [Core refactoring]
  - [Optimization]
```

### Pattern 4: Integration
```
CONTEXT: [Existing system] and [new component/service]
INTENT: Integrate [component] with [system] to enable [functionality]
CONSTRAINTS:
  - [API constraints]
  - [Error handling pattern]
  - [Configuration approach]
ACCEPTANCE_CRITERIA:
  - [Integration works]
  - [Error cases handled]
  - [Tests added]
PRIORITIES:
  - [Core integration]
  - [Error handling]
  - [Testing]
```

---

## Best Practices

### ✅ DO
1. **Be Specific**: Use file paths, function names, and concrete examples
2. **Provide Context**: Reference existing code patterns and structures
3. **Define Success**: Include clear acceptance criteria
4. **Set Constraints**: Specify what must be maintained or avoided
5. **Prioritize**: Order tasks if multiple changes are needed
6. **Reference Files**: Use code references when pointing to existing code
7. **Include Examples**: Show desired input/output when relevant

### ❌ DON'T
1. **Avoid Vague Requests**: "Make it better" → "Refactor X to improve Y"
2. **Don't Skip Context**: Always reference relevant existing code
3. **Don't Forget Constraints**: Mention what shouldn't change
4. **Don't Omit Criteria**: Define how to verify success
5. **Don't Mix Concerns**: Keep prompts focused on one task
6. **Don't Assume Knowledge**: Reference files and patterns explicitly

---

## Token Optimization Tips

### 1. Use Code References
Instead of pasting full code blocks, reference files:
```
Good: In agents/tutor_agent.py, the generate_quiz method...
Bad: [pastes 50 lines of code]
```

### 2. Reference Existing Patterns
Point to similar implementations:
```
Good: Follow the error handling pattern from scheduler_agent.py lines 45-60
Bad: Handle errors properly
```

### 3. Be Concise but Complete
Include all necessary info without redundancy:
```
Good: Add validation to generate_quiz using QuizSchema from core/utils.py
Bad: Add validation to the method that generates quizzes, you know the one 
     in tutor_agent.py, and use the schema thing from utils, you know what I mean
```

### 4. Batch Related Changes
Group related modifications in one prompt:
```
Good: Refactor all agent classes to use the new BaseAgent pattern
Bad: Refactor tutor_agent, then scheduler_agent, then motivator_agent...
```

---

## Example: Converting Natural Prompt to Structured Prompt

### Natural Prompt (Inefficient)
```
"Hey, I want to add error handling to the tutor agent. Make sure it 
doesn't break anything and handles errors nicely."
```

### Structured Prompt (Optimized)
```
CONTEXT: The tutor_agent.py file currently lacks comprehensive error 
handling. The scheduler_agent.py (lines 45-60) demonstrates the error 
handling pattern we use across agents.

INTENT: Add error handling to all public methods in TutorAgent class 
that interact with external services (RAG pipeline, LLM calls) to 
prevent crashes and provide user-friendly error messages.

CONSTRAINTS:
  - Follow the error handling pattern from scheduler_agent.py (try/except 
    with logging and user-friendly messages)
  - Use the existing logger from core/utils.py
  - Maintain backward compatibility with current API
  - Don't change method signatures
  - Handle: API failures, validation errors, timeout errors

ACCEPTANCE_CRITERIA:
  - All public methods have try/except blocks
  - Errors are logged with appropriate levels
  - User-facing errors return clear messages (no stack traces)
  - Existing tests in tests/test_tutor.py still pass
  - New tests cover error scenarios

PRIORITIES:
  1. Add error handling to generate_quiz method
  2. Add error handling to answer_question method
  3. Add error handling to analyze_weakness method
  4. Add tests for error cases
```

---

## Quick Reference Checklist

Before sending a prompt, ensure:
- [ ] Context is provided (what/where)
- [ ] Intent is clear (what to do)
- [ ] Constraints are specified (how/limitations)
- [ ] Acceptance criteria are defined (when done)
- [ ] Priorities are set (order of work)
- [ ] File paths are included
- [ ] Existing patterns are referenced
- [ ] Examples are provided if needed

---

## Usage Workflow

1. **Write your natural prompt** in plain language
2. **Review this document** to identify the components
3. **Convert using the template** above
4. **Optimize** by adding file references and constraints
5. **Send to Cursor** with the structured format

---

## Notes

- This structure works best for code changes and feature additions
- For simple questions, a shorter format may suffice
- Always include file paths when referencing code
- Use code references (startLine:endLine:filepath) when showing existing code
- Keep prompts focused - one main task per prompt for best results

