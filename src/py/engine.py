"""Search engine plugin handling"""

# https://mwax911.medium.com/building-a-plugin-architecture-with-python-7b4ab39ad4fc

import os, re
from abc import ABC, abstractmethod, abstractstaticmethod
from logging import Logger
from dataclasses import dataclass, field
from importlib import import_module, reload
from glob import iglob
from .image_sz import *
from .consts import *
try:
    from aqt import QApplication
except:
    from PyQt6.QtWidgets import QApplication

@dataclass
class Match:
    """dataclass containing data on one image"""

    height: int
    _height: int = field(init=False, repr=False)
    @property
    def height(self) -> int:
        if self._height == None:
            (self._width, self._height) = get_image_size(self.file)
        return self._height
    @height.setter
    def height(self, height: int): self._height = height

    width: int
    _width: int = field(init=False, repr=False)
    @property
    def width(self) -> int:
        if self._width == None:
            (self._width, self._height) = get_image_size(self.file)
        return self._width
    @width.setter
    def width(self, width: int): self._width = width

    title: str = None
    url: str = None
    file: str = None
    selected: bool = False

@dataclass
class Term:
    """Container class for one search term and its matches, deletes downloaded files on destruction"""    
    def __del__(self):
        for match in self.matches if self.matches else []:
            try: os.remove(match['file'])
            except: pass

    term: str = None
    #_term: str = field(init=True, repr=False)
    #@property
    #def term(self) -> str: return self._term
    #@property.setter

    template: str = None

    #query: str
    _query: str = None #field(init=False, repr=False)
    def query(self, template: str):
        """Return query for search term from template"""
        if self._query == None:
            # Replace all %0 with complete term
            q = re.sub(r"(?<!%)%0(?!\d)", self.term, template)
            # Parse term parts and replace corresponding %\d's in query
            for (i, part) in enumerate(self.term.split('\t')):
                q = re.sub(rf"(?<!%)%{str(i + 1)}(?!\d)", part, q)
            # Eat any remaining %\d's
            self._query = re.sub(r"(?<!%)%\d+", '', q)
        return self._query
    
    matches: list[Match] = None


class Engine(ABC):
    """
    Search engine base class, inherit and provide implementations for:
        def __init__(self, logger: Logger, config: any)
        def title(self) -> str: title/name of engine
        def legend(self) -> str: text to be inserted under query box
        def tooltip(self) -> str: text/HTML to be used as tooltip for the query box
        def search(self, hquery: str) -> [Match]
    """
    @abstractmethod
    def __init__(self, logger: Logger, config: any):
        pass
    @abstractstaticmethod
    def title() -> str:
        """Return title/name of engine."""
        return None
    @abstractmethod
    def legend(self) -> str:
        """Return text to be inserted under query box."""
        return None
    @abstractmethod
    def tooltip(self) -> str:
        """Return text/HTML to be used as tooltip for the query box."""
        return None
    @abstractmethod
    def search(self, query: str) -> list[Match]:
        """Return array of Match for query."""
        return None

def load_engines():
    """Load engines, return dict of title: engine"""
    for file in iglob(os.path.join(ADDON_DIR, ENGINES_SUBDIR, "*.py")):
        name = f"{ENGINES_SUBDIR}.{os.path.splitext(os.path.basename(file))[0]}"
        if module := sys.modules.get(f'{__package__}.{name}'):
            reload(module)
        else:
            import_module(f'.{name}', __package__)
    engines = {m.title(): m for m in Engine.__subclasses__()}
    return engines

