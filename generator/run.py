import asyncio
from pathlib import Path
from typing import Any

from generator.cdp import CDPTopDomain
from generator.generate import generate_to_dir
from generator.utils import request_protocol_json, update_cdp_version, update_pyproject_version

ROOT_PATH = Path(__file__).parent.parent.resolve()


def write_cdp_protocol(dir_path: Path, protocol_domains_data: list[dict[str, Any]]) -> None:
    """
    Write the CDP protocol data to the specified directory.

    Args:
        dir_path (Path): The path of the target directory.
        protocol_domains_data (list[dict[str, Any]]):
            A list of protocol domain data, where each element is a dictionary containing protocol domain information.
    """
    dir_path.mkdir(parents=True, exist_ok=True)

    top_domain = CDPTopDomain(domains=protocol_domains_data)
    generate_to_dir(top_domain, dir_path)


async def main():
    """

    Just generate the code, and leave the rest to Ruff.  ^.^

    """
    protocol_version, protocol_domains_data = await request_protocol_json()

    package_path = ROOT_PATH / 'cdpkit'

    update_cdp_version(package_path, protocol_version)
    update_pyproject_version(package_path.parent.joinpath('pyproject.toml'))
    write_cdp_protocol(package_path / 'protocol', protocol_domains_data)


if __name__ == '__main__':
    asyncio.run(main())
