from app.services.adapters.base import JobSourceAdapter
from app.services.adapters.registry import JobSourceRegistry, registry
from app.services.adapters.mock import MockJobSourceAdapter
from app.services.adapters.linkedin import LinkedInJobSourceAdapter
from app.services.adapters.indeed import IndeedJobSourceAdapter
from app.services.adapters.company_careers import CompanyCareersJobSourceAdapter

# Auto-register all default adapters in global registry
registry.register(MockJobSourceAdapter(), enabled_by_default=True)
registry.register(LinkedInJobSourceAdapter(), enabled_by_default=False)
registry.register(IndeedJobSourceAdapter(), enabled_by_default=False)
registry.register(CompanyCareersJobSourceAdapter(), enabled_by_default=False)

__all__ = [
    "JobSourceAdapter",
    "JobSourceRegistry",
    "registry",
    "MockJobSourceAdapter",
    "LinkedInJobSourceAdapter",
    "IndeedJobSourceAdapter",
    "CompanyCareersJobSourceAdapter",
]
