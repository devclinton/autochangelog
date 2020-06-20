from dataclasses import dataclass, field


@dataclass()
class ChangelogContext:
    src: str = field()
    verbose: bool = field(default=False)
    debug: bool = field(default=False)
