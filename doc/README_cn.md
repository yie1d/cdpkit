## CDPKit: 用 Python 实现的CDP([Chrome DevTools Protocol](https://github.com/ChromeDevTools/devtools-protocol/tree/master/json))工具箱

[English](../README.md)  | 中文

## 概述

CDPKit 是一个CDP工具箱。该项目的`protocol`部分基于[pydantic](https://github.com/pydantic/pydantic)，支持友好的代码提示功能及参数类型检查，还提供了`connection`部分，支持通过`remote-debugging-port`实现CDP交互。

## 主要功能  
- 基于`pydantic`，自动实现对命令的输入输出进行类型检查
- 支持对命令结果的类型提示，无需再根据文档看命令的返回
- 实现了根据[CDP json](https://github.com/ChromeDevTools/devtools-protocol/tree/master/json)生成`protocol`代码，更新快
- 提供了异步`CDPSessionManager`，无需自己再实现通信逻辑，可直接调用

## 安装
#### 1. 通过pip直接安装   
```shell
pip install cdpkits
```

#### 2. 通过[uv](https://github.com/astral-sh/uv)安装
- 2.1. [安装uv](https://docs.astral.sh/uv/getting-started/installation/)(如果当前未安装)
```shell
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS and Linux
# on Windows:
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
- 2.2. 克隆存储库
```shell
git clone https://github.com/yie1d/cdpkit.git  
cd cdpkit
```
- 2.3. 创建虚拟环境并激活
```shell
uv venv
source .venv/bin/activate  # On Unix/macOS
# Or on Windows:
# .venv\Scripts\activate
```
- 2.4. 安装依赖
```shell
uv sync
```

## 基础用法
### 快速开始
```python
import asyncio
from cdpkit.connection import CDPSessionManager
from cdpkit.protocol import Target


async def main():
    # 连接到当前已启动的浏览器（调试端口为9222）
    session_manager = CDPSessionManager(ws_endpoint='localhost:9222')
    cdp_session = await session_manager.get_session()
    
    # 获取所有已经打开的targets信息
    target_resp = await cdp_session.execute(Target.GetTargets())

    for target_info in target_resp.targetInfos:
        print(target_info.model_dump())



asyncio.run(main())

```
### 使用`CDPSessionExecutor`

```python
import asyncio
from cdpkit.connection import CDPSessionManager, CDPSessionExecutor
from cdpkit.protocol import Target, Page


async def on_dialog_open(event_data: Page.JavascriptDialogOpening):
    """
    alert弹窗的回调函数

    Args:
        event_data (Page.JavascriptDialogOpening): 该参数必须存在于回调函数中，类型为实际事件

    Returns:

    """
    print(event_data.message)

async def main():
    session_manager = CDPSessionManager(ws_endpoint='localhost:9225')
    browser_session = await session_manager.get_session()


    # 执行命令
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

    # 获取指定target会话
    cdp_session = await session_manager.get_session(target_id=target_id)
    session_executor = CDPSessionExecutor(session=cdp_session, session_manager=session_manager)

    # 通过CDPSessionExecutor执行
    # 启用页面事件
    await session_executor.execute_method(Page.Enable())

    # 监听事件
    await session_executor.on(
        event=Page.JavascriptDialogOpening,
        callback=on_dialog_open
    )

    # 可以在浏览器的控制台手动执行 alert('test Page.JavascriptDialogOpening event') 查看监听效果
    await asyncio.sleep(500)



asyncio.run(main())
```

### 更多用法
可以参考[webauto](https://github.com/yie1d/webauto.git) - 一个基于`CDPKit`的浏览器自动化工具（开发中。。。）
