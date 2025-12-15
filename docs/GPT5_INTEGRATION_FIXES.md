# GPT-5 Integration Fixes and Updates

This document details the comprehensive fixes and improvements made to support OpenAI's GPT-5 models, specifically the cost-effective GPT-5-Mini model.

## Overview

The system was updated to properly support OpenAI's GPT-5 models, which use a different API (Responses API) compared to older models (Chat Completions API). These changes ensure the application works correctly with the latest, most cost-effective LLM models.

## Key Changes Made

### 1. GPT Client Updates (`agents/gpt_client.py`)

#### API Endpoint Selection
- **Added conditional API routing**: The client now automatically detects GPT-5 models and uses the appropriate API
- **GPT-5 models**: Use Responses API (`/v1/responses`)
- **Older models**: Continue using Chat Completions API (`/v1/chat/completions`)

```python
# Automatic API selection based on model
if model.startswith("gpt-5"):
    # Use Responses API for GPT-5 models
    response = requests.post(
        f"{OPENAI_BASE_URL}/responses",
        json={"model": model, "input": prompt, "max_output_tokens": 2000}
    )
else:
    # Use Chat Completions API for older models
    response = requests.post(
        f"{OPENAI_BASE_URL}/chat/completions",
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_completion_tokens": 1000}
    )
```

#### Parameter Updates
- **`max_output_tokens`**: Changed from `max_completion_tokens` for Responses API
- **`input`**: Changed from `messages` for Responses API
- **Removed unsupported parameters**: Temperature parameter is not supported by GPT-5-Mini
- **Increased token limit**: From 1000 to 2000 tokens to handle complete JSON responses

#### Response Parsing
- **Updated response structure handling**: Responses API returns a different JSON format
- **New parsing logic**: Handles the nested `output` → `message` → `content` → `output_text` structure

```python
if model.startswith("gpt-5"):
    # Responses API format parsing
    output_items = response_data.get("output", [])
    for item in output_items:
        if item.get("type") == "message":
            content_items = item.get("content", [])
            for content in content_items:
                if content.get("type") == "output_text":
                    return content.get("text", "").strip()
else:
    # Chat Completions API format parsing
    choices = response_data.get("choices", [])
    if choices and len(choices) > 0:
        return choices[0]["message"]["content"].strip()
```

### 2. Model Configuration Updates

#### Default Model
- **Changed from**: `gpt-4-turbo` (expensive)
- **Changed to**: `gpt-5-mini` (40x more cost-effective)

```python
# Updated default model
DEFAULT_GPT_MODEL = "gpt-5-mini"
```

### 3. JSON Parsing Improvements (`agents/llm_triage_agent.py`)

#### Enhanced JSON Extraction
- **Fixed nested JSON handling**: Previous regex pattern failed on nested objects
- **Added multiple extraction approaches**: More robust JSON finding logic
- **Added JSON repair functionality**: Handles common JSON syntax issues

```python
# Robust JSON extraction with brace counting for nested objects
json_str = None
try:
    brace_count = 0
    start_idx = response.find('{')
    if start_idx != -1:
        for i, char in enumerate(response[start_idx:]):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_str = response[start_idx:start_idx+i+1]
                    break
except Exception:
    pass
```

#### JSON Repair Function
- **Added `_attempt_json_repair()` method**: Fixes common JSON issues
- **Handles missing commas, quotes, and trailing commas**
- **Provides fallback when parsing fails**

### 4. Input Handling Improvements (`main.py`)

#### Example Selection
- **Added numeric input support**: Users can now enter `1`, `2`, or `3` to select examples
- **Updated prompt**: Makes the selection options clearer

```python
# Enhanced input handling
if not user_input:
    user_input = example_requests[0]
    console.print(f"[dim]Using example: {user_input}[/dim]\n")
elif user_input.isdigit():
    example_index = int(user_input) - 1
    if 0 <= example_index < len(example_requests):
        selected_example = example_requests[example_index]
        console.print(f"[dim]Using example {user_input}: {selected_example}[/dim]\n")
        user_input = selected_example
```

### 5. Documentation Updates

#### Updated References
- **Changed "Ollama" to "LLMs (Ollama/GPT)"** in module docstrings and welcome messages
- **Updated class docstrings** to reflect multi-provider architecture

## Cost Optimization

### GPT-5 Model Comparison

| Model | Relative Cost | Speed | Best For |
|-------|--------------|-------|----------|
| GPT-5 (Full) | 40x | Slower | Complex tasks, highest quality |
| GPT-5-Mini | 1x (Baseline) | Faster | Moderate complexity, cost-sensitive |
| GPT-5-Nano | 0.25x | Fastest | Simple tasks, most cost-effective |

**Current Configuration**: Using GPT-5-Mini for optimal balance of cost and capability

## API Differences

### Chat Completions API (Older Models)
```json
{
  "model": "gpt-4-turbo",
  "messages": [{"role": "user", "content": "Hello"}],
  "max_completion_tokens": 1000,
  "temperature": 0.3
}
```

### Responses API (GPT-5 Models)
```json
{
  "model": "gpt-5-mini",
  "input": "Hello",
  "max_output_tokens": 2000
  // No temperature parameter supported
}
```

## Response Format Differences

### Chat Completions Response
```json
{
  "choices": [{
    "message": {
      "content": "Response text"
    }
  }]
}
```

### Responses API Response
```json
{
  "output": [{
    "type": "message",
    "content": [{
      "type": "output_text",
      "text": "Response text"
    }]
  }]
}
```

## Troubleshooting

### Common Issues and Solutions

1. **Empty LLM Responses**
   - **Cause**: Using wrong API endpoint or parameters
   - **Solution**: Ensure GPT-5 models use Responses API with correct parameters

2. **JSON Parsing Errors**
   - **Cause**: Incomplete JSON due to token limits
   - **Solution**: Increase `max_output_tokens` to 2000 or higher

3. **Parameter Errors**
   - **Cause**: Using Chat Completions parameters with Responses API
   - **Solution**: Remove `temperature`, use `max_output_tokens` instead of `max_completion_tokens`

4. **Fallback Parsing**
   - **Cause**: LLM response not in expected format
   - **Solution**: Check API response structure and update parsing logic

## Migration Guide

### For Developers

1. **Update model references**: Change any hardcoded `gpt-4-turbo` to `gpt-5-mini`
2. **Test with both APIs**: Ensure your code handles both response formats
3. **Review token usage**: GPT-5 models may use tokens differently
4. **Update documentation**: Reflect the new multi-provider architecture

### For Users

1. **No changes needed**: The system automatically uses the appropriate API
2. **Cost savings**: Enjoy 40x lower costs with GPT-5-Mini
3. **Better performance**: Faster responses with equivalent quality

## Future Considerations

1. **Model Switching**: Consider adding runtime model selection
2. **Cost Tracking**: Implement token usage monitoring
3. **Performance Benchmarking**: Compare different GPT-5 models
4. **Fallback Strategy**: Enhance fallback mechanisms for API failures

## References

- [OpenAI GPT-5 Documentation](https://platform.openai.com/docs/guides/reasoning)
- [Responses API Reference](https://platform.openai.com/docs/api-reference/responses/create)
- [Model Pricing](https://platform.openai.com/api/pricing/)

## Changelog

### Version 2.1.0 (Current)
- ✅ Added GPT-5 model support
- ✅ Implemented Responses API integration
- ✅ Optimized costs with GPT-5-Mini
- ✅ Enhanced JSON parsing and error handling
- ✅ Improved input handling and user experience

### Version 2.0.0
- ✅ Multi-provider architecture (Ollama/GPT)
- ✅ Initial GPT-4 support
- ✅ Basic error handling

### Version 1.0.0
- ✅ Ollama-only support
- ✅ Basic functionality
