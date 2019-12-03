import itertools
import re


DYNAMIC_TYPES = ['bytes', 'string']

STATIC_TYPE_ALIASES = ['uint', 'int', 'byte']
STATIC_TYPES = list(itertools.chain(
    ['address', 'bool'],
    ['uint{0}'.format(i) for i in range(8, 257, 8)],
    ['int{0}'.format(i) for i in range(8, 257, 8)],
    ['bytes{0}'.format(i) for i in range(1, 33)],
))

TYPE_REGEX = '|'.join((
    _type + r'(?![a-z0-9])'
    for _type
    in itertools.chain(STATIC_TYPES, STATIC_TYPE_ALIASES, DYNAMIC_TYPES)
))

CANONICAL_TYPE_REGEX = '|'.join((
    _type + r'(?![a-z0-9])'
    for _type
    in itertools.chain(DYNAMIC_TYPES, STATIC_TYPES)
))

NAME_REGEX = (
    r'[a-zA-Z_]'
    r'[a-zA-Z0-9_]*'
)

SUB_TYPE_REGEX = (
    r'\['
    r'[0-9]*'
    r'\]'
)

ARGUMENT_REGEX = (
    r'(?:{type})'
    r'(?:(?:{sub_type})*)?'
    r'\s+'
    '{name}'
).format(
    type=TYPE_REGEX,
    sub_type=SUB_TYPE_REGEX,
    name=NAME_REGEX,
)


def extract_function_name(raw_signature):
    fn_name_match = re.match(
        r'^(?:function\s+)?\s*(?P<fn_name>[a-zA-Z_][a-zA-Z0-9_]*).*\((?P<arglist>.*)\).*$',
        raw_signature,
        flags=re.DOTALL,
    )
    if fn_name_match is None:
        raise ValueError("Did not match function name")
    group_dict = fn_name_match.groupdict()
    fn_name = group_dict['fn_name']
    if fn_name == 'function':
        raise ValueError("Bad function name")
    arglist = group_dict['arglist']
    return fn_name, arglist


RAW_FUNCTION_REGEX = (
    r'function\s+{name}\s*\(\s*(?:{arg}(?:(?:\s*,\s*{arg}\s*)*)?)?\s*\)'.format(
        name=NAME_REGEX,
        arg=ARGUMENT_REGEX,
    )
)


def is_raw_function_signature(signature):
    match = re.fullmatch('^' + RAW_FUNCTION_REGEX + '$', signature)
    if match:
        try:
            extract_function_name(signature)
        except ValueError:
            return False
        else:
            return True
    else:
        return False


def extract_function_signatures(code):
    """
    Given a string of solidity code, extract all of the function declarations.
    """
    matches = re.findall(RAW_FUNCTION_REGEX, code)
    return matches or []


NORM_FUNCTION_REGEX = (
    '^'
    r'{fn_name}\('
    '('
    '({type})({sub_type})*'
    '(,({type})({sub_type})*)*'
    ')?'
    r'\)$'
).format(
    fn_name=NAME_REGEX,
    type=CANONICAL_TYPE_REGEX,
    sub_type=SUB_TYPE_REGEX,
)


def is_canonical_function_signature(signature):
    if re.fullmatch(NORM_FUNCTION_REGEX, signature):
        return True
    else:
        return False


def to_canonical_type(value):
    if value == 'int':
        return 'int256'
    elif value == 'uint':
        return 'uint256'
    elif value == 'byte':
        return 'bytes1'
    else:
        return value


FUNCTION_ARGUMENT_TYPES_REGEX = (
    '(?P<type>{type})'
    '(?P<sub_type>(?:{sub_type})*)'
    r'(?:\s*)'
).format(
    type=TYPE_REGEX,
    sub_type=SUB_TYPE_REGEX,
    name=NAME_REGEX,
)


def normalize_function_signature(raw_signature):
    fn_name, args = extract_function_name(raw_signature)
    raw_arguments = re.findall(FUNCTION_ARGUMENT_TYPES_REGEX, args)

    arguments = [
        "".join((to_canonical_type(t), sub))
        for t, sub in raw_arguments
    ]
    return "{fn_name}({fn_args})".format(fn_name=fn_name, fn_args=','.join(arguments))
