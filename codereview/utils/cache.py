import os
import json
import hashlib
from typing import Optional, Set
from codereview.models import ReviewResult
from codereview.utils.logging import get_logger

logger = get_logger("codivus.cache")


class ReviewCache:
    def __init__(self, cache_dir: str = ".codivus/cache"):
        self.cache_dir = cache_dir
        self.enabled = os.getenv("CODIVUS_NO_CACHE", "0") != "1"

    def _get_cache_key(
        self,
        filepath: str,
        code_content: str,
        modified_lines: Optional[Set[int]] = None,
        category_focus: Optional[str] = None,
    ) -> str:
        normalized_path = os.path.normpath(filepath).replace("\\", "/")
        inputs = f"{normalized_path}:{code_content}"
        if modified_lines is not None:
            inputs += f":{sorted(list(modified_lines))}"
        if category_focus:
            inputs += f":{category_focus.lower()}"
        return hashlib.sha256(inputs.encode("utf-8")).hexdigest()

    def get(
        self,
        filepath: str,
        code_content: str,
        modified_lines: Optional[Set[int]] = None,
        category_focus: Optional[str] = None,
    ) -> Optional[ReviewResult]:
        if not self.enabled:
            return None
        key = self._get_cache_key(
            filepath, code_content, modified_lines, category_focus
        )
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Cache hit for review of: {filepath}")
                return ReviewResult.model_validate(data)
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_path}: {str(e)}")
                try:
                    os.remove(cache_path)
                except Exception:
                    pass
        return None

    def set(
        self,
        filepath: str,
        code_content: str,
        result: ReviewResult,
        modified_lines: Optional[Set[int]] = None,
        category_focus: Optional[str] = None,
    ) -> None:
        if not self.enabled:
            return
        key = self._get_cache_key(
            filepath, code_content, modified_lines, category_focus
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json())
            logger.info(f"Cached review results for: {filepath}")
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_path}: {str(e)}")


stream_log = get_logger("codivus")
