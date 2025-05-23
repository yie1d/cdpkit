"""
This file is generated by generator/run.py based on the Chrome DevTools Protocol.


https://chromedevtools.github.io/devtools-protocol/tot/Profiler/

***************************************************
                    Methods
***************************************************
"""
from __future__ import annotations

from cdpkit.protocol._types import (
    Profiler,
)
from cdpkit.protocol.base import CDPMethod, InputModel, OutputModel


class Disable(CDPMethod[None]):

    INPUT_VALIDATOR = None
    OUTPUT_VALIDATOR = None


class Enable(CDPMethod[None]):

    INPUT_VALIDATOR = None
    OUTPUT_VALIDATOR = None


class GetBestEffortCoverageOutput(OutputModel):

    result: list[Profiler.ScriptCoverage]  # deprecated


class GetBestEffortCoverage(CDPMethod[GetBestEffortCoverageOutput]):  # deprecated
    """ Collect coverage data for the current isolate. The coverage data may be incomplete due to
    garbage collection. """

    INPUT_VALIDATOR = None
    OUTPUT_VALIDATOR = GetBestEffortCoverageOutput


class SetSamplingIntervalInput(InputModel):

    interval: int  # deprecated


class SetSamplingInterval(CDPMethod[None]):  # deprecated
    """ Changes CPU profiler sampling interval. Must be called before CPU profiles recording started. """

    INPUT_VALIDATOR = SetSamplingIntervalInput
    OUTPUT_VALIDATOR = None

    def __init__(
        self,
        *,
        interval: int
    ):
        super().__init__(
            interval=interval
        )


class Start(CDPMethod[None]):

    INPUT_VALIDATOR = None
    OUTPUT_VALIDATOR = None


class StartPreciseCoverageInput(InputModel):

    callCount: bool | None = None  # deprecated
    detailed: bool | None = None  # deprecated
    allowTriggeredUpdates: bool | None = None  # deprecated


class StartPreciseCoverageOutput(OutputModel):

    timestamp: float  # deprecated


class StartPreciseCoverage(CDPMethod[StartPreciseCoverageOutput]):  # deprecated
    """ Enable precise code coverage. Coverage data for JavaScript executed before enabling precise code
    coverage may be incomplete. Enabling prevents running optimized code and resets execution
    counters. """

    INPUT_VALIDATOR = StartPreciseCoverageInput
    OUTPUT_VALIDATOR = StartPreciseCoverageOutput

    def __init__(
        self,
        *,
        call_count: bool | None = None,
        detailed: bool | None = None,
        allow_triggered_updates: bool | None = None
    ):
        super().__init__(
            callCount=call_count,
            detailed=detailed,
            allowTriggeredUpdates=allow_triggered_updates
        )


class StopOutput(OutputModel):

    profile: Profiler.Profile  # deprecated


class Stop(CDPMethod[StopOutput]):

    INPUT_VALIDATOR = None
    OUTPUT_VALIDATOR = StopOutput


class StopPreciseCoverage(CDPMethod[None]):  # deprecated
    """ Disable precise code coverage. Disabling releases unnecessary execution count records and allows
    executing optimized code. """

    INPUT_VALIDATOR = None
    OUTPUT_VALIDATOR = None


class TakePreciseCoverageOutput(OutputModel):

    result: list[Profiler.ScriptCoverage]  # deprecated
    timestamp: float  # deprecated


class TakePreciseCoverage(CDPMethod[TakePreciseCoverageOutput]):  # deprecated
    """ Collect coverage data for the current isolate, and resets execution counters. Precise code
    coverage needs to have started. """

    INPUT_VALIDATOR = None
    OUTPUT_VALIDATOR = TakePreciseCoverageOutput
