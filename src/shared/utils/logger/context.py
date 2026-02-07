import contextvars
import uuid
trace_id_var = contextvars.ContextVar("trace_id", default=None)