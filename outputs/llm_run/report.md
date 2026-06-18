# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_golden.json
- Mode: llm
- Records: 40
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.95 | 1.0 | 0.05 |
| Avg attempts | 1 | 1.05 | 0.05 |
| Avg token estimate | 1094.75 | 1188.85 | 94.1 |
| Avg latency (ms) | 4741.1 | 4652.25 | -88.85 |

## Ước tính chi phí (token & thời gian)

| Metric | ReAct | Reflexion |
|---|---:|---:|
| Records (câu) | 20 | 20 |
| Total tokens | 21,895 | 23,777 |
| Token / câu — min | 913 | 920 |
| Token / câu — max | 1,970 | 3,477 |
| Token / câu — avg | 1,094.8 | 1,188.8 |
| Total time (s) | 94.8 | 93.0 |
| Latency / câu — min (ms) | 3,141 | 2,915 |
| Latency / câu — max (ms) | 12,180 | 15,358 |
| Latency / câu — avg (ms) | 4,741.1 | 4,652.2 |

**Tổng toàn benchmark:** 45,672 tokens, 187.9 s (~3.1 phút) cho 40 lượt chạy.

## Failure modes
```json
{
  "none": {
    "react": 19,
    "total": 39,
    "reflexion": 20
  },
  "wrong_final_answer": {
    "react": 1,
    "total": 1
  }
}
```

## Câu Reflexion cứu được (ReAct sai → Reflexion đúng) — 1 câu

| qid | Question | ReAct answer | Reflexion answer | Gold |
|---|---|---|---|---|
| gold2 | What genre of music is the composer of Swan Lake most known for? | Romantic period | classical | classical |

## So sánh chi tiết ReAct vs Reflexion (từng câu)

| qid | Question | ReAct ans | RA | Reflexion ans | Rx | Rx att. | Gold | Result |
|---|---|---|:--:|---|:--:|:--:|---|---|
| gold2 | What genre of music is the composer of Swan Lake most known… | Romantic period | ✗ | classical | ✓ | 2 | classical | ✅ saved by Reflexion |
| gold1 | What is the capital of the country where the Great Wall was… | Beijing | ✓ | Beijing | ✓ | 1 | Beijing | both correct |
| gold3 | What currency is used in the country where Machu Picchu is … | Peruvian sol | ✓ | Peruvian sol | ✓ | 1 | Peruvian sol | both correct |
| gold4 | In which body of water does the longest river in Africa emp… | Mediterranean Sea | ✓ | Mediterranean Sea | ✓ | 1 | Mediterranean Sea | both correct |
| gold5 | What programming language was used to originally write the … | C | ✓ | C | ✓ | 1 | C | both correct |
| gold6 | What is the official language of the country that borders F… | Dutch, French, and German | ✓ | Dutch, French, and German | ✓ | 1 | Dutch, French, and German | both correct |
| gold7 | What award did the director of the 1994 film that is set in… | None | ✓ | none | ✓ | 1 | no Academy Award win | both correct |
| gold8 | What planet is the NASA rover Curiosity currently exploring? | Mars | ✓ | Mars | ✓ | 1 | Mars | both correct |
| gold9 | What is the highest mountain in the country where the Colos… | Mont Blanc | ✓ | Mont Blanc | ✓ | 1 | Mont Blanc | both correct |
| gold10 | Which element did the scientist who developed the theory of… | uranium | ✓ | uranium | ✓ | 1 | uranium | both correct |
| gold11 | What ocean does the Amazon River flow into? | Atlantic Ocean | ✓ | Atlantic Ocean | ✓ | 1 | Atlantic Ocean | both correct |
| gold12 | What type of government does the country where the Taj Maha… | federal parliamentary dem… | ✓ | federal parliamentary dem… | ✓ | 1 | federal parliamentary dem… | both correct |
| gold13 | What is the population of the city where the headquarters o… | 66,000 | ✓ | 66,000 | ✓ | 1 | approximately 66000 | both correct |
| gold14 | What strait separates the continent where Mount Kilimanjaro… | Bab-el-Mandeb | ✓ | Bab-el-Mandeb | ✓ | 1 | Bab-el-Mandeb | both correct |
| gold15 | Who was the first person to set foot on the celestial body … | Neil Armstrong | ✓ | Neil Armstrong | ✓ | 1 | Neil Armstrong | both correct |
| gold16 | What sport is the club that plays at Camp Nou known for? | football | ✓ | football | ✓ | 1 | football | both correct |
| gold17 | What is the deepest point in the ocean that borders Japan t… | Challenger Deep | ✓ | Challenger Deep | ✓ | 1 | Challenger Deep | both correct |
| gold18 | What nationality was the architect who designed the museum … | Canadian-American | ✓ | Canadian-American | ✓ | 1 | Canadian-American | both correct |
| gold19 | What continent is the country where the pyramids of Giza ar… | Africa | ✓ | Africa | ✓ | 1 | Africa | both correct |
| gold20 | In what year was the treaty signed that ended the war in wh… | 1951 | ✓ | 1951 | ✓ | 1 | 1951 | both correct |

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
Benchmark on hotpot_golden.json (40 records). ReAct EM=0.95 vs Reflexion EM=1.0 (delta +0.050). Reflexion averaged 1.05 attempts vs 1 for ReAct, spending +94 tokens and -89 ms per question. Reflexion improved exact-match by +0.050 over ReAct by re-attempting questions that failed on the first hop, confirming that verbal self-reflection can recover multi-hop errors. Observed failure modes: wrong_final_answer (n=1). The cost/quality tradeoff means Reflexion is worth it only when first-attempt error rate is high enough to offset the extra actor+evaluator+reflector calls each retry adds.
