"""Điểm khởi chạy ứng dụng.  Cách dùng:  python main.py [duong_dan_file_json]
Mã thoát: 0 bình thường; 1 Python quá cũ; 2 thiếu Tkinter; 3 lỗi file dữ liệu."""
import os
import sys

from exceptions import FileDuLieuError
from utils import ghi_log

THU_MUC = os.path.dirname(os.path.abspath(__file__))


def main(argv):
    if sys.version_info < (3, 8):
        print("Cần Python 3.8 trở lên.", file=sys.stderr)
        return 1
    try:
        from gui import UngDung
    except ImportError as loi:
        print(f"Thiếu Tkinter: {loi}", file=sys.stderr)
        return 2
    duong_dan = argv[1] if len(argv) > 1 else os.path.join(THU_MUC, "data", "trung_tam.json")
    try:
        app = UngDung(duong_dan)
    except FileDuLieuError as loi:
        ghi_log("KHOI_DONG", str(loi))
        print(f"Không mở được dữ liệu: {loi}", file=sys.stderr)
        return 3
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
