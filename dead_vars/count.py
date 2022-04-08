import re

# re_vars = re.compile('Unused variable \'(.*)\'')
re_vars = re.compile('Unused variable \'(.*)\'')


def get_encoding(template_path):
    charsets = ['UTF-8', 'windows-1251']
    for i in charsets:
        try:
            with open(template_path, 'r', encoding=i) as f:
                f.read()
                return i
        except UnicodeDecodeError:
            pass


def create_regex():
    encoding = get_encoding('text.txt')
    with open('text.txt', 'r', encoding=encoding) as f:
        file = f.read()

    vars = '|'.join(re_vars.findall(file))
    asserts_regex = f"\\\"\$_(?:{vars})\\\""  # data.py
    # asserts_regex = f"def (?:{vars})\("  # functions
    # asserts_regex = f"(?:{vars})\("  # functions


    data_regex = f"^\s+(?:{vars})(?:\s+=\s+|=\s+|\s+=).*"

    with open('asserts_regex.txt', 'w') as f:
        f.write(asserts_regex)
    with open('data_regex.txt', 'w') as f:
        f.write(data_regex)


create_regex()
