from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class SrcData:
    items: Dict[str, List[Any]]
    src: str