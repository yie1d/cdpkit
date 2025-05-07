from __future__ import annotations

import textwrap
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from generator.utils import fill_ref, parse_ref, resolve_docstring


class CodeBase(BaseModel):
    """code生成父类"""
    model_config = ConfigDict(extra='forbid')


class CDPVariableType(StrEnum):
    """普通类型映射"""
    boolean = 'bool'
    integer = 'int'
    number = 'float'
    string = 'str'
    object = 'JSON_DICT'
    any = 'Any'


class CDPItem(CodeBase):
    """Item项类型，优先使用ref"""
    type: str | None = None
    ref: str | None = Field(default=None, alias='$ref')

    def get_py_type(
        self,
        domain_obj: CDPDomain | None = None,
        ref_imports_set: set[str] | None = None
    ):
        if self.ref:
            _type = self.ref
            if domain_obj:
                _type = fill_ref(_type, domain_obj.domain)
            if ref_imports_set:
                ref_imports_set.add(parse_ref(_type)[0])
        else:
            _type = CDPVariableType[self.type].value
        return _type


class CDPCommonObject(CodeBase):
    name: str | None = None
    id: str | None = None
    description: str | None = None
    experimental: bool = False
    deprecated: bool = False

    class_name_: str | None = Field(default=None, init=False)

    def textwrap_description(self, *args, **kwargs):
        if self.description:
            return ''.join(textwrap.wrap(
                self.description,
                *args,
                **kwargs
            ))
        else:
            return ''

    def resolve_docstring(self, by: int = 4) -> str:
        if self.description:
            return resolve_docstring(self.description, by=by)
        else:
            return ''

    @property
    def class_name(self) -> str:
        if self.class_name_ is None:
            if self.name:
                self.class_name_ = self.name[0].upper() + self.name[1:]
            else:
                self.class_name_ = self.id
        return self.class_name_

    def tips(self) -> str:
        _tips = ''
        if self.experimental:
            _tips += 'experimental'
        if self.description:
            if _tips:
                _tips += ' deprecated'
            else:
                _tips = 'deprecated'
        return _tips


class CDPProperty(CDPCommonObject, CDPItem):
    enum: list[str] | None = None
    items: CDPItem | None = None
    optional: bool = False

    default_value: Any = Field(default=None, init=False)

    def hint_type(
        self,
        domain_obj: CDPDomain | None = None,
        ref_imports_set: set[str] | None = None
    ) -> str:
        if self.enum:
            _type = f'Literal[{", ".join([f"\'{_}\'" for _ in self.enum])}]'
        elif self.items:
            _type = self.items.get_py_type(domain_obj, ref_imports_set)
            if self.type == 'array':
                _type = f'list[{_type}]'
        else:
            _type = self.get_py_type(domain_obj, ref_imports_set)

        if self.optional:
            if _type != 'Any':
                _type += ' | None'
            self.default_value = 'None'

        return _type


class CDPType(CDPCommonObject):
    type: str
    items: CDPItem | None = None
    enum: list[str] | None = None
    properties: list[CDPProperty] | None = None

    def hint_type(
        self,
        domain_obj: CDPDomain | None = None,
        ref_imports_set: set[str] | None = None
    ) -> str:
        if self.items:
            _type = self.items.get_py_type(domain_obj, ref_imports_set)
        else:
            _type = CDPVariableType[self.type].value
        return _type


class CDPParameter(CDPProperty):
    ...


class CDPReturn(CDPProperty):
    ...


class CDPCommand(CDPCommonObject):
    parameters: list[CDPParameter] | None = None
    returns: list[CDPReturn] | None = None
    redirect: str | None = None


class CDPEvent(CDPCommonObject):
    parameters: list[CDPParameter] | None = None


class CDPDomain(CodeBase):
    model_config = ConfigDict(extra='forbid')
    domain: str
    description: str = ''
    experimental: bool = False
    deprecated: bool = False
    dependencies: list[str] = Field(default_factory=list)
    types: list[CDPType] = Field(default_factory=list)
    commands: list[CDPCommand] = Field(default_factory=list)
    events: list[CDPEvent] = Field(default_factory=list)


class CDPTopDomain(BaseModel):
    domains: list[CDPDomain]
