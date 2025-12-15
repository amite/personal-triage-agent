# LLM Provider Setup Guide

This guide explains how to configure and switch between different LLM providers (Ollama vs GPT-4) in the Personal Task Manager Triage system.

## Quick Setup

### 1. Using Ollama (Default)

No configuration needed! The system defaults to Ollama.

```bash
# Just run the application normally
python main.py
```

### 2. Using GPT-4

#### Option A: Environment Variables (Recommended)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```ini
   LLM_PROVIDER=gpt
   OPENAI_API_KEY=your-api-key-here
   ```

3. Run the application:
   ```bash
   python main.py
   ```

#### Option B: Programmatic Configuration

```python
from agents.llm_factory import LLMFactory
from agents.llm_triage_agent import LLMTriageAgent

# Create GPT client
gpt_client = LLMFactory.create_llm_client("gpt", api_key="your-api-key")

# Use with agents
triage_agent = LLMTriageAgent(llm_client=gpt_client)
```

## Configuration Options

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LLM_PROVIDER` | Provider to use (`ollama` or `gpt`) | No | `ollama` |
| `OPENAI_API_KEY` | API key for GPT-4 | Only for GPT | None |

### Programmatic Usage

```python
from agents.llm_factory import LLMFactory

# Create specific clients
ollama_client = LLMFactory.create_llm_client("ollama")
gpt_client = LLMFactory.create_llm_client("gpt", api_key="your-key")

# Use with any agent
from agents.llm_triage_agent import LLMTriageAgent
from agents.llm_drafting_agent import LLMDraftingAgent

triage_agent = LLMTriageAgent(llm_client=gpt_client)
drafting_agent = LLMDraftingAgent(llm_client=ollama_client)
```

## Architecture

The system uses a Strategy Pattern with:

1. **`LLMClientBase`** - Abstract interface for all LLM clients
2. **`OllamaClient`** - Concrete implementation for Ollama
3. **`GPTClient`** - Concrete implementation for GPT-4
4. **`LLMFactory`** - Factory for creating and switching clients

This design allows seamless switching between providers without changing application code.