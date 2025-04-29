from pathlib import Path
import json
from typing import Any
import re
import textwrap
import builtins

from _format import *


def read_protocol_json(file_path: Path) -> tuple[str, list[dict[str, Any]]]:
    """
    读取protocol中的版本号及domain的数据

    Args:
        file_path [Path]: protocol json文件路径

    Returns:

    """
    with open(file_path, 'rb') as f:
        protocol_data = json.load(f)

    _version = protocol_data['version']

    return f'{_version["major"]}.{_version["minor"]}', protocol_data['domains']


def read_protocol(root_path: Path) -> tuple[str, list[dict[str, Any]]]:
    """
    读取protocol.json的数据，返回版本信息和domain数据

    Args:
        root_path [Path]: 根路径

    Returns:

    """
    protocol_dir = root_path.joinpath('generator/protocol')
    protocol_version, browser_protocol_domains = read_protocol_json(protocol_dir.joinpath('browser_protocol.json'))
    _, js_protocol_domains = read_protocol_json(protocol_dir.joinpath('js_protocol.json'))
    browser_protocol_domains.extend(js_protocol_domains)

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


def module_format(
    domain: str,
    description: str = '',
    other_imports: list[str] | None = None,
    all_methods_code: str = '',
    all_events_code: str = '',
) -> str:
    if other_imports:
        other_imports.insert(0, '')
        other_imports = ", ".join(other_imports)

    if all_methods_code:
        all_methods_code = f'{SPLIT_HINTS_TEMPLATE.format("Methods")}{all_methods_code}'

    if all_events_code:
        all_events_code = f'{SPLIT_HINTS_TEMPLATE.format("Events")}{all_events_code}'

    return MODULE_TEMPLATE.format(
        domain=domain,
        description=description,
        other_imports=other_imports,
        all_methods_code=all_methods_code,
        all_events_code=all_events_code
    )


def types_module_format(
    all_domains: list[str],
    types_code: str,
    types_for_class: str
) -> str:
    """
    格式化types模块的代码

    Args:
        all_domains: 
        types_code: 
        types_for_class: 

    Returns:

    """
    return TYPES_MODULE_TEMPLATE.format(
        all_domains=', \n'.join([indent(f'\'{domain}\'') for domain in all_domains]),
        types_code=types_code,
        types_for_class=types_for_class
    )


def types_public_class_format(
    class_name: str,
    properties: str,
) -> str:
    return TYPES_CLASS_TEMPLATE.format(
        class_name=class_name,
        parent='',
        description='',
        properties=properties
    )


def types_enum_class_format(
    class_name: str,
    description: str,
    enum_type: str,
    properties: str
) -> str:
    return TYPES_CLASS_TEMPLATE.format(
        class_name=class_name,
        parent=f'({enum_type}, enum.Enum)',
        description=description,
        properties=properties
    )


def types_enum_item_format(
    name: str,
    hint: str,
    value: str
) -> str:
    return TYPES_PROPERTY_TEMPLATE.format(
        name=name,
        hint=f': {hint}',
        value=f' = \'{value}\'',
        tips=''
    )


def types_simple_format(
    name: str,
    value: str
) -> str:
    return TYPES_PROPERTY_TEMPLATE.format(
        name=name,
        hint='',
        value=f' = {value}',
        tips=''
    )


def types_object_format(
    class_name: str,
    description: str,
    properties: str
):
    return TYPES_CLASS_TEMPLATE.format(
        class_name=class_name,
        description=description,
        parent='(CDPObject)',
        properties=properties
    )


def types_property_format(
    name: str,
    hint: str,
    value: str = '',
    tips: str = ''
):
    return TYPES_PROPERTY_TEMPLATE.format(
        name=name,
        hint=f': {hint}',
        value=f' = {value}' if value else '',
        tips=f'  # {tips}' if tips else ''
    )


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

    return rename_in_python(word)


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
