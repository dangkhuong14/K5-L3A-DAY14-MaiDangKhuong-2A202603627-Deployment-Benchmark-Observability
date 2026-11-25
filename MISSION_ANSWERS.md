# Day 14 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Viết API key trong app.py, nếu push lên git sẽ bị lộ
2. Viết cấu hình, configs trong app.py, không linh hoạt cấu hình.
3. Viết nhãn [DEBUG] rồi dùng print để in log sẽ gây khó kiểm soát khi config tắt chế độ DEBUG.
Khó tìm kiếm các dòng logs. Có thể gây lộ thông tin của người dùng qua câu hỏi và trả lời. Nếu
tải cao có thể gây làm chậm.
4. Không có health check endpoint. Nếu service bị crash sẽ không biết và không tự động restart
5. Harcode port, host, reload khi có thay đổi code. Khi deploy lên production sẽ không kiểm soát được.

### Exercise 1.3: Comparison table
| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
| Config | API key, host và port được viết trực tiếp trong `app.py`. | Đọc cấu hình qua `settings`. Ví dụ, biến môi trường `PORT` quyết định cổng chạy. | Có thể dùng cùng một bản code ở máy cá nhân và trên cloud, đồng thời cấp secret riêng cho từng môi trường. |
| Health check | Chỉ có trang chào ở `/`, thiếu endpoint kiểm tra trạng thái. | `GET /health` báo trạng thái và thời gian chạy. `GET /ready` trả 503 khi `is_ready` là `False`. | Nền tảng có thể kiểm tra ứng dụng còn phản hồi hay không. Bộ cân bằng tải có thể dùng `/ready` để chọn instance sẵn sàng nhận request. |
| Logging | `print()` ghi cả câu hỏi, câu trả lời và API key. | Dùng `logging` với mức DEBUG hoặc INFO theo cấu hình. Handler ghi sự kiện và độ dài câu hỏi, câu trả lời. | Có thể lọc log theo mức độ và theo dõi request mà không để lộ API key hay nội dung hội thoại trong log. |
| Shutdown | App dựa vào cơ chế dừng mặc định của Uvicorn. | Khi dừng, hàm `lifespan` đặt `is_ready = False` và ghi log bắt đầu, kết thúc shutdown. | Có thể theo dõi quá trình dừng và bổ sung việc đóng kết nối hoặc giải phóng tài nguyên trước khi tiến trình thoát. |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11` và `alapine:3.19`.
2. Working directory: `/app`.
3. Copy `requirements.txt` trước để docker dùng lại layer cài thư viện khi chỉ thay đổi mã nguồn.
4. `ENTRYPOINT` chọn chương trình chạy. `CMD` đặt lệnh hoặc đối số mặc định, có thể thay khi gọi `docker run`.

### Exercise 2.2: Build và run

Chạy từ gốc repo:

```bash
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
docker run -d --rm -p 127.0.0.1:56246:8000 my-agent:develop
curl -X POST "http://127.0.0.1:56246/ask?question=What%20is%20Docker%3F"
```

Kết quả: HTTP 200, `{"answer":"Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!"}`. Kích thước image develop: 1154,31 MB.

### Exercise 2.3: Image size comparison
- Develop: 1154,31 MB
- Production: 162,88 MB
- Difference: giảm 85,89%

Stage 1 (`builder`) cài `gcc`, `libpq-dev` và các thư viện Python. Stage 2 (`runtime`) dùng `python:3.11-slim`, chép thư viện Python từ builder và chạy mã nguồn bằng `appuser`. Image cuối nhỏ hơn nhờ base image slim và việc giữ công cụ biên dịch ở stage 1.

### Exercise 2.4: Docker Compose stack

```text
Client → nginx:80 → agent:8000
                       ├── REDIS_URL  → redis:6379
                       └── QDRANT_URL → qdrant:6333
```

Bốn service dùng chung mạng `internal`. Nginx chuyển request đến agent. Redis và Qdrant là hai dịch vụ được cấu hình cho agent. Trong bài này, handler `/ask` gọi mock LLM trực tiếp.

- `GET http://localhost/health` → HTTP 200, trả về `"status":"ok"`.
- `POST http://localhost/ask` với JSON `{"question":"Explain microservices"}` → HTTP 200, trả về `{"answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé."}`.

## Part 3: Cloud Deployment

### Exercise 3.2: Render deployment
- URL: https://lab14-ai20k-agent.onrender.com
- Screenshots: [Dashboard](screenshots/dashboard.png) · [Deployment Live](screenshots/running.png) · [Bốn phép thử HTTP](screenshots/test.png)
- Railway dùng `railway.toml` để chọn Dockerfile và kiểm tra `/health` cho service hiện tại. Render dùng `render.yaml` để mô tả cả web service và Key Value, chọn gói, region và tham chiếu `REDIS_URL` giữa hai dịch vụ.

### Exercise 3.3: Cloud Run CI/CD
1. Cloud Build cài dependencies rồi chạy `pytest tests/`.
2. Docker build image với hai tag `$COMMIT_SHA` và `latest`, sau đó push cả hai lên Container Registry.
3. Bước deploy dùng image theo commit để triển khai `ai-agent` ở `asia-southeast1`.
4. File `service.yaml` mô tả cấu hình Cloud Run tương ứng, gồm giới hạn 1–10 instance, startup probe `/ready`, liveness probe `/health` và tham chiếu Secret Manager.

## Part 4: API Security

### Exercise 4.1-4.3: Test results
Trích output `curl -i` khi gửi `POST /ask` với `{"question":"Hello"}` trong container lab.

```text
4.1 · Develop, thiếu X-API-Key
HTTP/1.1 401 Unauthorized
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

4.1 · Develop, có X-API-Key hợp lệ
HTTP/1.1 200 OK
{"question":"Hello","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."}

4.2 · Production, POST /auth/token bằng tài khoản student
HTTP/1.1 200 OK

4.3 · POST /ask với Bearer token, request đầu tiên
HTTP/1.1 200 OK

4.3 · Cùng token, request thứ 11 trong 60 giây
HTTP/1.1 429 Too Many Requests
x-ratelimit-limit: 10
x-ratelimit-remaining: 0
retry-after: 59
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":59}}
```

### Exercise 4.4: Cost guard implementation
Rate limit giới hạn số request mỗi phút. Cost guard giới hạn chi phí vì mỗi request có thể dùng số token khác nhau. Bản mẫu tính phí theo token đầu vào và đầu ra, lưu trong RAM và trả HTTP 402 khi người dùng đã hết ngân sách 1 USD/ngày.

Với yêu cầu 10 USD/tháng của Exercise 4.4, dùng khóa Redis theo người dùng và tháng. Trước khi gọi LLM, kiểm tra và giữ chỗ chi phí ước tính trong một thao tác nguyên tử để các request đồng thời không cùng tiêu phần ngân sách còn lại. Nếu vượt 10 USD thì trả 402. Sau khi gọi, cập nhật theo chi phí thực tế. Sang tháng mới dùng khóa mới.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes

- **5.1 — Health checks.** Bản develop trả `200 OK` cho cả hai endpoint. `/health` báo `status: ok`, cho biết tiến trình còn phản hồi. `/ready` báo `ready: true`, cho biết agent đã khởi tạo xong và có thể nhận request.
- **5.2 — Graceful shutdown.** Sau khi gửi `SIGTERM`, log lần lượt ghi `Graceful shutdown initiated...`, `Shutdown complete` và `Finished server process`. Lần thử này gửi tín hiệu sau khi hai request đã hoàn tất.
- **5.3 — Stateless.** Agent đọc và ghi lịch sử trong Redis theo khóa `session:<session_id>`. Nhờ có kho dữ liệu chung, instance nhận câu hỏi tiếp theo vẫn đọc được các lượt trao đổi trước.
- **5.4 — Load balancing.** Chạy Compose với `--scale agent=3`. Năm request `POST /chat` qua Nginx ở cổng 8080 lần lượt đến các instance có hậu tố `910638 → 81c888 → 8a495b → 910638 → 81c888`.
- **5.5 — Test stateless.** Với session `9f3d7915-d2d4-45eb-9f85-2bd669dd74c4`, `test_stateless.py` gửi 5 câu hỏi rồi đọc lại đủ 10 tin nhắn theo thứ tự (5 câu hỏi và 5 câu trả lời), dù cả 3 instance đã tham gia xử lý.

## Part 6: Checklist Deliverable

```text
  📋 Checklist Deliverable
     ✅ Dockerfile (multi-stage, < 500 MB)
     ✅ docker-compose.yml (agent + redis)
     ✅ .dockerignore
     ✅ Health check endpoint (GET /health)
     ✅ Readiness endpoint (GET /ready)
     ✅ API Key authentication
     ✅ Rate limiting
     ✅ Cost guard
     ✅ Config từ environment variables
     ✅ Structured logging
     ✅ Graceful shutdown
     ✅ Public URL ready (Railway / Render config)
----------------------------------------------------------------
  Result: 12/12 tiêu chí đạt · 41/41 checks passed
  🎉 PASS 12/12 — PRODUCTION READY! Deploy nào!
================================================================
```

## AI log

- Exercise 1.3 — Yêu cầu AI đối chiếu hai bản `app.py` và điền bảng so sánh. Phần tự kiểm tra của học viên: hiểu được các anti patterns và tại sao dùng nó
- CP3 — AI chạy hai bản API trong Docker, kiểm tra 401/200/429 và giải thích cost guard. Học viên đã tự kiểm tra.
- CP4 — AI chạy thử health, readiness, SIGTERM và script kiểm tra session trên 3 instance, rồi ghi kết quả vào Part 5. Học viên chưa ghi nhận tự kiểm tra.
- CP5 — AI hoàn thiện agent, Docker, Compose và cấu hình Railway, sửa lỗi Compose khi biến API key chưa đặt, rồi chạy bộ chấm đầy đủ trong WSL2 với Docker và đạt 12/12. Học viên đã tự kiểm tra.
- CP6 — AI triển khai agent Part 6 và Key Value trên Render, chạy bốn phép thử public (200/200/401/200) và đối chiếu các file cấu hình. Học viên chưa ghi nhận tự kiểm tra.
- CP8 — AI sửa đường dẫn home của user trong Dockerfile production, chạy Locust và promtool, đối chiếu trace với log, đo hai alert. Học viên phụ trách chụp ảnh minh chứng và báo cáo.
