"""
This file is generated by generator/run.py based on the Chrome DevTools Protocol.


https://chromedevtools.github.io/devtools-protocol/tot/ServiceWorker/

***************************************************
                    Events
***************************************************
"""
from __future__ import annotations

from cdpkit.protocol._types import (
    ServiceWorker,
)
from cdpkit.protocol.base import CDPEvent


class WorkerErrorReported(CDPEvent):

    errorMessage: ServiceWorker.ServiceWorkerErrorMessage


class WorkerRegistrationUpdated(CDPEvent):

    registrations: list[ServiceWorker.ServiceWorkerRegistration]


class WorkerVersionUpdated(CDPEvent):

    versions: list[ServiceWorker.ServiceWorkerVersion]
