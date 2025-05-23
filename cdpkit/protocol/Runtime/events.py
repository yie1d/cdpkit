"""
This file is generated by generator/run.py based on the Chrome DevTools Protocol.

Runtime domain exposes JavaScript runtime by means of remote evaluation and mirror objects.
Evaluation results are returned as mirror object that expose object type, string representation
and unique identifier that can be used for further object reference. Original objects are
maintained in memory unless they are either explicitly released or are released along with the
other objects in their object group.
https://chromedevtools.github.io/devtools-protocol/tot/Runtime/

***************************************************
                    Events
***************************************************
"""
from __future__ import annotations

from typing import Literal

from cdpkit.protocol._types import (
    Runtime,
)
from cdpkit.protocol.base import JSON_DICT, CDPEvent


class BindingCalled(CDPEvent):
    """ Notification is issued every time when binding is called. """

    name: str
    payload: str
    executionContextId: Runtime.ExecutionContextId  # deprecated


class ConsoleAPICalled(CDPEvent):
    """ Issued when console API was called. """

    type: Literal['log', 'debug', 'info', 'error', 'warning', 'dir', 'dirxml', 'table', 'trace', 'clear', 'startGroup', 'startGroupCollapsed', 'endGroup', 'assert', 'profile', 'profileEnd', 'count', 'timeEnd']  # deprecated
    args: list[Runtime.RemoteObject]  # deprecated
    executionContextId: Runtime.ExecutionContextId  # deprecated
    timestamp: Runtime.Timestamp  # deprecated
    stackTrace: Runtime.StackTrace | None = None  # deprecated
    context: str | None = None  # experimental deprecated


class ExceptionRevoked(CDPEvent):
    """ Issued when unhandled exception was revoked. """

    reason: str  # deprecated
    exceptionId: int  # deprecated


class ExceptionThrown(CDPEvent):
    """ Issued when exception was thrown and unhandled. """

    timestamp: Runtime.Timestamp  # deprecated
    exceptionDetails: Runtime.ExceptionDetails


class ExecutionContextCreated(CDPEvent):
    """ Issued when new execution context is created. """

    context: Runtime.ExecutionContextDescription  # deprecated


class ExecutionContextDestroyed(CDPEvent):
    """ Issued when execution context is destroyed. """

    executionContextId: Runtime.ExecutionContextId  # deprecated
    executionContextUniqueId: str | None = None  # experimental deprecated


class ExecutionContextsCleared(CDPEvent):
    """ Issued when all executionContexts were cleared in browser """

    ...


class InspectRequested(CDPEvent):
    """ Issued when object should be inspected (for example, as a result of inspect() command line API
    call). """

    object: Runtime.RemoteObject
    hints: JSON_DICT
    executionContextId: Runtime.ExecutionContextId | None = None  # experimental deprecated
