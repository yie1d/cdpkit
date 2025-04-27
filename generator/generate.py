import builtins
import re
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


def is_builtin(name: str) -> bool:
    """判断是否是builtin名"""
    try:
        getattr(builtins, name)
        return True
    except AttributeError:
        return False


def rename(word: str):
    """将驼峰命名改为下划线命名, 并防止内置函数名"""
    word = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', word)
    word = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', word)
    word = word.replace("-", "_")

    if is_builtin(word):
        return f'{word}_'
    return word.lower()


class CDPBaseType(str, Enum):
    boolean = 'bool'
    integer = 'int'
    number = 'float'
    object = 'dict'
    string = 'str'


class CDPItems(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type: str | None = None
    ref: str | None = Field(default=None, alias='$ref')


class BaseCDPItem(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    description: str | None = None
    experimental: bool = False
    deprecated: bool = False


class CDPProperty(BaseCDPItem):
    type: str | None = None
    ref: str | None = Field(default=None, alias="$ref")
    enum: list[str] | None = None
    items: CDPItems | None = None
    optional: bool = False


class CDPType(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str
    description: str | None = None
    type: str
    items: CDPItems | None = None
    enum: list[str] | None = None
    properties: list[CDPProperty] | None = None
    deprecated: bool = False
    experimental: bool = False


class CDPParameter(CDPProperty):
    ...


class CDPReturn(CDPProperty):
    ...


class CDPCommand(BaseCDPItem):
    parameters: list[CDPParameter] | None = None
    returns: list[CDPReturn] | None = None
    redirect: str | None = None


class CDPEvent(BaseCDPItem):
    parameters: list[CDPParameter] | None = None


class CDPDomain(BaseModel):
    model_config = ConfigDict(extra='forbid')
    domain: str
    description: str | None = None
    experimental: bool = False
    dependencies: list[str] | None = None
    types: list[CDPType] | None = None
    commands: list[CDPCommand] | None = None
    events: list[CDPEvent] | None = None
