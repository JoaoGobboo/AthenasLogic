from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from flask import Response, current_app, g, jsonify, request

from services.session_service import SessionStore

F = TypeVar("F", bound=Callable[..., Any])
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_SESSION_STORE_KEY = "session_store"


def get_session_store() -> SessionStore:
    store = current_app.extensions.get(_SESSION_STORE_KEY)
    if store is None:
        store = SessionStore()
        current_app.extensions[_SESSION_STORE_KEY] = store
    return store


def extract_bearer_token() -> str | None:
    header = request.headers.get("Authorization")
    if not header:
        return None
    if not header.lower().startswith("bearer "):
        return None
    token = header.split(" ", 1)[1].strip()
    return token or None


def require_auth(*, csrf: bool = True, role: str | None = None) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Response:
            token = extract_bearer_token()
            if not token:
                return jsonify({"error": "Missing bearer token"}), 401

            store = get_session_store()
            resolved = store.resolve(token)
            if resolved is None:
                return jsonify({"error": "Unauthorized"}), 401

            if csrf and request.method in _MUTATING_METHODS:
                header_token = request.headers.get("X-CSRF-Token")
                if not header_token or header_token != resolved.csrf_token:
                    return jsonify({"error": "Invalid CSRF token"}), 403

            if role is not None:
                user_role = getattr(resolved.user, "role", None)
                if user_role != role:
                    return jsonify({"error": "Forbidden"}), 403

            g.current_session = resolved
            g.current_user = resolved.user
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = ["extract_bearer_token", "get_session_store", "require_auth"]
