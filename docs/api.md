# API Reference

Complete class reference specifications for Codivus' core interfaces.

## Reviewer

```python
class Reviewer:
    def __init__(self, config: Optional[Config] = None):
        """Instantiates core code review engine loader."""
        
    def review_file(
        self, 
        filepath: str, 
        modified_lines: Optional[Set[int]] = None,
        category_focus: Optional[str] = None
    ) -> ReviewResult:
        """Reviews target file and returns ReviewResult."""
        
    def review_dir(self, dirpath: str, category_focus: Optional[str] = None) -> RepositoryReviewResult:
        """Runs folder recursive review return RepositoryReviewResult."""
```

## Plugin Interfaces

```python
class BasePlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identification name."""
        
    def get_analysers(self) -> List[Callable[[CodeContext], List[Issue]]]:
        """Custom static rules analysers."""
        
    def modify_prompt(self, context: CodeContext, prompt: str) -> str:
        """Alters generated LLM prompt query strings."""
        
    def on_review_start(self, context: CodeContext) -> None:
        """Lifecycle hook before parsing/rules execution."""
        
    def on_review_end(self, context: CodeContext, result: ReviewResult) -> None:
        """Lifecycle hook after ReviewResult constructs."""
```

## Models

```python
class Issue(BaseModel):
    title: str
    description: str
    severity: str
    category: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    suggestion: Optional[Suggestion]

class ReviewResult(BaseModel):
    summary: Summary
    score: Score
    issues: List[Issue]
    timestamp: str
```
