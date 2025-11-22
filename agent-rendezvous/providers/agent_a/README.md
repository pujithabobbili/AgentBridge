# Agent A: OCR+Regex

Fast, cost-effective event extraction using OCR and regex pattern matching.

## Characteristics

- **Cost**: $0.01 per request
- **Latency**: ~500ms
- **Confidence**: 0.75
- **Tags**: ocr, regex, fast, low-cost

## Approach

1. Perform OCR on input image/text
2. Apply regex patterns to extract:
   - Title (first significant line)
   - Dates (Nov 22–23, 2025 pattern)
   - Times (8:30 AM – 5:30 PM pattern)
   - Location (proper noun detection)
3. Return structured event data

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
./run_agent_a.sh
```

Service runs on http://localhost:7001


