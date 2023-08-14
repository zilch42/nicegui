from typing import Any, Callable, Dict, Iterable, List, Set, SupportsIndex, Union, overload
from . import events

class ObservableDict(dict):

    def __init__(self, data: Dict, on_change: Callable) -> None:
        super().__init__(data)
        for key, value in self.items():
            super().__setitem__(key, make_observable(value, on_change))
        self.on_change = on_change

    def pop(self, k: Any, d: Any = None) -> Any:
        item = super().pop(k, d)
        events.handle_event(self.on_change, None)
        return item

    def popitem(self) -> Any:
        item = super().popitem()
        events.handle_event(self.on_change, None)
        return item

    def update(self, *args: Any, **kwargs: Any) -> None:
        super().update(make_observable(dict(*args, **kwargs), self.on_change))
        events.handle_event(self.on_change, None)

    def clear(self) -> None:
        super().clear()
        events.handle_event(self.on_change, None)

    def setdefault(self, __key: Any, __default: Any = None) -> Any:
        item = super().setdefault(__key, make_observable(__default, self.on_change))
        events.handle_event(self.on_change, None)
        return item

    def __setitem__(self, __key: Any, __value: Any) -> None:
        super().__setitem__(__key, make_observable(__value, self.on_change))
        events.handle_event(self.on_change, None)

    def __delitem__(self, __key: Any) -> None:
        super().__delitem__(__key)
        events.handle_event(self.on_change, None)

    def __or__(self, other: Any) -> Any:
        return super().__or__(other)

    def __ior__(self, other: Any) -> Any:
        super().__ior__(make_observable(dict(other), self.on_change))
        events.handle_event(self.on_change, None)
        return self


class ObservableList(list):

    def __init__(self, data: List, on_change: Callable) -> None:
        super().__init__(data)
        for i, item in enumerate(self):
            super().__setitem__(i, make_observable(item, on_change))
        self.on_change = on_change

    def append(self, item: Any) -> None:
        super().append(make_observable(item, self.on_change))
        events.handle_event(self.on_change, None)

    def extend(self, iterable: Iterable) -> None:
        super().extend(make_observable(list(iterable), self.on_change))
        events.handle_event(self.on_change, None)

    def insert(self, index: SupportsIndex, object: Any) -> None:
        super().insert(index, make_observable(object, self.on_change))
        events.handle_event(self.on_change, None)

    def remove(self, value: Any) -> None:
        super().remove(value)
        events.handle_event(self.on_change, None)

    def pop(self, index: SupportsIndex = -1) -> Any:
        item = super().pop(index)
        events.handle_event(self.on_change, None)
        return item

    def clear(self) -> None:
        super().clear()
        events.handle_event(self.on_change, None)

    def sort(self, **kwargs: Any) -> None:
        super().sort(**kwargs)
        events.handle_event(self.on_change, None)

    def reverse(self) -> None:
        super().reverse()
        events.handle_event(self.on_change, None)

    def __delitem__(self, key: Union[SupportsIndex, slice]) -> None:
        super().__delitem__(key)
        events.handle_event(self.on_change, None)

    def __setitem__(self, key: Union[SupportsIndex, slice], value: Any) -> None:
        super().__setitem__(key, make_observable(value, self.on_change))
        events.handle_event(self.on_change, None)

    def __add__(self, other: Any) -> Any:
        return super().__add__(other)

    def __iadd__(self, other: Any) -> Any:
        super().__iadd__(make_observable(other, self.on_change))
        events.handle_event(self.on_change, None)
        return self


class ObservableSet(set):

    def __init__(self, data: set, on_change: Callable) -> None:
        super().__init__(data)
        for item in self:
            super().add(make_observable(item, on_change))
        self.on_change = on_change

    def add(self, item: Any) -> None:
        super().add(make_observable(item, self.on_change))
        events.handle_event(self.on_change, None)

    def remove(self, item: Any) -> None:
        super().remove(item)
        events.handle_event(self.on_change, None)

    def discard(self, item: Any) -> None:
        super().discard(item)
        events.handle_event(self.on_change, None)

    def pop(self) -> Any:
        item = super().pop()
        events.handle_event(self.on_change, None)
        return item

    def clear(self) -> None:
        super().clear()
        events.handle_event(self.on_change, None)

    def update(self, *s: Iterable[Any]) -> None:
        super().update(make_observable(set(*s), self.on_change))
        events.handle_event(self.on_change, None)

    def intersection_update(self, *s: Iterable[Any]) -> None:
        super().intersection_update(*s)
        events.handle_event(self.on_change, None)

    def difference_update(self, *s: Iterable[Any]) -> None:
        super().difference_update(*s)
        events.handle_event(self.on_change, None)

    def symmetric_difference_update(self, *s: Iterable[Any]) -> None:
        super().symmetric_difference_update(*s)
        events.handle_event(self.on_change, None)

    def __or__(self, other: Any) -> Any:
        return super().__or__(other)

    def __ior__(self, other: Any) -> Any:
        super().__ior__(make_observable(other, self.on_change))
        events.handle_event(self.on_change, None)
        return self

    def __and__(self, other: Any) -> set:
        return super().__and__(other)

    def __iand__(self, other: Any) -> Any:
        super().__iand__(make_observable(other, self.on_change))
        events.handle_event(self.on_change, None)
        return self

    def __sub__(self, other: Any) -> set:
        return super().__sub__(other)

    def __isub__(self, other: Any) -> Any:
        super().__isub__(make_observable(other, self.on_change))
        events.handle_event(self.on_change, None)
        return self

    def __xor__(self, other: Any) -> set:
        return super().__xor__(other)

    def __ixor__(self, other: Any) -> Any:
        super().__ixor__(make_observable(other, self.on_change))
        events.handle_event(self.on_change, None)
        return self


@overload
def make_observable(data: Dict, on_change: Callable) -> ObservableDict:
    ...


@overload
def make_observable(data: List, on_change: Callable) -> ObservableList:
    ...


@overload
def make_observable(data: Set, on_change: Callable) -> ObservableSet:
    ...


def make_observable(data: Any, on_change: Callable) -> Any:
    if isinstance(data, dict):
        return ObservableDict(data, on_change)
    if isinstance(data, list):
        return ObservableList(data, on_change)
    if isinstance(data, set):
        return ObservableSet(data, on_change)
    return data
