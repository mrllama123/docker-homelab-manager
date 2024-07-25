from fastapi import Request


def generate_paginated_list_link_header(
    request: Request,
    page: int,
    size: int,
    total_pages: int,
) -> str | None:
    next_page = page + 1 if page < total_pages else None
    url_http_prefix = "https://" if request.url.is_secure else "http://"
    url = f"{url_http_prefix}{request.url.hostname}{request.url.path}"
    if next_page:
        next_page_header = f'<{url}?page={next_page}&size={size}>; rel="next"'
        last_page_header = f'<{url}?page={total_pages}&size={size}>; rel="last"'
        prev_page_header = (
            f'<{url}?page={page - 1}&size={size}>; rel="prev"' if page > 1 else None
        )

        if prev_page_header:
            return f"{next_page_header}, {prev_page_header}, {last_page_header}"
        else:
            return f"{next_page_header}, {last_page_header}"

    else:
        return f'<{url}?page=1&size={size}>; rel="first", <{url}?page={total_pages}&size={size}>; rel="last"'
