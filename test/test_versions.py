import datetime
import re

import tomllib

from src.version import APP_VERSION, COPY_RIGHT


def test_verions():
    # check APP_VERSION is same to branch_name
    # branch_name = subprocess.run(["git", "branch", "--show-current"], encoding="utf-8", stdout=subprocess.PIPE)
    # branch_name = branch_name.stdout.strip().strip("Ver")
    # assert branch_name == APP_VERSION

    # check copyright year
    cur_yyyy = datetime.date.today().year
    matched = re.findall(r"-(\d{4})", COPY_RIGHT, flags=re.MULTILINE)
    yyyy = int(matched[0]) if matched else 0
    assert cur_yyyy <= yyyy <= cur_yyyy + 1  # accept +1 year

    # check version on build_mac.spec
    with open("build_mac.spec") as f:
        text = f.read()
    matched = re.findall(r"^\s*version='(\d.\d.\d)',?$", text, flags=re.MULTILINE)
    version = matched[0] if matched else ""
    assert version == APP_VERSION

    # check version_info.txt
    with open("src/version_info.txt") as f:
        text = f.read()
    matched = re.findall(r"^\s*filevers=\((\d, \d, \d, \d)\),?$", text, flags=re.MULTILINE)
    version = matched[0].replace(", ", ".") if matched else ""

    assert version == APP_VERSION + ".0"
    matched = re.findall(r"^\s*prodvers=\((\d, \d, \d, \d)\),?$", text, flags=re.MULTILINE)
    version = matched[0].replace(", ", ".") if matched else ""

    assert version == APP_VERSION + ".0"
    matched = re.findall(r"^\s*StringStruct\(u'FileVersion', u'(\d.\d.\d.\d)'\),?", text, flags=re.MULTILINE)
    version = matched[0].replace(", ", ".") if matched else ""

    assert version == APP_VERSION + ".0"
    matched = re.findall(r"^\s*StringStruct\(u'ProductVersion', u'(\d.\d.\d.\d)'\),?", text, flags=re.MULTILINE)
    version = matched[0].replace(", ", ".") if matched else ""
    assert version == APP_VERSION + ".0"

    matched = re.findall(r"^\s*StringStruct\(u'LegalCopyright',.*-(\d{4})'\),?", text, flags=re.MULTILINE)
    yyyy = int(matched[0]) if matched else ""
    assert cur_yyyy <= yyyy <= cur_yyyy + 1  # accept +1 year

    # check pyproject.toml
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    version = data["tool"]["poetry"]["version"]
    assert version == APP_VERSION
