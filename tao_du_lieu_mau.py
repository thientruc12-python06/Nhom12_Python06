"""Sinh dữ liệu mẫu ngẫu nhiên có thể tái lập bằng seed (Buổi 9: random + sys).

Cách dùng:  python tao_du_lieu_mau.py [seed] [so_hoc_vien] [duong_dan_json]
Ví dụ:      python tao_du_lieu_mau.py 2026 24
Mã thoát:   0 thành công, 1 tham số sai, 2 lỗi ghi file.
"""
import os
import random
import sys
from datetime import date, timedelta

from exceptions import FileDuLieuError, TrungTamError
from models import GiaoVien, HocVien, KhoaCoBan, KhoaGiaoTiep, KhoaLuyenThi, LopHoc
from services import TrungTamService
import storage
from utils import chuyen_so

THU_MUC = os.path.dirname(os.path.abspath(__file__))
HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Huỳnh", "Võ", "Đặng", "Bùi", "Phan", "Đỗ"]
DEM = ["Văn", "Thị", "Minh", "Ngọc", "Thanh", "Hoàng", "Quốc", "Gia"]
TEN = ["An", "Bình", "Chi", "Dũng", "Giang", "Hà", "Hùng", "Khoa", "Lan", "Linh",
       "Mai", "Nam", "Phúc", "Quân", "Thảo", "Trang", "Tú", "Vy", "Yến", "Lộc"]


def sinh_ngay_sinh(nam_nho, nam_lon):
    dau = date(nam_nho, 1, 1)
    return dau + timedelta(days=random.randint(0, (date(nam_lon, 12, 28) - dau).days))


def sinh_so_dien_thoai():
    return random.choice(["090", "091", "093", "097", "098"]) + "".join(
        str(random.randint(0, 9)) for _ in range(7))


def tao_du_lieu(so_hoc_vien=24):
    sv = TrungTamService()
    for i, (ten, mon) in enumerate([("Trần Mỹ Linh", "IELTS"), ("Lê Hoàng Nam", "Giao tiếp"),
                                    ("Nguyễn Thu Hà", "TOEIC")], start=1):
        sv.them_giao_vien(GiaoVien(f"GV{i:03d}", ten, sinh_ngay_sinh(1982, 1992),
                                   sinh_so_dien_thoai(), f"gv{i}@trungtam.vn", mon,
                                   random.choice([200000, 250000, 300000])))
    sv.them_khoa(KhoaCoBan("KH001", "Tiếng Anh nền tảng A1", 36, 3600000))
    sv.them_khoa(KhoaCoBan("KH002", "Tiếng Anh sơ cấp A2", 40, 4200000))
    sv.them_khoa(KhoaGiaoTiep("KH003", "Giao tiếp công sở", 30, 3800000, 400000))
    sv.them_khoa(KhoaLuyenThi("KH004", "Luyện thi IELTS 6.5", 48, 5000000, "IELTS", 600000))
    sv.them_khoa(KhoaLuyenThi("KH005", "Luyện thi TOEIC 700+", 40, 4500000, "TOEIC", 450000))
    lop_mau = [("L001", "A1 - Sáng T2/T4", "KH001", "GV002", 8, "Thứ 2, 4 (8:00-10:00)"),
               ("L002", "A2 - Tối T3/T5", "KH002", "GV002", 10, "Thứ 3, 5 (18:30-20:30)"),
               ("L003", "Giao tiếp - Cuối tuần", "KH003", "GV003", 8, "Thứ 7, CN (9:00-11:00)"),
               ("L004", "IELTS 6.5 - Tối T2/T4/T6", "KH004", "GV001", 12, "Thứ 2, 4, 6 (19:00-21:00)"),
               ("L005", "TOEIC 700+ - Tối T3/T5", "KH005", "GV003", 10, "Thứ 3, 5 (18:30-20:30)")]
    hom_nay = date.today()
    for ma, ten, khoa, gv, si_so, lich in lop_mau:
        sv.them_lop(LopHoc(ma, ten, khoa, gv, si_so,
                           hom_nay - timedelta(days=random.randint(30, 90)), lich))
    for i in range(1, so_hoc_vien + 1):
        ten = f"{random.choice(HO)} {random.choice(DEM)} {random.choice(TEN)}"
        sv.them_hoc_vien(HocVien(f"HV{i:03d}", ten, sinh_ngay_sinh(1995, 2010),
                                 sinh_so_dien_thoai(), f"hv{i:03d}@mail.com"))
    ds_hv = list(sv.hoc_vien)
    random.shuffle(ds_hv)
    for ma_hv in ds_hv:
        # mỗi học viên đăng ký 1-2 lớp (lớp đầy sẽ bị bỏ qua)
        for ma_lop in random.sample(list(sv.lop_hoc), k=random.choice([1, 1, 2])):
            try:
                dk = sv.dang_ky_lop(ma_hv, ma_lop, random.choices([0, 5, 10, 20], [6, 2, 2, 1])[0],
                                    hom_nay - timedelta(days=random.randint(5, 40)))
            except TrungTamError:
                continue
            kieu = random.choices(["du", "mot_phan", "chua"], [6, 3, 1])[0]
            if kieu == "du":
                sv.thu_hoc_phi(dk.ma, dk.phai_dong)
            elif kieu == "mot_phan":
                sv.thu_hoc_phi(dk.ma, round(dk.phai_dong * random.choice([0.3, 0.5, 0.7]), -3))
            if random.random() < 0.8:
                sv.nhap_diem(dk.ma, round(random.uniform(3.5, 10), 1), round(random.uniform(3.5, 10), 1))
    return sv


def main(argv):
    try:
        seed = int(argv[1]) if len(argv) > 1 else 2026
        so_hv = int(chuyen_so(argv[2], "Số học viên", int, 5, 200)) if len(argv) > 2 else 24
    except (ValueError, TrungTamError) as loi:
        print(f"Tham số không hợp lệ: {loi}", file=sys.stderr)
        print("Cách dùng: python tao_du_lieu_mau.py [seed] [so_hoc_vien] [duong_dan_json]", file=sys.stderr)
        return 1
    duong_dan = argv[3] if len(argv) > 3 else os.path.join(THU_MUC, "data", "trung_tam.json")
    random.seed(seed)
    sv = tao_du_lieu(so_hv)
    try:
        storage.luu_service(sv, duong_dan)
        storage.xuat_hoc_vien_csv(sv, os.path.join(os.path.dirname(duong_dan), "hoc_vien.csv"))
    except FileDuLieuError as loi:
        print(loi, file=sys.stderr)
        return 2
    print(f"Python {sys.version.split()[0]} ({sys.platform}) | seed={seed}")
    print("Đã tạo:", {k: v for k, v in sv.tong_quan().items()}, "->", duong_dan)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
