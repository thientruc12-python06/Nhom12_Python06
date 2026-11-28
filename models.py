from abc import ABC, abstractmethod
from datetime import date

from exceptions import DuLieuKhongHopLeError, RangBuocError
from utils import (chuan_hoa_ten, chuyen_so, dinh_dang_tien, format_date, kiem_tra_email,
                   kiem_tra_sdt, parse_date, phan_loai_diem, tong_de_quy)

CHUNG_CHI = ("IELTS", "TOEIC", "TOEFL")


def _ma_hop_le(ma):
    ma = str(ma).strip()
    if not ma:
        raise DuLieuKhongHopLeError("Mã không được để trống.")
    return ma


# Người
class Person(ABC):
    """Lớp trừu tượng cho người (học viên, giáo viên)."""

    def __init__(self, ma, ho_ten, ngay_sinh, sdt, email=""):
        self._ma = _ma_hop_le(ma)          # protected, chỉ đọc qua property
        self.ho_ten = ho_ten               # các thuộc tính dưới đây qua setter có kiểm tra
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


# Khóa học
class KhoaHoc(ABC):
    """Lớp trừu tượng cho khóa học. Mỗi loại khóa tự quy định cách tính học phí."""

    LOAI = ""
    TRUONG_RIENG = ()   # tên các thuộc tính riêng cần lưu/đọc từ JSON

    def __init__(self, ma, ten, so_buoi, hoc_phi_co_ban):
        self._ma = _ma_hop_le(ma)
        self.ten = ten
        self.so_buoi = so_buoi
        self.hoc_phi_co_ban = hoc_phi_co_ban

    @property
    def ma(self):
        return self._ma

    @property
    def ten(self):
        return self.__ten

    @ten.setter
    def ten(self, gia_tri):
        gia_tri = " ".join(str(gia_tri).split())
        if not gia_tri:
            raise DuLieuKhongHopLeError("Tên khóa học không được để trống.")
        self.__ten = gia_tri

    @property
    def so_buoi(self):
        return self.__so_buoi

    @so_buoi.setter
    def so_buoi(self, gia_tri):
        self.__so_buoi = chuyen_so(gia_tri, "Số buổi", int, 1, 500)

    @property
    def hoc_phi_co_ban(self):
        return self.__hoc_phi_co_ban

    @hoc_phi_co_ban.setter
    def hoc_phi_co_ban(self, gia_tri):
        self.__hoc_phi_co_ban = chuyen_so(gia_tri, "Học phí cơ bản", float, 0)

    @property
    def phu_phi(self):
        """Phụ phí riêng của loại khóa (mặc định không có)."""
        return 0

    @abstractmethod
    def tinh_hoc_phi(self):
        """Học phí thực tế của khóa (ghi đè ở lớp con -> đa hình)."""

    @abstractmethod
    def mo_ta_phu_phi(self):
        """Chuỗi mô tả cách tính phụ phí."""

    def to_dict(self):
        d = {"loai": self.LOAI, "ma": self._ma, "ten": self.ten,
             "so_buoi": self.so_buoi, "hoc_phi_co_ban": self.hoc_phi_co_ban}
        for k in self.TRUONG_RIENG:
            d[k] = getattr(self, k)
        return d

    @staticmethod
    def tu_dict(d):
        loai = d.get("loai")
        lop = KHOA_THEO_LOAI.get(loai)
        if lop is None:
            raise DuLieuKhongHopLeError(f"Loại khóa '{loai}' không được hỗ trợ.")
        rieng = {k: d[k] for k in lop.TRUONG_RIENG if k in d}
        return lop(d["ma"], d["ten"], d["so_buoi"], d["hoc_phi_co_ban"], **rieng)

    def __str__(self):
        return f"{self._ma} - {self.ten}"


class KhoaCoBan(KhoaHoc):
    LOAI = "Cơ bản"

    def tinh_hoc_phi(self):
        return self.hoc_phi_co_ban

    def mo_ta_phu_phi(self):
        return "Không phụ phí"


class KhoaGiaoTiep(KhoaHoc):
    LOAI = "Giao tiếp"
    TRUONG_RIENG = ("phu_phi_tai_lieu",)

    def __init__(self, ma, ten, so_buoi, hoc_phi_co_ban, phu_phi_tai_lieu=0):
        super().__init__(ma, ten, so_buoi, hoc_phi_co_ban)
        self.phu_phi_tai_lieu = phu_phi_tai_lieu

    @property
    def phu_phi_tai_lieu(self):
        return self.__tai_lieu

    @phu_phi_tai_lieu.setter
    def phu_phi_tai_lieu(self, gia_tri):
        self.__tai_lieu = chuyen_so(gia_tri, "Phí tài liệu", float, 0)

    @property
    def phu_phi(self):
        return self.__tai_lieu

    def tinh_hoc_phi(self):
        return self.hoc_phi_co_ban + self.__tai_lieu

    def mo_ta_phu_phi(self):
        return f"Phí tài liệu {dinh_dang_tien(self.__tai_lieu)}"


class KhoaLuyenThi(KhoaHoc):
    LOAI = "Luyện thi"
    TRUONG_RIENG = ("chung_chi", "phi_thi_thu")
    HE_SO = 1.2   # khóa luyện thi có hệ số học phí 1.2

    def __init__(self, ma, ten, so_buoi, hoc_phi_co_ban, chung_chi="IELTS", phi_thi_thu=0):
        super().__init__(ma, ten, so_buoi, hoc_phi_co_ban)
        self.chung_chi = chung_chi
        self.phi_thi_thu = phi_thi_thu

    @property
    def chung_chi(self):
        return self.__chung_chi

    @chung_chi.setter
    def chung_chi(self, gia_tri):
        if gia_tri not in CHUNG_CHI:
            raise DuLieuKhongHopLeError(f"Chứng chỉ phải thuộc: {', '.join(CHUNG_CHI)}.")
        self.__chung_chi = gia_tri

    @property
    def phi_thi_thu(self):
        return self.__phi_thi_thu

    @phi_thi_thu.setter
    def phi_thi_thu(self, gia_tri):
        self.__phi_thi_thu = chuyen_so(gia_tri, "Phí thi thử", float, 0)

    @property
    def phu_phi(self):
        return self.__phi_thi_thu

    def tinh_hoc_phi(self):
        return self.hoc_phi_co_ban * self.HE_SO + self.__phi_thi_thu

    def mo_ta_phu_phi(self):
        return f"Hệ số {self.HE_SO} + thi thử {dinh_dang_tien(self.__phi_thi_thu)} ({self.__chung_chi})"


KHOA_THEO_LOAI = {c.LOAI: c for c in (KhoaCoBan, KhoaGiaoTiep, KhoaLuyenThi)}


def tao_khoa(loai, ma, ten, so_buoi, hoc_phi_co_ban, phu_phi=0, chung_chi="IELTS"):
    """Hàm nhà máy (factory) tạo khóa học đúng loại từ dữ liệu form."""
    lop = KHOA_THEO_LOAI.get(loai)
    if lop is None:
        raise DuLieuKhongHopLeError("Hãy chọn loại khóa học.")
    if lop is KhoaGiaoTiep:
        return lop(ma, ten, so_buoi, hoc_phi_co_ban, phu_phi_tai_lieu=phu_phi or 0)
    if lop is KhoaLuyenThi:
        return lop(ma, ten, so_buoi, hoc_phi_co_ban, chung_chi=chung_chi, phi_thi_thu=phu_phi or 0)
    return lop(ma, ten, so_buoi, hoc_phi_co_ban)


# Lớp
class LopHoc:
    def __init__(self, ma, ten, ma_khoa, ma_gv, si_so_toi_da, ngay_khai_giang, lich_hoc=""):
        self._ma = _ma_hop_le(ma)
        self.ten = ten
        self.ma_khoa = ma_khoa
        self.ma_gv = ma_gv
        self.si_so_toi_da = si_so_toi_da
        self.ngay_khai_giang = ngay_khai_giang
        self.lich_hoc = lich_hoc

    @property
    def ma(self):
        return self._ma

    @property
    def ten(self):
        return self.__ten

    @ten.setter
    def ten(self, gia_tri):
        gia_tri = " ".join(str(gia_tri).split())
        if not gia_tri:
            raise DuLieuKhongHopLeError("Tên lớp không được để trống.")
        self.__ten = gia_tri

    @property
    def si_so_toi_da(self):
        return self.__si_so_toi_da

    @si_so_toi_da.setter
    def si_so_toi_da(self, gia_tri):
        self.__si_so_toi_da = chuyen_so(gia_tri, "Sĩ số tối đa", int, 1, 200)

    @property
    def ngay_khai_giang(self):
        return self.__khai_giang

    @ngay_khai_giang.setter
    def ngay_khai_giang(self, gia_tri):
        self.__khai_giang = parse_date(gia_tri)

    def to_dict(self):
        return {"ma": self._ma, "ten": self.ten, "ma_khoa": self.ma_khoa, "ma_gv": self.ma_gv,
                "si_so_toi_da": self.si_so_toi_da,
                "ngay_khai_giang": format_date(self.ngay_khai_giang), "lich_hoc": self.lich_hoc}

    @classmethod
    def tu_dict(cls, d):
        return cls(**d)

    def __str__(self):
        return f"{self._ma} - {self.ten}"


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
