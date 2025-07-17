from __future__ import annotations

import textwrap
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from generator.utils import fill_ref, parse_ref, resolve_docstring


class CodeBase(BaseModel):
    """
    Base class for code generation models.

    Parent class for all code generation-related data models, configured to forbid extra fields.
    """
    model_config = ConfigDict(extra='forbid')


class CDPVariableType(StrEnum):
    """
    Enumeration for common type mappings.

    Defines the mapping from CDP types to Python types.
    """
    boolean = 'bool'
    integer = 'int'
    number = 'float'
    string = 'str'
    object = 'JSON_DICT'
    any = 'Any'


class CDPItem(CodeBase):
    """
    CDP Base item type.

    Represents a basic data item with a type or reference.
    """
    type: str | None = None
    ref: str | None = Field(default=None, alias='$ref')

    def get_py_type(
        self,
        domain_obj: CDPDomain | None = None,
        ref_imports_set: set[str] | None = None
    ) -> str:
        """
        Get the corresponding Python type annotation.

        Resolves the final Python type from the type or reference and handles reference imports.

        Args:
            domain_obj (CDPDomain | None, optional):
                Domain object (if present, used to prefix domain-related references)
            ref_imports_set (set[str] | None, optional):
                Set of referenced imports (if present, automatically adds class names to import)

        Returns:
            str: Resolved Python type string.
        """
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
    """
    CDP Common object base class.

    Defines common fields and utility methods (e.g., description processing, class name generation).
    """
    name: str | None = None
    id: str | None = None
    description: str | None = None
    experimental: bool = False
    deprecated: bool = False

    class_name_: str | None = Field(default=None, init=False)  # Cached generated class name

    def textwrap_description(self, width: int, initial_indent: str):
        """
        Format the description text to a specified width and indentation.

        Args:
            width (int): Maximum characters per line
            initial_indent (str): Initial indentation string for the first line

        Returns:
            str: Wrapped and indented description text
        """
        if self.description:
            return ''.join(textwrap.wrap(
                self.description,
                width=width,
                initial_indent=initial_indent
            ))
        else:
            return ''

    def resolve_docstring(self, by: int = 4) -> str:
        """
        Resolve the description text into an indented docstring.

        Args:
            by (int, optional): Number of spaces for indentation (default: 4 spaces)

        Returns:
            str: Resolved docstring with indentation (empty string if no description)
        """
        if self.description:
            return resolve_docstring(self.description, by=by)
        else:
            return ''

    @property
    def class_name(self) -> str:
        """
        Generate a class name based on the `name` or `id` field.

        Rule: If `name` exists, convert to PascalCase; otherwise, use `id` (assumes `id` is already formatted).

        Returns:
            str: Generated class name
        """
        if self.class_name_ is None:
            if self.name:
                self.class_name_ = self.name[0].upper() + self.name[1:]
            else:
                self.class_name_ = self.id
        return self.class_name_

    def tips(self) -> str:
        """
        Generate a status tip string (experimental/deprecated markers).

        Returns:
            str: Combined tip string
        """
        _tips = ''
        if self.experimental:
            _tips += 'experimental'
        if self.deprecated:
            if _tips:
                _tips += ' deprecated'
            else:
                _tips = 'deprecated'
        return _tips


class CDPProperty(CDPCommonObject, CDPItem):
    """
    CDP Property definition class.

    Represents a field in a data structure
    """
    enum: list[str] | None = None
    items: CDPItem | None = None
    optional: bool = False

    default_value: Any = Field(default=None, init=False)

    def hint_type(
        self,
        domain_obj: CDPDomain | None = None,
        ref_imports_set: set[str] | None = None
    ) -> str:
        """
        Generate a type hint string with enum, array, and optional modifiers.

        Args:
            domain_obj (CDPDomain | None, optional): Domain object (for cross-domain reference resolution)
            ref_imports_set (set[str] | None, optional): Set of referenced imports (auto-adds classes to import)

        Returns:
            str: Full type hint string (e.g., "Literal['a', 'b'] | None")
        """
        if self.enum:
            _type = f'Literal[{", ".join([f"\'{_}\'" for _ in self.enum])}]'
        elif self.items:
            _type = self.items.get_py_type(domain_obj, ref_imports_set)
            if self.type == 'array':
                _type = f'list[{_type}]'
        else:
            _type = self.get_py_type(domain_obj, ref_imports_set)

        if self.optional or self.experimental:
            if _type != 'Any':  # Avoid redundant "Any | None"
                _type += ' | None'
            self.default_value = 'None'

        return _type


class CDPType(CDPCommonObject):
    """
    CDP type definition class.

    Represents complex data types (e.g., objects, arrays, enums).
    """
    type: str
    items: CDPItem | None = None
    enum: list[str] | None = None
    properties: list[CDPProperty] | None = None

    def hint_type(
        self,
        domain_obj: CDPDomain | None = None,
        ref_imports_set: set[str] | None = None
    ) -> str:
        """
        Generate a type hint string.

        Args:
            domain_obj (CDPDomain | None, optional): Domain object (for cross-domain reference resolution)
            ref_imports_set (set[str] | None, optional): Set of referenced imports (auto-adds classes to import)

        Returns:
            Resolved type hint string (e.g., "list[int]", "str", etc.)
        """
        if self.items:
            _type = self.items.get_py_type(domain_obj, ref_imports_set)
            if self.type == 'array':
                _type = f'list[{_type}]'
        else:
            _type = CDPVariableType[self.type].value
        return _type


class CDPParameter(CDPProperty):
    """CDP Parameter definition class, inherits from Property (supports optional, enum, reference, etc.)"""
    ...


class CDPReturn(CDPProperty):
    """CDP Return value definition class, inherits from Property (supports complex types and optional markers)"""
    ...


class CDPCommand(CDPCommonObject):
    """
    CDP Command definition class.

    Represents a callable command in the CDP protocol (with parameters and return values).
    """
    parameters: list[CDPParameter] | None = None
    returns: list[CDPReturn] | None = None
    redirect: str | None = None


class CDPEvent(CDPCommonObject):
    """
    CDP Event definition class.

    Represents an event in the CDP protocol (with trigger parameters).
    """
    parameters: list[CDPParameter] | None = None


class CDPDomain(CodeBase):
    """
    Domain definition class.

    Represents a complete domain in the CDP protocol (contains types, commands, events, etc.).
    """
    domain: str
    description: str = ''
    experimental: bool = False
    deprecated: bool = False
    dependencies: list[str] = Field(default_factory=list)
    types: list[CDPType] = Field(default_factory=list)
    commands: list[CDPCommand] = Field(default_factory=list)
    events: list[CDPEvent] = Field(default_factory=list)


class CDPTopDomain(BaseModel):
    """
    Top-level domain container class.

    Root model containing multiple CDP domains.
    """
    domains: list[CDPDomain]
