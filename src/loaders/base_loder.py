from abc import ABC, abstractmethod

class DocumentBaseLoader(ABC):
    """Abstract base class for all document loader implementations."""

    @abstractmethod
    def load(self) -> str:
        """Extract raw text content from the source."""
        raise NotImplementedError


    

