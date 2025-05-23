"""
This file is generated by generator/run.py based on the Chrome DevTools Protocol.


https://chromedevtools.github.io/devtools-protocol/tot/DeviceAccess/

***************************************************
                    Events
***************************************************
"""
from __future__ import annotations

from cdpkit.protocol._types import (
    DeviceAccess,
)
from cdpkit.protocol.base import CDPEvent


class DeviceRequestPrompted(CDPEvent):
    """ A device request opened a user prompt to select a device. Respond with the
    selectPrompt or cancelPrompt command. """

    id: DeviceAccess.RequestId
    devices: list[DeviceAccess.PromptDevice]
