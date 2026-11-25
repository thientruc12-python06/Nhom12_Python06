from datetime import date

from exceptions import (DuLieuKhongHopLeError, KhongTimThayError, LopDayError,
                        RangBuocError, TrungMaError, TrungTamError)
from models import DangKy, GiaoVien, HocVien, KhoaHoc, LopHoc
from services.chung_nhan import ChungNhanMixin
from services.quan_ly_hoc_phi import HocPhiMixin
from services.thong_ke import ThongKeMixin
from utils import ghi_log, ma_tiep_theo


class TrungTamService(HocPhiMixin, ThongKeMixin, ChungNhanMixin):
    def __init__(self):
        self.hoc_vien = {}
        self.giao_vien = {}
        self.khoa_hoc = {}
        self.lop_hoc = {}
        self.dang_ky = {}

    # tiện ích chung
    @staticmethod
    def _them(kho, doi_tuong, ten):
        if doi_tuong.ma in kho:
            raise TrungMaError(f"Mã {ten} '{doi_tuong.ma}' đã tồn tại.")
        kho[doi_tuong.ma] = doi_tuong

    @staticmethod
    def _lay(kho, ma, ten):
        try:
            return kho[ma]
        except KeyError:
            raise KhongTimThayError(f"Không tìm thấy {ten} có mã '{ma}'.") from None

    def _cap_nhat(self, kho, doi_tuong, ten):
        self._lay(kho, doi_tuong.ma, ten)
        kho[doi_tuong.ma] = doi_tuong

    # học viên
    def ma_hoc_vien_moi(self):
        return ma_tiep_theo(self.hoc_vien, "HV")

    def them_hoc_vien(self, hv):
        self._them(self.hoc_vien, hv, "học viên")

    def lay_hoc_vien(self, ma):
        return self._lay(self.hoc_vien, ma, "học viên")

    def cap_nhat_hoc_vien(self, hv):
        self._cap_nhat(self.hoc_vien, hv, "học viên")

    def xoa_hoc_vien(self, ma):
        self.lay_hoc_vien(ma)
        if any(dk.ma_hv == ma for dk in self.dang_ky.values()):
            raise RangBuocError("Học viên đã có đăng ký lớp, hãy hủy đăng ký trước khi xóa.")
        del self.hoc_vien[ma]

    # giáo viên
    def ma_giao_vien_moi(self):
        return ma_tiep_theo(self.giao_vien, "GV")

    def them_giao_vien(self, gv):
        self._them(self.giao_vien, gv, "giáo viên")

    def lay_giao_vien(self, ma):
        return self._lay(self.giao_vien, ma, "giáo viên")

    def cap_nhat_giao_vien(self, gv):
        self._cap_nhat(self.giao_vien, gv, "giáo viên")

    def xoa_giao_vien(self, ma):
        self.lay_giao_vien(ma)
        if any(lop.ma_gv == ma for lop in self.lop_hoc.values()):
            raise RangBuocError("Giáo viên đang được phân công dạy lớp, không thể xóa.")
        del self.giao_vien[ma]

    # khóa học
    def ma_khoa_moi(self):
        return ma_tiep_theo(self.khoa_hoc, "KH")

    def them_khoa(self, khoa):
        self._them(self.khoa_hoc, khoa, "khóa học")

    def lay_khoa(self, ma):
        return self._lay(self.khoa_hoc, ma, "khóa học")

    def cap_nhat_khoa(self, khoa):
        """Thay thế khóa (có thể đổi loại khóa); học phí mới chỉ áp dụng cho đăng ký sau đó."""
        self._cap_nhat(self.khoa_hoc, khoa, "khóa học")

    def xoa_khoa(self, ma):
        self.lay_khoa(ma)
        if any(lop.ma_khoa == ma for lop in self.lop_hoc.values()):
            raise RangBuocError("Khóa học đã có lớp, hãy xóa các lớp trước.")
        del self.khoa_hoc[ma]

    # lớp
    def ma_lop_moi(self):
        return ma_tiep_theo(self.lop_hoc, "L")

    def _kiem_tra_tham_chieu_lop(self, lop):
        if not lop.ma_khoa:
            raise DuLieuKhongHopLeError("Phải chọn khóa học cho lớp.")
        if not lop.ma_gv:
            raise DuLieuKhongHopLeError("Phải chọn giáo viên phụ trách.")
        self.lay_khoa(lop.ma_khoa)
        self.lay_giao_vien(lop.ma_gv)

    def them_lop(self, lop):
        self._kiem_tra_tham_chieu_lop(lop)
        self._them(self.lop_hoc, lop, "lớp")

    def lay_lop(self, ma):
        return self._lay(self.lop_hoc, ma, "lớp")

    def cap_nhat_lop(self, lop):
        self._kiem_tra_tham_chieu_lop(lop)
        self.lay_lop(lop.ma)
        if lop.si_so_toi_da < self.si_so(lop.ma):
            raise RangBuocError(
                f"Sĩ số tối đa ({lop.si_so_toi_da}) nhỏ hơn số học viên hiện có ({self.si_so(lop.ma)}).")
        self.lop_hoc[lop.ma] = lop

    def xoa_lop(self, ma):
        self.lay_lop(ma)
        if self.si_so(ma) > 0:
            raise RangBuocError("Lớp đã có học viên đăng ký, không thể xóa.")
        del self.lop_hoc[ma]

    def dang_ky_cua_lop(self, ma_lop):
        return [dk for dk in self.dang_ky.values() if dk.ma_lop == ma_lop]

    def si_so(self, ma_lop):
        return len(self.dang_ky_cua_lop(ma_lop))

    # đăng ký
    def dang_ky_lop(self, ma_hv, ma_lop, giam_gia=0, ngay=None):
        """Đăng ký học viên vào lớp: kiểm tra tồn tại, trùng đăng ký và sĩ số."""
        self.lay_hoc_vien(ma_hv)
        lop = self.lay_lop(ma_lop)
        if any(dk.ma_hv == ma_hv and dk.ma_lop == ma_lop for dk in self.dang_ky.values()):
            raise TrungMaError("Học viên đã đăng ký lớp này rồi.")
        if self.si_so(ma_lop) >= lop.si_so_toi_da:
            raise LopDayError(f"Lớp {lop.ma} đã đủ sĩ số ({lop.si_so_toi_da}/{lop.si_so_toi_da}).")
        hoc_phi = self.lay_khoa(lop.ma_khoa).tinh_hoc_phi()
        dk = DangKy(ma_tiep_theo(self.dang_ky, "DK", 4), ma_hv, ma_lop,
                    ngay or date.today(), hoc_phi, giam_gia)
        self.dang_ky[dk.ma] = dk
        return dk

    def lay_dang_ky(self, ma_dk):
        return self._lay(self.dang_ky, ma_dk, "đăng ký")

    def huy_dang_ky(self, ma_dk):
        dk = self.lay_dang_ky(ma_dk)
        if dk.da_dong > 0:
            raise RangBuocError("Đăng ký đã có thanh toán học phí, không thể hủy.")
        if dk.diem_tong_ket is not None or dk.diem_gk is not None or dk.diem_ck is not None:
            raise RangBuocError("Đăng ký đã có điểm, không thể hủy.")
        del self.dang_ky[ma_dk]

    #lưu / nạp dữ liệu
    def to_dict(self):
        return {
            "hoc_vien": [x.to_dict() for x in self.hoc_vien.values()],
            "giao_vien": [x.to_dict() for x in self.giao_vien.values()],
            "khoa_hoc": [x.to_dict() for x in self.khoa_hoc.values()],
            "lop_hoc": [x.to_dict() for x in self.lop_hoc.values()],
            "dang_ky": [x.to_dict() for x in self.dang_ky.values()],
        }

    def nap_tu_dict(self, du_lieu):
        """Nạp dữ liệu; bản ghi lỗi bị bỏ qua và được ghi vào danh sách cảnh báo + error.log."""
        canh_bao = []

        def nap(ten_muc, kho, tao, kiem_tra=None):
            for i, d in enumerate(du_lieu.get(ten_muc, []), start=1):
                try:
                    doi_tuong = tao(d)
                    if kiem_tra:
                        kiem_tra(doi_tuong)
                    self._them(kho, doi_tuong, ten_muc)
                except (TrungTamError, KeyError, TypeError, AttributeError) as loi:
                    thong_bao = f"Bỏ qua bản ghi {ten_muc} #{i}: {loi}"
                    canh_bao.append(thong_bao)
                    ghi_log("NAP_DU_LIEU", thong_bao)

        nap("hoc_vien", self.hoc_vien, HocVien.tu_dict)
        nap("giao_vien", self.giao_vien, GiaoVien.tu_dict)
        nap("khoa_hoc", self.khoa_hoc, KhoaHoc.tu_dict)
        nap("lop_hoc", self.lop_hoc, LopHoc.tu_dict, self._kiem_tra_tham_chieu_lop)
        nap("dang_ky", self.dang_ky, DangKy.tu_dict, self._kiem_tra_tham_chieu_dang_ky)
        return canh_bao

    def _kiem_tra_tham_chieu_dang_ky(self, dk):
        self.lay_hoc_vien(dk.ma_hv)
        self.lay_lop(dk.ma_lop)
