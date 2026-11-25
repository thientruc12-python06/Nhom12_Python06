class HocPhiMixin:
    def thu_hoc_phi(self, ma_dk, so_tien, ngay=None):
        self.lay_dang_ky(ma_dk).nop_tien(so_tien, ngay)

    def nhap_diem(self, ma_dk, diem_gk, diem_ck):
        self.lay_dang_ky(ma_dk).nhap_diem(diem_gk, diem_ck)

    def danh_sach_cong_no(self):
        """Danh sách đăng ký còn nợ học phí, nợ nhiều xếp trước."""
        ds = [dk for dk in self.dang_ky.values() if dk.cong_no > 0]
        return sorted(ds, key=lambda dk: dk.cong_no, reverse=True)
