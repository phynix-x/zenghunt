from abc import ABC, abstractmethod
from typing import Iterable

from ..models import NormalizedOffer


class StoreConnector(ABC):
    slug: str
    name: str

    @abstractmethod
    def fetch(self) -> Iterable[NormalizedOffer]:
        """Return only real offers obtained from an approved store/API/feed."""
        raise NotImplementedError
