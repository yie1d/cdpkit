import builtins
import json
import re
import textwrap
from pathlib import Path
from typing import Any

import aiohttp
import toml


async def request_protocol_json() -> tuple[str, list[dict[str, Any]]]:
    """
    Request to obtain the latest version number and domain content.

    Returns:
        tuple[str, list[dict[str, Any]]]:
            A tuple containing the protocol version number as a string and a list of dictionaries
            containing protocol domain information.
    """
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
    except (aiohttp.ClientError, KeyError) as err:
        raise Exception(f'Failed to get websocket address: {err}')

    return protocol_version, browser_protocol_domains


def update_version(version: str) -> str:
    major, minor, patch = version.split('.')
    patch = int(patch) + 1
    if patch >= 20:
        minor = str(int(minor) + 1)
        patch = 0
    else:
        patch = str(patch)
    return f'{major}.{minor}.{patch}'


def update_cdp_version(package_path: Path, protocol_version: str) -> None:
    """
    Update the CDP version number.

    Args:
        package_path (Path): The path of the package.
        protocol_version (str): The protocol version number.
    """
    version_file = package_path / '__init__.py'

    if version_file.exists():
        with version_file.open('r') as f:
            file_content = f.read()
    else:
        file_content = '__version__ = "0.0.0"'

    try:
        version = re.search(r'__version__ = [\'"](\d+\.\d+\.\d+)[\'"]', file_content).group(1)
    except AttributeError:
        version = '0.0.0'

    file_content = f"""__version__ = '{update_version(version)}'\n__cdp_version__ = '{protocol_version}.0'\n"""

    with version_file.open('w') as f:
        f.write(file_content)


def indent(text: str, by: int = 4) -> str:
    """
    Indent the text.

    Args:
        text (str): The text to be indented.
        by (int, optional): The number of spaces for indentation, default is 4.

    Returns:
        str: The indented text.
    """
    return textwrap.indent(text=text, prefix=' ' * by)


def resolve_docstring(docs: str, by: int = 4) -> str:
    """
    Resolve the docstring and indent it.

    Args:
        docs (str): The docstring.
        by (int, optional): The number of spaces for indentation, default is 4.

    Returns:
        str: The resolved and indented docstring.
    """
    return indent(f'""" {docs} """\n', by=by)


def is_builtin(name: str) -> bool:
    """
    Check if the name is a built-in name.

    Args:
        name (str): The name to be checked.

    Returns:
        bool: True if it is a built-in name, otherwise False.
    """
    try:
        getattr(builtins, name)
        return True
    except AttributeError:
        return False


def rename_in_python(name: str) -> str:
    """
    Replace hyphens in the string with underscores and handle built-in function name conflicts.

    Args:
        name (str): The string to be processed.

    Returns:
        str: The processed string.
    """
    name = name.replace("-", "_")

    if is_builtin(name):
        return f'{name}_'
    return name


def rename_camel2snake(name: str):
    """
    Convert camel case naming to underscore naming and prevent built-in function name conflicts.

    Args:
        name (str): The camel case naming string to be converted.

    Returns:
        str: The converted underscore naming string.
    """
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', name)
    name = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', name)

    return rename_in_python(name).lower()


def parse_ref(ref: str) -> tuple[str, str]:
    """
    Parse the reference string.

    Args:
        ref (str): The reference string.

    Returns:
        tuple[str, str]: A tuple containing the module name and the reference name.
    """
    if '.' in ref:
        module_name, ref = ref.split('.')
    else:
        module_name = ''
    return module_name, ref


def fill_ref(ref: str, module_name: str):
    """
    Fill the reference string.

    Args:
        ref (str): The reference string.
        module_name (str): The module name.

    Returns:
        str: The filled reference string.
    """
    _module, _ref = parse_ref(ref)
    if _module:
        return ref
    return f'{module_name}.{_ref}'


def update_pyproject_version(toml_path: Path):
    content = toml.load(toml_path)

    content['project']['version'] = update_version(content['project']['version'])

    with open(toml_path, 'w') as f:
        toml.dump(content, f)
