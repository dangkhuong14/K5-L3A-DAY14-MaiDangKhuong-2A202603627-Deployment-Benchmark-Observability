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

- [ ] Dashboard Grafana khi đang có tải (thấy rõ Golden Signals)
- [ ] Một trace chậm trong Jaeger (thấy span nào chiếm thời gian)
- [ ] Một trace lỗi trong Jaeger (có event `exception`)
- [ ] Trang Alerts của Prometheus với ít nhất 1 alert đang **firing**

### 4.2 Thí nghiệm "phá hệ thống"

| # | Thay đổi | Alert nào firing | Thời gian từ lúc đổi → firing | Panel nào phản ánh rõ nhất |
|---|---|---|---|---|
| A | `MOCK_ERROR_RATE=0.2` | | | |
| B | `MOCK_SLOW_RATE=0.3` | | | |
| C | `LLM_MODEL=mock-llm-large` | | | |
| D | `docker pause` 1 instance | | | |
| E | `AGENT_VERSION=v1` | | | |

**Thí nghiệm E không làm alert nào firing. Bạn sẽ phát hiện loại sự cố này trong production bằng cách nào?**

...

### 4.3 Debug bằng trace

Chọn 1 trace chậm nhất bạn tìm được:

- `trace_id`: ...
- Tổng thời gian: ... ms
- Span chiếm nhiều thời gian nhất: ... (... ms, ...%)
- Dòng log tương ứng (grep theo `trace_id`):

```json

```

---

## 5. Benchmark scaling (production, Locust headless, 100 users, 2 phút)

| Số instance | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---|---|---|---|---|---|
| 1 | | | | | |
| 3 | | | | | |

**Giải thích kết quả:** Scale có cải thiện p95 không? Nút thắt nằm ở đâu?

...

---

## 6. Kết luận

- 3 điều bạn học được về benchmark & observability:
  1. ...
  2. ...
  3. ...
- Nếu đưa agent này lên production thật, bạn sẽ thêm metric / alert nào nữa?

...
