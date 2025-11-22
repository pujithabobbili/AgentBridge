# Agent C: Template

Fastest, cheapest event extraction using template-based pattern matching.

## Characteristics

- **Cost**: $0.005 per request
- **Latency**: ~200ms
- **Confidence**: 0.60
- **Tags**: template, fastest, lowest-cost, basic

## Approach

1. Use template matching on input text
2. Extract event fields using simple patterns:
   - Title from first line
   - Date/time from known patterns
   - Location from last lines
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
./run_agent_c.sh
```

Service runs on http://localhost:7003


