"""
This file is generated by generator/run.py based on the Chrome DevTools Protocol.

This domain provides experimental commands only supported in headless mode.
https://chromedevtools.github.io/devtools-protocol/tot/HeadlessExperimental/

***************************************************
                    Methods
***************************************************
"""
from __future__ import annotations

from cdpkit.protocol._types import (
    HeadlessExperimental,
)
from cdpkit.protocol.base import CDPMethod, InputModel, OutputModel


class BeginFrameInput(InputModel):

    frameTimeTicks: float | None = None  # deprecated
    interval: float | None = None  # deprecated
    noDisplayUpdates: bool | None = None  # deprecated
    screenshot: HeadlessExperimental.ScreenshotParams | None = None  # deprecated


class BeginFrameOutput(OutputModel):

    hasDamage: bool  # deprecated
    screenshotData: str | None = None  # deprecated


class BeginFrame(CDPMethod[BeginFrameOutput]):  # deprecated
    """ Sends a BeginFrame to the target and returns when the frame was completed. Optionally captures a
    screenshot from the resulting frame. Requires that the target was created with enabled
    BeginFrameControl. Designed for use with --run-all-compositor-stages-before-draw, see also
    https://goo.gle/chrome-headless-rendering for more background. """

    INPUT_VALIDATOR = BeginFrameInput
    OUTPUT_VALIDATOR = BeginFrameOutput

    def __init__(
        self,
        *,
        frame_time_ticks: float | None = None,
        interval: float | None = None,
        no_display_updates: bool | None = None,
        screenshot: HeadlessExperimental.ScreenshotParams | None = None
    ):
        super().__init__(
            frameTimeTicks=frame_time_ticks,
            interval=interval,
            noDisplayUpdates=no_display_updates,
            screenshot=screenshot
        )


class Disable(CDPMethod[None]):  # deprecated
    """ Disables headless events for the target. """

    INPUT_VALIDATOR = None
    OUTPUT_VALIDATOR = None


class Enable(CDPMethod[None]):  # deprecated
    """ Enables headless events for the target. """

    INPUT_VALIDATOR = None
    OUTPUT_VALIDATOR = None
