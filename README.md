# Hệ thống Tạo Tín hiệu Màu LED (LED Color Signal Generator)

Đây là ứng dụng mô phỏng và điều khiển dải đèn LED, cho phép tạo các hiệu ứng ánh sáng phức tạp với khả năng tùy chỉnh cao.

## Tính năng chính

- **Mô phỏng dải đèn LED** với hỗ trợ nhiều hiệu ứng khác nhau
- **Giao diện responsive** với khả năng ẩn hiện bảng điều khiển giống macOS Dock
- **Hỗ trợ hiệu ứng Dock** với animation thu phóng khi di chuyển chuột
- **Điều khiển qua OSC** (Open Sound Control)
- **Chế độ ẩn hiện tự động** các bảng điều khiển
- **Hỗ trợ nhiều đoạn ánh sáng** trên cùng một dải đèn LED
- **Hiệu ứng fade-in/fade-out** với thời gian tùy chỉnh
- **Hiệu ứng phản xạ cạnh** hoặc quấn vòng

## Cài đặt

1. Clone repository:
```bash
git clone https://github.com/coderfake/color_signal_system.git
cd color_signal_system
```

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

3. Chạy ứng dụng:
```bash
python main.py
```

## Hướng dẫn sử dụng

### Giao diện

- **Bảng điều khiển trên**: Chứa các điều khiển toàn cục (phát/tạm dừng, FPS, chọn hiệu ứng)
- **Bảng điều khiển phải**: Chứa các điều khiển chi tiết (màu sắc, vị trí, kích thước, tốc độ)
- **Khu vực trung tâm**: Hiển thị mô phỏng dải đèn LED

### Các tính năng đặc biệt

- **Thu phóng**: Sử dụng con lăn chuột hoặc nút +/- trên bảng điều khiển
- **Di chuyển**: Kéo và thả để di chuyển vùng hiển thị
- **Ẩn/hiện bảng điều khiển**: 
  - Di chuyển chuột tới viền để hiện bảng điều khiển
  - Hoặc nhấp vào nút mũi tên ở viền
  - Bảng điều khiển tự động ẩn sau một khoảng thời gian không có tương tác

### Tùy chỉnh đoạn ánh sáng (Segment)

1. Chọn Effect ID và Segment ID từ bảng điều khiển
2. Tùy chỉnh các thuộc tính:
   - **Colors**: Màu sắc các điểm (chọn từ bảng màu)
   - **Move Speed**: Tốc độ di chuyển (dương: phải, âm: trái)
   - **Position**: Vị trí trên dải đèn
   - **Range**: Phạm vi di chuyển
   - **Edge Reflection**: Phản xạ tại cạnh hoặc quấn vòng
   - **Dimmer Time**: Thời gian và chuyển tiếp fade in/out

## Giao thức OSC

Ứng dụng hỗ trợ giao thức OSC để điều khiển từ xa với các định dạng tin nhắn sau:

- `/effect/{effect_ID}/segment/{segment_ID}/{param_name} {value}`
- `/palette/{palette_ID} {colors}`
- `/request/init request`

## Cấu trúc mã nguồn

- `main.py`: Điểm vào chính của ứng dụng
- `config.py`: Cấu hình và hằng số hệ thống
- `models/`: Chứa các lớp mô hình dữ liệu
- `controllers/`: Chứa các lớp xử lý điều khiển
- `ui/`: Chứa giao diện người dùng
- `utils/`: Chứa các tiện ích

## Yêu cầu hệ thống

- Python 3.7+
- pygame
- pygame_gui
- python-osc
- numpy

## Phát triển

### Thêm hiệu ứng mới

1. Tạo một lớp con kế thừa từ `LightEffect`
2. Triển khai phương thức `update_all()` và `get_led_output()`
3. Đăng ký hiệu ứng trong `main.py`

### Tùy chỉnh giao diện

Giao diện sử dụng `pygame_gui` và có thể tùy chỉnh qua:
- File theme.json
- Các hằng số giao diện trong config.py

## Giấy phép

Ứng dụng này được phát hành dưới giấy phép MIT.