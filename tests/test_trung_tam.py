import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import storage  # noqa: E402
from exceptions import (DuLieuKhongHopLeError, FileDuLieuError, KhongTimThayError,  # noqa: E402
                        LopDayError, RangBuocError, TrungMaError)
from models import (GiaoVien, HocVien, KhoaCoBan, KhoaGiaoTiep, KhoaHoc,  # noqa: E402
                    KhoaLuyenThi, LopHoc, Person, tao_khoa)
from services import TrungTamService  # noqa: E402
from utils import chuyen_so, ma_tiep_theo, phan_loai_diem, tong_de_quy  # noqa: E402


def tao_service():
    sv = TrungTamService()
    sv.them_giao_vien(GiaoVien("GV001", "trần mỹ linh", "01/01/1990", "0901234567", "", "IELTS", 250000))
    sv.them_khoa(KhoaCoBan("KH001", "Cơ bản A1", 36, 3000000))
    sv.them_khoa(KhoaGiaoTiep("KH002", "Giao tiếp", 30, 3000000, 500000))
    sv.them_khoa(KhoaLuyenThi("KH003", "IELTS", 40, 5000000, "IELTS", 600000))
    sv.them_lop(LopHoc("L001", "Lớp A1", "KH001", "GV001", 2, "01/09/2026", "T2-T4"))
    for i in (1, 2, 3):
        sv.them_hoc_vien(HocVien(f"HV00{i}", f"học viên {i}", "10/10/2005", f"090000000{i}"))
    return sv


class TestDongGoi(unittest.TestCase):
    def test_chuan_hoa_ho_ten(self):
        self.assertEqual(HocVien("HV1", "  nguyễn   văn  an ", "01/01/2000", "0900000000").ho_ten, "Nguyễn Văn An")

    def test_setter_chan_du_lieu_sai(self):
        hv = HocVien("HV1", "An", "01/01/2000", "0900000000")
        for thuoc_tinh, gia_tri in (("ho_ten", "   "), ("sdt", "123"), ("email", "abc"),
                                    ("ngay_sinh", "31/02/2000"), ("ngay_sinh", "01/01/2999")):
            with self.assertRaises(DuLieuKhongHopLeError, msg=thuoc_tinh):
                setattr(hv, thuoc_tinh, gia_tri)
        self.assertEqual(hv.ho_ten, "An")   # giá trị cũ không bị phá hỏng

    def test_thuoc_tinh_private_khong_truy_cap_truc_tiep(self):
        hv = HocVien("HV1", "An", "01/01/2000", "0900000000")
        with self.assertRaises(AttributeError):
            _ = hv.__ho_ten
        self.assertEqual(hv._Person__ho_ten, "An")  # name mangling

    def test_ma_chi_doc(self):
        hv = HocVien("HV1", "An", "01/01/2000", "0900000000")
        with self.assertRaises(AttributeError):
            hv.ma = "HV2"


class TestKeThuaDaHinh(unittest.TestCase):
    def test_lop_truu_tuong_khong_khoi_tao_duoc(self):
        with self.assertRaises(TypeError):
            Person("X", "A", "01/01/2000", "0900000000")
        with self.assertRaises(TypeError):
            KhoaHoc("K", "A", 10, 100)

    def test_hoc_phi_da_hinh(self):
        self.assertEqual(KhoaCoBan("K1", "A", 30, 3000000).tinh_hoc_phi(), 3000000)
        self.assertEqual(KhoaGiaoTiep("K2", "B", 30, 3000000, 500000).tinh_hoc_phi(), 3500000)
        self.assertAlmostEqual(KhoaLuyenThi("K3", "C", 30, 5000000, "IELTS", 600000).tinh_hoc_phi(), 6600000)

    def test_isinstance_issubclass(self):
        k = KhoaLuyenThi("K3", "C", 30, 5000000, "TOEIC", 0)
        self.assertTrue(isinstance(k, KhoaHoc))
        self.assertTrue(issubclass(KhoaGiaoTiep, KhoaHoc))
        self.assertFalse(isinstance(k, KhoaCoBan))

    def test_chung_chi_sai(self):
        with self.assertRaises(DuLieuKhongHopLeError):
            KhoaLuyenThi("K3", "C", 30, 5000000, "ABC", 0)

    def test_tu_dict_chon_dung_lop(self):
        goc = KhoaLuyenThi("K3", "C", 30, 5000000, "TOEIC", 450000)
        moi = KhoaHoc.tu_dict(goc.to_dict())
        self.assertIsInstance(moi, KhoaLuyenThi)
        self.assertEqual(moi.tinh_hoc_phi(), goc.tinh_hoc_phi())
        with self.assertRaises(DuLieuKhongHopLeError):
            KhoaHoc.tu_dict({"loai": "Lạ", "ma": "K", "ten": "x", "so_buoi": 1, "hoc_phi_co_ban": 1})

    def test_tao_khoa_factory(self):
        self.assertIsInstance(tao_khoa("Giao tiếp", "K9", "X", 10, 100, 5), KhoaGiaoTiep)
        with self.assertRaises(DuLieuKhongHopLeError):
            tao_khoa("", "K9", "X", 10, 100)


class TestNghiepVu(unittest.TestCase):
    def setUp(self):
        self.sv = tao_service()

    def test_trung_ma(self):
        with self.assertRaises(TrungMaError):
            self.sv.them_hoc_vien(HocVien("HV001", "Trùng", "01/01/2000", "0900000000"))

    def test_sinh_ma_tu_dong(self):
        self.assertEqual(self.sv.ma_hoc_vien_moi(), "HV004")
        self.assertEqual(ma_tiep_theo([], "KH"), "KH001")

    def test_dang_ky_kiem_tra_si_so(self):
        self.sv.dang_ky_lop("HV001", "L001")
        self.sv.dang_ky_lop("HV002", "L001")
        with self.assertRaises(LopDayError):
            self.sv.dang_ky_lop("HV003", "L001")
        self.assertEqual(self.sv.si_so("L001"), 2)

    def test_dang_ky_trung(self):
        self.sv.dang_ky_lop("HV001", "L001")
        with self.assertRaises(TrungMaError):
            self.sv.dang_ky_lop("HV001", "L001")

    def test_dang_ky_khong_ton_tai(self):
        with self.assertRaises(KhongTimThayError):
            self.sv.dang_ky_lop("HV999", "L001")
        with self.assertRaises(KhongTimThayError):
            self.sv.dang_ky_lop("HV001", "L999")

    def test_hoc_phi_va_cong_no(self):
        dk = self.sv.dang_ky_lop("HV001", "L001", giam_gia=10)
        self.assertEqual(dk.phai_dong, 2700000)
        self.sv.thu_hoc_phi(dk.ma, 1000000)
        self.assertEqual(dk.cong_no, 1700000)
        self.sv.thu_hoc_phi(dk.ma, 1700000)
        self.assertEqual(dk.cong_no, 0)
        self.assertEqual(len(dk.thanh_toan), 2)

    def test_nop_vuot_cong_no_hoac_so_am(self):
        dk = self.sv.dang_ky_lop("HV001", "L001")
        with self.assertRaises(RangBuocError):
            self.sv.thu_hoc_phi(dk.ma, 9999999999)
        with self.assertRaises(DuLieuKhongHopLeError):
            self.sv.thu_hoc_phi(dk.ma, -5)
        with self.assertRaises(DuLieuKhongHopLeError):
            self.sv.thu_hoc_phi(dk.ma, "abc")

    def test_giam_gia_ngoai_mien(self):
        with self.assertRaises(DuLieuKhongHopLeError):
            self.sv.dang_ky_lop("HV001", "L001", giam_gia=120)

    def test_diem_va_xep_loai(self):
        dk = self.sv.dang_ky_lop("HV001", "L001")
        self.assertEqual(dk.xep_loai, "Chưa có điểm")
        self.sv.nhap_diem(dk.ma, 8, 9)          # 0.4*8 + 0.6*9 = 8.6
        self.assertAlmostEqual(dk.diem_tong_ket, 8.6)
        self.assertEqual(dk.xep_loai, "Giỏi")
        with self.assertRaises(DuLieuKhongHopLeError):
            self.sv.nhap_diem(dk.ma, 11, 5)
        self.assertAlmostEqual(dk.diem_tong_ket, 8.6)   # lỗi không làm hỏng điểm cũ

    def test_bien_xep_loai(self):
        for diem, ket_qua in ((8, "Giỏi"), (7.99, "Khá"), (6.5, "Khá"), (6.49, "Trung bình"),
                              (5, "Trung bình"), (4.99, "Yếu"), (0, "Yếu"), (None, "Chưa có điểm")):
            self.assertEqual(phan_loai_diem(diem), ket_qua, diem)

    def test_rang_buoc_xoa(self):
        dk = self.sv.dang_ky_lop("HV001", "L001")
        for ham, ma in ((self.sv.xoa_hoc_vien, "HV001"), (self.sv.xoa_giao_vien, "GV001"),
                        (self.sv.xoa_khoa, "KH001"), (self.sv.xoa_lop, "L001")):
            with self.assertRaises(RangBuocError):
                ham(ma)
        self.sv.huy_dang_ky(dk.ma)
        self.sv.xoa_lop("L001")
        self.sv.xoa_khoa("KH001")
        self.assertNotIn("KH001", self.sv.khoa_hoc)

    def test_khong_huy_khi_da_dong_tien(self):
        dk = self.sv.dang_ky_lop("HV001", "L001")
        self.sv.thu_hoc_phi(dk.ma, 100000)
        with self.assertRaises(RangBuocError):
            self.sv.huy_dang_ky(dk.ma)

    def test_giam_si_so_toi_da_duoi_hien_co(self):
        self.sv.dang_ky_lop("HV001", "L001")
        self.sv.dang_ky_lop("HV002", "L001")
        with self.assertRaises(RangBuocError):
            self.sv.cap_nhat_lop(LopHoc("L001", "Lớp A1", "KH001", "GV001", 1, "01/09/2026"))

    def test_lop_phai_co_khoa_va_giao_vien(self):
        with self.assertRaises(DuLieuKhongHopLeError):
            self.sv.them_lop(LopHoc("L002", "X", "", "GV001", 5, "01/09/2026"))
        with self.assertRaises(KhongTimThayError):
            self.sv.them_lop(LopHoc("L002", "X", "KH999", "GV001", 5, "01/09/2026"))

    def test_hoc_phi_dang_ky_khong_doi_khi_sua_khoa(self):
        dk = self.sv.dang_ky_lop("HV001", "L001")
        self.sv.cap_nhat_khoa(KhoaCoBan("KH001", "Cơ bản A1", 36, 9999999))
        self.assertEqual(dk.hoc_phi, 3000000)

    def test_thong_ke(self):
        a = self.sv.dang_ky_lop("HV001", "L001")
        b = self.sv.dang_ky_lop("HV002", "L001")
        self.sv.nhap_diem(a.ma, 9, 9)           # tổng kết 9.0
        self.sv.nhap_diem(b.ma, 3, 4)           # tổng kết 3.6
        self.sv.thu_hoc_phi(a.ma, 3000000)
        tk = self.sv.thong_ke_lop("L001")
        self.assertEqual(tk["si_so"], 2)
        self.assertEqual(tk["ty_le_lap_day"], 100)
        self.assertAlmostEqual(tk["diem_tb"], 6.3)
        self.assertEqual(tk["so_dat"], 1)
        self.assertEqual(tk["da_thu"], 3000000)
        self.assertEqual(tk["cong_no"], 3000000)
        self.assertEqual(tk["phan_bo"]["Giỏi"], 1)
        self.assertEqual(tk["phan_bo"]["Yếu"], 1)
        dt = self.sv.doanh_thu_theo_khoa()
        self.assertEqual(dt["KH001"]["so_hv"], 2)
        self.assertEqual(dt["KH002"]["so_hv"], 0)
        self.assertEqual([d.ma for d in self.sv.danh_sach_cong_no()], [b.ma])

    def test_xuat_chung_nhan(self):
        dk = self.sv.dang_ky_lop("HV001", "L001")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RangBuocError):          # chưa có điểm
                self.sv.xuat_chung_nhan(dk.ma, tmp)
            self.sv.nhap_diem(dk.ma, 4, 4)
            with self.assertRaises(RangBuocError):          # điểm < 5
                self.sv.xuat_chung_nhan(dk.ma, tmp)
            self.sv.nhap_diem(dk.ma, 8, 8)
            with self.assertRaises(RangBuocError):          # còn nợ
                self.sv.xuat_chung_nhan(dk.ma, tmp)
            self.sv.thu_hoc_phi(dk.ma, dk.phai_dong)
            duong_dan = self.sv.xuat_chung_nhan(dk.ma, tmp)
            with open(duong_dan, encoding="utf-8") as f:
                noi_dung = f.read()
            self.assertIn("Học Viên 1", noi_dung)
            self.assertIn("Giỏi", noi_dung)


class TestLuuTru(unittest.TestCase):
    def test_luu_va_nap_lai(self):
        sv = tao_service()
        dk = sv.dang_ky_lop("HV001", "L001", 5, date.today() - timedelta(days=3))
        sv.thu_hoc_phi(dk.ma, 500000)
        sv.nhap_diem(dk.ma, 7, 8)
        with tempfile.TemporaryDirectory() as tmp:
            duong_dan = os.path.join(tmp, "d.json")
            storage.luu_service(sv, duong_dan)
            storage.luu_service(sv, duong_dan)            # lần 2 tạo .bak
            self.assertTrue(os.path.exists(duong_dan + ".bak"))
            sv2, canh_bao = storage.nap_service(duong_dan)
        self.assertEqual(canh_bao, [])
        self.assertEqual(sv2.to_dict(), sv.to_dict())
        self.assertEqual(sv2.dang_ky[dk.ma].cong_no, dk.cong_no)

    def test_file_khong_ton_tai_tra_ve_service_rong(self):
        sv, canh_bao = storage.nap_service("/khong/co/file.json")
        self.assertEqual((len(sv.hoc_vien), canh_bao), (0, []))

    def test_json_hong(self):
        with tempfile.TemporaryDirectory() as tmp:
            duong_dan = os.path.join(tmp, "hong.json")
            with open(duong_dan, "w", encoding="utf-8") as f:
                f.write("{ khong phai json")
            with self.assertRaises(FileDuLieuError):
                storage.nap_service(duong_dan)
            with open(duong_dan, "w", encoding="utf-8") as f:
                f.write("[1, 2, 3]")
            with self.assertRaises(FileDuLieuError):
                storage.nap_service(duong_dan)

    def test_ban_ghi_loi_bi_bo_qua_va_canh_bao(self):
        du_lieu = tao_service().to_dict()
        du_lieu["hoc_vien"].append({"ma": "HV009", "ho_ten": "", "ngay_sinh": "01/01/2000", "sdt": "0900000000"})
        du_lieu["hoc_vien"].append({"ma": "HV010"})                       # thiếu trường
        du_lieu["lop_hoc"].append({"ma": "L009", "ten": "X", "ma_khoa": "KH999", "ma_gv": "GV001",
                                   "si_so_toi_da": 5, "ngay_khai_giang": "01/01/2026"})
        du_lieu["khoa_hoc"].append({"loai": "Lạ", "ma": "KH9", "ten": "x", "so_buoi": 1, "hoc_phi_co_ban": 1})
        du_lieu["dang_ky"].append({"ma": "DK1", "ma_hv": "HV777", "ma_lop": "L001",
                                   "ngay_dk": "01/01/2026", "hoc_phi": 1})
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)        # error.log ghi vào thư mục tạm
            try:
                sv = TrungTamService()
                canh_bao = sv.nap_tu_dict(du_lieu)
            finally:
                os.chdir(cwd)
        self.assertEqual(len(canh_bao), 5)
        self.assertEqual(len(sv.hoc_vien), 3)
        self.assertNotIn("L009", sv.lop_hoc)

    def test_nhap_csv(self):
        sv = tao_service()
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                csv_path = os.path.join(tmp, "hv.csv")
                with open(csv_path, "w", encoding="utf-8") as f:
                    f.write("ma,ho_ten,ngay_sinh,sdt,email\n"
                            ",nguyễn hải đăng,12/03/2004,0912345678,\n"
                            ",Sai SĐT,12/03/2004,123,\n"
                            "HV001,Trùng Mã,12/03/2004,0912345679,\n")
                ok, loi = storage.nhap_hoc_vien_csv(sv, csv_path)
                self.assertEqual((ok, len(loi)), (1, 2))
                self.assertIn("HV004", sv.hoc_vien)
                with open(csv_path, "w", encoding="utf-8") as f:
                    f.write("ten,sdt\nA,0900000000\n")
                with self.assertRaises(FileDuLieuError):
                    storage.nhap_hoc_vien_csv(sv, csv_path)
                with self.assertRaises(FileDuLieuError):
                    storage.nhap_hoc_vien_csv(sv, os.path.join(tmp, "khong_co.csv"))
            finally:
                os.chdir(cwd)

    def test_xuat_csv_hoc_vien(self):
        sv = tao_service()
        with tempfile.TemporaryDirectory() as tmp:
            duong_dan = os.path.join(tmp, "o.csv")
            storage.xuat_hoc_vien_csv(sv, duong_dan)
            with open(duong_dan, encoding="utf-8-sig") as f:
                dong = f.read().splitlines()
        self.assertEqual(len(dong), 4)
        self.assertEqual(dong[0], "ma,ho_ten,ngay_sinh,sdt,email")


class TestTienIch(unittest.TestCase):
    def test_chuyen_so(self):
        self.assertEqual(chuyen_so("1,500,000", "x", float), 1500000)
        self.assertEqual(chuyen_so(" 12 ", "x", int), 12)
        for sai in ("abc", "1.5", float("nan"), True, None):
            with self.assertRaises(DuLieuKhongHopLeError):
                chuyen_so(sai, "x", int)

    def test_tong_de_quy(self):
        self.assertEqual(tong_de_quy([]), 0)
        self.assertEqual(tong_de_quy([1, 2, 3, 4]), 10)


if __name__ == "__main__":
    unittest.main()

