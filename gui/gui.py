import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

import storage
from exceptions import RangBuocError, TrungTamError
from models import CHUNG_CHI, KHOA_THEO_LOAI, GiaoVien, HocVien, LopHoc, tao_khoa
from utils import (NHAN_XEP_LOAI, TEN_TRUNG_TAM, chuyen_so, dinh_dang_tien,
                   format_date, ghi_log)
from widgets import BieuDoCot, DateEntry, GradeBadge


def lay_ma(chuoi):
    """Tách mã từ chuỗi combobox dạng 'MA - Tên'."""
    return chuoi.split(" - ")[0].strip() if chuoi else ""


def nhan_doi_tuong(doi_tuong):
    return f"{doi_tuong.ma} - {getattr(doi_tuong, 'ten', None) or doi_tuong.ho_ten}"


def khop(tu_khoa, *chuoi):
    return tu_khoa in " ".join(str(c) for c in chuoi).lower()


class Truong:
    """Mô tả một trường nhập của form."""

    def __init__(self, khoa, nhan, kieu="text", gia_tri="", chi_doc=False, danh_sach=()):
        self.khoa, self.nhan, self.kieu = khoa, nhan, kieu
        self.gia_tri, self.chi_doc, self.danh_sach = gia_tri, chi_doc, list(danh_sach)


class CrudTab(ttk.Frame):
    
    TIEU_DE_FORM = "Thông tin"

    def __init__(self, master, app, cot, truong):
        super().__init__(master, padding=8)
        self.app, self.truong = app, truong
        self.bien, self.o_nhap, self.combo = {}, {}, {}

        trai = ttk.Frame(self)
        trai.pack(side="left", fill="both", expand=True)
        tim = ttk.Frame(trai)
        tim.pack(fill="x", pady=(0, 6))
        ttk.Label(tim, text="Tìm kiếm:").pack(side="left")
        self.tim_var = tk.StringVar()
        ttk.Entry(tim, textvariable=self.tim_var, width=30).pack(side="left", padx=6)
        self.tim_var.trace_add("write", lambda *_: self.lam_moi())

        khung = ttk.Frame(trai)
        khung.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(khung, columns=[c[0] for c in cot], show="headings", selectmode="browse")
        for ma_cot, tieu_de, rong in cot:
            self.tree.heading(ma_cot, text=tieu_de)
            self.tree.column(ma_cot, width=rong, anchor="w")
        thanh = ttk.Scrollbar(khung, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=thanh.set)
        self.tree.pack(side="left", fill="both", expand=True)
        thanh.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._khi_chon)

        phai = ttk.LabelFrame(self, text=self.TIEU_DE_FORM, padding=10)
        phai.pack(side="right", fill="y", padx=(10, 0))
        for i, t in enumerate(truong):
            ttk.Label(phai, text=t.nhan + ":").grid(row=i, column=0, sticky="w", pady=3)
            if t.kieu == "date":
                w = DateEntry(phai, t.gia_tri or None)
                self.o_nhap[t.khoa] = w
            else:
                bien = tk.StringVar(value=t.gia_tri)
                self.bien[t.khoa] = bien
                if t.kieu == "combo":
                    w = ttk.Combobox(phai, textvariable=bien, values=t.danh_sach, width=28, state="readonly")
                    self.combo[t.khoa] = w
                else:
                    w = ttk.Entry(phai, textvariable=bien, width=30,
                                  state="readonly" if t.chi_doc else "normal")
            w.grid(row=i, column=1, sticky="w", pady=3, padx=(6, 0))
        nut = ttk.Frame(phai)
        nut.grid(row=len(truong), column=0, columnspan=2, pady=(12, 0))
        for chu, lenh in (("Thêm", self._them), ("Cập nhật", self._cap_nhat),
                          ("Xóa", self._xoa), ("Làm trống", self.lam_trong)):
            ttk.Button(nut, text=chu, command=lenh, width=9).pack(side="left", padx=2)
        self.khung_phu = ttk.Frame(phai)
        self.khung_phu.grid(row=len(truong) + 1, column=0, columnspan=2, pady=(8, 0))
        self.lam_trong()

    # đọc/ghi giá trị form
    def doc_form(self):
        ket_qua = {t.khoa: (self.o_nhap[t.khoa].get() if t.kieu == "date" else self.bien[t.khoa].get().strip())
                   for t in self.truong}
        return ket_qua

    def dat_form(self, d):
        for t in self.truong:
            gia_tri = d.get(t.khoa, t.gia_tri)
            if t.kieu == "date":
                # ô ngày không bao giờ để trống: mặc định là hôm nay
                self.o_nhap[t.khoa].set(gia_tri or format_date(date.today()))
            else:
                self.bien[t.khoa].set("" if gia_tri is None else str(gia_tri))

    def lam_trong(self):
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())
        self.dat_form({t.khoa: t.gia_tri for t in self.truong})
        if "ma" in self.bien:
            self.bien["ma"].set("(tự sinh)")

    def ma_dang_chon(self):
        sel = self.tree.selection()
        if not sel:
            raise RangBuocError("Hãy chọn một dòng trong bảng trước.")
        return sel[0]

    def _khi_chon(self, _event=None):
        sel = self.tree.selection()
        if sel:
            self.dat_form(self.nap_form(sel[0]))

    def lam_moi(self):
        dang_chon = self.tree.selection()
        self.cap_nhat_combo()
        self.tree.delete(*self.tree.get_children())
        tu_khoa = self.tim_var.get().strip().lower()
        for iid, gia_tri in self.lay_dong(tu_khoa):
            self.tree.insert("", "end", iid=iid, values=gia_tri)
        if dang_chon and self.tree.exists(dang_chon[0]):
            self.tree.selection_set(dang_chon[0])

    # hành động
    def _them(self):
        def tac_vu():
            doi_tuong = self.tao_doi_tuong(self.doc_form(), self.ma_moi())
            self.them(doi_tuong)
            self.lam_trong()
            return f"Đã thêm {doi_tuong.ma}"
        self.app.thuc_hien(tac_vu)

    def _cap_nhat(self):
        def tac_vu():
            ma = self.ma_dang_chon()
            self.cap_nhat(self.tao_doi_tuong(self.doc_form(), ma))
            return f"Đã cập nhật {ma}"
        self.app.thuc_hien(tac_vu)

    def _xoa(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Xóa", "Hãy chọn một dòng trong bảng trước.")
            return
        if not messagebox.askyesno("Xác nhận", f"Xóa {sel[0]}?"):
            return

        def tac_vu():
            self.xoa(sel[0])
            self.lam_trong()
            return f"Đã xóa {sel[0]}"
        self.app.thuc_hien(tac_vu)

    # các hook cho lớp con ghi đè
    def cap_nhat_combo(self):
        pass

    def lay_dong(self, tu_khoa):
        raise NotImplementedError

    def nap_form(self, ma):
        raise NotImplementedError

    def tao_doi_tuong(self, form, ma):
        raise NotImplementedError

    def ma_moi(self):
        raise NotImplementedError

    def them(self, doi_tuong):
        raise NotImplementedError

    def cap_nhat(self, doi_tuong):
        raise NotImplementedError

    def xoa(self, ma):
        raise NotImplementedError


class HocVienTab(CrudTab):
    TIEU_DE_FORM = "Học viên"

    def __init__(self, master, app):
        super().__init__(master, app,
                         [("ma", "Mã", 70), ("ho_ten", "Họ tên", 170), ("ngay_sinh", "Ngày sinh", 90),
                          ("sdt", "Điện thoại", 100), ("email", "Email", 160), ("so_lop", "Số lớp", 55)],
                         [Truong("ma", "Mã", chi_doc=True), Truong("ho_ten", "Họ tên"),
                          Truong("ngay_sinh", "Ngày sinh", "date", "01/01/2005"),
                          Truong("sdt", "Điện thoại"), Truong("email", "Email")])
        ttk.Button(self.khung_phu, text="Nhập từ CSV…", command=self._nhap_csv).pack(side="left", padx=2)
        ttk.Button(self.khung_phu, text="Xuất CSV…", command=self._xuat_csv).pack(side="left", padx=2)

    def lay_dong(self, tu_khoa):
        sv = self.app.service
        for hv in sorted(sv.hoc_vien.values(), key=lambda h: h.ma):
            if khop(tu_khoa, hv.ma, hv.ho_ten, hv.sdt, hv.email):
                so_lop = sum(1 for dk in sv.dang_ky.values() if dk.ma_hv == hv.ma)
                yield hv.ma, (hv.ma, hv.ho_ten, format_date(hv.ngay_sinh), hv.sdt, hv.email, so_lop)

    def nap_form(self, ma):
        hv = self.app.service.lay_hoc_vien(ma)
        return {"ma": hv.ma, "ho_ten": hv.ho_ten, "ngay_sinh": format_date(hv.ngay_sinh),
                "sdt": hv.sdt, "email": hv.email}

    def tao_doi_tuong(self, f, ma):
        return HocVien(ma, f["ho_ten"], f["ngay_sinh"], f["sdt"], f["email"])

    def ma_moi(self):
        return self.app.service.ma_hoc_vien_moi()

    def them(self, doi_tuong):
        self.app.service.them_hoc_vien(doi_tuong)

    def cap_nhat(self, doi_tuong):
        self.app.service.cap_nhat_hoc_vien(doi_tuong)

    def xoa(self, ma):
        self.app.service.xoa_hoc_vien(ma)

    def _nhap_csv(self):
        duong_dan = filedialog.askopenfilename(title="Chọn file CSV học viên",
                                               filetypes=[("CSV", "*.csv"), ("Tất cả", "*.*")])
        if not duong_dan:
            return

        def tac_vu():
            ok, loi = storage.nhap_hoc_vien_csv(self.app.service, duong_dan)
            if loi:
                messagebox.showwarning("Một số dòng bị bỏ qua",
                                       f"Nhập thành công {ok} dòng.\n\n" + "\n".join(loi[:15]))
            return f"Nhập CSV: {ok} thành công, {len(loi)} lỗi"
        self.app.thuc_hien(tac_vu)

    def _xuat_csv(self):
        duong_dan = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="hoc_vien.csv",
                                                 filetypes=[("CSV", "*.csv")])
        if duong_dan:
            self.app.thuc_hien(lambda: (storage.xuat_hoc_vien_csv(self.app.service, duong_dan),
                                        f"Đã xuất {duong_dan}")[1], luu=False)


class GiaoVienTab(CrudTab):
    TIEU_DE_FORM = "Giáo viên"

    def __init__(self, master, app):
        super().__init__(master, app,
                         [("ma", "Mã", 70), ("ho_ten", "Họ tên", 160), ("ngay_sinh", "Ngày sinh", 90),
                          ("sdt", "Điện thoại", 100), ("chuyen_mon", "Chuyên môn", 110),
                          ("luong_gio", "Lương/giờ", 90), ("so_lop", "Số lớp", 55)],
                         [Truong("ma", "Mã", chi_doc=True), Truong("ho_ten", "Họ tên"),
                          Truong("ngay_sinh", "Ngày sinh", "date", "01/01/1990"),
                          Truong("sdt", "Điện thoại"), Truong("email", "Email"),
                          Truong("chuyen_mon", "Chuyên môn"), Truong("luong_gio", "Lương/giờ (đ)", gia_tri="0")])

    def lay_dong(self, tu_khoa):
        sv = self.app.service
        for gv in sorted(sv.giao_vien.values(), key=lambda g: g.ma):
            if khop(tu_khoa, gv.ma, gv.ho_ten, gv.sdt, gv.chuyen_mon):
                so_lop = sum(1 for lop in sv.lop_hoc.values() if lop.ma_gv == gv.ma)
                yield gv.ma, (gv.ma, gv.ho_ten, format_date(gv.ngay_sinh), gv.sdt, gv.chuyen_mon,
                              dinh_dang_tien(gv.luong_gio), so_lop)

    def nap_form(self, ma):
        gv = self.app.service.lay_giao_vien(ma)
        d = gv.to_dict()
        d["luong_gio"] = f"{gv.luong_gio:.0f}"
        return d

    def tao_doi_tuong(self, f, ma):
        return GiaoVien(ma, f["ho_ten"], f["ngay_sinh"], f["sdt"], f["email"],
                        f["chuyen_mon"], f["luong_gio"] or 0)

    def ma_moi(self):
        return self.app.service.ma_giao_vien_moi()

    def them(self, doi_tuong):
        self.app.service.them_giao_vien(doi_tuong)

    def cap_nhat(self, doi_tuong):
        self.app.service.cap_nhat_giao_vien(doi_tuong)

    def xoa(self, ma):
        self.app.service.xoa_giao_vien(ma)


class KhoaHocTab(CrudTab):
    TIEU_DE_FORM = "Khóa học"

    def __init__(self, master, app):
        super().__init__(master, app,
                         [("ma", "Mã", 70), ("ten", "Tên khóa", 170), ("loai", "Loại", 80),
                          ("so_buoi", "Số buổi", 60), ("hoc_phi_co_ban", "Học phí cơ bản", 105),
                          ("hoc_phi", "Học phí thực", 105), ("phu_phi", "Cách tính phụ phí", 210)],
                         [Truong("ma", "Mã", chi_doc=True), Truong("ten", "Tên khóa"),
                          Truong("loai", "Loại khóa", "combo", "Cơ bản", danh_sach=list(KHOA_THEO_LOAI)),
                          Truong("so_buoi", "Số buổi", gia_tri="30"),
                          Truong("hoc_phi_co_ban", "Học phí cơ bản (đ)", gia_tri="3000000"),
                          Truong("phu_phi", "Phụ phí tài liệu/thi thử (đ)", gia_tri="0"),
                          Truong("chung_chi", "Chứng chỉ (luyện thi)", "combo", "IELTS", danh_sach=CHUNG_CHI)])

    def lay_dong(self, tu_khoa):
        for k in sorted(self.app.service.khoa_hoc.values(), key=lambda x: x.ma):
            if khop(tu_khoa, k.ma, k.ten, k.LOAI):
                # k.tinh_hoc_phi() và k.mo_ta_phu_phi() là lời gọi đa hình theo loại khóa
                yield k.ma, (k.ma, k.ten, k.LOAI, k.so_buoi, dinh_dang_tien(k.hoc_phi_co_ban),
                             dinh_dang_tien(k.tinh_hoc_phi()), k.mo_ta_phu_phi())

    def nap_form(self, ma):
        k = self.app.service.lay_khoa(ma)
        return {"ma": k.ma, "ten": k.ten, "loai": k.LOAI, "so_buoi": k.so_buoi,
                "hoc_phi_co_ban": f"{k.hoc_phi_co_ban:.0f}", "phu_phi": f"{k.phu_phi:.0f}",
                "chung_chi": getattr(k, "chung_chi", "IELTS")}

    def tao_doi_tuong(self, f, ma):
        return tao_khoa(f["loai"], ma, f["ten"], f["so_buoi"], f["hoc_phi_co_ban"],
                        f["phu_phi"] or 0, f["chung_chi"])

    def ma_moi(self):
        return self.app.service.ma_khoa_moi()

    def them(self, doi_tuong):
        self.app.service.them_khoa(doi_tuong)

    def cap_nhat(self, doi_tuong):
        self.app.service.cap_nhat_khoa(doi_tuong)

    def xoa(self, ma):
        self.app.service.xoa_khoa(ma)


class LopHocTab(CrudTab):
    TIEU_DE_FORM = "Lớp học"

    def __init__(self, master, app):
        super().__init__(master, app,
                         [("ma", "Mã", 60), ("ten", "Tên lớp", 170), ("khoa", "Khóa học", 150),
                          ("gv", "Giáo viên", 120), ("si_so", "Sĩ số", 60),
                          ("khai_giang", "Khai giảng", 85), ("lich", "Lịch học", 170)],
                         [Truong("ma", "Mã", chi_doc=True), Truong("ten", "Tên lớp"),
                          Truong("khoa", "Khóa học", "combo"), Truong("giao_vien", "Giáo viên", "combo"),
                          Truong("si_so_toi_da", "Sĩ số tối đa", gia_tri="10"),
                          Truong("ngay_khai_giang", "Ngày khai giảng", "date"),
                          Truong("lich_hoc", "Lịch học")])

    def cap_nhat_combo(self):
        sv = self.app.service
        self.combo["khoa"]["values"] = [nhan_doi_tuong(k) for k in sorted(sv.khoa_hoc.values(), key=lambda x: x.ma)]
        self.combo["giao_vien"]["values"] = [nhan_doi_tuong(g) for g in sorted(sv.giao_vien.values(), key=lambda x: x.ma)]

    def lay_dong(self, tu_khoa):
        sv = self.app.service
        for lop in sorted(sv.lop_hoc.values(), key=lambda x: x.ma):
            khoa, gv = sv.khoa_hoc.get(lop.ma_khoa), sv.giao_vien.get(lop.ma_gv)
            ten_khoa, ten_gv = (khoa.ten if khoa else "?"), (gv.ho_ten if gv else "?")
            if khop(tu_khoa, lop.ma, lop.ten, ten_khoa, ten_gv):
                yield lop.ma, (lop.ma, lop.ten, ten_khoa, ten_gv, f"{sv.si_so(lop.ma)}/{lop.si_so_toi_da}",
                               format_date(lop.ngay_khai_giang), lop.lich_hoc)

    def nap_form(self, ma):
        sv = self.app.service
        lop = sv.lay_lop(ma)
        return {"ma": lop.ma, "ten": lop.ten, "khoa": nhan_doi_tuong(sv.lay_khoa(lop.ma_khoa)),
                "giao_vien": nhan_doi_tuong(sv.lay_giao_vien(lop.ma_gv)),
                "si_so_toi_da": lop.si_so_toi_da, "ngay_khai_giang": format_date(lop.ngay_khai_giang),
                "lich_hoc": lop.lich_hoc}

    def tao_doi_tuong(self, f, ma):
        return LopHoc(ma, f["ten"], lay_ma(f["khoa"]), lay_ma(f["giao_vien"]),
                      f["si_so_toi_da"], f["ngay_khai_giang"], f["lich_hoc"])

    def ma_moi(self):
        return self.app.service.ma_lop_moi()

    def them(self, doi_tuong):
        self.app.service.them_lop(doi_tuong)

    def cap_nhat(self, doi_tuong):
        self.app.service.cap_nhat_lop(doi_tuong)

    def xoa(self, ma):
        self.app.service.xoa_lop(ma)


class DangKyTab(ttk.Frame):
    """Đăng ký lớp (kiểm tra sĩ số) và theo dõi học phí, công nợ."""

    def __init__(self, master, app):
        super().__init__(master, padding=8)
        self.app = app
        dk = ttk.LabelFrame(self, text="Đăng ký học viên vào lớp", padding=8)
        dk.pack(fill="x")
        self.hv_var, self.lop_var, self.giam_var = tk.StringVar(), tk.StringVar(), tk.StringVar(value="0")
        ttk.Label(dk, text="Học viên:").grid(row=0, column=0, sticky="w")
        self.cb_hv = ttk.Combobox(dk, textvariable=self.hv_var, width=30, state="readonly")
        self.cb_hv.grid(row=0, column=1, padx=6)
        ttk.Label(dk, text="Lớp:").grid(row=0, column=2, sticky="w")
        self.cb_lop = ttk.Combobox(dk, textvariable=self.lop_var, width=38, state="readonly")
        self.cb_lop.grid(row=0, column=3, padx=6)
        ttk.Label(dk, text="Giảm giá (%):").grid(row=0, column=4, sticky="w")
        ttk.Entry(dk, textvariable=self.giam_var, width=5).grid(row=0, column=5, padx=6)
        ttk.Label(dk, text="Ngày:").grid(row=0, column=6, sticky="w")
        self.ngay_dk = DateEntry(dk)
        self.ngay_dk.grid(row=0, column=7, padx=6)
        ttk.Button(dk, text="Đăng ký", command=self._dang_ky).grid(row=0, column=8, padx=4)
        ttk.Button(dk, text="Hủy đăng ký", command=self._huy).grid(row=0, column=9, padx=4)

        cot = [("ma", "Mã ĐK", 70), ("hv", "Học viên", 160), ("lop", "Lớp", 160), ("hoc_phi", "Học phí", 95),
               ("giam", "Giảm", 50), ("phai_dong", "Phải đóng", 95), ("da_dong", "Đã đóng", 95),
               ("cong_no", "Công nợ", 95), ("tt", "Trạng thái", 80)]
        khung = ttk.Frame(self)
        khung.pack(fill="both", expand=True, pady=8)
        self.tree = ttk.Treeview(khung, columns=[c[0] for c in cot], show="headings", selectmode="browse")
        for ma_cot, tieu_de, rong in cot:
            self.tree.heading(ma_cot, text=tieu_de)
            self.tree.column(ma_cot, width=rong, anchor="w")
        self.tree.tag_configure("no", foreground="#b71c1c")
        thanh = ttk.Scrollbar(khung, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=thanh.set)
        self.tree.pack(side="left", fill="both", expand=True)
        thanh.pack(side="left", fill="y")

        hp = ttk.LabelFrame(self, text="Thu học phí / công nợ", padding=8)
        hp.pack(fill="x")
        self.tien_var, self.chi_no = tk.StringVar(), tk.BooleanVar(value=False)
        ttk.Label(hp, text="Số tiền nộp (đ):").pack(side="left")
        ttk.Entry(hp, textvariable=self.tien_var, width=14).pack(side="left", padx=6)
        ttk.Label(hp, text="Ngày nộp:").pack(side="left")
        self.ngay_nop = DateEntry(hp)
        self.ngay_nop.pack(side="left", padx=6)
        ttk.Button(hp, text="Thu học phí", command=self._thu).pack(side="left", padx=4)
        ttk.Checkbutton(hp, text="Chỉ hiện còn nợ", variable=self.chi_no,
                        command=self.lam_moi).pack(side="left", padx=12)
        ttk.Button(hp, text="Xuất công nợ CSV…", command=self._xuat_cong_no).pack(side="left", padx=4)
        self.tong_no = ttk.Label(hp, text="", foreground="#b71c1c")
        self.tong_no.pack(side="right")

    def lam_moi(self):
        sv = self.app.service
        self.cb_hv["values"] = [nhan_doi_tuong(h) for h in sorted(sv.hoc_vien.values(), key=lambda x: x.ma)]
        self.cb_lop["values"] = [f"{nhan_doi_tuong(l)} ({sv.si_so(l.ma)}/{l.si_so_toi_da})"
                                 for l in sorted(sv.lop_hoc.values(), key=lambda x: x.ma)]
        dang_chon = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for dk in sorted(sv.dang_ky.values(), key=lambda x: x.ma):
            if self.chi_no.get() and dk.cong_no <= 0:
                continue
            hv, lop = sv.hoc_vien.get(dk.ma_hv), sv.lop_hoc.get(dk.ma_lop)
            self.tree.insert("", "end", iid=dk.ma, tags=("no",) if dk.cong_no > 0 else (), values=(
                dk.ma, hv.ho_ten if hv else dk.ma_hv, lop.ten if lop else dk.ma_lop,
                dinh_dang_tien(dk.hoc_phi), f"{dk.giam_gia:g}%", dinh_dang_tien(dk.phai_dong),
                dinh_dang_tien(dk.da_dong), dinh_dang_tien(dk.cong_no),
                "Còn nợ" if dk.cong_no > 0 else "Đã đủ"))
        if dang_chon and self.tree.exists(dang_chon[0]):
            self.tree.selection_set(dang_chon[0])
        self.tong_no.config(text=f"Tổng công nợ: {dinh_dang_tien(sv.tong_quan()['cong_no'])}")

    def _ma_dk_chon(self):
        sel = self.tree.selection()
        if not sel:
            raise RangBuocError("Hãy chọn một đăng ký trong bảng.")
        return sel[0]

    def _dang_ky(self):
        def tac_vu():
            ngay = self.ngay_dk.get_date()
            giam = chuyen_so(self.giam_var.get() or 0, "Giảm giá (%)", float, 0, 100)
            dk = self.app.service.dang_ky_lop(lay_ma(self.hv_var.get()), lay_ma(self.lop_var.get()), giam, ngay)
            return f"Đã đăng ký {dk.ma}, học phí phải đóng {dinh_dang_tien(dk.phai_dong)}"
        self.app.thuc_hien(tac_vu)

    def _huy(self):
        def tac_vu():
            ma = self._ma_dk_chon()
            self.app.service.huy_dang_ky(ma)
            return f"Đã hủy đăng ký {ma}"
        self.app.thuc_hien(tac_vu)

    def _thu(self):
        def tac_vu():
            ma = self._ma_dk_chon()
            self.app.service.thu_hoc_phi(ma, self.tien_var.get(), self.ngay_nop.get_date())
            self.tien_var.set("")
            return f"Đã thu học phí cho {ma}"
        self.app.thuc_hien(tac_vu)

    def _xuat_cong_no(self):
        duong_dan = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="cong_no.csv",
                                                 filetypes=[("CSV", "*.csv")])
        if not duong_dan:
            return
        sv = self.app.service

        def tac_vu():
            dong = [[dk.ma, dk.ma_hv, sv.hoc_vien[dk.ma_hv].ho_ten, dk.ma_lop, dk.phai_dong, dk.da_dong, dk.cong_no]
                    for dk in sv.danh_sach_cong_no()]
            storage.xuat_csv(duong_dan, ["ma_dk", "ma_hv", "ho_ten", "ma_lop", "phai_dong", "da_dong", "cong_no"], dong)
            return f"Đã xuất {len(dong)} dòng công nợ"
        self.app.thuc_hien(tac_vu, luu=False)


class DiemTab(ttk.Frame):
    """Nhập điểm, xếp loại, GradeBadge, biểu đồ Canvas và xuất chứng nhận."""

    def __init__(self, master, app):
        super().__init__(master, padding=8)
        self.app = app
        trai = ttk.Frame(self)
        trai.pack(side="left", fill="both", expand=True)
        dau = ttk.Frame(trai)
        dau.pack(fill="x")
        ttk.Label(dau, text="Chọn lớp:").pack(side="left")
        self.lop_var = tk.StringVar()
        self.cb_lop = ttk.Combobox(dau, textvariable=self.lop_var, width=45, state="readonly")
        self.cb_lop.pack(side="left", padx=6)
        self.cb_lop.bind("<<ComboboxSelected>>", lambda _e: self.lam_moi())

        cot = [("ma", "Mã ĐK", 70), ("hv", "Học viên", 160), ("gk", "Giữa kỳ (40%)", 90),
               ("ck", "Cuối kỳ (60%)", 90), ("tk", "Tổng kết", 70), ("xl", "Xếp loại", 90)]
        khung = ttk.Frame(trai)
        khung.pack(fill="both", expand=True, pady=8)
        self.tree = ttk.Treeview(khung, columns=[c[0] for c in cot], show="headings", selectmode="browse")
        for ma_cot, tieu_de, rong in cot:
            self.tree.heading(ma_cot, text=tieu_de)
            self.tree.column(ma_cot, width=rong, anchor="w")
        thanh = ttk.Scrollbar(khung, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=thanh.set)
        self.tree.pack(side="left", fill="both", expand=True)
        thanh.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._khi_chon)

        form = ttk.LabelFrame(trai, text="Nhập điểm (thang 10)", padding=8)
        form.pack(fill="x")
        self.gk_var, self.ck_var = tk.StringVar(), tk.StringVar()
        ttk.Label(form, text="Giữa kỳ:").pack(side="left")
        ttk.Entry(form, textvariable=self.gk_var, width=7).pack(side="left", padx=6)
        ttk.Label(form, text="Cuối kỳ:").pack(side="left")
        ttk.Entry(form, textvariable=self.ck_var, width=7).pack(side="left", padx=6)
        ttk.Button(form, text="Lưu điểm", command=self._luu_diem).pack(side="left", padx=6)
        ttk.Button(form, text="Xuất chứng nhận", command=self._xuat_chung_nhan).pack(side="left", padx=6)
        self.badge = GradeBadge(form)
        self.badge.pack(side="right")

        phai = ttk.Frame(self)
        phai.pack(side="right", fill="both", padx=(10, 0))
        self.bd_phan_bo = BieuDoCot(phai, "Phân bố xếp loại của lớp", width=360)
        self.bd_phan_bo.pack(fill="both", expand=True, pady=(0, 8))
        self.bd_diem = BieuDoCot(phai, "Điểm tổng kết từng học viên", gia_tri_toi_da=10, width=360)
        self.bd_diem.pack(fill="both", expand=True)

    def lam_moi(self):
        sv = self.app.service
        self.cb_lop["values"] = [nhan_doi_tuong(l) for l in sorted(sv.lop_hoc.values(), key=lambda x: x.ma)]
        dang_chon = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        ma_lop = lay_ma(self.lop_var.get())
        ds = sorted(sv.dang_ky_cua_lop(ma_lop), key=lambda x: x.ma) if ma_lop in sv.lop_hoc else []
        nhan_bd, diem_bd = [], []
        for dk in ds:
            hv = sv.hoc_vien.get(dk.ma_hv)
            ten = hv.ho_ten if hv else dk.ma_hv
            tk_ = dk.diem_tong_ket
            self.tree.insert("", "end", iid=dk.ma, values=(
                dk.ma, ten, "" if dk.diem_gk is None else dk.diem_gk,
                "" if dk.diem_ck is None else dk.diem_ck, "" if tk_ is None else f"{tk_:.2f}", dk.xep_loai))
            if tk_ is not None:
                nhan_bd.append(ten.split()[-1])
                diem_bd.append(tk_)
        if dang_chon and self.tree.exists(dang_chon[0]):
            self.tree.selection_set(dang_chon[0])
        phan_bo = sv.phan_bo_xep_loai(ds)
        self.bd_phan_bo.dat_du_lieu(NHAN_XEP_LOAI, [phan_bo[n] for n in NHAN_XEP_LOAI])
        self.bd_diem.dat_du_lieu(nhan_bd, diem_bd)

    def _khi_chon(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        dk = self.app.service.lay_dang_ky(sel[0])
        self.gk_var.set("" if dk.diem_gk is None else dk.diem_gk)
        self.ck_var.set("" if dk.diem_ck is None else dk.diem_ck)
        self.badge.dat_xep_loai(dk.xep_loai, dk.diem_tong_ket)

    def _ma_dk_chon(self):
        sel = self.tree.selection()
        if not sel:
            raise RangBuocError("Hãy chọn một học viên trong bảng.")
        return sel[0]

    def _luu_diem(self):
        def tac_vu():
            ma = self._ma_dk_chon()
            self.app.service.nhap_diem(ma, self.gk_var.get(), self.ck_var.get())
            dk = self.app.service.lay_dang_ky(ma)
            self.badge.dat_xep_loai(dk.xep_loai, dk.diem_tong_ket)
            return f"Đã lưu điểm {ma}: {dk.xep_loai}"
        self.app.thuc_hien(tac_vu)

    def _xuat_chung_nhan(self):
        def tac_vu():
            duong_dan = self.app.service.xuat_chung_nhan(
                self._ma_dk_chon(), os.path.join(self.app.thu_muc_du_lieu, "chung_nhan"))
            messagebox.showinfo("Chứng nhận", f"Đã xuất chứng nhận:\n{duong_dan}\n\nMở file bằng trình duyệt để in.")
            return f"Đã xuất {duong_dan}"
        self.app.thuc_hien(tac_vu, luu=False)


class ThongKeTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=8)
        self.app = app
        self.tong_quan = ttk.Label(self, font=("Segoe UI", 10, "bold"))
        self.tong_quan.pack(anchor="w")
        giua = ttk.Frame(self)
        giua.pack(fill="both", expand=True, pady=8)
        trai = ttk.Frame(giua)
        trai.pack(side="left", fill="both", expand=True)
        ttk.Label(trai, text="Thống kê theo lớp").pack(anchor="w")
        cot_lop = [("ma", "Lớp", 60), ("ten", "Tên lớp", 150), ("si_so", "Sĩ số", 60), ("ty_le", "Lấp đầy", 65),
                   ("tb", "Điểm TB", 65), ("dat", "Đạt", 45), ("phai", "Phải thu", 95), ("da", "Đã thu", 95),
                   ("no", "Công nợ", 95)]
        self.tree_lop = self._tao_tree(trai, cot_lop)
        ttk.Label(trai, text="Doanh thu theo khóa học").pack(anchor="w", pady=(8, 0))
        cot_khoa = [("ma", "Khóa", 60), ("ten", "Tên khóa", 170), ("so_hv", "Lượt ĐK", 65),
                    ("phai", "Phải thu", 105), ("da", "Đã thu", 105), ("no", "Công nợ", 105)]
        self.tree_khoa = self._tao_tree(trai, cot_khoa)
        phai = ttk.Frame(giua)
        phai.pack(side="right", fill="both", padx=(10, 0))
        self.bieu_do = BieuDoCot(phai, "Phân bố xếp loại toàn trung tâm", width=340)
        self.bieu_do.pack(fill="both", expand=True)
        ttk.Button(phai, text="Xuất thống kê lớp CSV…", command=self._xuat).pack(pady=6)

    @staticmethod
    def _tao_tree(cha, cot):
        t = ttk.Treeview(cha, columns=[c[0] for c in cot], show="headings", height=7)
        for ma_cot, tieu_de, rong in cot:
            t.heading(ma_cot, text=tieu_de)
            t.column(ma_cot, width=rong, anchor="w")
        t.pack(fill="both", expand=True)
        return t

    def _dong_lop(self):
        sv = self.app.service
        for ma in sorted(sv.lop_hoc):
            tk_ = sv.thong_ke_lop(ma)
            yield (tk_["ma"], tk_["ten"], f"{tk_['si_so']}/{tk_['toi_da']}", f"{tk_['ty_le_lap_day']:.0f}%",
                   "" if tk_["diem_tb"] is None else f"{tk_['diem_tb']:.2f}", tk_["so_dat"],
                   tk_["phai_thu"], tk_["da_thu"], tk_["cong_no"])

    def lam_moi(self):
        sv = self.app.service
        tq = sv.tong_quan()
        self.tong_quan.config(text=(
            f"{TEN_TRUNG_TAM}: {tq['hoc_vien']} học viên | {tq['giao_vien']} giáo viên | {tq['khoa_hoc']} khóa | "
            f"{tq['lop_hoc']} lớp | {tq['dang_ky']} lượt đăng ký | Đã thu {dinh_dang_tien(tq['da_thu'])} | "
            f"Công nợ {dinh_dang_tien(tq['cong_no'])}"))
        self.tree_lop.delete(*self.tree_lop.get_children())
        for d in self._dong_lop():
            hien_thi = d[:6] + tuple(dinh_dang_tien(x) for x in d[6:])
            self.tree_lop.insert("", "end", values=hien_thi)
        self.tree_khoa.delete(*self.tree_khoa.get_children())
        for d in sv.doanh_thu_theo_khoa().values():
            self.tree_khoa.insert("", "end", values=(
                d["ma"], d["ten"], d["so_hv"], dinh_dang_tien(d["phai_thu"]),
                dinh_dang_tien(d["da_thu"]), dinh_dang_tien(d["cong_no"])))
        phan_bo = sv.phan_bo_xep_loai(sv.dang_ky.values())
        self.bieu_do.dat_du_lieu(NHAN_XEP_LOAI, [phan_bo[n] for n in NHAN_XEP_LOAI])

    def _xuat(self):
        duong_dan = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="thong_ke_lop.csv",
                                                 filetypes=[("CSV", "*.csv")])
        if duong_dan:
            def tac_vu():
                dong = list(self._dong_lop())
                storage.xuat_csv(duong_dan, ["lop", "ten", "si_so", "lap_day", "diem_tb", "dat",
                                             "phai_thu", "da_thu", "cong_no"], dong)
                return f"Đã xuất {len(dong)} lớp"
            self.app.thuc_hien(tac_vu, luu=False)


class UngDung(tk.Tk):
    def __init__(self, duong_dan_du_lieu):
        super().__init__()
        self.title(f"Quản lý {TEN_TRUNG_TAM}")
        self.geometry("1280x720")
        self.minsize(1000, 600)
        self.duong_dan = duong_dan_du_lieu
        self.thu_muc_du_lieu = os.path.dirname(os.path.abspath(duong_dan_du_lieu))
        self.service, canh_bao = storage.nap_service(duong_dan_du_lieu)
        self.trang_thai = tk.StringVar(value=f"Dữ liệu: {duong_dan_du_lieu}")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)
        self.tabs = []
        for ten, lop in (("Học viên", HocVienTab), ("Giáo viên", GiaoVienTab), ("Khóa học", KhoaHocTab),
                         ("Lớp học", LopHocTab), ("Đăng ký & Học phí", DangKyTab),
                         ("Điểm & Xếp loại", DiemTab), ("Thống kê", ThongKeTab)):
            tab = lop(self.notebook, self)
            self.notebook.add(tab, text=ten)
            self.tabs.append(tab)
        ttk.Label(self, textvariable=self.trang_thai, relief="sunken", anchor="w").pack(fill="x", side="bottom")
        self.notebook.bind("<<NotebookTabChanged>>", lambda _e: self.lam_moi_tat_ca())
        self.protocol("WM_DELETE_WINDOW", self.thoat)
        self.lam_moi_tat_ca()
        if canh_bao:
            self.after(300, lambda: messagebox.showwarning(
                "Cảnh báo khi nạp dữ liệu", "\n".join(canh_bao[:15]) + "\n\nChi tiết xem file error.log."))

    def lam_moi_tat_ca(self):
        for tab in self.tabs:
            tab.lam_moi()

    def thuc_hien(self, tac_vu, luu=True):
        """Chạy một tác vụ nghiệp vụ, bắt mọi ngoại lệ, tự lưu và làm mới giao diện khi thành công."""
        try:
            thong_bao = tac_vu()
            if luu:
                storage.luu_service(self.service, self.duong_dan)
            self.lam_moi_tat_ca()
            self.trang_thai.set(thong_bao)
        except TrungTamError as loi:
            self.trang_thai.set(f"Lỗi: {loi}")
            messagebox.showerror("Không thực hiện được", str(loi))
        except Exception as loi:  # noqa: BLE001 - lưới an toàn cuối cùng, vẫn ghi log
            ghi_log("LOI_KHONG_XAC_DINH", f"{type(loi).__name__}: {loi}")
            messagebox.showerror("Lỗi không xác định", f"{type(loi).__name__}: {loi}\n(Đã ghi vào error.log)")

    def thoat(self):
        try:
            storage.luu_service(self.service, self.duong_dan)
        except TrungTamError as loi:
            if not messagebox.askyesno("Lỗi lưu dữ liệu", f"{loi}\n\nVẫn thoát?"):
                return
        self.destroy()
