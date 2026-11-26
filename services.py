import html
import os
from datetime import date

from exceptions import (DuLieuKhongHopLeError, FileDuLieuError, KhongTimThayError,
                        LopDayError, RangBuocError, TrungMaError, TrungTamError)
from models import DangKy, GiaoVien, HocVien, KhoaHoc, LopHoc
from utils import (NHAN_XEP_LOAI, TEN_TRUNG_TAM, chuyen_so, dinh_dang_tien,
                   format_date, ghi_log, ma_tiep_theo, parse_date, tinh_trung_binh)


class TrungTamService:
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

    # học phí và điểm
    def thu_hoc_phi(self, ma_dk, so_tien, ngay=None):
        self.lay_dang_ky(ma_dk).nop_tien(so_tien, ngay)

    def nhap_diem(self, ma_dk, diem_gk, diem_ck):
        self.lay_dang_ky(ma_dk).nhap_diem(diem_gk, diem_ck)

    # thống kê
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

    def danh_sach_cong_no(self):
        """Danh sách đăng ký còn nợ học phí, nợ nhiều xếp trước."""
        ds = [dk for dk in self.dang_ky.values() if dk.cong_no > 0]
        return sorted(ds, key=lambda dk: dk.cong_no, reverse=True)

    def tong_quan(self):
        return {
            "hoc_vien": len(self.hoc_vien), "giao_vien": len(self.giao_vien),
            "khoa_hoc": len(self.khoa_hoc), "lop_hoc": len(self.lop_hoc),
            "dang_ky": len(self.dang_ky),
            "da_thu": sum(dk.da_dong for dk in self.dang_ky.values()),
            "cong_no": sum(dk.cong_no for dk in self.dang_ky.values()),
        }

    # chứng nhận
    def xuat_chung_nhan(self, ma_dk, thu_muc="chung_nhan"):
        """Xuất chứng nhận hoàn thành khóa học dạng HTML (mở bằng trình duyệt để in)."""
        dk = self.lay_dang_ky(ma_dk)
        if dk.diem_tong_ket is None:
            raise RangBuocError("Học viên chưa có đủ điểm giữa kỳ và cuối kỳ.")
        if dk.diem_tong_ket < 5:
            raise RangBuocError(f"Điểm tổng kết {dk.diem_tong_ket} < 5, chưa đủ điều kiện cấp chứng nhận.")
        if dk.cong_no > 0:
            raise RangBuocError(f"Học viên còn nợ học phí {dinh_dang_tien(dk.cong_no)}.")
        hv = self.lay_hoc_vien(dk.ma_hv)
        lop = self.lay_lop(dk.ma_lop)
        khoa = self.lay_khoa(lop.ma_khoa)
        gv = self.lay_giao_vien(lop.ma_gv)
        e = html.escape
        noi_dung = f"""<!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="utf-8">
            <title>Chứng nhận {e(dk.ma)}</title>

            <style>
                body {{
                    font-family: Georgia, serif;
                    background: #f4f1ea;
                    margin: 0;
                    padding: 30px;
                }}

                .khung {{
                    max-width: 760px;
                    margin: auto;
                    background: #fff;
                    border: 10px double #8a6d3b;
                    padding: 50px;
                    text-align: center;
                }}

                h1 {{
                    color: #8a6d3b;
                    letter-spacing: 3px;
                }}

                .ten {{
                    font-size: 34px;
                    margin: 18px 0;
                    color: #222;
                }}

                .phu {{
                    color: #555;
                    margin: 6px 0;
                }}

                .ky {{
                    display: flex;
                    justify-content: space-between;
                    margin-top: 60px;
                }}
            </style>
        </head>

        <body>
            <div class="khung">

                <div class="phu">{e(TEN_TRUNG_TAM)}</div>

                <h1>CHỨNG NHẬN HOÀN THÀNH KHÓA HỌC</h1>

                <p class="phu">Chứng nhận học viên</p>

                <div class="ten">{e(hv.ho_ten)}</div>

                <p class="phu">
                    Mã học viên: {e(hv.ma)}
                    &nbsp;|&nbsp;
                    Ngày sinh: {format_date(hv.ngay_sinh)}
                </p>

                <p>
                    đã hoàn thành khóa
                    <b>{e(khoa.ten)}</b>
                    ({e(khoa.LOAI)})
                    – lớp <b>{e(lop.ten)}</b>
                </p>

                <p>
                    Điểm tổng kết:
                    <b>{dk.diem_tong_ket:.2f}</b>
                    – Xếp loại:
                    <b>{e(dk.xep_loai)}</b>
                </p>

                <div class="ky">

                    <div>
                        Giáo viên phụ trách
                        <br><br><br>
                        <b>{e(gv.ho_ten)}</b>
                    </div>

                    <div>
                        TP. Hồ Chí Minh, ngày {date.today():%d/%m/%Y}
                        <br>
                        Giám đốc trung tâm
                        <br><br><br>
                    </div>

                </div>

                <p class="phu">
                    Số chứng nhận: CN-{e(dk.ma)}
                </p>

            </div>
        </body>
        </html>
        """
        try:
            os.makedirs(thu_muc, exist_ok=True)
            duong_dan = os.path.join(thu_muc, f"ChungNhan_{dk.ma}.html")
            with open(duong_dan, "w", encoding="utf-8") as f:
                f.write(noi_dung)
        except OSError as loi:
            raise FileDuLieuError(f"Không ghi được file chứng nhận: {loi}") from loi
        return duong_dan

    # lưu / nạp dữ liệu
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
