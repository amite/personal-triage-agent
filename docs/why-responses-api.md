# Why We Use the Responses API Instead of Completions API

## Overview

Our `GPTClient` implementation uses OpenAI's **Responses API** (`client.responses.create()`) instead of the traditional Chat Completions API (`client.chat.completions.create()`). This document explains the technical and practical reasons for this architectural choice.

## Key Benefits of the Responses API

### 1. **Chain of Thought (CoT) Support for GPT-5 Models**

The primary advantage of the Responses API, especially for GPT-5 models like `gpt-5-nano` (our default model), is its ability to **pass chain of thought (CoT) reasoning between turns**. This capability:

- **Improves intelligence**: Internal evaluations show a 3% improvement in SWE-bench with the same prompt and setup
- **Reduces reasoning tokens**: Fewer generated reasoning tokens means lower costs
- **Increases cache hit rates**: 40% to 80% improvement in cache utilization compared to Chat Completions
- **Decreases latency**: Faster response times due to better internal reasoning reuse

This feature is **exclusive to the Responses API** and is not available in Chat Completions.

### 2. **Agentic by Default**

The Responses API is designed as an agentic loop, allowing the model to:

- Call multiple tools within a single API request (e.g., `web_search`, `image_generation`, `file_search`, `code_interpreter`)
- Integrate with remote MCP servers
- Execute custom functions
- Handle complex multi-step workflows without manual orchestration

This makes it ideal for agent-based applications like our triage agent.

### 3. **Lower Costs**

The improved cache utilization (40-80% improvement) directly translates to:

- Fewer tokens processed
- Lower API costs
- Better performance for repeated or similar queries

### 4. **Stateful Context**

The Responses API supports stateful conversations through the `store: true` parameter, which:

- Maintains state from turn to turn
- Preserves reasoning and tool context across interactions
- Enables more coherent multi-turn conversations

### 5. **Flexible Inputs**

The API accepts:

- Simple string inputs (like our current implementation)
- Lists of messages (for more complex conversation structures)
- Instructions for system-level guidance

This flexibility allows for easier evolution of our implementation.

### 6. **Future-Proof**

OpenAI recommends the Responses API for all new projects. It's designed as:

- A **superset** of the Chat Completions API (includes all Chat Completions functionality)
- The recommended approach for upcoming models
- The evolution of Chat Completions with added simplicity and powerful primitives

## Technical Implementation Details

### Current Implementation

In `agents/gpt_client.py`, we use:

```python
response = self.client.responses.create(
    model=model,
    input=prompt,
    max_output_tokens=2000,
    timeout=60.0
)
```

### Model-Specific Considerations

- **GPT-5 models**: Don't support the `temperature` parameter in the Responses API (as noted in our code comments)
- **Non-GPT-5 models**: Can still use temperature and other traditional parameters
- **Response structure**: The Responses API uses a different response structure (`output` array with `message` items) compared to Chat Completions

### Response Parsing

The Responses API returns a structured response that we parse:

1. First, we try the SDK convenience property `response.output_text` (if available)
2. Fallback to manual parsing of the `response.output` array structure:
   - Navigate through `output` → `message` items → `content` array → `output_text` items → `text`

This parsing logic is more complex than Chat Completions but provides access to richer response metadata.

## Migration Context

### Why Not Chat Completions?

While Chat Completions remains supported and functional, it lacks:

- Chain of thought passing between turns (critical for GPT-5 models)
- Built-in agentic capabilities
- Stateful conversation management
- The performance and cost benefits mentioned above

### Compatibility

The Responses API is a **superset** of Chat Completions, meaning:

- All Chat Completions functionality is available
- Both APIs will continue to be supported
- Incremental migration is possible (though we've chosen Responses from the start)

## Recommendations

For our use case (a personal triage agent using GPT-5 models), the Responses API is the optimal choice because:

1. **We use GPT-5 models**: The CoT passing feature provides significant benefits
2. **Agentic workflows**: Our agent needs to call tools and make decisions, which aligns with the Responses API's design
3. **Cost efficiency**: The improved cache utilization reduces operational costs
4. **Future compatibility**: We're aligned with OpenAI's recommended approach for new projects

## References

- [OpenAI Responses API Documentation](https://platform.openai.com/docs/guides/responses-vs-chat-completions)
- [Migrating to Responses API Guide](https://platform.openai.com/docs/guides/migrate-to-responses)
- [GPT-5 Model Documentation](https://platform.openai.com/docs/guides/gpt-5)

## Summary

We use the Responses API because it provides superior performance, lower costs, and better capabilities for GPT-5 models, especially for agentic applications. While it requires slightly more complex response parsing, the benefits far outweigh the implementation complexity, and it positions our codebase for future OpenAI model improvements.

