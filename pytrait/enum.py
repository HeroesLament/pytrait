# pytrait/enum.py

import itertools as it
import sys
from enum import Enum as PyEnum
from typing import Any, Dict, Tuple

from .impl import Impl

################################################################################
# 1. INTERNAL BASE ENUM (NO TRAIT METACLASS)
################################################################################

class _BaseEnum(PyEnum):
    """
    A plain subclass of Python's Enum. 
    It overrides require_inherit_traits with a no-op to avoid any PyTrait checks.
    """

    # No-op method so if `Impl.__init__` calls `cls.require_inherit_traits`, it won't fail.
    @classmethod
    def require_inherit_traits(cls, name, bases):
        pass

################################################################################
# 2. TRAIT-AWARE ENUM METACLASS
################################################################################

class EnumTraitMeta(type(_BaseEnum), Impl):
    """
    Metaclass for PyTrait-compatible Enums.
    - Skips trait checks for the base 'Enum' class itself.
    - Gathers blanket impls for user-defined Enums.
    """
    def __new__(meta, name: str, bases: Tuple[Any], attrs: Dict[str, Any], **kwargs):
        # Detect if we're creating the special 'Enum' class in this module.
        if name == "Enum" and attrs.get("__module__") == "pytrait.enum":
            # Create the base Enum class without blanket logic.
            cls = super().__new__(meta, name, bases, attrs, **kwargs)
            cls.traits = frozenset()
            return cls

        # For user-defined Enums, gather specific + blanket impls
        impl_bases = Impl.registry.get(name, [])
        traits_implemented = set(it.chain.from_iterable(impl.traits() for impl in impl_bases))
        traits_to_check_for_blanket_impls = traits_implemented.copy()

        while traits_to_check_for_blanket_impls:
            trait = traits_to_check_for_blanket_impls.pop()
            additional_impls = Impl.blanket_registry.get(trait.__name__)
            if additional_impls:
                impl_bases.extend(additional_impls)
                new_traits = set(it.chain.from_iterable(impl.traits() for impl in additional_impls))
                traits_implemented.update(new_traits)
                traits_to_check_for_blanket_impls.update(new_traits)

        # Merge any Impl bases into original bases
        bases = bases + tuple(impl_bases)

        # Create the user-defined Enum
        cls = super().__new__(meta, name, bases, attrs, **kwargs)
        cls.traits = frozenset(traits_implemented)
        return cls

    def __init__(cls, name, bases, attrs, **kwargs):
        # Skip trait checks if this is our special 'Enum' base class
        if name == "Enum" and cls.__module__ == "pytrait.enum":
            super(type(_BaseEnum), cls).__init__(name, bases, attrs, **kwargs)
            return

        # For user-defined Enums, do the usual PyTrait validation
        cls.require_inherit_traits(name, bases)
        super().__init__(name, bases, attrs, **kwargs)


################################################################################
# 3. PUBLIC ENUM CLASS
################################################################################

class Enum(_BaseEnum, metaclass=EnumTraitMeta):
    """
    The public, PyTrait-compatible Enum class.
    Users should subclass this, e.g.:

        from pytrait.enum import Enum

        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3
    """
    pass
