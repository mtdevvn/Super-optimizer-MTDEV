<div align="center">

<img src="docs/readme/mtdev-banner.gif" width="100%" alt="OPTIMIZE SUPER by MTDEV — banner neon chuyển động: Monitor, Clean, Optimize, Restore." />

# ⚡ OPTIMIZE SUPER | MTDEV

**Theo dõi hiệu năng • Dọn dẹp có kiểm soát • Sao lưu cài đặt • Khôi phục thay đổi**

Một bộ công cụ Windows dành cho PC và laptop, được phát triển bằng **Python + PySide6**.

<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&amp;logo=python&amp;logoColor=white" alt="Python 3.11 trở lên" /></a>
<a href="https://doc.qt.io/qtforpython-6/"><img src="https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge&amp;logo=qt&amp;logoColor=white" alt="Giao diện PySide6" /></a>
<img src="https://img.shields.io/badge/Target-Windows%2010%20%7C%2011%20x64-536DFE?style=for-the-badge" alt="Hệ điều hành mục tiêu Windows 10 và 11 x64" />
<img src="https://img.shields.io/badge/Brand-MTDEV-A78BFA?style=for-the-badge" alt="Phát triển bởi MTDEV" />

<br />

<a href="#cai-dat">🚀 Cài đặt</a> ·
<a href="#tinh-nang">✨ Tính năng</a> ·
<a href="#giao-dien">🖥️ Giao diện</a> ·
<a href="#su-dung">🎮 Sử dụng</a> ·
<a href="#build-exe">📦 Build EXE</a> ·
<a href="https://github.com/mtdevvn/Super-optimizer-MTDEV/issues">💬 Báo lỗi</a>

</div>

---

> **Trạng thái dự án:** mã nguồn ứng dụng đã được triển khai; **19 kiểm thử tự động** đã chạy thành công trên môi trường Linux. Các tích hợp Windows và bản `.exe` cần được kiểm tra trực tiếp trên Windows 10/11 trước khi phát hành. Xem [báo cáo kiểm thử](docs/TEST_REPORT.md) và [checklist Windows](docs/WINDOWS_ACCEPTANCE.md).

<a name="gioi-thieu"></a>
## 💎 Giới thiệu

**OPTIMIZE SUPER | MTDEV** tập hợp những công cụ thường dùng khi kiểm tra và quản lý hiệu năng Windows vào một giao diện dark/light với điểm nhấn xanh neon và tím.

Ứng dụng hiển thị dữ liệu hệ thống thực, cho phép xem trước file sẽ xóa, ghi lại thao tác và lưu trạng thái ban đầu của những cài đặt có hỗ trợ khôi phục. Bạn chọn thao tác, xem giải thích và xác nhận thay đổi.

<div align="center">

**REAL SYSTEM DATA** &nbsp; ✦ &nbsp; **REVIEW BEFORE CLEANUP** &nbsp; ✦ &nbsp; **BACKUP BEFORE CHANGE**

</div>

<a name="tinh-nang"></a>
## ✨ Tính năng

| Công cụ | Bạn có thể làm gì? |
| :--- | :--- |
| 📊 **System Dashboard** | Xem CPU, RAM, dung lượng ổ đĩa, tốc độ mạng, thời gian hoạt động và thông tin phần cứng. |
| ⚡ **Super Optimize** | Chọn riêng từng bước: dọn file tạm, kiểm tra startup/tiến trình, giảm hiệu ứng Windows và thay đổi power plan được hỗ trợ. |
| 🎮 **Gaming Boost** | Mở cài đặt Game Mode, đọc chẩn đoán GPU scheduling, lưu danh sách game và power profile tùy chọn. |
| 🧠 **RAM Management** | Xem ứng dụng dùng nhiều RAM, đóng ứng dụng được chọn sau xác nhận và theo dõi bộ nhớ trước/hiện tại. |
| 🧹 **Storage Cleaner** | Quét file tạm, cache hỗ trợ và Recycle Bin; xem đường dẫn, dung lượng trước khi xóa. |
| 🔎 **File Analysis** | Tìm file từ 100 MB và nhóm file trùng nội dung bằng SHA-256; chỉ phân tích, không tự xóa file cá nhân. |
| 🚀 **Startup Manager** | Xem Run keys/thư mục Startup, tắt mục đã chọn và khôi phục cấu hình đã lưu. |
| ⚙️ **Process Manager** | Tìm tiến trình, sắp xếp CPU/RAM và đóng tiến trình người dùng được phép sau khi xác nhận. |
| 🌐 **Network Tools** | Xem kết nối, đổi IPv4 DNS sang Cloudflare/Google, flush DNS và khôi phục cấu hình trước đó. |
| 🛠️ **Windows Tools** | Mở nhanh Windows Update, Device Manager, Task Manager, Security, Power Options và System Restore. |
| 🛡️ **Restore Center** | Xem nhật ký, hoàn tác thay đổi hỗ trợ, tạo restore point khi Windows cho phép và xuất báo cáo. |
| 🎨 **Personalization** | Dark/light, điều hướng Việt/Anh, hiệu ứng chuyển trang, khay hệ thống và lịch quét dọn dẹp khi ứng dụng đang chạy. |

<details>
<summary><b>📡 Phạm vi hỗ trợ cảm biến và các giới hạn cần biết</b></summary>

- CPU/GPU có thể hiển thị **Unavailable** khi driver hoặc nguồn cảm biến không cung cấp dữ liệu.
- GPU usage/temperature hiện dùng `nvidia-smi` nếu có tại vị trí được hỗ trợ; lấy mẫu GPU NVIDIA đầu tiên. AMD/Intel có thể hiển thị tên GPU nhưng chưa có số liệu tải/nhiệt độ từ bộ đọc này.
- CPU temperature qua psutil thường không khả dụng trên Windows nếu không có nguồn cảm biến phù hợp.
- HAGS được kiểm tra qua thông tin DirectX; kết quả không xác định sẽ hướng dẫn kiểm tra trong Windows Settings.
- Power plan High performance chỉ được áp dụng nếu đã có trên thiết bị. Một số laptop Modern Standby không hỗ trợ plan này.
- Browser cache tùy chọn hiện giới hạn ở disk cache của profile mặc định Chrome/Edge; cần đóng trình duyệt trước khi dọn.
- Startup Manager liệt kê Run keys và Startup folders; không quản lý toàn bộ scheduled tasks, services hoặc packaged startup apps.
- Điều hướng có lựa chọn tiếng Việt/Anh; mô tả kỹ thuật và báo cáo vẫn bằng tiếng Anh.
- Ứng dụng không tạo số FPS, không hứa tăng FPS cố định và không cam kết đổi DNS sẽ giảm ping.

</details>

<a name="giao-dien"></a>
## 🖥️ Giao diện

> Các ảnh dưới đây được chụp từ giao diện chạy trên **máy kiểm thử Linux**, sử dụng dữ liệu thực của máy kiểm thử. Đây là ảnh tham khảo bố cục, không phải bằng chứng đã kiểm thử tích hợp Windows.

<div align="center">

<img src="docs/readme/dashboard-dark.png" width="100%" alt="Dashboard dark mode với các thẻ CPU, GPU, bộ nhớ và mạng trên môi trường kiểm thử Linux." />

**Dark interface · Neon accents · Live monitoring**

</div>

<details>
<summary><b>🌙 Xem Super Optimize và giao diện sáng</b></summary>

### Super Optimize

<img src="docs/readme/optimization-dark.png" width="100%" alt="Trang Super Optimize với các thao tác có thể chọn riêng và khu vực báo cáo." />

### Light Mode — Process Manager

<img src="docs/readme/processes-light.png" width="100%" alt="Process Manager ở chế độ sáng với ô tìm kiếm và bảng tiến trình." />

</details>

<a name="cai-dat"></a>
## 🚀 Cài đặt và chạy

### Cách nhanh: tải ZIP

1. Trên trang GitHub, chọn **Code → Download ZIP** và giải nén.
2. Cài **Python 3.11 bản 64-bit** từ [python.org](https://www.python.org/downloads/windows/), gồm Python Launcher.
3. Mở thư mục chứa `main.py` và nhấp đúp **`launch_windows.bat`**.
4. Đợi cài thư viện lần đầu; giao diện ứng dụng sẽ mở sau khi hoàn tất.

**Lần cài thư viện đầu tiên cần Internet. Các tính năng cốt lõi hoạt động offline sau khi cài xong.**

### Dành cho người dùng Git

```powershell
git clone https://github.com/mtdevvn/Super-optimizer-MTDEV.git
cd Super-optimizer-MTDEV
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

> Các lệnh và script mặc định dùng Python **3.11**. Nếu dùng phiên bản mới hơn, thay `-3.11` bằng phiên bản đã cài.

<a name="su-dung"></a>
## 🎮 Bắt đầu sử dụng

| Bước | Thao tác |
| :---: | :--- |
| **01** | Mở **Dashboard** để xem tình trạng CPU, RAM, mạng và ổ đĩa. |
| **02** | Vào **Storage Cleaner**, chọn vị trí cần dọn và chạy quét. |
| **03** | Đọc đường dẫn/dung lượng, bỏ chọn file muốn giữ rồi xác nhận danh sách cần xóa. |
| **04** | Với **Super Optimize**, chọn từng thao tác phù hợp trước khi chạy. |
| **05** | Kiểm tra kết quả; dùng **Restore Center** để hoàn tác các thay đổi có hỗ trợ. |

**Quyền quản trị:** bắt đầu bằng quyền người dùng thông thường. Nếu thao tác yêu cầu quyền cao hơn, vào **Settings → Restart as administrator**, xác nhận UAC bằng cùng tài khoản rồi thử lại.

<a name="an-toan"></a>
## 🛡️ Kiểm soát và khôi phục

- **Xem trước khi xóa:** chỉ các file phù hợp trong vị trí dọn dẹp được hỗ trợ mới được đề xuất; file mới hơn 48 giờ và file thực thi được loại trừ.
- **Sao lưu trước thay đổi:** lưu trạng thái ban đầu cho registry, power plan, DNS, startup và tùy chọn animation được quản lý.
- **Giữ các chức năng bảo mật:** không cung cấp thao tác tắt Defender, Firewall, Windows Update hoặc dịch vụ thiết yếu.
- **Bảo vệ tiến trình:** chặn tiến trình Windows, service/session-0, tiến trình được bảo vệ và tiến trình thuộc người dùng khác.
- **Báo lỗi rõ ràng:** thao tác bị từ chối hoặc không được hỗ trợ sẽ được báo trong kết quả.
- **Hoàn tác có phạm vi:** Restore Center khôi phục cài đặt đã lưu của ứng dụng; không reset toàn bộ Windows.

> **Xóa file và làm trống Recycle Bin là thao tác không thể hoàn tác bằng ứng dụng.** Đóng tiến trình có thể làm mất công việc chưa lưu. Hãy đọc danh sách và thông báo xác nhận trước khi tiếp tục.

<details>
<summary><b>🗂️ Dữ liệu ứng dụng được lưu ở đâu?</b></summary>

```text
%LOCALAPPDATA%\MTDEV\OptimizeSuper\
```

Thư mục này chứa cấu hình, nhật ký và bản sao lưu. Giữ lại các bản sao lưu để sử dụng tính năng hoàn tác. Nhật ký có thể chứa đường dẫn máy, tên ứng dụng hoặc cấu hình mạng; không đưa dữ liệu riêng này lên kho công khai.

Lịch quét dọn dẹp chỉ hoạt động khi ứng dụng đang chạy và vẫn yêu cầu xem lại danh sách trước khi xóa.

</details>

<a name="build-exe"></a>
## 📦 Đóng gói thành `.exe`

Thực hiện **trên Windows với Python x64**. Nhấp đúp **`build_windows.bat`**, hoặc chạy:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm OptimizeSuper.spec
```

File đầu ra:

```text
dist\OptimizeSuper-MTDEV.exe
```

Bản đóng gói được cấu hình để chứa Python và thư viện cần thiết, giúp máy đích chạy mà không cần cài Python riêng. Hãy kiểm tra bản build trên máy Windows 10/11 sạch trước khi chia sẻ. Kho mã nguồn không đồng nghĩa với việc đã có sẵn một bản `.exe` được kiểm chứng.

<a name="kien-truc"></a>
## 🧩 Công nghệ và tổ chức mã nguồn

| Thành phần | Vai trò |
| :--- | :--- |
| **Python 3.11+** | Ngôn ngữ chính. |
| **PySide6 / Qt** | Giao diện, bảng dữ liệu và chuyển trang. |
| **psutil** | Đọc dữ liệu CPU, RAM, ổ đĩa, mạng và tiến trình. |
| **QThread / QThreadPool** | Đọc số liệu và xử lý tác vụ dài ngoài luồng giao diện. |
| **Windows APIs / PowerShell** | Các thao tác riêng của Windows. |
| **PyInstaller** | Cấu hình đóng gói executable trên Windows. |

| Vị trí | Nội dung |
| :--- | :--- |
| `main.py` | Điểm khởi động ứng dụng. |
| `core/` | Cấu hình, nhật ký, luồng xử lý, monitoring và lệnh Windows. |
| `modules/` | Cleaner, processes, startup, gaming, DNS và restore engine. |
| `ui/` | Các trang giao diện, widget và theme. |
| `assets/` | Logo, icon và thông tin phiên bản. |
| `tests/` | Kiểm thử tự động cho các luồng xử lý và biện pháp bảo vệ. |
| `docs/` | Báo cáo kiểm thử, tài liệu kỹ thuật và hình giao diện. |

<a name="kiem-thu"></a>
## 🧪 Kiểm thử và tài liệu

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

**19 kiểm thử tự động đã chạy thành công trên môi trường phát triển Linux** trong bản mã nguồn ban đầu. Các kiểm thử bao gồm chính sách dọn file, sao lưu trước thay đổi, thứ tự hoàn tác, kiểm soát PID và giao diện offscreen. Đây không phải kết quả CI trực tiếp hay chứng nhận tương thích Windows.

- 📋 [Báo cáo kiểm thử](docs/TEST_REPORT.md)
- 🪟 [Checklist kiểm tra trên Windows 10/11](docs/WINDOWS_ACCEPTANCE.md)
- 📖 [Tài liệu kỹ thuật chi tiết](docs/TECHNICAL_GUIDE.md)

<details>
<summary><b>❓ Ứng dụng chưa mở sau khi chạy file BAT?</b></summary>

Mở CMD tại thư mục chứa `main.py`, rồi chạy:

```bat
call launch_windows.bat
```

Giữ cửa sổ thông báo để đọc lỗi. Kiểm tra Python bằng:

```bat
py -3.11 --version
```

Nếu cần hỗ trợ, gửi phiên bản Windows, phiên bản Python, bước vừa thực hiện và ảnh/thông báo lỗi. Không gửi mật khẩu, token hoặc dữ liệu cá nhân trong log.

</details>

<a name="dong-gop"></a>
## 🤝 Góp ý và phát triển

Bạn có thể [mở issue](https://github.com/mtdevvn/Super-optimizer-MTDEV/issues) để báo lỗi, đề xuất tính năng hoặc gửi ảnh lỗi. Pull request nên mô tả vấn đề, thay đổi và cách kiểm tra; thay đổi cài đặt hệ thống cần có cơ chế sao lưu và khôi phục phù hợp.

Nếu dự án hữu ích, bạn có thể **⭐ Star** để theo dõi.

---

<div align="center">

### ◈ MTDEV

**OPTIMIZE SUPER — Performance, with control.**

Phát triển bởi [**mtdevvn**](https://github.com/mtdevvn) · [Kho mã nguồn](https://github.com/mtdevvn/Super-optimizer-MTDEV) · [Báo lỗi](https://github.com/mtdevvn/Super-optimizer-MTDEV/issues)

<a href="#"><img src="https://img.shields.io/badge/BACK%20TO%20TOP-↑-8B5CF6?style=for-the-badge" alt="Trở về đầu trang" /></a>

</div>
