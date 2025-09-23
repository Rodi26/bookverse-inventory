

import math
from typing import Any, List, Tuple, TypeVar

from sqlalchemy.orm import Query
from pydantic import BaseModel

T = TypeVar('T')


class PaginationMeta(BaseModel):

    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


def create_pagination_meta(
        total: int,
        page: int,
        per_page: int) -> PaginationMeta:

    pages = max(1, math.ceil(total / per_page))

    return PaginationMeta(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


def paginate_query(
    query: Query,
    page: int = 1,
    per_page: int = 20
) -> Tuple[List[Any], PaginationMeta]:

    page = max(1, page)
    per_page = max(1, min(per_page, 100))

    total = query.count()

    offset = (page - 1) * per_page

    items = query.offset(offset).limit(per_page).all()

    pagination = create_pagination_meta(
        total=total,
        page=page,
        per_page=per_page
    )

    return items, pagination


def validate_pagination_params(page: int, per_page: int) -> Tuple[int, int]:

    if page < 1:
        raise ValueError(
            f"Page number must be 1 or greater. Got: {page}. "
            "Demo tip: Page numbers are 1-based, not 0-based."
        )

    if per_page < 1:
        raise ValueError(
            f"Items per page must be 1 or greater. Got: {per_page}"
        )

    if per_page > 100:
        raise ValueError(
            f"Items per page cannot exceed 100 for demo purposes. Got: {per_page}. "
            "Demo tip: Large page sizes can impact performance.")

    return page, per_page


class PaginationHelper:

    def __init__(self, default_per_page: int = 20, max_per_page: int = 100):

        self.default_per_page = default_per_page
        self.max_per_page = max_per_page

    def paginate(
        self,
        query: Query,
        page: int = 1,
        per_page: int = None
    ) -> Tuple[List[Any], PaginationMeta]:

        if per_page is None:
            per_page = self.default_per_page

        per_page = min(per_page, self.max_per_page)

        return paginate_query(query, page, per_page)

    def get_page_info(
            self,
            total: int,
            page: int,
            per_page: int = None) -> PaginationMeta:

        if per_page is None:
            per_page = self.default_per_page

        per_page = min(per_page, self.max_per_page)

        return create_pagination_meta(total, page, per_page)
