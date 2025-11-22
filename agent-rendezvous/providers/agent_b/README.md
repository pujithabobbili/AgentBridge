# Agent B: OCR+LLM

High-confidence event extraction using OCR and LLM-like sophisticated parsing.

## Characteristics

- **Cost**: $0.05 per request
- **Latency**: ~2000ms
- **Confidence**: 0.90
- **Tags**: ocr, llm, high-confidence, sophisticated

## Approach

1. Perform OCR on input image/text
2. Apply LLM-like context understanding:
   - Flexible date pattern matching
   - Context-aware location detection
   - Time extraction with validation
3. Return structured event data with high confidence

## Example

**Input:**
```
Global Scoop AI Hackathon

Nov 22–23, 2025 8:30 AM – 5:30 PM

Santa Clara
```

**Output:**
```json
{
  "title": "Global Scoop AI Hackathon",
  "start": "Nov 22, 2025 8:30 AM",
  "end": "Nov 23, 2025 5:30 PM",
  "location": "Santa Clara"
}
```

## Running

```bash
cd providers
./run_agent_b.sh
```

Service runs on http://localhost:7002


