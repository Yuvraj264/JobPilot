from typing import Dict, List, Optional
from app.services.adapters.base import JobSourceAdapter


class JobSourceRegistry:
    """
    Central Registry managing all registered Job Source Adapters.
    Prevents hardcoded `if source == 'linkedin'` checks across application logic.
    """

    def __init__(self):
        self._adapters: Dict[str, JobSourceAdapter] = {}
        self._enabled_sources: Dict[str, bool] = {}

    def register(self, adapter: JobSourceAdapter, enabled_by_default: bool = True):
        name = adapter.source_name().lower()
        self._adapters[name] = adapter
        if name not in self._enabled_sources:
            self._enabled_sources[name] = enabled_by_default

    def get(self, source_name: str) -> Optional[JobSourceAdapter]:
        return self._adapters.get(source_name.lower())

    def list_adapters(self) -> List[JobSourceAdapter]:
        return list(self._adapters.values())

    def enable(self, source_name: str):
        name = source_name.lower()
        if name in self._adapters:
            self._enabled_sources[name] = True

    def disable(self, source_name: str):
        name = source_name.lower()
        if name in self._adapters:
            self._enabled_sources[name] = False

    def is_enabled(self, source_name: str) -> bool:
        return self._enabled_sources.get(source_name.lower(), False)

    def get_enabled_adapters(self) -> List[JobSourceAdapter]:
        return [ad for name, ad in self._adapters.items() if self._enabled_sources.get(name, False)]


# Global Registry Instance
registry = JobSourceRegistry()
