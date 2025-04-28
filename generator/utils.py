from pathlib import Path
import json
from typing import Any
import re


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
