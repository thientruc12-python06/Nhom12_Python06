from abc import ABC, abstractmethod
from datetime import date

from exceptions import DuLieuKhongHopLeError
from utils import (chuan_hoa_ten, chuyen_so, format_date, kiem_tra_email,
                   kiem_tra_sdt, parse_date)

def _ma_hop_le(ma):
    ma = str(ma).strip()
    if not ma:
        raise DuLieuKhongHopLeError("Mã không được để trống.")
    return ma

# Người
class Person(ABC):
    """Lớp trừu tượng cho người (học viên, giáo viên)."""

    def __init__(self, ma, ho_ten, ngay_sinh, sdt, email=""):
        self._ma = _ma_hop_le(ma)         
        self.ho_ten = ho_ten               
        self.ngay_sinh = ngay_sinh
        self.sdt = sdt
        self.email = email

    @property
    def ma(self):
        return self._ma

    @property
    def ho_ten(self):
        return self.__ho_ten

    @ho_ten.setter
    def ho_ten(self, gia_tri):
        gia_tri = chuan_hoa_ten(gia_tri)
        if not gia_tri:
            raise DuLieuKhongHopLeError("Họ tên không được để trống.")
        self.__ho_ten = gia_tri

    @property
    def ngay_sinh(self):
        return self.__ngay_sinh

    @ngay_sinh.setter
    def ngay_sinh(self, gia_tri):
        ngay = parse_date(gia_tri)
        if ngay > date.today() or ngay.year < 1900:
            raise DuLieuKhongHopLeError("Ngày sinh không hợp lệ (không được ở tương lai).")
        self.__ngay_sinh = ngay

    @property
    def sdt(self):
        return self.__sdt

    @sdt.setter
    def sdt(self, gia_tri):
        gia_tri = str(gia_tri).strip()
        if not kiem_tra_sdt(gia_tri):
            raise DuLieuKhongHopLeError("Số điện thoại phải gồm đúng 10 chữ số.")
        self.__sdt = gia_tri

    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, gia_tri):
        gia_tri = str(gia_tri or "").strip()
        if not kiem_tra_email(gia_tri):
            raise DuLieuKhongHopLeError("Email không đúng định dạng (ví dụ: ten@mail.com).")
        self.__email = gia_tri

    @property
    def tuoi(self):
        hom_nay, ns = date.today(), self.__ngay_sinh
        return hom_nay.year - ns.year - ((hom_nay.month, hom_nay.day) < (ns.month, ns.day))

    @abstractmethod
    def vai_tro(self):
        """Tên vai trò hiển thị (đa hình)."""

    def to_dict(self):
        return {"ma": self._ma, "ho_ten": self.ho_ten,
                "ngay_sinh": format_date(self.ngay_sinh),
                "sdt": self.sdt, "email": self.email}

    @classmethod
    def tu_dict(cls, d):
        return cls(**d)

    def __str__(self):
        return f"{self._ma} - {self.ho_ten}"


class HocVien(Person):
    def vai_tro(self):
        return "Học viên"


class GiaoVien(Person):
    def __init__(self, ma, ho_ten, ngay_sinh, sdt, email="", chuyen_mon="", luong_gio=0):
        super().__init__(ma, ho_ten, ngay_sinh, sdt, email)
        self.chuyen_mon = chuyen_mon
        self.luong_gio = luong_gio

    @property
    def chuyen_mon(self):
        return self.__chuyen_mon

    @chuyen_mon.setter
    def chuyen_mon(self, gia_tri):
        self.__chuyen_mon = " ".join(str(gia_tri or "").split())

    @property
    def luong_gio(self):
        return self.__luong_gio

    @luong_gio.setter
    def luong_gio(self, gia_tri):
        self.__luong_gio = chuyen_so(gia_tri, "Lương theo giờ", float, 0)

    def vai_tro(self):
        return "Giáo viên"

    def to_dict(self):
        d = super().to_dict()
        d.update(chuyen_mon=self.chuyen_mon, luong_gio=self.luong_gio)
        return d

