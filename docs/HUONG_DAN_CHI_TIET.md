# Hướng dẫn chi tiết — Lab 16: Reflexion Agent

Tài liệu này giải thích **chi tiết và cụ thể** từng phần của lab: kiến trúc, luồng dữ liệu, từng file mã nguồn, các phần `TODO` cần hoàn thiện, cách chạy, cách chấm điểm, và cách mở rộng. Đọc cùng với [README.md](../README.md).

---

## 1. Mục tiêu học tập

Sau khi hoàn thành lab, bạn sẽ:

1. Hiểu sự khác nhau giữa **ReAct Agent** (1 lần thử) và **Reflexion Agent** (nhiều lần thử + tự phản chiếu).
2. Triển khai vòng lặp **self-reflection**: khi trả lời sai, agent tự phân tích lỗi và rút ra chiến thuật mới cho lần thử tiếp theo.
3. Thay thế **mock runtime** (giả lập deterministic) bằng **LLM thật**.
4. Chạy **benchmark** so sánh hai agent trên cùng một bộ dữ liệu multi-hop QA.
5. Đo lường thực tế: **token, latency, exact-match (EM)**, và phân tích **failure modes**.

---

## 2. Reflexion Agent là gì?

Reflexion là kiến trúc agent dựa trên bài báo *"Reflexion: Language Agents with Verbal Reinforcement Learning"* (Shinn et al., 2023). Ý tưởng cốt lõi:

> Thay vì cập nhật trọng số mô hình (RL truyền thống), agent học bằng cách **viết ra phản chiếu bằng ngôn ngữ tự nhiên** sau mỗi lần thất bại, rồi đưa phản chiếu đó vào ngữ cảnh của lần thử tiếp theo.

Ba vai trò (3 "actor" trong hệ thống):

| Vai trò | Nhiệm vụ | Hàm trong code |
|---|---|---|
| **Actor** | Đọc câu hỏi + context (+ reflection memory) → sinh câu trả lời | `actor_answer()` |
| **Evaluator** (Judge) | Chấm câu trả lời đúng/sai (score 0/1) + giải thích lý do | `evaluator()` |
| **Reflector** | Khi sai: phân tích nguyên nhân → rút bài học → đề xuất chiến thuật mới | `reflector()` |

Vòng lặp:

```
attempt 1 → Actor trả lời → Evaluator chấm
   └─ đúng?  → dừng, trả về kết quả
   └─ sai?   → Reflector phân tích → ghi vào reflection_memory
attempt 2 → Actor trả lời (CÓ reflection_memory) → Evaluator chấm
   └─ ... lặp đến khi đúng hoặc hết max_attempts
```

**ReAct Agent** trong lab này là trường hợp đặc biệt: `max_attempts = 1`, không có reflection → dùng làm **baseline** để so sánh.

---

## 3. Kiến trúc & luồng dữ liệu

```
                    data/*.json  (danh sách QAExample)
                          │
                          ▼
                  run_benchmark.py
                          │  load_dataset()
          ┌───────────────┴───────────────┐
          ▼                               ▼
     ReActAgent                      ReflexionAgent
   (max_attempts=1)                (max_attempts=3)
          │                               │
          │   BaseAgent.run(example)      │
          ▼                               ▼
   ┌──────────────────────────────────────────┐
   │  for attempt in 1..max_attempts:         │
   │    answer = actor_answer(...)            │  ← mock_runtime / LLM
   │    judge  = evaluator(...)               │  ← mock_runtime / LLM
   │    if judge.score == 1: break            │
   │    reflection = reflector(...)           │  ← mock_runtime / LLM  (TODO)
   │    reflection_memory.append(...)         │  (TODO)
   └──────────────────────────────────────────┘
          │
          ▼
     RunRecord (mỗi example → 1 record / agent)
          │
          ▼
   reporting.py: build_report() → summarize() + failure_breakdown()
          │
          ├─► outputs/<run>/react_runs.jsonl
          ├─► outputs/<run>/reflexion_runs.jsonl
          ├─► outputs/<run>/report.json   ← autograde.py đọc file này
          └─► outputs/<run>/report.md
                          │
                          ▼
                   autograde.py  → in điểm /100
```

---

## 4. Giải thích từng file mã nguồn

### 4.1 `src/reflexion_lab/schemas.py` — Kiểu dữ liệu (Pydantic)

Định nghĩa toàn bộ cấu trúc dữ liệu. Các model **đã hoàn thiện**:

- **`ContextChunk`**: một đoạn ngữ cảnh `{title, text}`.
- **`QAExample`**: một câu hỏi benchmark — `qid`, `difficulty` (`easy`/`medium`/`hard`), `question`, `gold_answer`, `context: list[ContextChunk]`.
- **`AttemptTrace`**: log của **một lần thử** — `attempt_id`, `answer`, `score`, `reason`, `reflection?`, `token_estimate`, `latency_ms`.
- **`RunRecord`**: kết quả **một example qua một agent** — gồm `predicted_answer`, `is_correct`, `attempts`, tổng `token_estimate`/`latency_ms`, `failure_mode`, danh sách `reflections` và `traces`.
- **`ReportPayload`**: cấu trúc báo cáo cuối — 6 key bắt buộc: `meta`, `summary`, `failure_modes`, `examples`, `extensions`, `discussion`.
- **`ReflexionState`** (TypedDict): state gợi ý nếu bạn muốn triển khai theo kiểu graph/state-machine.

**⚠️ TODO cần hoàn thiện (2 model đang là `pass`):**

```python
class JudgeResult(BaseModel):
    # TODO: định nghĩa score, reason, missing_evidence, spurious_claims, ...
    pass

class ReflectionEntry(BaseModel):
    # TODO: định nghĩa attempt_id, failure_reason, lesson, next_strategy, ...
    pass
```

Để code chạy được, hai model này **phải khớp với cách `mock_runtime.py` đang dùng**:

- `JudgeResult` được khởi tạo với: `score`, `reason`, `missing_evidence`, `spurious_claims` → xem [mock_runtime.py:19-22](../src/reflexion_lab/mock_runtime.py#L19-L22).
- `ReflectionEntry` được khởi tạo với: `attempt_id`, `failure_reason`, `lesson`, `next_strategy` → xem [mock_runtime.py:26](../src/reflexion_lab/mock_runtime.py#L26).

Gợi ý triển khai tối thiểu để mock chạy được:

```python
class JudgeResult(BaseModel):
    score: int                              # 0 hoặc 1
    reason: str
    missing_evidence: list[str] = Field(default_factory=list)
    spurious_claims: list[str] = Field(default_factory=list)

class ReflectionEntry(BaseModel):
    attempt_id: int
    failure_reason: str
    lesson: str
    next_strategy: str
```

> Đoạn trên chỉ là bản tối thiểu. Mục **4.1.1** dưới đây phân tích kỹ các phương án và phương án **đã được triển khai thật** trong scaffold.

#### 4.1.1 Phân tích & đánh giá các phương án triển khai `JudgeResult` / `ReflectionEntry`

Trước tiên cần chốt các **ràng buộc cứng** rút ra từ codebase — phương án nào cũng phải thỏa:

- **Từ `mock_runtime.py`:**
  - `JudgeResult(score=1, reason=...)` khi đúng → **chỉ truyền `score` + `reason`** → `missing_evidence`/`spurious_claims` **bắt buộc có default**, nếu không Pydantic raise lỗi.
  - `JudgeResult(score=0, reason=..., missing_evidence=[...], spurious_claims=[])` khi sai → đủ 4 field.
  - `ReflectionEntry(attempt_id=..., failure_reason=judge.reason, lesson=..., next_strategy=...)` → 4 field, đều được truyền.
- **Từ `agents.py`:** `judge.score` phải so sánh được `== 1` và vào `bool(...)` → kiểu số. `judge.reason` vào `AttemptTrace.reason: str`. `reflection.next_strategy` được append vào `reflection_memory` → là field **then chốt** quyết định attempt sau có cải thiện.
- **Từ `reporting.py`/jsonl:** cả 2 model bị `model_dump_json()` → field phải JSON-serializable (str/int/list[str] đều OK).

**`JudgeResult` — 3 phương án:**

| Tiêu chí | A (tối thiểu) | **B (đã triển khai)** | C (structured đầy đủ) |
|---|---|---|---|
| Khớp mock | ✅ | ✅ | ✅ |
| Parse JSON từ LLM | nhận cả `score=5` | ✅ `Literal[0,1]` chặn rác | LLM dễ trả thiếu field required → vỡ |
| Đúng ngữ nghĩa EM nhị phân | ✅ | ✅ (đúng nhất) | ✅ |
| Hỗ trợ bonus `structured_evaluator` | ❌ | một phần (`confidence`) | ✅ |
| Rủi ro crash khi JSON xấu | Thấp | Thấp | **Cao** (nhiều field required) |

**`ReflectionEntry` — 3 phương án:**

| Tiêu chí | A (tối thiểu) | **B (đã triển khai)** | C (gắn tag failure_mode) |
|---|---|---|---|
| Bảo vệ field then chốt `next_strategy` | ✅ required | ✅ required | ✅ |
| Robust khi LLM thiếu field mô tả | ❌ vỡ nếu thiếu `lesson` | ✅ default `""` | ✅ |
| Hỗ trợ phân tích failure mode | ❌ | ❌ | ✅ (Reflector tự gán mode) |
| Rủi ro / độ phức tạp | Thấp | Thấp | Trung bình |

**Các quyết định thiết kế chính của Phương án B:**

- **`score: Literal[0, 1]` (không phải `int`):** cả pipeline (`is_correct = bool(score)`, EM = `1.0 if is_correct else 0.0`) là **nhị phân** → `Literal[0,1]` phản ánh đúng ngữ nghĩa và **chặn LLM trả `0.7`**. Chỉ chọn `int`/`float` nếu cố tình chấm theo confidence (phải sửa thêm `summarize`).
- **`reason` để required (fail-loud):** thuộc đường đúng/sai và là nguồn cho `ReflectionEntry.failure_reason` → để trống là dấu hiệu parse hỏng, cần báo lỗi sớm.
- **Hai list `missing_evidence`/`spurious_claims` có default** — ràng buộc cứng, không phải lựa chọn.
- **`next_strategy` required, còn `failure_reason`/`lesson` có default `""` (fail-safe):** hai field sau chỉ mang tính mô tả cho report, không ảnh hưởng vòng lặp → cho default để **một lần parse hỏng không làm sập benchmark 100 mẫu**.
- **`extra="ignore"`:** khi sang LLM thật, model trả thừa key sẽ được bỏ qua thay vì vỡ.

**Kết luận:** Phương án B là điểm cân bằng tốt nhất giữa *fail-loud ở đường then chốt* (`score`, `reason`, `next_strategy` → required) và *fail-safe ở field mô tả* (default cho list và `lesson`/`failure_reason`). Nâng lên **C** chỉ khi nhắm bonus `structured_evaluator` hoặc muốn Reflector tự gán `failure_mode`. Tránh **A** cho bản nộp cuối (thiếu validation, dễ nhận rác/crash).

> Dù schema chặt đến đâu cũng không cứu được JSON hỏng → khi nối LLM thật, luôn bọc `model_validate_json()` trong `try/except` với nhánh fallback (vd coi như `score=0`, `next_strategy="retry, suy luận từng hop"`).

### 4.2 `src/reflexion_lab/mock_runtime.py` — Giả lập LLM (deterministic)

Mục đích: cho bạn chạy được toàn bộ pipeline **trước khi tốn tiền API**. Kết quả cố định, dựa trên `qid`.

- **`FIRST_ATTEMPT_WRONG`**: map các câu (`hp2`, `hp4`, `hp6`, `hp8`) sẽ **cố tình trả lời sai ở lần đầu** để demo cơ chế reflection cứu được lỗi.
- **`FAILURE_MODE_BY_QID`**: gán loại lỗi cho từng câu (`incomplete_multi_hop`, `wrong_final_answer`, `entity_drift`).
- **`actor_answer()`**: với câu "dễ" trả về `gold_answer` luôn; với câu trong `FIRST_ATTEMPT_WRONG`:
  - ReAct → luôn sai (vì chỉ 1 attempt).
  - Reflexion → sai ở attempt 1 (khi `reflection_memory` rỗng), **đúng từ attempt 2** (giả lập "đã học được").
- **`evaluator()`**: so khớp `normalize_answer(gold) == normalize_answer(answer)` → score 1; ngược lại score 0 kèm lý do.
- **`reflector()`**: trả về `ReflectionEntry` với chiến thuật gợi ý theo từng câu.

> 3 hàm này được **thay bằng LLM thật** ở Bước B4 (xem `llm_runtime.py`). Lưu ý: interface đã được nâng lên trả về `tuple[result, Usage]` (token/latency thật cho B5) — mock cũng tuân theo để hai backend dùng chung một giao diện.

#### 4.2.1 Phân tích & đánh giá các phương án nối LLM thật (B4)

**Bối cảnh đã chốt:** provider là **OpenAI-compatible endpoint qua gateway ckey.vn**, model `gpt-5.4-mini`, gọi bằng `openai` SDK + `base_url` của ckey.vn, key nạp từ `.env` (`python-dotenv`). Có 4 nhóm quyết định độc lập:

**① Kiến trúc tích hợp**

| | A. Sửa thẳng `mock_runtime.py` | **B. Module `llm_runtime.py` + cờ backend (đã chọn)** | C. Lớp adapter injectable |
|---|---|---|---|
| Công sức | Thấp nhất | Thấp–TB | Cao |
| Giữ mock cho autograde | ❌ mất mock | ✅ (bonus `mock_mode_for_autograding`) | ✅ |
| Chuyển provider sau này | Khó | Dễ | Dễ nhất |
| Rủi ro | Mất khả năng chạy offline | Thấp | Over-engineer cho lab |

→ **Chọn B:** `llm_runtime.py` cùng vai trò, chọn backend qua env `REFLEXION_BACKEND=mock|llm` ([agents.py](../src/reflexion_lab/agents.py#L9-L14)). Giữ mock để autograde chạy không cần API và `report.mode` tự ghi `"mock"`/`"llm"`.

**② Lấy token/latency thật về `agents.py` (mâu thuẫn cốt lõi với B5)**

Số liệu usage nằm trong response **bên trong** 3 hàm, nhưng chúng vốn chỉ trả `str`/`JudgeResult`/`ReflectionEntry`. Ba cách:

| | 2a. Accumulator mức module | **2b. Trả tuple `(result, Usage)` (đã chọn)** | 2c. Client có `.last_usage` |
|---|---|---|---|
| Giữ signature gốc | ✅ | ❌ phải sửa `agents.py` | ✅ |
| Tường minh / sạch | TB (state ẩn) | **Cao nhất** | TB |
| An toàn đa luồng | ❌ global | ✅ | ✅ |

→ **Chọn 2b:** vì B5 vốn đã phải sửa `agents.py`. 3 hàm trả thêm `Usage` (prompt/completion/total tokens + latency_ms). `agents.py` cộng dồn Actor + Evaluator (+ **Reflector**) vào đúng trace của attempt — vá luôn lỗ hổng "chưa tính cost reflector" đã nêu ở mục 4.4.1.

**③ Parse output (khớp prompt đã viết)**

| | 3a. `response_format=json_object` | **3b. Free-text + parse thủ công + fallback (đã chọn)** |
|---|---|---|
| Độ tin cậy JSON | Cao **nếu** gateway hỗ trợ | Luôn chạy được |
| Rủi ro với ckey.vn | Gateway/model mini có thể không hỗ trợ | Phòng thủ sẵn |

→ **Chọn 3b làm nền, bật 3a khi có thể:** `llm_client.chat(json_mode=True)` thử bật `response_format`, nếu gateway từ chối thì **tự hạ cấp** rồi gọi lại. Parse: Actor trích sau `FINAL ANSWER:`; Evaluator/Reflector dùng `model_validate(...)` trong `try/except`, JSON hỏng → fallback (`score=0` / `next_strategy` mặc định) để **không sập benchmark 100 mẫu**.

**④ Vận hành**

- **Số lời gọi:** N câu (2N records) ≈ ReAct `2N` + Reflexion `2..8`/câu → **N=50 ≈ 300–500 call; N=100 ≈ 600–1000 call**. `gpt-5.4-mini` rẻ nên hợp, nhưng cần retry/backoff cho rate-limit gateway.
- **Determinism:** `temperature=0` cho Evaluator + Actor (tái lập benchmark); Reflector để `0.4` cho đa dạng chiến thuật.
- **Config:** thêm `openai` vào [requirements.txt](../requirements.txt); `.env` (xem [.env.example](../.env.example)) chứa `OPENAI_API_KEY`, `OPENAI_BASE_URL` (ckey.vn), `OPENAI_MODEL`, `REFLEXION_BACKEND`.

**Các file thêm/đổi của B4–B5:** [llm_client.py](../src/reflexion_lab/llm_client.py) (client + retry/timeout), [llm_runtime.py](../src/reflexion_lab/llm_runtime.py) (3 hàm + parse fallback), `Usage` trong [schemas.py](../src/reflexion_lab/schemas.py), backend switch + usage thật trong [agents.py](../src/reflexion_lab/agents.py), `mode=BACKEND` trong [run_benchmark.py](../run_benchmark.py).

> ⚠️ Cần xác nhận với ckey.vn: **`OPENAI_BASE_URL` chính xác** và **chuỗi model id** (`gpt-5.4-mini` hay biến thể) — điền vào `.env`. `.env.example` đang để base URL phỏng đoán `https://api.ckey.vn/v1`, hãy đối chiếu tài liệu ckey.vn.

### 4.3 `src/reflexion_lab/prompts.py` — System Prompts (TODO)

Ba prompt đang rỗng, cần viết:

- **`ACTOR_SYSTEM`**: hướng dẫn model đọc context, suy luận multi-hop, và chỉ trả về câu trả lời ngắn gọn. Nếu có reflection memory, phải áp dụng nó.
- **`EVALUATOR_SYSTEM`**: yêu cầu model so sánh `predicted` với `gold_answer` và **trả về JSON** đúng schema `JudgeResult` (`score`, `reason`, ...).
- **`REFLECTOR_SYSTEM`**: yêu cầu model phân tích vì sao sai và đề xuất `next_strategy`, trả về JSON đúng schema `ReflectionEntry`.

Gợi ý: yêu cầu LLM trả về **JSON thuần** để parse bằng `JudgeResult.model_validate_json(...)` / `ReflectionEntry.model_validate_json(...)`.

### 4.4 `src/reflexion_lab/agents.py` — Vòng lặp chính (TODO)

`BaseAgent.run()` chạy vòng lặp attempt. Hai nhóm TODO:

**(a) Logic Reflexion — [agents.py:31-35](../src/reflexion_lab/agents.py#L31-L35):**

Hiện tại scaffold gốc chỉ có `pass`. Nếu **không** triển khai khối này, Reflexion agent sẽ không bao giờ cải thiện — `reflection_memory` luôn rỗng nên `actor_answer()` vẫn trả lời sai mọi attempt. Phân tích chi tiết các phương án ở **mục 4.4.1**; bản **đã triển khai** trong scaffold là **Phương án C**:

```python
if self.agent_type == "reflexion" and attempt_id < self.max_attempts:
    reflection = reflector(example, attempt_id, judge)
    reflections.append(reflection)            # -> RunRecord.reflections (report đếm được)
    trace.reflection = reflection             # -> đính vào trace của attempt sai
    memo = (
        f"[Attempt {attempt_id}] Sai vì: {reflection.failure_reason}. "
        f"Bài học: {reflection.lesson}. Lần sau: {reflection.next_strategy}"
    )
    reflection_memory.append(memo)            # Actor dùng cho attempt kế tiếp
traces.append(trace)
```

#### 4.4.1 Phân tích & đánh giá các phương án triển khai Reflexion loop

**Ràng buộc rút từ codebase** (mọi phương án phải thỏa):

- Khối TODO nằm **sau** `if judge.score == 1: break` và **trước** `traces.append(trace)` → chỉ chạy khi **trả lời sai**, và `trace` của attempt hiện tại chưa lưu nên còn mutate được.
- Chữ ký `reflector(example, attempt_id, judge)` ([mock_runtime.py:24](../src/reflexion_lab/mock_runtime.py#L24)) — **không** nhận `reflection_memory` → mỗi reflection độc lập, không "thấy" reflection trước.
- `actor_answer()` của mock chỉ xét **truthiness** của `reflection_memory` (`not reflection_memory`) → với mock, *append bất cứ gì* cũng đủ cải thiện EM; **nội dung memo chỉ thực sự quan trọng khi dùng LLM thật**.
- `reflection_memory: list[str]` → phần tử là **chuỗi**. `RunRecord.reflections` và `AttemptTrace.reflection` sẽ rỗng/None nếu không chủ động ghi; `reporting.py` dùng `len(r.reflections)` cho `reflection_count`.
- `ReActAgent` có `max_attempts=1` → cần đảm bảo ReAct **không** reflect.

**So sánh các phương án:**

| Tiêu chí | A (tối thiểu) | B (guard + ghi nhận) | **C (đã triển khai)** | D (production/extension) |
|---|---|---|---|---|
| Cải thiện EM trên mock | ✅ | ✅ | ✅ | ✅ |
| Chặn ReAct reflect | một phần¹ | ✅ | ✅ | ✅ |
| Bỏ reflect ở attempt cuối (tiết kiệm cost) | ❌ | ✅ | ✅ | ✅ |
| Ghi `RunRecord.reflections` (report) | ❌ luôn 0 | ✅ | ✅ | ✅ |
| Đính `trace.reflection` | ❌ | ✅ | ✅ | ✅ |
| Chất lượng memo cho **LLM thật** | thấp | trung bình (chỉ `next_strategy`) | **cao** (failure_reason + lesson + strategy) | cao |
| Robust khi reflector lỗi | ❌ | ❌ | ❌ | ✅ (try/except) |
| Hỗ trợ bonus (`memory_compression`/`adaptive`) | ❌ | một phần | một phần | ✅ |
| Độ phức tạp | Thấp | Thấp | Thấp–TB | TB–Cao |

¹ A dựa vào việc ReAct có `max_attempts=1`; nếu ai đó đặt ReAct `max_attempts>1`, A vẫn gọi reflector cho ReAct (sai ngữ nghĩa). B/C/D có guard `attempt_id < max_attempts` nên an toàn hơn nhưng vẫn nên giữ điều kiện `agent_type == "reflexion"` cho rõ ràng.

**Các quyết định thiết kế chính (Phương án C):**

- **Guard `attempt_id < self.max_attempts` (quan trọng nhất):** reflect ở attempt **cuối** tạo ra một `ReflectionEntry` không bao giờ được Actor dùng (vòng lặp kết thúc ngay sau đó). Với mock chỉ phí; với **LLM thật là một lần gọi API lãng phí tiền + latency**. Thông tin "vì sao thất bại lần cuối" đã có trong `judge.reason`/`failure_mode` nên guard là default đúng.
- **`reflections.append(...)` + `trace.reflection = ...`:** không bắt buộc để pipeline *chạy*, nhưng bắt buộc để **report có ý nghĩa** — thiếu thì `examples[].reflection_count` ([reporting.py:26](../src/reflexion_lab/reporting.py#L26)) luôn `0`, làm rỗng phần Analysis và "≥20 examples chi tiết". Trên mock, EM của A và C **giống hệt**; khác biệt chỉ lộ ra ở report.
- **Memo giàu ngữ cảnh (điểm phân biệt của C):** vì `reflector` *không* nhận memory cũ nên mỗi reflection bị cô lập; nhúng thêm `failure_reason` + `lesson` giúp Actor (LLM thật) hiểu *tại sao sai* chứ không chỉ *làm gì tiếp*. Đổi lại tốn thêm token mỗi attempt — chấp nhận được, và là tiền đề cho bonus `memory_compression` khi memo dài.
- **Hạch toán cost của chính lời gọi `reflector` (liên quan TODO (b)):** `token_estimate`/`latency_ms` đang tính **trước** khối reflection nên **chưa gồm chi phí reflector**. Với LLM thật nên cộng usage của reflector vào trace của attempt đã kích hoạt nó, nếu không benchmark sẽ **báo cost của Reflexion thấp hơn thực tế**.

**Kết luận:** Phương án C cân bằng tốt giữa tính đúng (guard cost, report đầy đủ) và chất lượng memo cho LLM thật, độ phức tạp vẫn thấp. Nâng lên **D** (try/except quanh `reflector`, chống lặp memo, cap độ dài memory) khi đã nối LLM thật hoặc nhắm bonus `memory_compression`/`adaptive_max_attempts`. Tránh **A** cho bản nộp (report `reflection_count` luôn 0).

> ⚠️ Quirk của mock: `actor_answer()` trả đúng từ attempt 2 chỉ dựa vào `attempt_id`, **không thực sự cần nội dung `reflection_memory`**. Nên EM "đẹp" trên mock *không* chứng minh loop đúng — hãy xác nhận qua `reflection_count > 0` trong report và kiểm thử thật với LLM.

**(b) Token & latency thật — [agents.py:20-23](../src/reflexion_lab/agents.py#L20-L23):**

Hiện đang **hardcode** theo công thức giả. Khi dùng LLM thật, thay bằng giá trị từ response:

```python
token_estimate = response.usage.total_tokens   # ví dụ với OpenAI-style API
latency_ms = int((t_end - t_start) * 1000)
```

`ReActAgent` = `BaseAgent(agent_type="react", max_attempts=1)`; `ReflexionAgent` = `max_attempts=3` (mặc định).

### 4.5 `src/reflexion_lab/reporting.py` — Tổng hợp báo cáo

- **`summarize()`**: nhóm record theo `agent_type`, tính `em` (exact match), `avg_attempts`, `avg_token_estimate`, `avg_latency_ms`; và **`delta_reflexion_minus_react`** (chênh lệch giữa 2 agent).
- **`failure_breakdown()`**: đếm số lần mỗi `failure_mode` xuất hiện theo agent.
- **`build_report()`**: ghép thành `ReportPayload`. **Lưu ý:** `extensions` và `discussion` đang được **hardcode sẵn** trong hàm này — nếu bạn triển khai extension thật hoặc viết discussion riêng, hãy cập nhật ở đây (hoặc truyền vào).
- **`save_report()`**: ghi `report.json` + `report.md`.

### 4.6 `src/reflexion_lab/utils.py` — Tiện ích

- `normalize_answer()`: lowercase, bỏ ký tự đặc biệt, gộp khoảng trắng → dùng cho so khớp EM.
- `load_dataset()`: đọc JSON → list `QAExample` (validate bằng Pydantic).
- `save_jsonl()`: ghi từng record một dòng JSON.

### 4.7 `run_benchmark.py` — Điểm vào (CLI, dùng Typer)

Chạy cả ReAct và Reflexion trên cùng dataset, lưu jsonl + report. Tham số:

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--dataset` | `data/hotpot_mini.json` | File dữ liệu đầu vào |
| `--out-dir` | `outputs/sample_run` | Thư mục xuất kết quả |
| `--reflexion-attempts` | `3` | Số attempt tối đa của Reflexion |

### 4.8 `autograde.py` — Chấm điểm tự động

Đọc `report.json` và chấm **/100** (chi tiết ở mục 7).

---

## 5. Cài đặt & chạy thử với mock

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Linux/macOS
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Lưu ý:** Phải hoàn thiện `JudgeResult` và `ReflectionEntry` trong `schemas.py` trước, nếu không import sẽ lỗi khi `mock_runtime` khởi tạo các model rỗng.

```bash
# Chạy benchmark (mock)
python run_benchmark.py --dataset data/hotpot_mini.json --out-dir outputs/sample_run

# Chấm điểm
python autograde.py --report-path outputs/sample_run/report.json

# Chạy test
pytest -q
```

Kết quả mong đợi với mock (sau khi hoàn thiện reflexion loop): Reflexion có **EM cao hơn** ReAct trên các câu `hp2/hp4/hp6/hp8`, nhưng `avg_attempts`, token và latency cũng cao hơn.

### 5.1 Chạy với LLM thật (backend = llm)

```bash
# 1) Cài đặt (đã gồm openai)
pip install -r requirements.txt

# 2) Tạo .env từ mẫu rồi điền key/base_url của ckey.vn
cp .env.example .env        # Windows: copy .env.example .env
#   REFLEXION_BACKEND=llm
#   OPENAI_API_KEY=...      (key ckey.vn)
#   OPENAI_BASE_URL=...     (base url ckey.vn, vd https://api.ckey.vn/v1)
#   OPENAI_MODEL=gpt-5.4-mini

# 3) Chạy benchmark thật (report.mode sẽ là "llm", token/latency là số đo thật)
python run_benchmark.py --dataset data/my_test_set.json --out-dir outputs/llm_run
```

- Backend chọn theo env `REFLEXION_BACKEND` ([agents.py](../src/reflexion_lab/agents.py#L9-L14)); để trống/`=mock` → dùng mock (autograde không cần API).
- Khi `=llm`, mỗi attempt gọi Actor + Evaluator (+ Reflector nếu sai và còn attempt). Xem ước lượng số lời gọi ở mục 4.2.1 ④ để liệu chi phí.

---

## 6. Các bước bạn cần làm (checklist)

- [ ] **B1.** Hoàn thiện `JudgeResult` và `ReflectionEntry` trong [schemas.py](../src/reflexion_lab/schemas.py).
- [ ] **B2.** Triển khai logic Reflexion loop trong [agents.py:31-35](../src/reflexion_lab/agents.py#L31-L35).
- [ ] **B3.** Viết 3 system prompt trong [prompts.py](../src/reflexion_lab/prompts.py).
- [x] **B4.** Nối LLM thật qua [llm_runtime.py](../src/reflexion_lab/llm_runtime.py) + [llm_client.py](../src/reflexion_lab/llm_client.py) (OpenAI-compatible/ckey.vn, `gpt-5.4-mini`), chọn bằng `REFLEXION_BACKEND` — xem phân tích mục 4.2.1.
- [x] **B5.** `token_estimate` + `latency_ms` lấy từ `Usage` thật (gồm cả cost của Reflector) trong [agents.py](../src/reflexion_lab/agents.py).
- [ ] **B6.** Tạo dataset ≥ **100 mẫu** và chạy benchmark.
- [ ] **B7.** (Bonus) Triển khai ≥1 extension và cập nhật `extensions`/`discussion` trong [reporting.py](../src/reflexion_lab/reporting.py).

### Cách nối LLM thật (gợi ý)

Giữ signature `actor_answer(example, attempt_id, agent_type, reflection_memory) -> str`, bên trong:

```python
# Ví dụ pseudo-code (áp dụng cho mọi provider: OpenAI/Gemini/Ollama/vLLM)
messages = [
    {"role": "system", "content": ACTOR_SYSTEM},
    {"role": "user", "content": build_user_prompt(example, reflection_memory)},
]
resp = client.chat(messages)          # gọi API
return parse_answer(resp.text)        # trích câu trả lời cuối
```

Tương tự cho `evaluator()` (parse ra `JudgeResult`) và `reflector()` (parse ra `ReflectionEntry`). Dùng `model_validate_json()` để parse JSON LLM trả về; bọc `try/except` để xử lý khi LLM trả JSON hỏng.

---

## 7. Cách tính điểm (autograde.py — /100)

### Core Flow (80đ)

| Hạng mục | Điểm | Điều kiện kiểm tra trong `autograde.py` |
|---|---:|---|
| **Schema completeness** | 30 | Đủ 6 key: `meta`, `summary`, `failure_modes`, `examples`, `extensions`, `discussion`. Điểm = `30 × (số key có / 6)`. |
| **Experiment completeness** | 30 | +10 nếu `summary` có **cả** `react` và `reflexion`; +10 nếu `meta.num_records >= 100`; +10 nếu `len(examples) >= 20`. |
| **Analysis depth** | 20 | +8 nếu `len(failure_modes) >= 3`; +12 nếu `len(discussion) >= 250` ký tự. |

### Bonus (20đ)

`+10` cho mỗi extension được nhận diện (tối đa 20đ). Danh sách hợp lệ trong code:

```
structured_evaluator, reflection_memory, benchmark_report_json,
mock_mode_for_autograding, adaptive_max_attempts, memory_compression,
mini_lats_branching, plan_then_execute
```

> **Lưu ý quan trọng:** Điểm bonus tính dựa trên **danh sách `extensions` ghi trong `report.json`** giao với tập hợp lệ — *không* kiểm tra bạn có thật sự code extension hay không. Phần code thật sẽ được **chấm thủ công** (xem dòng cuối output autograde: *"Manual review required for code quality, actual token logic, and reasoning depth."*). Đừng "ghi khống" extension.

### Để đạt điểm tối đa Core Flow

1. `num_records >= 100` → dataset cần ≥ 50 câu (mỗi câu sinh 2 record: react + reflexion). **Nên dùng ≥ 50 câu** hoặc ≥100 câu cho an toàn.
2. `examples >= 20` → tự nhiên đạt khi num_records ≥ 100.
3. `failure_modes >= 3` → cần ≥3 loại lỗi xuất hiện → dataset phải đa dạng đủ để agent mắc nhiều kiểu lỗi.
4. `discussion >= 250` ký tự → viết phân tích thật, không bỏ trống.

---

## 8. Tạo dữ liệu test (Bước 4 của README)

`data/hotpot_mini.json` chỉ có 8 câu và được "thiết kế riêng" cho mock. Để benchmark thật cần ≥100 record (≥50 câu).

**Format một `QAExample`:**

```json
{
  "qid": "my_q1",
  "difficulty": "medium",
  "question": "Câu hỏi multi-hop...",
  "gold_answer": "Đáp án đúng",
  "context": [
    {"title": "Nguồn 1", "text": "Thông tin liên quan..."},
    {"title": "Nguồn 2", "text": "Thông tin liên quan..."}
  ]
}
```

Nguồn dữ liệu:
- [HotpotQA dataset](https://hotpotqa.github.io/) — chuyển đổi sang format `QAExample`.
- Bản mini có sẵn: https://drive.google.com/file/d/1382R9RhGUFZZpuRsfi8BMKuv3yorOB9H/view?usp=sharing
- Hoặc tự viết câu hỏi multi-hop.

Lưu vào `data/` rồi chạy: `python run_benchmark.py --dataset data/my_test_set.json --out-dir outputs/my_run`.

> Vì có **Golden Test Set** ở cuối buổi (dữ liệu chưa từng thấy), hãy đảm bảo agent hoạt động tốt trên **nhiều loại câu hỏi**, không overfit `hotpot_mini.json`.

---

## 9. Failure modes (loại lỗi multi-hop)

`RunRecord.failure_mode` nhận một trong các giá trị:

| Mode | Ý nghĩa |
|---|---|
| `none` | Trả lời đúng |
| `incomplete_multi_hop` | Dừng lại ở hop đầu, chưa hoàn thành chuỗi suy luận (vd: ra "London" thay vì "River Thames") |
| `entity_drift` | Lệch sang thực thể sai ở hop sau |
| `wrong_final_answer` | Câu trả lời cuối sai |
| `looping` | Lặp vô ích giữa các attempt |
| `reflection_overfit` | Reflection làm agent đi sai hướng (over-correct) |

Phân tích các mode này là phần **Analysis depth** trong rubric.

---

## 10. Bonus Extensions (gợi ý triển khai)

| Extension | Ý tưởng |
|---|---|
| `structured_evaluator` | Evaluator trả JSON có cấu trúc (missing_evidence, spurious_claims) thay vì chỉ 0/1 |
| `reflection_memory` | Lưu & tái sử dụng reflection qua các attempt (cốt lõi của lab) |
| `adaptive_max_attempts` | Dừng sớm/kéo dài attempt tùy độ khó hoặc tín hiệu evaluator |
| `memory_compression` | Nén/tóm tắt reflection memory khi quá dài |
| `mini_lats_branching` | Thử nhiều nhánh câu trả lời (LATS-style) rồi chọn nhánh tốt nhất |
| `plan_then_execute` | Actor lập kế hoạch các hop trước rồi mới trả lời |
| `benchmark_report_json` | Xuất report JSON đầy đủ (đã có sẵn trong scaffold) |
| `mock_mode_for_autograding` | Giữ chế độ mock để autograde chạy không cần API |

Sau khi code, **cập nhật danh sách `extensions`** trong [reporting.py:27](../src/reflexion_lab/reporting.py#L27) để được tính điểm bonus.

---

## 11. Câu hỏi thường gặp (FAQ)

**Q: Import lỗi ngay khi chạy?**
A: Bạn chưa định nghĩa `JudgeResult`/`ReflectionEntry` trong `schemas.py`. `mock_runtime.py` khởi tạo chúng với các field cụ thể — model rỗng (`pass`) sẽ không nhận field và Pydantic báo lỗi.

**Q: Reflexion EM bằng ReAct, không cải thiện gì?**
A: Bạn chưa triển khai logic ở [agents.py:31-35](../src/reflexion_lab/agents.py#L31-L35) — `reflection_memory` vẫn rỗng nên Actor không "học" được.

**Q: `num_records` của tôi chỉ 16?**
A: Vì `hotpot_mini.json` có 8 câu × 2 agent = 16. Cần dataset ≥ 50 câu để đạt ≥100 record.

**Q: Tôi không có API key, chạy được không?**
A: Được — dùng mock runtime (mặc định, mode=`"mock"`). Phần LLM thật là yêu cầu của Bước 3+.

**Q: Token/latency của tôi trông "đẹp" một cách đáng ngờ?**
A: Vì đang hardcode theo công thức trong `agents.py`. Phải thay bằng số đo thật từ response của LLM.

---

## 12. Tham chiếu nhanh các vị trí TODO

| File | Dòng | Việc cần làm |
|---|---|---|
| [schemas.py](../src/reflexion_lab/schemas.py#L16-L22) | 16-22 | Định nghĩa `JudgeResult`, `ReflectionEntry` |
| [agents.py](../src/reflexion_lab/agents.py#L31-L35) | 31-35 | Logic Reflexion loop |
| [agents.py](../src/reflexion_lab/agents.py#L20-L23) | 20-23 | Token & latency thật |
| [prompts.py](../src/reflexion_lab/prompts.py) | 4-14 | 3 system prompt |
| [mock_runtime.py](../src/reflexion_lab/mock_runtime.py) | 8-26 | Thay 3 hàm bằng LLM thật |
| [reporting.py](../src/reflexion_lab/reporting.py#L27) | 27 | Cập nhật `extensions` + `discussion` |
