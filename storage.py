"""Đọc/ghi dữ liệu JSON và CSV (Buổi 8): dùng with, bắt ngoại lệ cụ thể, sao lưu trước khi ghi."""
import csv
import json
import os
import shutil

from exceptions import FileDuLieuError, TrungTamError
from models import HocVien
from services import TrungTamService
from utils import format_date, ghi_log


def doc_json(duong_dan):
    try:
        with open(duong_dan, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileDuLieuError(f"Không tìm thấy file dữ liệu: {duong_dan}") from None
    except json.JSONDecodeError as loi:
        raise FileDuLieuError(f"File JSON sai định dạng ({duong_dan}): {loi}") from loi
    except (OSError, UnicodeDecodeError) as loi:
        raise FileDuLieuError(f"Không đọc được file {duong_dan}: {loi}") from loi


def luu_json(du_lieu, duong_dan):
    """Ghi an toàn: sao lưu file cũ (.bak), ghi file tạm rồi đổi tên để tránh hỏng dữ liệu."""
    tam = duong_dan + ".tmp"
    try:
        thu_muc = os.path.dirname(duong_dan)
        if thu_muc:
            os.makedirs(thu_muc, exist_ok=True)
        if os.path.exists(duong_dan):
            shutil.copy2(duong_dan, duong_dan + ".bak")
        with open(tam, "w", encoding="utf-8") as f:
            json.dump(du_lieu, f, ensure_ascii=False, indent=2)
        os.replace(tam, duong_dan)
    except (OSError, TypeError) as loi:
        raise FileDuLieuError(f"Không ghi được file {duong_dan}: {loi}") from loi


def nap_service(duong_dan):
    """Trả về (service, danh sách cảnh báo). File chưa có -> service rỗng."""
    service = TrungTamService()
    if not os.path.exists(duong_dan):
        return service, []
    du_lieu = doc_json(duong_dan)
    if not isinstance(du_lieu, dict):
        raise FileDuLieuError("Cấu trúc JSON không hợp lệ: phần gốc phải là một đối tượng.")
    return service, service.nap_tu_dict(du_lieu)


def luu_service(service, duong_dan):
    luu_json(service.to_dict(), duong_dan)


def xuat_csv(duong_dan, tieu_de, cac_dong):
    """Xuất CSV dùng utf-8-sig để Excel đọc đúng tiếng Việt."""
    try:
        with open(duong_dan, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(tieu_de)
            writer.writerows(cac_dong)
    except OSError as loi:
        raise FileDuLieuError(f"Không ghi được file {duong_dan}: {loi}") from loi


def xuat_hoc_vien_csv(service, duong_dan):
    xuat_csv(duong_dan, ["ma", "ho_ten", "ngay_sinh", "sdt", "email"],
             [[h.ma, h.ho_ten, format_date(h.ngay_sinh), h.sdt, h.email]
              for h in service.hoc_vien.values()])


def nhap_hoc_vien_csv(service, duong_dan):
    """Nhập học viên từ CSV bằng DictReader. Trả về (số dòng thành công, danh sách lỗi)."""
    thanh_cong, loi_dong = 0, []
    try:
        with open(duong_dan, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            thieu = {"ho_ten", "ngay_sinh", "sdt"} - set(reader.fieldnames or [])
            if thieu:
                raise FileDuLieuError(f"File CSV thiếu cột: {', '.join(sorted(thieu))}")
            for so_dong, dong in enumerate(reader, start=2):
                try:
                    ma = (dong.get("ma") or "").strip() or service.ma_hoc_vien_moi()
                    service.them_hoc_vien(HocVien(ma, dong["ho_ten"], dong["ngay_sinh"],
                                                  dong["sdt"], dong.get("email") or ""))
                    thanh_cong += 1
                except TrungTamError as loi:
                    thong_bao = f"Dòng {so_dong}: {loi}"
                    loi_dong.append(thong_bao)
                    ghi_log("NHAP_CSV", thong_bao)
    except FileNotFoundError:
        raise FileDuLieuError(f"Không tìm thấy file CSV: {duong_dan}") from None
    except (OSError, UnicodeDecodeError, csv.Error) as loi:
        raise FileDuLieuError(f"Không đọc được file CSV: {loi}") from loi
    return thanh_cong, loi_dong
