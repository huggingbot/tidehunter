"""Singleton metaclass"""
from abc import ABCMeta
from typing import Any, Callable, TypeVar, cast

TAttribute = TypeVar("TAttribute")


class DummyAttribute:
    pass


def abstract_attribute(obj: Callable[[Any], TAttribute] = None) -> TAttribute:
    _obj = cast(Any, obj)
    if obj is None:
        _obj = DummyAttribute()
    _obj.__is_abstract_attribute__ = True
    return cast(TAttribute, _obj)


class BaseABCMeta(ABCMeta):
    def __call__(cls, *args, **kwargs):
        instance = ABCMeta.__call__(cls, *args, **kwargs)
        abstract_attributes = {
            name
            for name in dir(instance)
            if getattr(getattr(instance, name), "__is_abstract_attribute__", False)
        }
        if abstract_attributes:
            raise NotImplementedError(
                "Can't instantiate abstract class {} with"
                " abstract attributes: {}".format(
                    cls.__name__, ", ".join(abstract_attributes)
                )
            )
        return instance


class Singleton(type):
    """A metaclass to create singleton classes"""

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
