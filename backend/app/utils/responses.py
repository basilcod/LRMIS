from typing import Any, Mapping


def success_response(
    data: Any = None,
    message: str = "OK",
    meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta is not None:
        response["meta"] = dict(meta)
    return response


def list_response(
    items: list[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "OK",
) -> dict[str, Any]:
    return success_response(
        data=items,
        message=message,
        meta={
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    )


def error_response(
    message: str,
    code: str = "error",
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": dict(details or {}),
        },
    }
