# CLAUDE.md - Project Guidelines

## Workflow Principles
When asked to do a simple task (commit, push, quick fix), do it quickly without extensive exploration or cleanup unless explicitly requested.

## Communication Guidelines
Before claiming a task is 'already complete' or 'done', verify by showing the user the specific output or asking for confirmation.

## Debugging
When debugging or investigating issues, set a time limit for exploration (3-4 tool calls). If not making progress, pause and summarize findings to the user rather than continuing to explore indefinitely.

## Project Overview
This is a Python/TypeScript portfolio project (StudyPal). Primary stack:
- Python backend with FastAPI
- TypeScript/Next.js frontend
- RAG pipeline with vector stores
- Terraform for infrastructure
- AWS App Runner for deployment

## Useful Prompts

### Tighter Debugging
```
Diagnose why [X] is failing. Don't fix anything yet - just tell me the root cause in 2-3 sentences, then stop.
```

### Progress Checkpoints
```
After every 3 tool calls, pause and give me a one-line status update. If you're not making progress, stop and ask me for guidance.
```

### Deployment Prerequisites
```
Before deploying, list all prerequisites (images, env vars, DB state, etc.) and verify each one exists. Only proceed to deploy after confirming all prerequisites are met.
```
