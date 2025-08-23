# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '09/08/2025 00:00'

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Set, Tuple

from core.logger import getLogger


@dataclass
class Event:
    '''Event data structure.'''

    name: str
    data: Optional[Dict[str, Any]] = None
    source: Optional[str] = None


class EventBus:
    '''Simple async event bus for host communication.'''

    def __init__(self) -> None:
        self.log = getLogger(self.__class__.__name__)
        self._subscribers: Dict[str, Set[Tuple[bool, Callable | None]]] = {}
        self._lock = asyncio.Lock()

    async def _handle_callback(self, callback: Callable | None, event: Event, once: bool) -> None:
        '''Handle individual callback execution with error handling.'''
        try:
            if once:
                await self.unsubscribe(event.name, callback)
            if callback:
                await callback(event)
        except Exception as e:
            self.log.exception(f'Error in event callback for <{event.name}/{event.source}>: <{e}>')

    def _task_done_callback(self, task: asyncio.Task) -> None:
        '''Handle task completion and log any exceptions.'''
        try:
            task.result()
        except Exception as e:
            self.log.exception(f'Unhandled exception in event callback task: <{e}>')

    async def subscribe(self, event_name: str, callback: Callable | None, once: bool = False) -> None:
        '''Subscribe to an event.'''
        async with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = set()
            self._subscribers[event_name].add((once, callback))

    async def unsubscribe(self, event_name: str, callback: Callable | None) -> None:
        '''Unsubscribe from an event.'''
        async with self._lock:
            if event_name in self._subscribers:
                remove_list = [(once, cb) for (once, cb) in self._subscribers[event_name] if cb == callback]
                for item in remove_list:
                    self._subscribers[event_name].discard(item)
                if not self._subscribers[event_name]:
                    del self._subscribers[event_name]

    async def emit(self, name: str, data: Optional[Dict[str, Any]] = None, source: Optional[str] = None) -> None:
        '''
        Emit an event to all subscribers without blocking the event loop.

        Args:
            name (str): The name of the event.
            data (Optional[Dict[str, Any]]): The event data.
            source (Optional[str]): The source of the event.
        '''
        event = Event(name=name, data=data, source=source)
        self.log.debug(f'Emitting event: <{event.name} by {event.source}>')

        if event.name in self._subscribers:
            for once, callback in self._subscribers[event.name].copy():
                try:
                    task = asyncio.create_task(self._handle_callback(callback, event, once))
                    task.add_done_callback(self._task_done_callback)
                except Exception as e:
                    self.log.error(f'Error creating task for callback: <{e}>')


if 'events' in __name__:
    # global event bus instance
    EmulatorEventBus = EventBus()
