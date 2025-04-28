from pathlib import Path
from typing import Any
from generator.utils import read_protocol, update_cdp_version
from generator.cdp_generate import CDPTopDomain

ROOT_PATH = Path(__file__).parent.parent.resolve()


def write_cdp_protocol(dir_path: Path, protocol_domains_data: list[dict[str, Any]]) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)

    top_domain = CDPTopDomain(domains=protocol_domains_data)
    top_domain.to_dir(dir_path)


def main():
    protocol_version, protocol_domains_data = read_protocol(ROOT_PATH)

    package_path = ROOT_PATH / 'cdpkit'

    update_cdp_version(package_path, protocol_version)
    write_cdp_protocol(package_path / 'protocol', protocol_domains_data)


if __name__ == '__main__':
    main()
