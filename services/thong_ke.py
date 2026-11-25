"""Thống kê lớp, doanh thu theo khóa, tổng quan (mixin của TrungTamService)."""
from utils import NHAN_XEP_LOAI, tinh_trung_binh


class ThongKeMixin:
    @staticmethod
    def phan_bo_xep_loai(ds_dang_ky):
        dem = {nhan: 0 for nhan in NHAN_XEP_LOAI}
        for dk in ds_dang_ky:
            dem[dk.xep_loai] += 1
        return dem

    def thong_ke_lop(self, ma_lop):
        lop = self.lay_lop(ma_lop)
        ds = self.dang_ky_cua_lop(ma_lop)
        diem = [dk.diem_tong_ket for dk in ds if dk.diem_tong_ket is not None]
        return {
            "ma": lop.ma, "ten": lop.ten, "si_so": len(ds), "toi_da": lop.si_so_toi_da,
            "ty_le_lap_day": len(ds) / lop.si_so_toi_da * 100,
            "diem_tb": tinh_trung_binh(*diem),
            "so_dat": sum(1 for d in diem if d >= 5),
            "phai_thu": sum(dk.phai_dong for dk in ds),
            "da_thu": sum(dk.da_dong for dk in ds),
            "cong_no": sum(dk.cong_no for dk in ds),
            "phan_bo": self.phan_bo_xep_loai(ds),
        }

    def doanh_thu_theo_khoa(self):
        ket_qua = {ma: {"ma": ma, "ten": k.ten, "so_hv": 0, "phai_thu": 0, "da_thu": 0, "cong_no": 0}
                   for ma, k in self.khoa_hoc.items()}
        for dk in self.dang_ky.values():
            lop = self.lop_hoc.get(dk.ma_lop)
            if lop is None or lop.ma_khoa not in ket_qua:
                continue
            dong = ket_qua[lop.ma_khoa]
            dong["so_hv"] += 1
            dong["phai_thu"] += dk.phai_dong
            dong["da_thu"] += dk.da_dong
            dong["cong_no"] += dk.cong_no
        return ket_qua

    def tong_quan(self):
        return {
            "hoc_vien": len(self.hoc_vien), "giao_vien": len(self.giao_vien),
            "khoa_hoc": len(self.khoa_hoc), "lop_hoc": len(self.lop_hoc),
            "dang_ky": len(self.dang_ky),
            "da_thu": sum(dk.da_dong for dk in self.dang_ky.values()),
            "cong_no": sum(dk.cong_no for dk in self.dang_ky.values()),
        }
