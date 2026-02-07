import logging # ContextVar가 정의된 곳
from shared.utils.logger.context import trace_id_var



class TraceIDFilter(logging.Filter):
    def filter(self, record):
        if trace_id_var.get() :
            record.trace_id = trace_id_var.get()
        return True