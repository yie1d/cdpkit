from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from cdpkit.logger import logger
from generator.cdp import (
    CDPCommand,
    CDPDomain,
    CDPEvent,
    CDPProperty,
    CDPTopDomain,
    CDPType,
    CDPVariableType,
)
from generator.format import (
    make_class,
    make_common_types_module,
    make_methods_init,
    make_module,
    make_property,
    make_ref_imports,
)
from generator.utils import indent, rename_camel2snake, rename_in_python


@dataclass
class GenerateContext:
    """
    Code generation context class.

    Stores global information required during the generation process.
    """
    domain: CDPDomain | None = None
    ref_imports_set: set[str] | None = None
    files_all: dict[str, list[str]] | None = None

    def get_imports(self) -> set[str]:
        """
        Get the set of class names to be imported (filter out invalid keys).

        Returns:
            set[str]: Processed set of referenced imports (set of class names as strings)
        """
        if self.ref_imports_set is None:
            return set()
        else:
            # Keys to be deleted
            delete_keys = ['']
            if not self.domain.types:
                delete_keys.append(self.domain.domain)

            for _key in delete_keys:
                try:
                    self.ref_imports_set.remove(_key)
                except KeyError:
                    pass
            return self.ref_imports_set

    def clear_ref(self) -> None:
        """Clear the set of referenced imports (reset the context)."""
        if self.ref_imports_set is not None:
            self.ref_imports_set.clear()

    def add_files_all(self, file_type: str, var_name: str) -> None:
        """
        Add a variable name to the file mapping.

        Args:
            file_type (str): File type (e.g., "types", "events")
            var_name (str): Variable name to be added to the corresponding file type
        """
        if self.files_all is None:
            return

        self.files_all[file_type.lower()].append(var_name)


class CodeGenerator:
    """Base class for code generation, providing context management."""
    def __init__(
        self,
        context: GenerateContext
    ) -> None:
        self.context = context


class GenerateProperty(CodeGenerator):
    """Property generator for handling code generation of CDPProperty objects."""
    def __init__(self, property_obj: CDPProperty, context: GenerateContext):
        super().__init__(context)
        self.property_obj = property_obj

        # if property is optional, default_value will be created
        self._hint: str = self.property_obj.hint_type(self.context.domain, self.context.ref_imports_set)
        self._name: str | None = None
        self._default_value: str | None = None
        self._tips: str | None = None
        self._snake_name: str | None = None

    @property
    def snake_name(self) -> str:
        """Get the property name in snake case (convert from camel case)."""
        if self._snake_name is None:
            self._snake_name = rename_camel2snake(self.property_obj.name)
        return self._snake_name

    @property
    def hint(self):
        """Get the type hint string (including optional, enum, etc. modifiers)."""
        return self._hint

    @property
    def name(self) -> str:
        """Get the property name."""
        if self._name is None:
            self._name = self.property_obj.name
        return self._name

    @property
    def default_value(self) -> str:
        """Get the default value."""
        if self._default_value is None:
            self._default_value = self.property_obj.default_value
        return self._default_value

    @property
    def tips(self) -> str:
        """Get the status tips (experimental/deprecated markers)."""
        if self._tips is None:
            self._tips = self.property_obj.tips()
        return self._tips

    def generate_simple_code(self) -> str:
        """
        Generate simple property code (without description).

        Returns:
            str: Generated property code string (e.g., "name: str | None = None  # tips")
        """
        return make_property(
            name=self.name,
            hint=self.hint,
            value=self.default_value,
            tips=self.tips
        )

    def generate_code(self) -> str:
        """
        Generate complete property code (including description and indentation).

        Returns:
            str: Generated property code with description and indentation
        """
        _description = self.property_obj.textwrap_description(width=80, initial_indent='    # ')

        return _description + '\n' + indent(self.generate_simple_code()) + '\n'


class GenerateType(CodeGenerator):
    """Type generator for handling code generation of CDPType objects."""
    def __init__(
        self,
        type_obj: CDPType,
        context: GenerateContext,
        just_import: bool = False
    ) -> None:
        super().__init__(context=context)
        self._type_obj = type_obj
        self._just_import = just_import

        self.class_name = f'{context.domain.domain}{type_obj.id}'

    def generate_simple_code(self) -> str:
        """
        Generate simple type code (for basic types).

        Returns:
            str: Generated type code string (including docstring and property)
        """
        return self._type_obj.resolve_docstring(0) + '\n' + make_property(
            name=self.class_name,
            value=self._type_obj.hint_type(self.context.domain, self.context.ref_imports_set).replace('.', '')
        ) + '\n'

    def generate_type_enum_code(self) -> str:
        """
        Generate enum type code (for CDPType with enum).

        Returns:
            str: Generated enum class code
        """
        enum_properties_list = []

        for enum_item in self._type_obj.enum:
            enum_properties_list.append(indent(make_property(
                name=rename_in_python(enum_item).upper(),
                value=f'"{enum_item}"'
            )))

        enum_item_type = CDPVariableType[self._type_obj.type]

        match enum_item_type:
            case CDPVariableType.string:
                enum_parent = 'enum.StrEnum'
            case CDPVariableType.integer:
                enum_parent = 'enum.IntEnum'
            case _:
                enum_parent = f'{enum_item_type.value}, enum.Enum'

        return make_class(
            class_name=self.class_name,
            parent=enum_parent,
            description=self._type_obj.resolve_docstring(),
            properties='\n'.join(enum_properties_list),
        )

    def generate_object_code(self) -> str:
        """
        Generate object type code (for CDPType with properties).

        Returns:
            str: Generated object class code (inheriting from CDPObject)
        """
        properties_code_list = []

        for _property in self._type_obj.properties:
            properties_code_list.append(GenerateProperty(_property, self.context).generate_code())

        return make_class(
            class_name=self.class_name,
            parent='CDPObject',
            description=self._type_obj.resolve_docstring(),
            properties='\n'.join(properties_code_list)
        )

    def generate_code(self, just_import: bool = False) -> str:
        """
        Generate type code (select the generation method based on the type).

        Args:
            just_import (bool, optional): Whether to generate only import code (default: False)

        Returns:
            str: Generated type code (enum class, object class, or simple type)
        """
        logger.debug(f'Generating types for {self.context.domain.domain}')

        if self._just_import or just_import:
            return make_property(
                name=self._type_obj.id,
                value=self.class_name
            )
        else:
            if self._type_obj.enum:
                return self.generate_type_enum_code()
            elif self._type_obj.properties:
                return self.generate_object_code()
            else:
                return self.generate_simple_code()


class CommandInput:
    """Command input model generator for handling command parameters."""
    def __init__(self, command_generator_obj: 'GenerateCommand'):
        self._command_generator_obj = command_generator_obj

        self._properties_list = []
        self._init_input_properties_list = []
        self._init_super_use_properties_list = []
        self.input_class = 'None'
        self.code = ''

        self._init()

    @property
    def properties(self) -> str:
        """Get the property code of the input model (with indentation)."""
        if self._properties_list:
            return ' ' * 4 + f'\n{" " * 4}'.join(self._properties_list)
        return ''

    @property
    def init_input_properties(self) -> str:
        """Get the parameter code of the input model's initialization method (with indentation)."""
        if self._init_input_properties_list:
            return ' ' * 4 * 2 + f',\n{" " * 4 * 2}'.join(self._init_input_properties_list)
        return ''

    @property
    def init_super_use_properties(self) -> str:
        """Get the parameter code of the parent class's initialization method (with indentation)."""
        if self._init_super_use_properties_list:
            return ' ' * 4 * 3 + f',\n{" " * 4 * 3}'.join(self._init_super_use_properties_list)
        return ''

    def _init(self):
        """Initialize parameter processing (parse command parameters and generate code)."""
        if not self._command_generator_obj.command_obj.parameters:
            return

        self.input_class = f'{self._command_generator_obj.command_obj.class_name}Input'

        for _parameter in self._command_generator_obj.command_obj.parameters:
            parameter_obj = GenerateProperty(_parameter, self._command_generator_obj.context)
            self._properties_list.append(parameter_obj.generate_simple_code())
            self._init_input_properties_list.append(make_property(
                name=parameter_obj.snake_name,
                hint=parameter_obj.hint,
                value=parameter_obj.default_value
            ))
            self._init_super_use_properties_list.append(make_property(
                name=parameter_obj.name,
                value=parameter_obj.snake_name
            ))
        self.code = make_class(
            class_name=self.input_class,
            parent='InputModel',
            properties=self.properties
        )


class GenerateCommand(CodeGenerator):
    """Command generator for handling code generation of CDPCommand objects."""
    def __init__(self, command_obj: CDPCommand, context: GenerateContext):
        super().__init__(context)
        self.command_obj = command_obj

    def generate_output(self) -> tuple[str, str]:
        """
        Generate the command output model code.

        Returns:
            tuple[str, str]:
                Output class name and generated code (tuple, the first element is the class name, the second is the
                 code string)
        """
        if self.command_obj.returns is None:
            return 'None', ''

        if len(self.command_obj.returns) == 0:
            code = ''
            output_class = 'None'
        else:
            output_class = f'{self.command_obj.class_name}Output'

            output_model_properties_list = []

            for _return in self.command_obj.returns:
                _return_obj = GenerateProperty(property_obj=_return, context=self.context)
                output_model_properties_list.append(indent(_return_obj.generate_simple_code()))

            code = make_class(
                class_name=output_class,
                parent='OutputModel',
                properties='\n'.join(output_model_properties_list)
            )
        return output_class, code

    def generate_code(self) -> str:
        """
        Generate complete command code (input model, output model, command class).

        Returns:
            str: Generated command code string (including input, output models, and command class)
        """
        input_obj = CommandInput(self)

        output_class, output_code = self.generate_output()

        k_v = zip(('INPUT_VALIDATOR', 'OUTPUT_VALIDATOR'), (input_obj.input_class, output_class))
        properties_code = '\n'.join(map(lambda x: indent(make_property(name=x[0], value=x[1]), by=4), k_v))

        functions_code = make_methods_init(input_obj.init_input_properties, input_obj.init_super_use_properties)

        return f'{input_obj.code}\n\n{output_code}\n\n' + make_class(
            class_name=self.command_obj.class_name,
            parent=f'CDPMethod[{output_class}]',
            tips=self.command_obj.tips(),
            description=self.command_obj.resolve_docstring(),
            properties=properties_code,
            functions=functions_code
        )


class GenerateEvent(CodeGenerator):
    """Event generator for handling code generation of CDPEvent objects."""
    def __init__(self, event_obj: CDPEvent, context: GenerateContext):
        super().__init__(context)
        self._event_obj = event_obj

    def generate_code(self) -> str:
        """
        Generate event class code (including parameter properties).

        Returns:
            str: Generated event class code string (inheriting from CDPEvent)
        """
        properties_code_list = []

        if self._event_obj.parameters:
            for _parameter in self._event_obj.parameters:
                parameter_obj = GenerateProperty(_parameter, self.context)
                properties_code_list.append(indent(parameter_obj.generate_simple_code()))
        else:
            properties_code_list.append(indent('...'))

        return make_class(
            class_name=self._event_obj.class_name,
            parent='CDPEvent',
            description=self._event_obj.resolve_docstring(),
            properties='\n'.join(properties_code_list)
        )


def generate_domain_types(file_path: Path, context: GenerateContext) -> None:
    """
    Generate the domain type code file.

    Args:
        file_path (Path): Output file path
        context (GenerateContext): Code generation context object
    """
    types_code_list = []
    for domain_type in context.domain.types:
        generate_types_obj = GenerateType(
                type_obj=domain_type,
                context=context,
                just_import=True
            )
        types_code_list.append(
            generate_types_obj.generate_code()
        )
        context.ref_imports_set.add(generate_types_obj.class_name)
        context.add_files_all('types', domain_type.id)

    if types_code_list:
        with file_path.open('w', encoding='utf-8') as f:
            f.write(make_module(
                domain=context.domain.domain,
                description=context.domain.description,
                ref_imports=make_ref_imports(context.get_imports()),
                main_code='\n'.join(types_code_list),
                hints='Types'
            ))


def generate_domain_events(file_path: Path, context: GenerateContext) -> None:
    """
    Generate the domain event code file.

    Args:
        file_path (Path): Output file path
        context (GenerateContext): Code generation context object
    """
    event_code = ''

    for domain_event in context.domain.events:
        logger.debug(f'domain_event: {domain_event}')
        event_code += GenerateEvent(domain_event, context=context).generate_code()
        context.add_files_all('events', domain_event.class_name)

    with file_path.open('w', encoding='utf-8') as f:
        f.write(make_module(
            domain=context.domain.domain,
            description=context.domain.description,
            ref_imports=make_ref_imports(context.get_imports()),
            main_code=event_code,
            hints='Events'
        ))


def generate_commands_code(file_path: Path, context: GenerateContext) -> None:
    """
    Generate the domain command code file.

    Args:
        file_path (Path): Output file path
        context (GenerateContext): Code generation context object
    """
    commands_code = ''

    for domain_command in context.domain.commands:
        generate_command_obj = GenerateCommand(domain_command, context=context)
        commands_code += generate_command_obj.generate_code()
        context.add_files_all('methods', domain_command.class_name)

    with file_path.open('w', encoding='utf-8') as f:
        f.write(make_module(
            domain=context.domain.domain,
            description=context.domain.description,
            ref_imports=make_ref_imports(context.get_imports()),
            main_code=commands_code,
            hints='Methods'
        ))


def generate_types_file(file_path: Path, has_types_domain: list[CDPDomain]) -> None:
    """
    Generate the global types file (including types from all domains).

    Args:
        file_path (Path): Output file path
        has_types_domain (list[CDPDomain]): List of domains containing types
    """
    types_for_class = ''
    generate_code = ''

    for domain in has_types_domain:
        domain_context = GenerateContext(domain)

        domain_types_properties_list = []
        for _type in domain.types:

            generate_code += GenerateType(_type, domain_context).generate_code()

            domain_types_properties_list.append(indent(make_property(
                name=_type.id,
                value=f'{domain.domain}{_type.id}'
            )))

        types_for_class += make_class(
            class_name=domain.domain,
            properties='\n'.join(domain_types_properties_list)
        )

    with file_path.open('w', encoding='utf-8') as f:
        f.write(make_common_types_module(
            generate_code,
            types_for_class
        ))


def generate_domain(domain_dir_path: Path, domain: CDPDomain) -> None:
    """
    Generate all code files for a single domain (types, events, commands).

    Args:
        domain_dir_path (Path): Domain directory path
        domain (CDPDomain): Domain object
    """
    domain_dir_path.mkdir(exist_ok=True)
    context = GenerateContext(domain=domain, ref_imports_set=set(), files_all=defaultdict(list))

    generate_domain_types(domain_dir_path / 'types.py', context)
    context.clear_ref()
    context.ref_imports_set.add(domain.domain)

    generate_domain_events(domain_dir_path / 'events.py', context)
    context.clear_ref()
    context.ref_imports_set.add(domain.domain)

    generate_commands_code(domain_dir_path / 'methods.py', context)
    context.clear_ref()
    context.ref_imports_set.add(domain.domain)

    init_content = ''

    all_imports = ''
    for k, v in context.files_all.items():
        v_list = ",\n".join([indent(_, 4) for _ in v])
        init_content += f'from .{k} import (\n{v_list}\n)\n'
        all_imports += f'{v_list},\n'

    with domain_dir_path.joinpath('__init__.py').open('w', encoding='utf-8') as f:
        f.write(f'{init_content}\n__all__ = [\n{all_imports}]\n')


def generate_to_dir(top_domain: CDPTopDomain, output_dir: Path):
    """
    Generate code for all domains to the output directory.

    Args:
        top_domain (CDPTopDomain): Top-level domain object (containing all CDP domains)
        output_dir (Path): Output directory path
    """
    has_types_domain = []

    for domain in top_domain.domains:
        generate_domain(output_dir / f'{domain.domain}', domain)

        if domain.types:
            has_types_domain.append(domain)

    generate_types_file(output_dir / '_types.py', has_types_domain)  # Generate the global types file
