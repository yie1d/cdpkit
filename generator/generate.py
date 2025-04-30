from collections import defaultdict
from pathlib import Path
from dataclasses import dataclass, field
from generator.logger import logger
from generator.cdp import CDPTopDomain, CDPDomain, CDPType, CDPVariableType, CDPProperty
from generator.format import *
from generator.exceptions import GeneratorNameNotFound
from generator.utils import rename_in_python, indent


@dataclass
class GenerateContext:
    domain: CDPDomain | None = None
    ref_imports_set: set[str] | None = None


class CodeGenerator:
    def __init__(
        self,
        context: GenerateContext
    ) -> None:
        self.context = context


class GenerateProperty(CodeGenerator):
    def __init__(self, property_obj: CDPProperty, context: GenerateContext):
        super().__init__(context)
        self.property_obj = property_obj

    def generate_code(self, with_description: bool = True):
        if with_description:
            _description = self.property_obj.textwrap_description(width=80, initial_indent='    # ')
        else:
            _description = ''

        # if property is optional, default_value will be created
        _hint = self.property_obj.hint_type(self.context.domain, self.context.ref_imports_set)

        return _description + '\n' + indent(make_property(
            name=self.property_obj.name,
            hint=_hint,
            value=self.property_obj.default_value,
            tips=self.property_obj.tips()
        ))


class GenerateTypes(CodeGenerator):
    def __init__(
        self,
        type_obj: CDPType,
        context: GenerateContext
    ) -> None:
        super().__init__(context=context)
        self.type_obj = type_obj

        self.class_name = f'{context.domain.domain}{type_obj.id}'

    def generate_simple_code(self):
        return self.type_obj.resolve_docstring(0) + '\n' + make_property(
            name=self.class_name,
            value=self.type_obj.hint_type(self.context.domain, self.context.ref_imports_set).replace('.', '')
        )

    def generate_type_enum_code(self):
        enum_properties = ''

        for enum_item in self.type_obj.enum:
            enum_properties += indent(make_property(
                name=rename_in_python(enum_item).upper(),
                value=f'"{enum_item}"'
            ))

        return make_class(
            class_name=self.class_name,
            parent=f'{CDPVariableType[self.type_obj.type].value}, enum.Enum',
            description=self.type_obj.resolve_docstring(),
            properties=enum_properties
        )

    def generate_object_code(self):
        properties_code = ''

        for _property in self.type_obj.properties:
            properties_code += GenerateProperty(_property, self.context).generate_code()

        return make_class(
            class_name=self.class_name,
            parent='CDPObject',
            description=self.type_obj.resolve_docstring(),
            properties=properties_code
        )

    def generate_code(self):
        logger.debug(f'Generating types for {self.context.domain.domain}')

        if self.type_obj.enum:
            return self.generate_type_enum_code()
        elif self.type_obj.properties:
            return self.generate_object_code()
        else:
            return self.generate_simple_code()


def generate_types(file_path: Path, has_types_domain: list[CDPDomain]) -> None:
    """写入所有CDPDomain的类型到文件"""
    types_for_class = ''
    generate_code = ''
    module_all = []

    for domain in has_types_domain:
        domain_context = GenerateContext(domain)

        domain_types_properties = ''
        for _type in domain.types:
            generate_code += GenerateTypes(_type, domain_context).generate_code()

            domain_types_properties += indent(make_property(
                name=_type.id,
                value=f'{domain.domain}{_type.id}'
            ))

        types_for_class += make_class(
            class_name=domain.domain,
            properties=domain_types_properties
        )
        module_all.append(indent(f'\'{domain.domain}\''))

    with file_path.open('w', encoding='utf-8') as f:
        f.write(make_types_module(
            ',\n'.join(module_all),
            generate_code,
            types_for_class
        ))


def generate_to_dir(top_domain: CDPTopDomain, output_dir: Path):
    """写入所有CDPDomain文件到文件夹路径"""
    has_types_domain = []

    for domain in top_domain.domains:
        # domain.to_file(output_dir / f'{domain.domain}.py')

        if domain.types:
            has_types_domain.append(domain)

    # 统一写入types到同一文件，防止互相导入
    generate_types(output_dir / '_types.py', has_types_domain)
