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
1. Base image: [Your answer]
2. Working directory: [Your answer]
...

### Exercise 2.3: Image size comparison
- Develop: [X] MB
- Production: [Y] MB
- Difference: [Z]%

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

- Exercise 1.3 — Yêu cầu AI đối chiếu hai bản `app.py` và điền bảng so sánh. Phần tự kiểm tra của học viên: chưa ghi nhận.
