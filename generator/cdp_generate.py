from __future__ import annotations
from enum import Enum
from generator.logger import logger

from pydantic import BaseModel, Field, ConfigDict
from generator.utils import *


class CDPCommonType(str, Enum):
    """普通类型映射"""
    boolean = 'bool'
    integer = 'int'
    number = 'float'
    string = 'str'
    object = 'JSON_DICT'
    any = 'Any'


class CDPCodeGenerator(BaseModel):
    """code生成父类"""
    ...


class CDPItems(CDPCodeGenerator):
    """Item项类型，优先使用ref"""
    model_config = ConfigDict(extra='forbid')
    type: str | None = None
    ref: str | None = Field(default=None, alias='$ref')


class BaseCDPItem(CDPCodeGenerator):
    """通过cdp项内容"""
    model_config = ConfigDict(extra='forbid')
    name: str
    description: str | None = None
    experimental: bool = False
    deprecated: bool = False


class CDPProperty(BaseCDPItem):
    """CDP对象的属性，"""
    type: str | None = None
    ref: str | None = Field(default=None, alias="$ref")
    enum: list[str] | None = None
    items: CDPItems | None = None
    optional: bool = False
    
    def generate_code(self, domain_obj: CDPDomain) -> str:
        _description = ''
        if self.description:
            _description = ''.join(textwrap.wrap(self.description, width=80, initial_indent='    # '))

        if self.enum:
            _type = f'Literal[{", ".join([f"\'{_}\'" for _ in self.enum])}]'
        elif self.items:
            if self.items.ref:
                _type = fill_ref(self.items.ref, domain_obj.domain)
            else:
                _type = CDPCommonType[self.items.type].value
        elif self.ref:
            _type = fill_ref(self.ref, domain_obj.domain)
        else:
            _type = CDPCommonType[self.type].value

        _option = ''
        _value = ''
        if self.optional:
            if _type != 'Any':
                _option = ' | None'
            _value = 'None'

        _tips = ''
        if self.experimental:
            _tips = 'experimental'
        if self.deprecated:
            if _tips:
                _tips += f' deprecated'
            else:
                _tips = 'deprecated'

        return (f'{_description}\n' if _description else '') + indent(types_property_format(
            name=self.name,
            hint=f'{_type}{_option}',
            value=_value,
            tips=_tips
        ))


class CDPType(CDPCodeGenerator):
    model_config = ConfigDict(extra='forbid')
    id: str
    description: str | None = None
    type: str
    items: CDPItems | None = None
    enum: list[str] | None = None
    properties: list[CDPProperty] | None = None
    deprecated: bool = False
    experimental: bool = False
    
    def generate_enum_code(self, domain_obj: CDPDomain) -> str:
        enum_items_code = ''
        for enum_item in self.enum:
            enum_items_code += indent(
                types_enum_item_format(
                    rename_in_python(enum_item).upper(),
                    CDPCommonType[self.type].value,
                    enum_item
                )
            )

        return types_enum_class_format(
            class_name=f'{domain_obj.domain}{self.id}',
            description=resolve_docstring(self.description) if self.description else '',
            enum_type=CDPCommonType[self.type].value,
            properties=enum_items_code
        )

    def generate_object_code(self, domain_obj: CDPDomain) -> str:
        properties = ''

        for _property in self.properties:
            properties += _property.generate_code(domain_obj=domain_obj)

        return types_object_format(
            class_name=f'{domain_obj.domain}{self.id}',
            description=resolve_docstring(self.description) if self.description else '',
            properties=properties
        )

    def generate_simple_code(self, domain_obj: CDPDomain) -> str:
        if self.items:
            if self.items.ref:
                _type = fill_ref(self.items.ref, domain_obj.domain)
                _type = _type.replace('.', '')
            else:
                _type = CDPCommonType[self.items.type].value
        else:
            _type = CDPCommonType[self.type].value

        return (resolve_docstring(self.description, 0) if self.description else '') + types_simple_format(
            name=f'{domain_obj.domain}{self.id}',
            value=_type
        )
    
    def generate_code(self, domain_obj: CDPDomain) -> str:
        logger.debug(f'Generating code for {self.id} {self.type}')
        if self.enum:
            return self.generate_enum_code(domain_obj=domain_obj)
        elif self.properties:
            return self.generate_object_code(domain_obj=domain_obj)
        else:
            return self.generate_simple_code(domain_obj=domain_obj)


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


class CDPDomain(CDPCodeGenerator):
    model_config = ConfigDict(extra='forbid')
    domain: str
    description: str = ''
    experimental: bool = False
    deprecated: bool = False
    dependencies: list[str] = Field(default_factory=list)
    types: list[CDPType] = Field(default_factory=list)
    commands: list[CDPCommand] = Field(default_factory=list)
    events: list[CDPEvent] = Field(default_factory=list)

    def generate_code(self):
        logger.debug(f'Generating code for {self.domain}')
        other_imports = set()

        # if self.types:
        #     body_code += SPLIT_HINTS.format('Types')
        #     for item in self.types:
        #         body_code += f'\n\n{item.generate_code(_imports)}'

        all_methods_code = ''
        # if self.commands:
        #     body_code += SPLIT_HINTS.format('Methods')
        #     for item in self.commands:
        #         body_code += f'\n\n{item.generate_code(_imports)}'
        #
        all_events_code = ''
        # if self.events:
        #     body_code += SPLIT_HINTS.format('Events')
        #     for item in self.events:
        #         body_code += f'\n\n{item.generate_code(_imports)}'


        # 在递归生成code的过程中会将ref的导入顺便解析
        for _key in ('', self.domain):
            try:
                other_imports.remove(_key)
            except KeyError:
                ...

        return module_format(
            domain=self.domain,
            description=self.description,
            other_imports=list(other_imports),
            all_methods_code=all_methods_code,
            all_events_code=all_events_code
        )

    def to_file(self, file_path: Path) -> None:
        """生成domain文件到file_path"""
        logger.debug(f'{self.domain} to file {file_path}')
        with file_path.open('w', encoding='utf-8') as f:
            f.write(self.generate_code())


class CDPTopDomain(BaseModel):
    domains: list[CDPDomain]

    @staticmethod
    def types_to_file(file_path: Path, has_types_domain: list[CDPDomain]) -> None:
        types_code = ''
        types_for_class = ''
        all_domains = []

        for _domain_obj in has_types_domain:
            properties = ''
            for _type in _domain_obj.types:
                types_code += _type.generate_code(domain_obj=_domain_obj)
                properties += indent(f'{_type.id} = {_domain_obj.domain}{_type.id}\n')
            types_for_class += types_public_class_format(
                class_name=_domain_obj.domain,
                properties=properties
            )
            all_domains.append(_domain_obj.domain)

        source = types_module_format(
            all_domains=all_domains,
            types_code=types_code,
            types_for_class=types_for_class
        )
        
        with file_path.open('w', encoding='utf-8') as f:
            f.write(source)

    def to_dir(self, dir_path: Path):
        """写入所有CDPDomain文件到文件夹路径"""
        has_types_domain = []

        for domain in self.domains:
            # domain.to_file(dir_path / f'{domain.domain}.py')

            if domain.types:
                has_types_domain.append(domain)

        # 统一写入types到同一文件，防止互相导入
        self.types_to_file(dir_path / '_types.py', has_types_domain)


