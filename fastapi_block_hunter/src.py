import asyncio
import contextvars
import traceback
from asyncio import tasks
from asyncio.events import Handle

from fastapi import FastAPI
from starlette.datastructures import URL
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

current_url = contextvars.ContextVar[URL]("current_fastapi_http_url")


class Config:
    verbose: bool = False


class BlockingCallDebuggerMiddleware(BaseHTTPMiddleware):
    """Store the url being processed in the current request in a context variable.

    This middleware will register the `current_fastapi_http_url` context variable in the request scope so that when
    the `asyncio` slow callback logger is called, we can identify where the slow callback is coming from.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        current_url.set(request.url)
        return await call_next(request)


def format_source_traceback(source_traceback: list[traceback.FrameSummary]) -> str:
    summary = ""
    for frame in source_traceback:
        summary += f"{frame.filename}:{frame.lineno} - {frame.line}\n"
    return summary


def log_blocking_fastapi_code(handle: Handle, endpoint_url: URL) -> str:
    """Check if the handle comes from a FastAPI endpoint and generate log message if it does."""
    msg = f"The event loop has been blocked while processing request:\nURL: {endpoint_url}"
    cb = handle._callback  # type: ignore
    cb_self = getattr(cb, "__self__", None)

    if not isinstance(cb_self, tasks.Task) or not Config.verbose:
        return msg

    if not handle._args or not isinstance(handle._args[0], asyncio.Future):
        return msg

    future_source_traceback = handle._args[0]._source_traceback  # type: ignore

    msg += "\nThe blocking code starts at Unknown"
    msg += "\nThe blocking code ends when the following coroutine is resumed:"
    msg += f"\n{format_source_traceback(future_source_traceback)}"
    return msg


def _custom_format_handle(handle: Handle) -> str:
    cb = handle._callback  # type: ignore

    endpoint_url = handle._context.get(current_url)  # type: ignore
    if endpoint_url:
        msg = log_blocking_fastapi_code(
            handle,
            endpoint_url,
        )
        return msg

    if isinstance(getattr(cb, "__self__", None), tasks.Task):
        # format the task
        return repr(cb.__self__)
    else:
        return str(handle)


async def setup_asyncio_debug_mode(
    slow_callback_duration_threshold_seconds: float = 0.1,
    *,
    event_loop_to_patch: asyncio.AbstractEventLoop | None = None,
) -> None:
    """Set up the asyncio debug mode.

    Args:
        slow_callback_duration_threshold_seconds (float): The duration in seconds after which a
            callback is considered slow in seconds.
        set_asyncio_debug_mode (bool): Whether to set the asyncio debug mode.
        event_loop_to_patch (asyncio.AbstractEventLoop | None): The event loop to patch. If None,
            the running event loop is used.

    """
    event_loop = event_loop_to_patch if event_loop_to_patch else asyncio.get_running_loop()
    event_loop.set_debug(True)
    event_loop.slow_callback_duration = slow_callback_duration_threshold_seconds


def add_block_hunter_middleware(app: FastAPI, *, verbose: bool = False) -> FastAPI:
    """Add the block hunter middleware to the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application to add the middleware to.
        verbose (bool): Whether to print the full stack trace of the coroutine that was
            called when the event loop resumed after the blocking call.

    Returns:
        The FastAPI application with the middleware added.

    """
    Config.verbose = verbose
    asyncio.base_events._format_handle = _custom_format_handle  # type: ignore
    app.add_middleware(BlockingCallDebuggerMiddleware)
    return app
