from abc import ABCMeta
from typing import Any, Dict, List, Tuple, Type
import itertools as it

from .errors import InheritanceError
from .impl import Impl


class EnumVariant:
    """
    Represents a single variant of a pytrait Enum.
    Variants are created automatically by the Enum metaclass and exposed as attributes.
    """

    __slots__ = ("_enum_cls", "_name")

    def __init__(self, enum_cls: Type, name: str):
        self._enum_cls = enum_cls
        self._name = name

    def __str__(self):
        return self._name

    def __repr__(self):
        return f"<{self._enum_cls.__name__}.{self._name}>"

    def __eq__(self, other):
        return (
            isinstance(other, EnumVariant)
            and self._enum_cls is other._enum_cls
            and self._name == other._name
        )

    def __hash__(self):
        return hash((self._enum_cls, self._name))

    @property
    def name(self):
        """Returns the name of this enum variant, as a string."""
        return self._name

    @property
    def enum(self):
        """Returns the parent enum class this variant belongs to."""
        return self._enum_cls

    def __getattr__(self, attr: str):
        """
        Resolves missing attributes by lazily injecting trait methods from Impl blocks
        into the enum class, then binding and returning the requested method.
        """
        if not hasattr(self._enum_cls, attr):
            from pytrait.impl import Impl
            impl_bases = Impl.registry.get(self._enum_cls.__name__, [])
            for base in impl_bases:
                for name in dir(base):
                    if name.startswith("__"):
                        continue
                    value = getattr(base, name)
                    if callable(value) and not hasattr(self._enum_cls, name):
                        setattr(self._enum_cls, name, value)

        method = getattr(self._enum_cls, attr)
        if callable(method):
            return method.__get__(self, type(self))
        return method


class Enum(ABCMeta):
    """
    Metaclass for defining pytrait Enums.

    Use `metaclass=Enum` to define a trait-aware enum. Variants are declared using
    `auto()`. Trait implementations for the enum are automatically injected via
    Impl blocks registered using `target="MyEnum"`.

    Example:
        class Color(metaclass=Enum):
            RED = auto()
            BLUE = auto()
    """

    def __new__(mcls, name: str, bases: Tuple[type], attrs: Dict[str, Any], **kwargs):
        if __debug__ and bases:
            raise InheritanceError(f"Enum {name} must have no explicit superclasses.")

        variant_names = [k for k, v in list(attrs.items()) if isinstance(v, _AutoEnumToken)]
        for key in variant_names:
            del attrs[key]

        impl_bases = Impl.registry.get(name, [])
        traits_implemented = set(it.chain.from_iterable(impl.traits() for impl in impl_bases))
        traits_to_check = traits_implemented.copy()

        while traits_to_check:
            trait = traits_to_check.pop()
            blanket = Impl.blanket_registry.get(trait.__name__)
            if not blanket:
                continue
            impl_bases.extend(blanket)
            new_traits = set(it.chain.from_iterable(impl.traits() for impl in blanket))
            traits_implemented.update(new_traits)
            traits_to_check.update(new_traits)

        all_bases = tuple(impl_bases)
        cls = super().__new__(mcls, name, all_bases, attrs)
        cls._variant_names = variant_names
        cls._variants: Dict[str, EnumVariant] = {}

        for var_name in variant_names:
            variant = EnumVariant(cls, var_name)
            cls._variants[var_name] = variant
            setattr(cls, var_name, variant)

        cls.traits = frozenset(traits_implemented)

        for base in impl_bases:
            for attr in dir(base):
                if attr.startswith("__"):
                    continue
                value = getattr(base, attr)
                if callable(value) and not hasattr(cls, attr):
                    setattr(cls, attr, value)

        ABCMeta.__init__(cls, name, all_bases, attrs)

        return cls

    def __iter__(cls):
        """Iterate over all enum variants."""
        return iter(cls._variants.values())

    def __getitem__(cls, item: str):
        """Access an enum variant by name."""
        return cls._variants[item]

    def __contains__(cls, item: Any):
        """Check if a value is one of the enum's variants."""
        return item in cls._variants.values()

    def variant_names(cls) -> List[str]:
        """Return a list of all variant names, as strings."""
        return list(cls._variant_names)

    def variants(cls) -> List[EnumVariant]:
        """Return a list of all EnumVariant objects."""
        return list(cls._variants.values())


class _AutoEnumToken:
    pass


def auto():
    """
    Declare an enum variant inside a pytrait Enum.

    Example:
        class MyEnum(metaclass=Enum):
            A = auto()
            B = auto()
    """
    return _AutoEnumToken()
