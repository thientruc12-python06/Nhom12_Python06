from datetime import date

from exceptions import DuLieuKhongHopLeError, RangBuocError
from models.person import _ma_hop_le
from utils import chuyen_so, format_date, parse_date, phan_loai_diem, tong_de_quy

# Đăng ký
def _doc_diem(gia_tri):
    if gia_tri is None or (isinstance(gia_tri, str) and not gia_tri.strip()):
        return None
    return chuyen_so(gia_tri, "Điểm", float, 0, 10)


class DangKy:
    """Một lượt đăng ký của học viên vào lớp: gồm học phí, các lần thanh toán và điểm."""
    TRONG_SO_GIUA_KY = 0.4
    TRONG_SO_CUOI_KY = 0.6

    def __init__(self, ma, ma_hv, ma_lop, ngay_dk, hoc_phi, giam_gia=0,
                 thanh_toan=None, diem_gk=None, diem_ck=None):
        self._ma = _ma_hop_le(ma)
        self._ma_hv = _ma_hop_le(ma_hv)
        self._ma_lop = _ma_hop_le(ma_lop)
        self.ngay_dk = ngay_dk
        self.__hoc_phi = chuyen_so(hoc_phi, "Học phí", float, 0)
        self.giam_gia = giam_gia
        self.__thanh_toan = []
        for gd in (thanh_toan or []):
            self.__thanh_toan.append({
                "ngay": format_date(gd["ngay"]),
                "so_tien": chuyen_so(gd["so_tien"], "Số tiền", float, 0)})
        self.__diem_gk = None
        self.__diem_ck = None
        self.nhap_diem(diem_gk, diem_ck)

    @property
    def ma(self):
        return self._ma

    @property
    def ma_hv(self):
        return self._ma_hv

    @property
    def ma_lop(self):
        return self._ma_lop

    @property
    def ngay_dk(self):
        return self.__ngay_dk

    @ngay_dk.setter
    def ngay_dk(self, gia_tri):
        self.__ngay_dk = parse_date(gia_tri)

    @property
    def hoc_phi(self):
        return self.__hoc_phi

    @property
    def giam_gia(self):
        return self.__giam_gia

    @giam_gia.setter
    def giam_gia(self, gia_tri):
        self.__giam_gia = chuyen_so(gia_tri, "Giảm giá (%)", float, 0, 100)

    @property
    def thanh_toan(self):
        return [dict(g) for g in self.__thanh_toan]

    @property
    def phai_dong(self):
        return round(self.__hoc_phi * (1 - self.__giam_gia / 100))

    @property
    def da_dong(self):
        return tong_de_quy([g["so_tien"] for g in self.__thanh_toan])

    @property
    def cong_no(self):
        return max(0, self.phai_dong - self.da_dong)

    def nop_tien(self, so_tien, ngay=None):
        so_tien = chuyen_so(so_tien, "Số tiền nộp", float)
        if so_tien <= 0:
            raise DuLieuKhongHopLeError("Số tiền nộp phải lớn hơn 0.")
        if so_tien > self.cong_no:
            raise RangBuocError(
                f"Số tiền nộp ({so_tien:,.0f} đ) vượt quá công nợ ({self.cong_no:,.0f} đ).")
        self.__thanh_toan.append({"ngay": format_date(ngay or date.today()), "so_tien": so_tien})

    @property
    def diem_gk(self):
        return self.__diem_gk

    @property
    def diem_ck(self):
        return self.__diem_ck

    def nhap_diem(self, diem_gk, diem_ck):
        gk, ck = _doc_diem(diem_gk), _doc_diem(diem_ck)   # kiểm tra cả hai rồi mới gán
        self.__diem_gk, self.__diem_ck = gk, ck

    @property
    def diem_tong_ket(self):
        if self.__diem_gk is None or self.__diem_ck is None:
            return None
        return round(self.TRONG_SO_GIUA_KY * self.__diem_gk
                     + self.TRONG_SO_CUOI_KY * self.__diem_ck, 2)

    @property
    def xep_loai(self):
        return phan_loai_diem(self.diem_tong_ket)

    def to_dict(self):
        return {"ma": self._ma, "ma_hv": self._ma_hv, "ma_lop": self._ma_lop,
                "ngay_dk": format_date(self.ngay_dk), "hoc_phi": self.__hoc_phi,
                "giam_gia": self.__giam_gia, "thanh_toan": self.thanh_toan,
                "diem_gk": self.__diem_gk, "diem_ck": self.__diem_ck}

    @classmethod
    def tu_dict(cls, d):
        return cls(**d)

