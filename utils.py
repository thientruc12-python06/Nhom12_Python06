"""Các hàm tiện ích dùng chung (Buổi 1-2: hàm, tham số mặc định, *args, đệ quy;
Buổi 8: ghi log lỗi; Buổi 9: module sys)."""
import math
import re
import sys
from datetime import date, datetime

from exceptions import DuLieuKhongHopLeError

TEN_TRUNG_TAM = "Trung tâm Ngoại ngữ Sài Gòn"
DATE_FMT = "%d/%m/%Y"
LOG_FILE = "error.log"
NHAN_XEP_LOAI = ("Giỏi", "Khá", "Trung bình", "Yếu", "Chưa có điểm")


def ghi_log(loai, thong_bao, file=LOG_FILE):
    """Ghi nối tiếp một dòng nhật ký lỗi (không làm mất log cũ)."""
    try:
        with open(file, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | {loai} | {thong_bao}\n")
    except OSError as loi:
        print(f"Không ghi được log: {loi}", file=sys.stderr)


def chuan_hoa_ten(chuoi):
    """Xóa khoảng trắng thừa và viết hoa chữ cái đầu mỗi từ."""
    return " ".join(str(chuoi).split()).title()


def parse_date(gia_tri):
    """Chuyển chuỗi dd/mm/yyyy (hoặc date/datetime) thành đối tượng date."""
    if isinstance(gia_tri, datetime):
        return gia_tri.date()
    if isinstance(gia_tri, date):
        return gia_tri
    try:
        return datetime.strptime(str(gia_tri).strip(), DATE_FMT).date()
    except ValueError:
        raise DuLieuKhongHopLeError(
            f"Ngày '{gia_tri}' không hợp lệ (định dạng đúng: dd/mm/yyyy)."
        ) from None


def format_date(ngay):
    return parse_date(ngay).strftime(DATE_FMT)


def kiem_tra_sdt(sdt):
    return re.fullmatch(r"\d{10}", str(sdt)) is not None


def kiem_tra_email(email):
    """Email có thể để trống; nếu có thì phải đúng dạng đơn giản a@b.c."""
    return email == "" or re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


def chuyen_so(gia_tri, ten_truong="Giá trị", kieu=float, toi_thieu=None, toi_da=None):
    """Chuyển giá trị sang số, kiểm tra miền giá trị. Ném DuLieuKhongHopLeError nếu sai."""
    thong_bao_kieu = f"{ten_truong} phải là số{' nguyên' if kieu is int else ''}."
    if isinstance(gia_tri, bool):
        raise DuLieuKhongHopLeError(thong_bao_kieu)
    try:
        if isinstance(gia_tri, str):
            gia_tri = gia_tri.strip().replace(",", "").replace(" ", "")
        so = float(gia_tri)
        if not math.isfinite(so):
            raise ValueError
        if kieu is int:
            if so != int(so):
                raise ValueError
            so = int(so)
    except (ValueError, TypeError):
        raise DuLieuKhongHopLeError(thong_bao_kieu) from None
    if toi_thieu is not None and so < toi_thieu:
        raise DuLieuKhongHopLeError(f"{ten_truong} phải >= {toi_thieu}.")
    if toi_da is not None and so > toi_da:
        raise DuLieuKhongHopLeError(f"{ten_truong} phải <= {toi_da}.")
    return so


def dinh_dang_tien(so_tien):
    return f"{so_tien:,.0f}".replace(",", ".") + " đ"


def tong_de_quy(ds, i=0):
    """Tổng các phần tử của danh sách bằng đệ quy (Buổi 2)."""
    if i >= len(ds):
        return 0
    return ds[i] + tong_de_quy(ds, i + 1)


def tinh_trung_binh(*diem):
    """Trung bình cộng của số lượng điểm không cố định; None nếu không có điểm nào."""
    return sum(diem) / len(diem) if diem else None


def phan_loai_diem(diem):
    """Xếp loại theo điểm tổng kết (thang 10)."""
    if diem is None:
        return "Chưa có điểm"
    if diem >= 8:
        return "Giỏi"
    if diem >= 6.5:
        return "Khá"
    if diem >= 5:
        return "Trung bình"
    return "Yếu"


def ma_tiep_theo(danh_sach_ma, tien_to, do_dai=3):
    """Sinh mã mới dạng HV001, HV002, ... dựa trên mã lớn nhất hiện có."""
    so = [
        int(m[len(tien_to):])
        for m in danh_sach_ma
        if m.startswith(tien_to) and m[len(tien_to):].isdigit()
    ]
    return f"{tien_to}{max(so, default=0) + 1:0{do_dai}d}"
