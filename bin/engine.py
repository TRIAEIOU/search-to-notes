"""Search engine plugin handling"""

# https://mwax911.medium.com/building-a-plugin-architecture-with-python-7b4ab39ad4fc

from logging import Logger
from dataclasses import dataclass

@dataclass
class Match:
    """Dataclass containing data on one image"""
    title: str = None
    url: str = None
    file: str = None
    height: int = -1
    width: int = -1
    selected: bool = None

class Engines(type):
    """Container class for list of found Engines"""
    engines: list[type] = []

    def __init__(class_, name, base, attrs):
        super().__init__(class_)
        if name != 'Engine':
            Engines.engines.append(class_)

class Engine(object, metaclass=Engines):
    """
    Search engine base class, inherit and provide implementations for:
        def __init__(self, logger: Logger):
        def legend() -> str: text to be inserted under query box
        def tooltip() -> str: text/HTML to be used as tooltip for the query box
        def search(query: str) -> [Match]
    """
    logger: Logger
    def __init__(self, logger: Logger):
        """Virtual function"""
        self.logger = logger
        return
    def legend(self) -> str:
        """Virtual function"""
        return ""
    def tooltip(self) -> str:
        """Virtual function"""
        return ""
    def search(self, query: str) -> list[Match]:
        """Virtual function"""
        return []
