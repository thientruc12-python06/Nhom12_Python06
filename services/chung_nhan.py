"""Xuất chứng nhận hoàn thành khóa học dạng HTML (mixin của TrungTamService)."""
import html
import os
from datetime import date

from exceptions import FileDuLieuError, RangBuocError
from utils import TEN_TRUNG_TAM, dinh_dang_tien, format_date


class ChungNhanMixin:
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
<html lang="vi"><head><meta charset="utf-8"><title>Chứng nhận {e(dk.ma)}</title>
<style>
body{{font-family:Georgia,serif;background:#f4f1ea;margin:0;padding:30px}}
.khung{{max-width:760px;margin:auto;background:#fff;border:10px double #8a6d3b;padding:50px;text-align:center}}
h1{{color:#8a6d3b;letter-spacing:3px}} .ten{{font-size:34px;margin:18px 0;color:#222}}
.phu{{color:#555;margin:6px 0}} .ky{{display:flex;justify-content:space-between;margin-top:60px}}
</style></head><body><div class="khung">
<div class="phu">{e(TEN_TRUNG_TAM)}</div>
<h1>CHỨNG NHẬN HOÀN THÀNH KHÓA HỌC</h1>
<p class="phu">Chứng nhận học viên</p>
<div class="ten">{e(hv.ho_ten)}</div>
<p class="phu">Mã học viên: {e(hv.ma)} &nbsp;|&nbsp; Ngày sinh: {format_date(hv.ngay_sinh)}</p>
<p>đã hoàn thành khóa <b>{e(khoa.ten)}</b> ({e(khoa.LOAI)}) – lớp <b>{e(lop.ten)}</b></p>
<p>Điểm tổng kết: <b>{dk.diem_tong_ket:.2f}</b> – Xếp loại: <b>{e(dk.xep_loai)}</b></p>
<div class="ky"><div>Giáo viên phụ trách<br><br><br><b>{e(gv.ho_ten)}</b></div>
<div>TP. Hồ Chí Minh, ngày {date.today():%d/%m/%Y}<br>Giám đốc trung tâm<br><br><br></div></div>
<p class="phu">Số chứng nhận: CN-{e(dk.ma)}</p>
</div></body></html>"""
        try:
            os.makedirs(thu_muc, exist_ok=True)
            duong_dan = os.path.join(thu_muc, f"ChungNhan_{dk.ma}.html")
            with open(duong_dan, "w", encoding="utf-8") as f:
                f.write(noi_dung)
        except OSError as loi:
            raise FileDuLieuError(f"Không ghi được file chứng nhận: {loi}") from loi
        return duong_dan
