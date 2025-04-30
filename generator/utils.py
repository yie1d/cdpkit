import builtins
import json
import re
import textwrap
from pathlib import Path
from typing import Any


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


# def module_format(
#     domain: str,
#     description: str = '',
#     all_types_code: str = '',
#     all_methods_code: str = '',
#     all_events_code: str = '',
#     ref_imports: set[str] | None = None,
# ) -> str:
#     if all_types_code:
#         all_types_code = f'{SPLIT_HINTS_TEMPLATE.format(hints="Types")}{all_types_code}'
#
#     if all_methods_code:
#         all_methods_code = f'{SPLIT_HINTS_TEMPLATE.format(hints="Methods")}{all_methods_code}'
#
#     if all_events_code:
#         all_events_code = f'{SPLIT_HINTS_TEMPLATE.format(hints="Events")}{all_events_code}'
#
#     if ref_imports:
#         ref_imports = f'from cdpkit.protocol._types import {", ".join(ref_imports)}'
#
#     return MODULE_TEMPLATE.format(
#         domain=domain,
#         description=description,
#         all_types_code=all_types_code,
#         all_methods_code=all_methods_code,
#         all_events_code=all_events_code,
#         ref_imports=ref_imports
#     )
#

#
# def command_class_format(
#     class_name: str,
#     return_type: str,
#     tips: str,
#     description: str,
#     properties: str,
#     input_validator: str,
#     output_validator: str
# ):
#
#     if input_validator:
#         input_validator = indent(f'INPUT_VALIDATOR = {input_validator}\n')
#     else:
#         input_validator = ''
#     if output_validator:
#         output_validator = indent(f'OUTPUT_VALIDATOR = {output_validator}\n')
#     else:
#         output_validator = ''
#     return TYPES_CLASS_TEMPLATE.format(
#         class_name=class_name,
#         description=description,
#         parent=f'(CDPMethod[{return_type}])',
#         tips=tips,
#         properties=f'{input_validator}{output_validator}{properties}'
#     )
#
#
# def return_class_format(class_name: str, properties: str):
#     if properties:
#         return TYPES_CLASS_TEMPLATE.format(
#             class_name=class_name,
#             description='',
#             parent=f'(OutputModel)',
#             tips='',
#             properties=properties
#         )
#     else:
#         return ''


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
