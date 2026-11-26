"""Hệ thống ngoại lệ riêng của ứng dụng (Buổi 8: ngoại lệ do người dùng định nghĩa)."""


class TrungTamError(Exception):
    """Lớp ngoại lệ gốc: mọi lỗi nghiệp vụ của ứng dụng đều kế thừa từ lớp này."""


class DuLieuKhongHopLeError(TrungTamError):
    """Dữ liệu nhập vào sai định dạng hoặc ngoài miền giá trị cho phép."""


class TrungMaError(TrungTamError):
    """Mã đối tượng đã tồn tại."""


class KhongTimThayError(TrungTamError):
    """Không tìm thấy đối tượng theo mã."""


class LopDayError(TrungTamError):
    """Lớp đã đủ sĩ số, không nhận thêm học viên."""


class RangBuocError(TrungTamError):
    """Vi phạm ràng buộc nghiệp vụ (xóa đối tượng đang được tham chiếu, nộp vượt công nợ, ...)."""


class FileDuLieuError(TrungTamError):
    """Lỗi đọc/ghi file dữ liệu (không tồn tại, hỏng định dạng JSON, không ghi được)."""
