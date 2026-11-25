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

### Exercise 3.1: Railway deployment
- URL: https://your-app.railway.app
- Screenshot: [Link to screenshot in repo]

## Part 4: API Security

### Exercise 4.1-4.3: Test results
[Paste your test outputs]

### Exercise 4.4: Cost guard implementation
[Explain your approach]

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
[Your explanations and test results]

## AI log

- Exercise 1.3 — Yêu cầu AI đối chiếu hai bản `app.py` và điền bảng so sánh. Phần tự kiểm tra của học viên: hiểu được các anti patterns và tại sao dùng nó
