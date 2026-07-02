---
name: segment-ugc
description: Use when segmenting a UGC video into individual clips for ad creative mixing. Uses scene detection and semantic boundaries to produce timestamped segments with labels.
user_invocable: true
version: "1.0.0"
tags: [ad-creative, video, ugc]
---

# Segment Ugc

## Usage
```
/segment-ugc <context or file reference>
```

## Workflow
1. **Input**: Receive and parse the input
2. **Process**: Execute core analysis/processing
3. **Output**: Produce structured output

## Output Format
```
## Segment Ugc Results

### Key Findings
- [Finding 1]
- [Finding 2]

### Recommendations
- [Recommendation 1]
```
