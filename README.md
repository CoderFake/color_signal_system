# Hệ Thống Điều Khiển LED Tape Light

Hệ thống hoàn chỉnh để điều khiển đèn LED dải với các hiệu ứng và hình ảnh động đẹp mắt. Bao gồm cả ứng dụng desktop Python để điều khiển và phần cứng ESP32 để triển khai.

## Tính năng

### Ứng dụng máy tính (Python)

- **Giao diện GUI đẹp mắt**: Giao diện hiện đại, responsive với theme tối
- **Mô phỏng LED theo thời gian thực**: Xem trước hiệu ứng LED trước khi áp dụng vào phần cứng
- **Nhiều hiệu ứng**: Tạo và kết hợp các đoạn ánh sáng khác nhau với nhiều hiệu ứng
- **Thư viện Preset**: Các hiệu ứng sẵn có bao gồm:
  - Rainbow Flow (Dòng cầu vồng)
  - Breathing (Nhịp thở)
  - Police Lights (Đèn cảnh sát)
  - Color Wipe (Quét màu)
  - Pulse (Nhịp đập)
  - Cylon (Hiệu ứng con mắt)
  - Rainbow Cycle (Chu kỳ cầu vồng)
  - Và nhiều hiệu ứng khác!
- **Điều khiển hiệu ứng**: Điều chỉnh các thông số như tốc độ, màu sắc, thời gian, độ trong suốt
- **Giao thức OSC**: Điều khiển phần cứng LED qua mạng bằng OSC
- **Tìm kiếm thiết bị**: Tự động tìm các bộ điều khiển LED trên mạng
- **Lưu/Tải**: Lưu các hiệu ứng tùy chỉnh để sử dụng sau

### Bộ điều khiển phần cứng ESP32

- **Cài đặt WiFi dễ dàng**: Kết nối với mạng WiFi thông qua giao diện web responsive
- **Hỗ trợ đầy đủ hiệu ứng**: Triển khai tất cả các hiệu ứng từ ứng dụng desktop
- **Tương thích WS2812B**: Điều khiển lên đến 100 LED WS2812B
- **Điều khiển qua OSC**: Nhận lệnh từ ứng dụng desktop qua WiFi
- **Nút reset**: Nhấn giữ nút reset để cấu hình lại WiFi
- **Hoạt động độc lập**: Có thể chạy hiệu ứng ngay cả khi không có kết nối với ứng dụng desktop

## Yêu cầu hệ thống

### Ứng dụng desktop

- Python 3.8 hoặc mới hơn
- Các thư viện: tkinter, customtkinter, Pillow, python-osc, zeroconf

### Phần cứng

- ESP32 (ESP32-WROOM hoặc tương đương)
- Dải LED WS2812B
- Nguồn 5V phù hợp với số lượng LED sử dụng

## Hướng dẫn cài đặt

### Cài đặt ứng dụng Python

1. Clone hoặc tải xuống repository:
```bash
git clone https://github.com/coderfake/color-signal-system.git
cd led-tape-control
```

2. Cài đặt các thư viện phụ thuộc:
```bash
pip install -r requirements.txt
```

3. Chạy ứng dụng:
```bash
python main.py
```

### Cài đặt phần cứng ESP32

1. Cài đặt Arduino IDE và cấu hình cho ESP32
   - Tải Arduino IDE từ [arduino.cc](https://www.arduino.cc/en/software)
   - Cài đặt ESP32 boards: vào File > Preferences > Additional Boards Manager URLs và thêm:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Cài đặt ESP32 từ Tools > Board > Boards Manager, tìm "esp32" và cài đặt

2. Cài đặt các thư viện cần thiết:
   - FastLED: Sketch > Include Library > Manage Libraries, tìm "FastLED" và cài đặt
   - ESPAsyncWebServer: tải từ [GitHub](https://github.com/me-no-dev/ESPAsyncWebServer)
   - AsyncTCP: tải từ [GitHub](https://github.com/me-no-dev/AsyncTCP)
   - ArduinoJSON: Sketch > Include Library > Manage Libraries, tìm "ArduinoJSON" và cài đặt
   - ArduinoOSC: Sketch > Include Library > Manage Libraries, tìm "ArduinoOSC" và cài đặt

3. Kết nối phần cứng:
   - Kết nối dải LED WS2812B với ESP32 (mặc định GPIO5)
   - Đảm bảo sử dụng nguồn đủ công suất cho LED
   - Thêm điện trở 330-500 Ohm giữa chân dữ liệu của ESP32 và đầu vào LED

4. Tải mã nguồn lên ESP32:
   - Mở file `esp32_led_controller.ino` trong Arduino IDE
   - Chọn board ESP32 phù hợp từ Tools > Board
   - Chọn cổng COM phù hợp từ Tools > Port
   - Nhấn nút Upload để tải mã nguồn lên ESP32

## Hướng dẫn sử dụng

### Cấu hình ban đầu cho ESP32

Khi khởi động lần đầu tiên, ESP32 sẽ tạo một điểm truy cập WiFi:
1. Kết nối điện thoại hoặc máy tính đến WiFi có tên `LED_Controller_XXXX` (XXXX là 4 ký tự cuối địa chỉ MAC)
2. Mật khẩu mặc định là `12345678`
3. Một trang web cấu hình sẽ tự động mở ra (hoặc hãy mở trình duyệt và truy cập `192.168.4.1`)
4. Quét tìm mạng WiFi, chọn mạng của bạn và nhập mật khẩu
5. ESP32 sẽ khởi động lại và kết nối với mạng WiFi của bạn

### Sử dụng ứng dụng desktop

1. Khởi động ứng dụng Python:
```bash
python main.py
```

2. Kết nối với bộ điều khiển LED:
   - Chọn "Connection" > "Scan Network" để tìm kiếm bộ điều khiển ESP32
   - Chọn "Connection" > "Connect to Device" và chọn thiết bị từ danh sách

3. Sử dụng giao diện để tạo và điều khiển hiệu ứng:
   - Tạo hiệu ứng mới từ menu File > New Effect
   - Thêm segment bằng nút "+" trong phần Segment Controls
   - Áp dụng preset có sẵn bằng cách chọn từ dropdown và nhấn "Apply"
   - Tùy chỉnh thông số trong các tab: Basic, Colors, Timing
   - Kích hoạt chế độ tự động chuyển đổi hiệu ứng bằng cách chọn "Auto-cycle Presets"

4. Lưu và tải cấu hình:
   - File > Save Configuration để lưu cấu hình hiện tại
   - File > Load Configuration để tải cấu hình đã lưu

### Reset ESP32

Nếu bạn cần cấu hình lại WiFi hoặc gặp vấn đề kết nối:
1. Nhấn giữ nút BOOT (GPIO0) trên ESP32 trong 10 giây
2. LED sẽ nhấp nháy màu đỏ, sau đó ESP32 sẽ khởi động lại ở chế độ cấu hình
3. Thực hiện lại các bước cấu hình ban đầu

## Cấu trúc dự án

```
color_signal_system/
│
├── core/                   # Các chức năng cốt lõi
│   ├── light_segment.py    # Quản lý đoạn ánh sáng
│   ├── light_effect.py     # Quản lý nhiều đoạn ánh sáng
│   └── effects_manager.py  # Quản lý hiệu ứng và chuyển đổi
│
├── communication/          # Mô-đun giao tiếp
│   ├── osc_handler.py      # Xử lý OSC
│   └── device_scanner.py   # Quét thiết bị trong mạng
│
├── gui/                    # Giao diện người dùng
│   ├── main_window.py      # Cửa sổ chính
│   ├── led_simulator.py    # Mô phỏng LED
│   ├── effect_preview.py   # Xem trước hiệu ứng
│   ├── theme_manager.py    # Theme tùy chỉnh
│   └── assets/             # Hình ảnh và tài nguyên
│
├── utils/                  # Tiện ích
│   ├── color_utils.py      # Xử lý màu sắc
│   ├── effect_presets.py   # Các hiệu ứng preset
│   ├── auto_cycler.py      # Tự động chuyển hiệu ứng
│   └── config_manager.py   # Quản lý cấu hình
│
├── esp32_led_controller/   # Mã nguồn cho ESP32
│   ├── esp32_led_controller.ino  # File chính
│   ├── config.h            # Cấu hình
│   ├── led_helpers.h       # Xử lý LED
│   └── osc_handlers.h      # Xử lý OSC
│
└── main.py                 # Điểm khởi đầu ứng dụng
```

## Xử lý sự cố

### Ứng dụng Python

- **Không tìm thấy thiết bị trên mạng**:
  - Đảm bảo ESP32 đã kết nối WiFi thành công (đèn LED nhấp nháy xanh lá khi kết nối)
  - Kiểm tra ESP32 và máy tính của bạn kết nối cùng mạng
  - Thử khởi động lại ứng dụng và ESP32

- **Hiệu ứng không được gửi đến ESP32**:
  - Kiểm tra kết nối OSC trong menu Connection > OSC Settings
  - Đảm bảo cổng OSC là 7700 (mặc định)

- **Ứng dụng không khởi động**:
  - Xác nhận tất cả thư viện đã được cài đặt bằng `pip install -r requirements.txt`
  - Kiểm tra file log trong thư mục `logs/error.log`

### ESP32

- **ESP32 không tạo điểm truy cập WiFi**:
  - Kiểm tra nguồn điện có đủ công suất không
  - Thử nhấn nút reset
  - Tải lại mã nguồn

- **LED không hoạt động**:
  - Kiểm tra kết nối vật lý (chân dữ liệu, GND, 5V)
  - Đảm bảo cài đặt đúng GPIO trong `config.h` (mặc định GPIO5)
  - Đảm bảo nguồn điện đủ cho số lượng LED sử dụng

- **Hiệu ứng không mượt mà**:
  - Giảm số lượng LED hoặc độ phức tạp của hiệu ứng
  - Đảm bảo ESP32 không có quá nhiều tác vụ khác đang chạy

## Đóng góp

Đóng góp cho dự án rất được hoan nghênh! Hãy gửi Pull Requests hoặc mở Issues trên GitHub.

## Giấy phép

MIT License - Xem file LICENSE để biết thêm chi tiết.