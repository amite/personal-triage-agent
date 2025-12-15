# JSON Parsing Refactoring - LLMTriageAgent

## Problem Statement

The original `llm_triage_agent.py` had **over 150 lines of complex, unmaintainable JSON parsing logic** (lines 116-275 in the original) that attempted to handle malformed LLM responses through multiple fallback strategies:

1. **Brace counting algorithm** - to find balanced JSON objects
2. **Regex pattern matching** - to extract JSON by pattern
3. **Direct parsing attempts** - to parse full response as JSON
4. **JSON repair function** - to fix common syntax errors (missing commas, quotes, etc.)

### Issues with This Approach

- **Unmaintainable**: Multiple overlapping strategies with duplicated logic
- **Fragile**: Regex patterns were complex and easy to break
- **Inefficient**: Tried multiple approaches sequentially instead of being direct
- **Reactive**: Tried to fix broken JSON instead of preventing the issue

## Solution: Pydantic Structured Output

Using Pydantic models for validation provides:

1. **Direct validation** - Pydantic handles JSON parsing and validation in one step
2. **Type safety** - Clear schema definition with validation rules
3. **Simple fallback** - One lightweight extraction method for edge cases
4. **Maintainability** - Self-documenting schema, fewer lines of code

## Implementation Details

### New Models

```python
class TaskItem(BaseModel):
    """Structured task item from LLM"""
    tool: str = Field(description="Tool name: reminder_tool, drafting_tool, or search_tool")
    content: str = Field(description="Task content or description")

class TaskResponse(BaseModel):
    """Structured task response from LLM"""
    tasks: List[TaskItem] = Field(description="List of identified tasks")
    reasoning: str = Field(description="Reasoning for identified tasks")
```

### Simplified `parse_request_with_llm()` Method

**Old approach**: ~120 lines of complex parsing logic
**New approach**: ~20 lines of clean, direct logic

```python
# Direct Pydantic validation
try:
    parsed = TaskResponse.model_validate_json(response)
    tasks = [{"tool": task.tool, "content": task.content} for task in parsed.tasks]
    logger.info(f"Successfully parsed {len(tasks)} tasks")
    return tasks, parsed.reasoning
except Exception as e:
    logger.warning(f"Pydantic parsing failed: {e}, attempting fallback extraction")
    return self._fallback_extract_json(response, request)
```

### Lightweight Fallback: `_fallback_extract_json()`

Replaces the old `_attempt_json_repair()` method with a simpler approach:
- Uses **simple brace counting** to locate JSON object boundaries
- Applies **Pydantic validation** to extracted JSON
- Falls back to **rule-based parsing** if all else fails

**Key improvement**: Only one extraction method instead of three different strategies.

## Code Reduction

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total Lines | 367 | 277 | -90 lines (-24%) |
| JSON Parsing Logic | ~150 | ~35 | -115 lines (-77%) |
| Methods | 4 | 3 | -1 method |
| Fallback Approaches | 3 | 1 | -2 approaches |

## Benefits

### Maintainability
- Self-documenting schema makes intent clear
- Fewer edge cases to handle
- Easier to debug when issues occur
- Reduced cognitive load when reading code

### Robustness
- Pydantic validates structure automatically
- Clear error messages when parsing fails
- Type safety prevents runtime errors

### Performance
- Direct validation instead of sequential attempts
- No regex compilation for pattern matching
- Cleaner call stack

## Migration Notes

### No Breaking Changes
The refactoring is **fully backward compatible**:
- Same method signature: `parse_request_with_llm(request: str) -> ParseResult`
- Same return type: `Tuple[List[Dict[str, str]], str]`
- Same behavior with Ollama and GPT clients

### Pydantic Dependency
- **Pydantic is already a dependency** (used elsewhere in the project)
- No new dependencies added

### Testing Recommendations

1. **Test with well-formed LLM responses**
   - Verify Pydantic parsing works correctly
   - Confirm task extraction matches original behavior

2. **Test with malformed responses**
   - Missing JSON object
   - Incomplete JSON
   - JSON with trailing content

3. **Test with both LLM providers**
   - Ollama responses
   - GPT-5-Mini responses

## Future Improvements

1. **Consider OpenAI Structured Output API** for GPT-5-Mini
   - GPT-5-Mini supports structured output via `response_format`
   - Could eliminate fallback extraction entirely for GPT

2. **Stricter Prompting**
   - More explicit prompt instructions
   - Example outputs in prompt
   - Temperature control (already at 0.3)

3. **Schema Validation in Prompts**
   - Include JSON schema in prompt
   - Helps LLM understand exact format required

## References

- [Pydantic v2 Documentation](https://docs.pydantic.dev/)
- [GPT-5 Structured Output (OpenAI Docs)](https://platform.openai.com/docs/guides/structured-outputs)
- [Original Documentation](../docs/)
