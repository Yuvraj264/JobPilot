from typing import Dict, List, Optional
from app.services.automation.adapters.base import ApplicationAdapter
from app.services.automation.adapters.mock import MockApplicationAdapter
from app.services.automation.adapters.linkedin import LinkedInApplicationAdapter
from app.services.automation.adapters.indeed import IndeedApplicationAdapter
from app.services.automation.adapters.generic_career import GenericCareerApplicationAdapter


class ApplicationAdapterRegistry:
    """
    Registry for managing and resolving ApplicationAdapters.
    """
    def __init__(self):
        self._adapters: Dict[str, ApplicationAdapter] = {}

    def register(self, adapter: ApplicationAdapter):
        self._adapters[adapter.name()] = adapter

    def get(self, name: str) -> Optional[ApplicationAdapter]:
        return self._adapters.get(name)

    def list(self) -> List[ApplicationAdapter]:
        return list(self._adapters.values())

    def capabilities(self) -> Dict[str, Dict[str, bool]]:
        return {name: ad.get_capabilities() for name, ad in self._adapters.items()}


# Global Registry Instance
registry = ApplicationAdapterRegistry()
registry.register(MockApplicationAdapter())
registry.register(LinkedInApplicationAdapter())
registry.register(IndeedApplicationAdapter())
registry.register(GenericCareerApplicationAdapter())

