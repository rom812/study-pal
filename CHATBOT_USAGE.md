# Study Pal Chatbot - Usage Guide

## Overview

The Study Pal Chatbot is an interactive AI tutor that combines:
- **RAG (Retrieval Augmented Generation)**: Retrieves relevant content from your study materials
- **Conversation Memory**: Remembers the last 10 exchanges for context-aware responses
- **GPT-4**: Provides natural, helpful explanations

## Getting Started

### 1. Start the Chatbot

```bash
python main.py --chat
```

Or simply:
```bash
python main.py
```

### 2. Load Study Materials

Before asking questions, load your PDF study materials:

```
💭 You: /ingest tests/fixtures/calculus_sample.pdf
```

### 3. Chat Naturally

Ask questions about your materials:

```
💭 You: What is a derivative?
🎓 Tutor: A derivative measures the rate of change...

💭 You: Can you give me an example?
🎓 Tutor: Sure! Let's say you have the function f(x) = x²...
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/ingest <path>` | Load a PDF file into knowledge base |
| `/count` | Show number of chunks in knowledge base |
| `/status` | Show system status (model, memory, materials) |
| `/clear` | Clear conversation history |
| `/clear-materials` | Clear all study materials |
| `/quit` or `/exit` | Exit the chatbot |

## Features

### 1. Context-Aware Responses

The chatbot remembers your previous questions:

```
💭 You: What is an integral?
🎓 Tutor: An integral is the opposite of a derivative...

💭 You: How does it relate to what we discussed earlier?
🎓 Tutor: Great question! Remember we talked about derivatives...
```

### 2. RAG-Powered Answers

Answers are based on your actual study materials:

```
💭 You: What does my textbook say about limits?
🎓 Tutor: [Retrieves relevant sections from your PDF and provides answer]
```

### 3. Sliding Window Memory

The chatbot remembers the last 10 message exchanges (20 messages total).
Older messages are automatically removed to manage context size.

## Example Session

```
🎓 Welcome to Study Pal Tutor Chatbot!
============================================================

💭 You: /ingest calculus_notes.pdf
✓ Successfully ingested calculus_notes.pdf (42 chunks)

💭 You: What is a derivative?
🎓 Tutor: A derivative represents the instantaneous rate of change...

💭 You: Can you explain that with the example from my notes?
🎓 Tutor: Certainly! In your notes, there's an example about velocity...

💭 You: /status
📊 System Status:
  Model: gpt-4
  Temperature: 0.7
  Knowledge base: 42 chunks
  Conversation: 6 messages in memory window

💭 You: /quit
👋 Goodbye! Happy studying! 📚
```

## Tips

1. **Load materials first**: The chatbot works best when you've ingested study materials
2. **Ask follow-up questions**: The memory allows for natural conversation flow
3. **Use /clear if stuck**: Clear conversation history if the context becomes confused
4. **Check /status**: Monitor your knowledge base and conversation state

## Architecture

```
User Question
     ↓
[Retrieve context from study materials]
     ↓
[Load conversation history]
     ↓
[Combine: System Prompt + Context + History + Question]
     ↓
[GPT-4 generates response]
     ↓
[Save to conversation memory]
     ↓
Response to User
```

## Customization

You can customize the chatbot by modifying parameters in `agents/tutor_chatbot.py`:

```python
chatbot = TutorChatbot(
    tutor_agent=tutor_agent,
    model_name="gpt-4",       # Change model
    temperature=0.7,          # Adjust creativity (0-1)
    memory_k=10,              # Change memory window size
)
```

## Troubleshooting

### No relevant context found

If the chatbot says "No relevant context found":
1. Make sure you've ingested materials with `/ingest`
2. Check that your question relates to the materials
3. Try rephrasing your question

### Memory issues

If responses seem off:
1. Use `/clear` to reset conversation
2. Check `/status` to see memory state
3. Reduce `memory_k` if context is too large

### API errors

If you get OpenAI API errors:
1. Check your `.env` file has `OPENAI_API_KEY`
2. Verify your API key is valid
3. Check your OpenAI account has credits

## Next Steps

- See [README.md](README.md) for full project documentation
- Run `python main.py --tutor-demo` for a guided demo
- Explore `agents/tutor_chatbot.py` to understand the implementation