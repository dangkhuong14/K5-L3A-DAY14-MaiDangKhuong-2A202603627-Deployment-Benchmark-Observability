# Benchmark & Observability Report — Day 14

**Họ tên:** Mai Đăng Khương  
**Ngày chạy:** 25/11/2026  
**Môi trường:** WSL2, Ubuntu 24.04 LTS, Python 3.12.3, 12 CPU logic, 7.7 GiB RAM. Client và agent cùng chạy trên localhost.

## 1. SLO của agent

| SLI | SLO | Lý do chọn ngưỡng này |
|---|---|---|
| p95 latency `/ask` | ≤ 500 ms | Ngưỡng của load test để ít nhất 95% request thành công được phản hồi trong nửa giây. |
| Error rate `/ask` | ≤ 2% | Ngân sách lỗi của load test là 6 trên 300 request. |
| Accuracy trên golden dataset | ≥ 85% trong CI | Chặn phiên bản dưới ngưỡng Exercise 7.3. Riêng nghiệm thu bản sửa KB yêu cầu 100% và 0 regression. |

Exercise 7.1: `/metrics` xuất Counter `http_requests_total`, Gauge `agent_in_flight_requests` và Histogram `agent_question_length_chars`. Sau một câu “Hello”, giá trị `_count` của histogram tăng từ 0 lên 1. Middleware gắn nhãn theo mẫu route và gom URL lạ vào `unmatched` để số chuỗi thời gian không tăng theo từng URL.

## 2. Benchmark hiệu năng (develop, `load_test.py`)

### 2.1 Concurrency vs latency (agent v2)

Mỗi lượt gửi 300 request với `MOCK_SLOW_RATE=0.03`. Các percentile tính trên request HTTP 200.

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO |
|---|---|---|---|---|---|---|
| 1 | 4.21 | 191.7 | 219.4 | 1693.0 | 1.00% | PASS |
| 10 | 43.14 | 189.1 | 220.4 | 1684.4 | 1.33% | PASS |
| 50 | 108.52 | 197.2 | 266.7 | 1689.4 | 0.67% | PASS |
| 100 | 60.10 | 430.1 | 2756.0 | 3097.3 | 1.33% | FAIL |

**Nhận xét:** Tăng concurrency từ 1 lên 10 giúp xử lý song song thời gian chờ mock LLM. Từ 50 lên 100, throughput giảm trong khi p95 tăng hơn 10 lần. Kết quả phù hợp với hiện tượng tranh chấp tài nguyên hoặc xếp hàng; phép đo này chưa xác định được nút thắt cụ thể.

### 2.2 Tail latency

Mỗi lượt khởi động lại v2, giữ 300 request và concurrency 20.

| `MOCK_SLOW_RATE` | avg (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|
| 0 | 191.5 | 219.9 | 231.3 |
| 0.03 | 230.7 | 227.3 | 1688.8 |
| 0.1 | 348.2 | 1686.1 | 1713.7 |

**Nhận xét:** Ở mức 3%, p99 đã vượt 1.6 giây trong khi trung bình chỉ tăng 39.2 ms. Ở mức 10%, cả p95 cũng rơi vào nhóm request chậm. SLO theo percentile thể hiện thời gian chờ của nhóm người dùng mà số trung bình che khuất.

## 3. Benchmark chất lượng (develop, `eval/run_eval.py`)

| Chỉ số | Agent v1 | Agent v2 | Agent v2 (sau khi sửa KB) |
|---|---|---|---|
| Accuracy | 1/23 (4.3%) | 21/23 (91.3%) | 23/23 (100%) |
| Avg tokens / câu | 56.5 | 108.8 | 113.3 |
| Tổng cost (USD, mô phỏng) | 0.000396 | 0.000758 | 0.000787 |
| Cost / câu đúng (USD) | 0.00039555 | 0.00003607 | 0.00003423 |
| Quality gate | FAIL (80%) | PASS (80%, 0 regression) | PASS (100%, 0 regression) |

**Những câu v2 trả lời sai ban đầu và cách sửa**

| ID | Keyword bị thiếu | Thay đổi trong KB |
|---|---|---|
| security-02 | token, hết hạn, chữ ký | Bổ sung cách xác minh chữ ký và thời điểm hết hạn của JWT khi so với API key. |
| scaling-03 | cpu, memory, custom metrics | Bổ sung cách Kubernetes HPA dùng các tín hiệu này để điều chỉnh số pod. |

**Nhận xét:** Retrieval tăng số token và p95 eval từ 189.6 lên 218.3 ms, đồng thời giúp v2 trả lời đúng thêm 20 câu. V2 sau sửa có p95 216.5 ms và tổng cost cao nhất, nhưng cost trên mỗi câu đúng thấp nhất vì cả 23 câu đều đạt.

**CI:** Chạy `python eval/run_eval.py --url http://localhost:8002 --min-accuracy 0.85 --baseline reports/eval_v2.json` trên agent của pull request. Script trả mã 1 khi accuracy dưới 85% hoặc có câu baseline đúng chuyển thành sai. Đặt job này làm required status check để chặn merge khi job thất bại.

---

## 4. Observability stack (production)

### 4.1 Screenshot

- [x] [Dashboard Grafana khi đang có tải](screenshots/grafana-dashboard.png) trong thí nghiệm gây lỗi và tăng độ trễ: 15.5 req/s, lỗi 18%, p95 1.90 s, 8 request đang xử lý và 2 instance.
- [x] [Trace chậm trong Jaeger](screenshots/jaeger-slow-trace.png) cho thấy bước gọi model chiếm gần toàn bộ thời gian.
- [x] [Trace lỗi trong Jaeger](screenshots/jaeger-error-trace.png) hiển thị event `exception` ở span `agent.run` với thông báo upstream LLM trả 503.
- [x] [Trang Alerts của Prometheus](screenshots/prometheus-alert-firing.png) hiển thị `AgentHighErrorRate` và `AgentHighLatencyP95` cùng **firing**.

**Exercise 7.4.** Với 30 user và 2 instance, Prometheus đo được p95 của `/ask` là 291.31 ms và trung bình là 225.55 ms trong cửa sổ 1 phút. Một số request chậm kéo dài thời gian chờ ở đuôi phân bố. Hai instance nhận 9.44 và 9.15 request/s, tương ứng khoảng 51% và 49% tải.

Input đạt 1359.34 token/s, output đạt 721.79 token/s. Agent v2 gửi cả system prompt, câu hỏi và ngữ cảnh truy xuất cho model. Nginx trả HTTP 404 khi gọi `http://localhost:8080/metrics`; Prometheus scrape trực tiếp các instance trên mạng Docker.

### 4.2 Thí nghiệm "phá hệ thống"

| # | Thay đổi | Alert nào firing | Thời gian từ lúc đổi → firing | Panel nào phản ánh rõ nhất |
|---|---|---|---|---|
| A | `MOCK_ERROR_RATE=0.2` | AgentHighErrorRate | 88 s | Error rate |
| B | `MOCK_SLOW_RATE=0.3` (giữ A) | AgentHighLatencyP95 và AgentHighErrorRate cùng firing | 145 s | Latency p95 |
| C | `LLM_MODEL=mock-llm-large` | Chưa chạy | — | — |
| D | `docker pause` 1 instance | Chưa chạy | — | — |
| E | `AGENT_VERSION=v1` | Chưa chạy | — | — |

Hai lượt dùng 30 user, 2 instance. Thời gian tính từ lúc bắt đầu tạo lại agent đến lần đầu đọc được trạng thái firing qua API Prometheus (kiểm tra mỗi 2 giây). Bộ test rule bằng promtool đã đạt.

**Phát hiện suy giảm chất lượng:** Theo dõi phiên bản đang phục vụ, chạy câu hỏi canary có đáp án và so accuracy theo phiên bản. CP7 ghi nhận v1 chỉ đúng 1/23 dù server vẫn trả lời. Gate so với baseline có thể phát hiện hồi quy trước khi chuyển traffic.

### 4.3 Debug bằng trace

Chọn 1 trace chậm nhất bạn tìm được:

- `trace_id`: `71b47b3dd2d9508b26f51b40ffc306ac`
- Tổng thời gian: 1721.56 ms (trace chậm nhất trong mẫu truy vấn).
- Span `agent.run` bao trùm 1719.54 ms. Bên trong, `chat mock-llm-small` chiếm 1693.33 ms, tương đương 98.36% tổng thời gian.
- Dòng log tương ứng (grep theo `trace_id`):

```json
{"ts": "2026-11-25T16:10:50.389740+00:00", "level": "INFO", "service": "observable-agent", "instance": "bba95059fe02", "event": "http_request", "trace_id": "71b47b3dd2d9508b26f51b40ffc306ac", "span_id": "7b13db715aade416", "request_id": "0ffe02191876", "method": "POST", "route": "/ask", "status": 200, "ms": 1720.9}
```

Trace lỗi `7a57a13abc6ba32095eca56f434ea120` có event `exception` trong span gọi model. Log HTTP cùng ID ghi `POST /ask` trả 503.

---

## 5. Benchmark scaling (production, Locust headless, 100 users, 2 phút)

| Số instance | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---|---|---|---|---|---|
| 1 | 60.67 | 210 | 1200 | 2600 | 59/7158 |
| 3 | 66.00 | 190 | 240 | 1700 | 62/7891 |

**Giải thích kết quả:** Scale có cải thiện p95 không? Nút thắt nằm ở đâu?

Theo hàng `Aggregated` trong hai CSV, p95 giảm 80% khi tăng từ 1 lên 3 instance. RPS tăng 8.8% với cùng 100 user; Locust có thời gian nghỉ giữa các request. p99 vẫn ở mức 1.7 giây với 3 instance, phù hợp với tail latency của mock LLM thấy trong trace.

---

## 6. Kết luận

- 3 điều bạn học được về benchmark & observability:
  1. Đọc p95 và p99 cùng RPS để thấy tác động của scaling lên người dùng chờ lâu.
  2. Dùng cùng trace ID để tìm request trong log, rồi đọc span con để xác định bước gây chậm.
  3. Đo từ lúc áp dụng thay đổi đến lúc alert firing vì cửa sổ rate, chu kỳ scrape và thời gian giữ điều kiện đều ảnh hưởng.
- Nếu đưa agent này lên production thật, bạn sẽ thêm metric / alert nào nữa?

Theo dõi tỷ lệ câu hỏi canary trả lời đúng theo phiên bản và cảnh báo khi tỷ lệ này giảm so với baseline.
