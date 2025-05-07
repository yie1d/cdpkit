import asyncio
from pathlib import Path
from typing import Any

from generator.cdp import CDPTopDomain
from generator.generate import generate_to_dir
from generator.utils import request_protocol_json, update_cdp_version

ROOT_PATH = Path(__file__).parent.parent.resolve()


def write_cdp_protocol(dir_path: Path, protocol_domains_data: list[dict[str, Any]]) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)

    top_domain = CDPTopDomain(domains=protocol_domains_data)
    generate_to_dir(top_domain, dir_path)


async def main():
    protocol_version, protocol_domains_data = await request_protocol_json()

    package_path = ROOT_PATH / 'cdpkit'

    update_cdp_version(package_path, protocol_version)
    write_cdp_protocol(package_path / 'protocol', protocol_domains_data)


if __name__ == '__main__':
    asyncio.run(main())
