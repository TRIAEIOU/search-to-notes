import os, re
from dataclasses import fields, is_dataclass, asdict
from types import GenericAlias
from typing import TypeVar
from aqt import mw
from anki import lang

# Versioning ######################################################################
def strvercmp(left: str, right: str) -> int:
    """Compares semantic version strings.\n
    Returns:    left version is larger: > 0
                right version is larger: < 0
                versions are equal: 0"""

    pat = re.compile('^([0-9]+)\.?([0-9]+)?\.?([0-9]+)?([a-z]+)?([0-9]+)?$')
    l = pat.match(left).groups()
    r = pat.match(right).groups()
    for i in range(5):
        if l[i] != r[i]:
            if i == 3:
                return 1 if l[3] == None or (r[3] != None and l > r) else -1
            else:
                return 1 if r[i] == None or (l[i] != None and int(l[i]) > int(r[i])) else -1
    return 0

def get_version() -> str:
    """Get current version string (from meta.json)."""
    meta = mw.addonManager.addon_meta(os.path.dirname(__file__))
    return meta.human_version if meta.human_version else '0.0.0'

def set_version(version: str):
    """Set version (to meta.json)."""
    meta = mw.addonManager.addon_meta(os.path.dirname(__file__))
    meta.human_version = version
    mw.addonManager.write_addon_meta(meta)

# Configuration ##################################################################
# Concept from https://stackoverflow.com/a/65945186
T = TypeVar('T')

_cache = {}
def dc_from_dict(class_: T, dict_: dict) -> T:
    """Instantiate dataclass from dict"""
    def parse(c, d):
        if not is_dataclass(c):
            return d
        elif c not in _cache:
            _cache[c] = {f for f in fields(c) if f.init}

        vals = {}
        for f in _cache[c]:
            if not f.name in d:
                vals[f.name] = None
            elif isinstance(f.type, GenericAlias) and f.type.__origin__ == list:
                vals[f.name] = [parse(f.type.__args__[0], dd) for dd in d[f.name]]
            else:
                vals[f.name] = parse(f.type, d[f.name])
        return c(**vals)

    return parse(class_, dict_)

def dict_from_dc(dataclass_: T):
    """Convert dataclass to dict"""
    return dataclass_.__dict__

def load_config(class_: T) -> T:
    """Load addon config into supplied data class, discarding fields not in dataclass"""
    return dc_from_dict(class_, mw.addonManager.getConfig(__name__))
    

def write_config(config: type):
    """Write config dataclass to addon config.json"""
    mw.addonManager.writeConfig(dict_from_dc(config))
    
class Translator:
    pass

# Translations ################################################
def load_translation(translations: dict[str, dict[str, str]]):
    """Load translation from dict: {'en_GB': {'some string': 'some other string'}}"""
    current = lang.compatMap.get(lang.current_lang, lang.current_lang.replace('-', '_'))
    t.lang = translations.get(current, {})

def t(string: str):
    """Translate given string using the current language."""
    return t.lang.get(string, string)
