import builtins
import asyncio
import aiohttp
import json
import re
import textwrap
from pathlib import Path
from typing import Any


async def request_protocol_json() -> tuple[str, list[dict[str, Any]]]:
    """请求获取最新的版本号及domain内容"""
    protocol_version = None
    browser_protocol_domains = []

    try:
        async with aiohttp.ClientSession(trust_env=True) as session:
            for protocol_name in ('browser_protocol', 'js_protocol'):
                async with session.get(
                    f'https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/refs/heads/master/json/{protocol_name}.json',
                ) as resp:
                    data = await resp.text()
                    protocol_data = json.loads(data)
                    browser_protocol_domains.extend(protocol_data['domains'])

                    if protocol_version is None:
                        _version = protocol_data['version']
                        protocol_version = f'{_version["major"]}.{_version["minor"]}'
    except aiohttp.ClientError as err:
        raise Exception(f'Failed to get websocket address: {err}')
    except KeyError as err:
        raise Exception(f'Failed to get websocket address: {err}')

    return protocol_version, browser_protocol_domains


def update_cdp_version(package_path: Path, protocol_version: str) -> None:
    """
    更新cdp版本号
    """
    version_file = package_path / '__init__.py'

    if version_file.exists():
        with version_file.open('r') as f:
            file_content = f.read()
    else:
        file_content = '__version__ = "0.0.0"'

    try:
        version = re.search(r'__version__ = [\'"](\d+\.\d+\.\d)[\'"]', file_content).group(1)
    except AttributeError:
        version = '0.0.0'

    major, minor, patch = version.split('.')
    minor = int(minor) + 1
    if minor >= 20:
        major = str(int(major) + 1)
        minor = 0
    else:
        minor = str(minor)

    file_content = f"""__version__ = '{major}.{minor}.{patch}'\n__cdp_version__ = '{protocol_version}.0'\n"""

    with version_file.open('w') as f:
        f.write(file_content)


def indent(text: str, by: int = 4) -> str:
    return textwrap.indent(text=text, prefix=' ' * by)


def resolve_docstring(docs: str, by: int = 4) -> str:
    return indent(f'""" {docs} """\n', by=by)


def is_builtin(name: str) -> bool:
    """判断是否是builtin名"""
    try:
        getattr(builtins, name)
        return True
    except AttributeError:
        return False


def rename_in_python(word: str) -> str:
    word = word.replace("-", "_")

    if is_builtin(word):
        return f'{word}_'
    return word


def rename_camel2snake(word: str):
    """将驼峰命名改为下划线命名, 并防止内置函数名"""
    word = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', word)
    word = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', word)

    return rename_in_python(word).lower()


def parse_ref(ref: str) -> tuple[str, str]:
    if '.' in ref:
        module_name, ref = ref.split('.')
    else:
        module_name = ''
    return module_name, ref


def fill_ref(ref: str, module_name: str):
    _module, _ref = parse_ref(ref)
    if _module:
        return ref
    return f'{module_name}.{_ref}'
