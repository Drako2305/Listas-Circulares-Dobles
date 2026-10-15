from collections.abc import Iterator
from dataclasses import dataclass

from trainyard.models import Wagon


@dataclass
class _Node:
    wagon: Wagon
    previous: "_Node | None" = None
    next: "_Node | None" = None


class DoublyCircularWagonList:
    """A circular doubly linked list that stores and navigates train wagons."""

    def __init__(self) -> None:
        self._head: _Node | None = None
        self._tail: _Node | None = None
        self._current: _Node | None = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    @property
    def current(self) -> Wagon | None:
        return self._current.wagon if self._current else None

    def append(self, wagon: Wagon) -> None:
        if self.find(wagon.wagon_id) is not None:
            raise ValueError(f"Wagon {wagon.wagon_id} already exists.")

        node = _Node(wagon)
        if self._head is None:
            node.previous = node
            node.next = node
            self._head = self._tail = self._current = node
        else:
            assert self._tail is not None and self._head is not None
            node.previous = self._tail
            node.next = self._head
            self._tail.next = node
            self._head.previous = node
            self._tail = node
        self._size += 1

    def find(self, wagon_id: str) -> Wagon | None:
        node = self._head
        for _ in range(self._size):
            assert node is not None
            if node.wagon.wagon_id == wagon_id:
                return node.wagon
            node = node.next
        return None

    def remove(self, wagon_id: str) -> Wagon:
        node = self._head
        for _ in range(self._size):
            assert node is not None
            if node.wagon.wagon_id == wagon_id:
                break
            node = node.next
        else:
            raise KeyError(f"Wagon {wagon_id} was not found.")

        if self._size == 1:
            self._head = self._tail = self._current = None
        else:
            assert node.previous is not None and node.next is not None
            node.previous.next = node.next
            node.next.previous = node.previous
            if node is self._head:
                self._head = node.next
            if node is self._tail:
                self._tail = node.previous
            if node is self._current:
                self._current = node.next

        self._size -= 1
        return node.wagon

    def move(self, direction: str) -> Wagon | None:
        if self._current is None:
            return None
        if direction == "next":
            self._current = self._current.next
        elif direction == "previous":
            self._current = self._current.previous
        else:
            raise ValueError("direction must be 'next' or 'previous'.")
        return self._current.wagon

    def wagons(self, direction: str = "next") -> Iterator[Wagon]:
        if direction not in ("next", "previous"):
            raise ValueError("direction must be 'next' or 'previous'.")
        node = self._head if direction == "next" else self._tail
        for _ in range(self._size):
            assert node is not None
            yield node.wagon
            node = node.next if direction == "next" else node.previous

    def reset(self) -> None:
        self._head = self._tail = self._current = None
        self._size = 0
