"""Domain layer - Core business logic and rules.

This layer contains:
- Entities: Core business objects with identity
- Value Objects: Immutable objects defined by their attributes
- Domain Services: Stateless operations on domain objects
- Domain Events: Events that represent state changes
- Repository Protocols: Interfaces for persistence
- Exceptions: Domain-specific errors

Dependency Rule: Domain layer NEVER depends on outer layers.
"""

__version__ = "0.1.0"
