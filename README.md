## CDPKit: A Python Implementation of the CDP([Chrome DevTools Protocol](https://github.com/ChromeDevTools/devtools-protocol/tree/master/json))Toolkit

English  | [中文](doc/README_cn.md) 

## Overview

CDPKit is a toolkit for the Chrome DevTools Protocol (CDP). The protocol component of this project is built on [pydantic](https://github.com/pydantic/pydantic), supporting friendly code completion and parameter type checking. It also provides a connection module that enables CDP interactions via the `remote-debugging-port`.

## Key Features  
- **Type Safety**: Leverages `pydantic` to automatically implement type checking for command inputs and outputs.
- **Rich Type Hints**: Provides type hints for command results, eliminating the need to consult documentation for return values.
- **Dynamic Code Generation**: Generates protocol code based on the official [CDP JSON](https://github.com/ChromeDevTools/devtools-protocol/tree/master/json) schema, ensuring fast updates.
- **Async Performance**: Offers an asynchronous CDPSessionManager that abstracts communication logic, allowing direct method calls.

## Installation
#### 1. Install by pip
```shell
pip install cdpkits
```

#### 2. Install by [uv](https://github.com/astral-sh/uv)
- 2.1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/)(if not currently installed)
```shell
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS and Linux
# on Windows:
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
- 2.2. Clone the repository:
```shell
git clone https://github.com/yie1d/cdpkit.git  
cd cdpkit
```
- 2.3. Create a new virtual environment and activate it:
```shell
uv venv
source .venv/bin/activate  # On Unix/macOS
# Or on Windows:
# .venv\Scripts\activate
```
- 2.4. Install dependencies:
```shell
uv sync
```

## Basic Usage
### Quick Start
```python
import asyncio
from cdpkit.connection import CDPSessionManager
from cdpkit.protocol import Target


async def main():
    # Connect to the currently running browser (debug port 9222)
    session_manager = CDPSessionManager(ws_endpoint='localhost:9222')
    cdp_session = await session_manager.get_session()
    
    # Get information on all currently open targets.
    target_resp = await cdp_session.execute(Target.GetTargets())

    for target_info in target_resp.targetInfos:
        print(target_info.model_dump())



asyncio.run(main())

```
### Use `CDPSessionExecutor`

```python
import asyncio
from cdpkit.connection import CDPSessionManager, CDPSessionExecutor
from cdpkit.protocol import Target, Page


async def on_dialog_open(event_data: Page.JavascriptDialogOpening):
    """
    Callback function for the alert dialog

    Args:
        event_data (Page.JavascriptDialogOpening): 
            If the event_data parameter is provided, 
            it must be used as the parameter for receiving the event and must match the actual event type.

    Returns:

    """
    print(event_data.message)

async def main():
    session_manager = CDPSessionManager(ws_endpoint='localhost:9225')
    browser_session = await session_manager.get_session()


    # execute command
    target_resp = await browser_session.execute(Target.GetTargets(filter_=[{
        'type': 'page',
        'exclude': False
    }]))

    target_id = None
    for target_info in target_resp.targetInfos:
        if not target_info.url.startswith('devtools://') and not target_info.url.startswith('chrome-extension://'):
            target_id = target_info.targetId
            break

    if not target_id:
        raise Exception('No target found')

    # Retrieve the specified target session
    cdp_session = await session_manager.get_session(target_id=target_id)
    session_executor = CDPSessionExecutor(session=cdp_session, session_manager=session_manager)

    # execute by CDPSessionExecutor
    # Enable page events
    await session_executor.execute_method(Page.Enable())

    # Listen for events
    await session_executor.on(
        event=Page.JavascriptDialogOpening,
        callback=on_dialog_open
    )

    # You can manually run alert('test Page.JavascriptDialogOpening event') in the browser's console to see the listener in action.
    await asyncio.sleep(500)



asyncio.run(main())
```

### More usage
You can refer to [webauto](https://github.com/yie1d/webauto.git) — a browser-automation tool based on `CDPKit` (work in progress).