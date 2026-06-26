import contextvars
import logging

# Context variable — set once per request, automatically propagated across async calls
session_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("session_id", default="local")

class SessionFilter(logging.Filter):
    """Injects session_id into every log record."""
    def filter(self, record: logging.LogRecord) -> bool:
        record.session_id = session_id_var.get()
        return True

def setup_logging() -> None:
    """Configure structured logging with session ID injection."""
    root_logger = logging.getLogger()
    
    # Avoid duplicate SessionFilter handlers
    for h in root_logger.handlers:
        if any(isinstance(f, SessionFilter) for f in h.filters):
            return
            
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | session=%(session_id)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(SessionFilter())
    
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def bind_session_id(ctx) -> str:
    """Extracts session ID from ADK Context and binds it to contextvars."""
    session_id = "local"
    if hasattr(ctx, "session") and ctx.session and getattr(ctx.session, "id", None):
        session_id = ctx.session.id
    elif hasattr(ctx, "run_id") and ctx.run_id:
        session_id = ctx.run_id
    session_id_var.set(session_id)
    return session_id
