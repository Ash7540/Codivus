import time
from contextlib import contextmanager
from typing import Generator
from codereview.utils.logging import get_logger

logger = get_logger("codivus.telemetry")

@contextmanager
def time_operation(operation_name: str) -> Generator[None, None, None]:
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        duration = end_time - start_time
        logger.info(f"Operation '{operation_name}' completed in {duration:.4f} seconds.")
