"""Widget tự xây dựng: DateEntry (chọn ngày), GradeBadge (huy hiệu xếp loại), BieuDoCot (biểu đồ Canvas)."""
import calendar
import math
import tkinter as tk
from datetime import date
from tkinter import ttk

from exceptions import DuLieuKhongHopLeError
from utils import format_date, parse_date


class DateEntry(ttk.Frame):
    """Ô nhập ngày dd/mm/yyyy kèm nút mở lịch chọn ngày (không phụ thuộc thư viện ngoài)."""

    def __init__(self, master, value=None, width=12):
        super().__init__(master)
        self._var = tk.StringVar(value=format_date(value) if value else format_date(date.today()))
        ttk.Entry(self, textvariable=self._var, width=width).pack(side="left")
        ttk.Button(self, text="▾", width=3, command=self._mo_lich).pack(side="left", padx=(2, 0))

    def get(self):
        return self._var.get().strip()

    def get_date(self):
        return parse_date(self.get())

    def set(self, value):
        self._var.set(format_date(value) if value else "")

    def _mo_lich(self):
        try:
            hien_tai = self.get_date()
        except DuLieuKhongHopLeError:
            hien_tai = date.today()
        _LichChon(self, hien_tai, self.set)


class _LichChon(tk.Toplevel):
    def __init__(self, master, ngay, callback):
        super().__init__(master)
        self.title("Chọn ngày")
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self._nam, self._thang, self._callback = ngay.year, ngay.month, callback
        dau = ttk.Frame(self)
        dau.pack(fill="x", padx=6, pady=6)
        ttk.Button(dau, text="◀", width=3, command=lambda: self._doi_thang(-1)).pack(side="left")
        self._nhan = ttk.Label(dau, anchor="center", width=16)
        self._nhan.pack(side="left", expand=True)
        ttk.Button(dau, text="▶", width=3, command=lambda: self._doi_thang(1)).pack(side="left")
        self._luoi = ttk.Frame(self)
        self._luoi.pack(padx=6, pady=(0, 6))
        self._ve()

    def _doi_thang(self, d):
        thang = self._thang + d
        if thang > 12:
            self._nam, thang = self._nam + 1, 1
        elif thang < 1:
            self._nam, thang = self._nam - 1, 12
        self._thang = thang
        self._ve()

    def _ve(self):
        for w in self._luoi.winfo_children():
            w.destroy()
        self._nhan.config(text=f"Tháng {self._thang}/{self._nam}")
        for c, t in enumerate(["T2", "T3", "T4", "T5", "T6", "T7", "CN"]):
            ttk.Label(self._luoi, text=t, width=4, anchor="center").grid(row=0, column=c)
        for r, tuan in enumerate(calendar.monthcalendar(self._nam, self._thang), start=1):
            for c, ngay in enumerate(tuan):
                if ngay:
                    ttk.Button(self._luoi, text=str(ngay), width=4,
                               command=lambda n=ngay: self._chon(n)).grid(row=r, column=c)

    def _chon(self, ngay):
        self._callback(date(self._nam, self._thang, ngay))
        self.destroy()



class GradeBadge(tk.Canvas):
    """Huy hiệu xếp loại bo tròn, đổi màu theo xếp loại."""
    MAU = {
        "Giỏi": "#2e7d32",
        "Khá": "#1565c0",
        "Trung bình": "#ef6c00",
        "Yếu": "#c62828",
        "Chưa có điểm": "#9e9e9e"
    }

    def __init__(self, master, width=190, height=40):
        super().__init__(
            master,
            width=width,
            height=height,
            highlightthickness=0
        )

        # Không sử dụng self._w vì Tkinter đã dùng tên này
        self._rong = width
        self._cao = height

        self.dat_xep_loai("Chưa có điểm", None)

    def dat_xep_loai(self, xep_loai, diem=None):
        self.delete("all")

        mau = self.MAU.get(
            xep_loai,
            self.MAU["Chưa có điểm"]
        )

        w, h = self._rong, self._cao

        self.create_oval(
            2, 2, h - 2, h - 2,
            fill=mau, outline=mau
        )

        self.create_oval(
            w - h + 2, 2, w - 2, h - 2,
            fill=mau, outline=mau
        )

        self.create_rectangle(
            h / 2, 2, w - h / 2, h - 2,
            fill=mau, outline=mau
        )

        chu = (
            xep_loai
            if diem is None
            else f"{xep_loai} ({diem:.2f})"
        )

        self.create_text(
            w / 2,
            h / 2,
            text=chu,
            fill="white",
            font=("Segoe UI", 11, "bold")
        )

class BieuDoCot(tk.Canvas):
    """Biểu đồ cột vẽ bằng Canvas, tự vẽ lại khi đổi kích thước cửa sổ."""

    def __init__(self, master, tieu_de="", gia_tri_toi_da=None, **kw):
        kw.setdefault("height", 210)
        kw.setdefault("bg", "white")
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", "#cccccc")
        super().__init__(master, **kw)
        self._tieu_de, self._tran = tieu_de, gia_tri_toi_da
        self._nhan, self._gia_tri = [], []
        self.bind("<Configure>", lambda _e: self.ve())

    def dat_du_lieu(self, nhan, gia_tri, tieu_de=None):
        self._nhan, self._gia_tri = list(nhan), list(gia_tri)
        if tieu_de is not None:
            self._tieu_de = tieu_de
        self.ve()

    def ve(self):
        self.delete("all")
        w, h = max(self.winfo_width(), 260), max(self.winfo_height(), 160)
        trai, phai, tren, duoi = 38, 14, 30, 34
        self.create_text(w / 2, 14, text=self._tieu_de, font=("Segoe UI", 10, "bold"))
        if not self._nhan or not any(self._gia_tri):
            self.create_text(w / 2, h / 2, text="Chưa có dữ liệu", fill="#888888")
            return
        tran = self._tran or max(1, math.ceil(max(self._gia_tri)))
        vung_w, vung_h, y_day = w - trai - phai, h - tren - duoi, h - duoi
        buoc = max(1, math.ceil(tran / 5))
        for v in range(0, int(tran) + 1, buoc):
            y = y_day - v / tran * vung_h
            self.create_line(trai, y, w - phai, y, fill="#e6e6e6")
            self.create_text(trai - 6, y, text=str(v), anchor="e", font=("Segoe UI", 8))
        self.create_line(trai, tren, trai, y_day)
        self.create_line(trai, y_day, w - phai, y_day)
        rong_o = vung_w / len(self._nhan)
        rong_cot = rong_o * 0.6
        for i, (nhan, gt) in enumerate(zip(self._nhan, self._gia_tri)):
            x0 = trai + i * rong_o + (rong_o - rong_cot) / 2
            y0 = y_day - gt / tran * vung_h
            mau = GradeBadge.MAU.get(nhan, "#4c78a8")
            self.create_rectangle(x0, y0, x0 + rong_cot, y_day, fill=mau, outline=mau)
            self.create_text(x0 + rong_cot / 2, y0 - 8, text=f"{gt:g}", font=("Segoe UI", 8, "bold"))
            self.create_text(x0 + rong_cot / 2, y_day + 12, text=nhan, font=("Segoe UI", 8))
