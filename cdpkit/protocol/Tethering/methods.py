"""
This file is generated by generator/run.py based on the Chrome DevTools Protocol.

The Tethering domain defines methods and events for browser port binding.
https://chromedevtools.github.io/devtools-protocol/tot/Tethering/

***************************************************
                    Methods
***************************************************
"""
from __future__ import annotations

from cdpkit.protocol.base import CDPMethod, InputModel


class BindInput(InputModel):

    port: int  # deprecated


class Bind(CDPMethod[None]):  # deprecated
    """ Request browser port binding. """

    INPUT_VALIDATOR = BindInput
    OUTPUT_VALIDATOR = None

    def __init__(
        self,
        *,
        port: int
    ):
        super().__init__(
            port=port
        )


class UnbindInput(InputModel):

    port: int  # deprecated


class Unbind(CDPMethod[None]):  # deprecated
    """ Request browser port unbinding. """

    INPUT_VALIDATOR = UnbindInput
    OUTPUT_VALIDATOR = None

    def __init__(
        self,
        *,
        port: int
    ):
        super().__init__(
            port=port
        )
