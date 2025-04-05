from functools import wraps
from typing import Callable
from pytrait.enum import EnumVariant
from pytrait.impl import Impl

def requires_traits(**trait_map):
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            bound = fn.__code__.co_varnames
            all_args = dict(zip(bound, args))
            all_args.update(kwargs)

            for arg_name, trait_or_traits in trait_map.items():
                if arg_name not in all_args:
                    raise TypeError(f"Missing required argument: {arg_name}")
                value = all_args[arg_name]
                traits_required = (
                    trait_or_traits
                    if isinstance(trait_or_traits, (tuple, list))
                    else (trait_or_traits,)
                )

                if isinstance(value, EnumVariant):
                    target_cls = value.enum
                else:
                    target_cls = type(value)

                impls = Impl.registry.get(target_cls.__name__, [])
                traits = set()
                for impl in impls:
                    for trait in impl.traits():
                        traits.add(trait)
                        for attr in dir(impl):
                            if attr.startswith("__"):
                                continue
                            val = getattr(impl, attr)
                            if callable(val) and not hasattr(target_cls, attr):
                                setattr(target_cls, attr, val)
                target_cls.traits = frozenset(traits)

                for trait in traits_required:
                    if trait not in getattr(target_cls, "traits", set()):
                        raise TypeError(
                            f"{arg_name} must implement trait {trait.__name__}, got {value!r}"
                        )

            return fn(*args, **kwargs)
        return wrapper
    return decorator
