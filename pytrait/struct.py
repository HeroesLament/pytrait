from abc import ABCMeta
from dataclasses import dataclass
import itertools as it
import sys
from typing import Any, Dict, Tuple

from .errors import InheritanceError, MultipleImplementationError
from .impl import Impl


class Struct(Impl):
    """
    Use metaclass=Struct when declaring a class, in order for the class to be a Struct
    in the trait system. The class will automatically find Impl blocks to inherit from.

    Struct is a metaclass, and must subclass the metaclass Impl because classes of type
    Struct subclass classes of type Impl.
    """
    def __new__(meta, name: str, bases: Tuple[Any], attrs: Dict[str, Any], **kwargs):
        """
        Passing keyword args after metaclass=Struct will provide options to dataclass.
        """

        # Ensure that we have no explicit superclasses
        if __debug__ and len(bases) > 0:
            raise InheritanceError(
                f"Struct {name} must have no explicit superclasses."
            )

        # Automatically add Impls for this Struct to bases
        impl_bases = Impl.registry[name]
        traits_implemented = set(
            it.chain.from_iterable(impl.traits() for impl in impl_bases)
        )
        traits_to_check_for_blanket_impls = traits_implemented.copy()

        # Automatically add blanket Impls for this struct
        # (Recursive logic to gather all relevant super-traits)
        while traits_to_check_for_blanket_impls:
            trait = traits_to_check_for_blanket_impls.pop()
            additional_impls = Impl.blanket_registry.get(trait.__name__)
            if additional_impls is None:
                continue
            impl_bases.extend(additional_impls)
            traits = set(
                it.chain.from_iterable(impl.traits() for impl in additional_impls)
            )
            traits_implemented.update(traits)
            traits_to_check_for_blanket_impls.update(traits)

        bases = bases + tuple(impl_bases)

        # Create the class normally using ABCMeta
        cls = super(ABCMeta, meta).__new__(meta, name, bases, attrs)

        # Track which traits are implemented
        cls.traits = frozenset(traits_implemented)

        # Disable slot usage by default, so no second pass is performed
        # If 'slots' was explicitly provided, we force it to False anyway.
        kwargs["slots"] = False

        # Finally, convert to a dataclass
        return dataclass(cls, **kwargs)

    def __init__(cls, name: str, bases: Tuple[Impl], attrs: Dict[str, Any], **kwargs):
        if __debug__:
            # Check that we only inherit directly from Impls, and that no two Impls
            # share a method of the same name.

            # Mapping from methodname to the name of the trait that we got the
            # method from
            methodnames_seen: Dict[str, str] = dict()
            for base in bases:
                trait_name = base.__bases__[0].__name__
                if base.__class__ is not Impl:
                    raise InheritanceError(
                        f"Struct {name} must only inherit from classes of type "
                        f"Impl, got class {base}"
                    )
                for attr, value in attrs.items():
                    if callable(value):
                        # Make sure no two traits clash with the same methods
                        if attr in methodnames_seen:
                            raise MultipleImplementationError(
                                f"Method {attr}() defined twice, due to Traits "
                                f"{methodnames_seen[attr]} and "
                                f"{trait_name}"
                            )
                            methodnames_seen[attr] = trait_name

        super(ABCMeta, cls).__init__(name, bases, attrs)
