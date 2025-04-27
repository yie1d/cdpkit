import json
import re
from pathlib import Path
from typing import Any
from generator.generate import CDPDomain

ROOT_PATH = Path(__file__).parent.parent


def read_protocol_json() -> tuple[str, list[dict[str, Any]]]:
    """读取protocol中的版本号及domain的数据"""
    protocol_dir = ROOT_PATH.joinpath('generator/protocol')

    protocol_version = None
    protocol_domains = []
    for protocol_file in protocol_dir.glob('*.json'):
        with open(protocol_file, 'rb') as f:
            protocol_data = json.load(f)

        _version = protocol_data['version']

        if protocol_version is None:
            protocol_version = f'{_version["major"]}.{_version["minor"]}'

        protocol_domains.extend(protocol_data['domains'])
    protocol_domains.sort(key=lambda x: x['domain'])
    return protocol_version, protocol_domains


def update_cdp_version(protocol_version: str) -> None:
    """更新cdp版本"""
    version_file = ROOT_PATH.joinpath('cdpkit/__init__.py')

    with version_file.open('r') as f:
        file_content = f.read()

    version = re.search(r'__version__ = [\'"](\d+\.\d+\.\d)[\'"]', file_content).group(1)
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


def main():
    protocol_version, protocol_domains = read_protocol_json()

    update_cdp_version(protocol_version)

    for domain_data in protocol_domains:
        domain_obj = CDPDomain(**domain_data)


if __name__ == '__main__':
    main()
