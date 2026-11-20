"""分页工具：page_size 上限 100，超出按 100 截断。"""

from app.core.config import settings


def clamp_page(page: int | None) -> int:
    page = int(page or 1)
    return page if page >= 1 else 1


def clamp_page_size(page_size: int | None) -> int:
    """page_size 默认 10，上限 100，超出按 100 截断。"""
    size = int(page_size or settings.DEFAULT_PAGE_SIZE)
    if size < 1:
        size = settings.DEFAULT_PAGE_SIZE
    if size > settings.MAX_PAGE_SIZE:
        size = settings.MAX_PAGE_SIZE
    return size


def page_offset(page: int, page_size: int) -> int:
    return (page - 1) * page_size


def normalize(page: int | None, page_size: int | None) -> tuple[int, int, int]:
    """返回 (page, page_size, offset)。"""
    p = clamp_page(page)
    s = clamp_page_size(page_size)
    return p, s, page_offset(p, s)
