import glob
import os.path
import re
import importlib.util


func_param = re.compile(r'\w+\(\s*self,(.+)\):')
file_data_params = re.compile(r'@file_data\((.+)\)')
re_not_space = re.compile(r'^\S+')
re_skip_ddt = re.compile(r"skip_ddt\(([\\'\"]{1,2}[\w\s]+[\\'\"]{1,2}), ([\w\d]+)\)")
re_empty = re.compile(r'\s+')
re_def = re.compile(r'(def|class)\s{1,3}\w+\(')


replace_dict = {
    '@id_check(': '@pytest.mark.id_check(',
    '@skip(': '@pytest.mark.skip(',
    'self.fail(': 'pytest.fail(',
    'self.skip(': 'pytest.skip(',
    'def setup_class(cls):': 'def setUpClass(cls):',
    'def setup(self):': 'def setUp(self):',
    'def teardown(self):': 'def tearDown(self):',
    'def teardown_class(cls):': 'def tearDownClass(cls):',
    'reset_caret_color()': 'self.browser.reset_caret_color()'
}

re_tags = re.compile('(TAGS_TO_START|TAGS_NOT_TO_START) = .*(-)')


def convert_skip_if(file_str):
    if '@skip_if(' not in file_str:
        return file_str

    new_line = ''
    for line in file_str.split('\n'):
        if '@skip_if(' in line:
            line = line.replace('@skip_if(', '@pytest.mark.skipif(')
            f, reason = line.split(',', 1)
            if reason.strip().endswith(')'):
                reason = reason.strip()[:-1]
                line = f'{f}, reason={reason})'
            else:
                reason = reason.strip()
                line = f'{f}, reason={reason}'
        new_line += line + '\n'
    return new_line


def convert_config(file_path):
    f = os.path.split(file_path)[0]
    for config_file in glob.glob(f'{f}/config/*.ini'):
        lines = ''
        with open(config_file, 'r', encoding='utf-8') as f_c:
            ls = f_c.readlines()
            for line in ls:
                if re_tags.search(line):
                    line = line.replace('-', '_')
                lines += line + '\n'
        with open(config_file, 'w', encoding='utf-8') as file:
            file.write(lines)


def convert_mark(file_str, file_path):

    def patch(file_str2):
        file_str2 = file_str2.replace('\n', '')
        indent, _ = file_str2.split('@mark', 1)
        s_strip = file_str2.strip()
        s_strip = s_strip.replace('@mark(', '').replace('"', "").replace("'", "").replace(')', '')
        params = [p.strip().replace('-', '_') for p in s_strip.split(',')]
        return '\n'.join([f'{indent}@pytest.mark.{p}' for p in params if p])

    new_lines = ''
    mark_str = ''
    path_config = False
    for line in file_str.split('\n'):
        line_strip = line.strip()

        # if '@mark' in line and not path_config:
        #     convert_config(file_path)
        #     path_config = True
        if not line_strip.startswith('#'):
            if '@mark' in line and line_strip.endswith(')'):
                line = patch(line)
            elif '@mark' in line:
                mark_str += line
            elif mark_str and line_strip.endswith(')'):
                line = patch(mark_str)
                mark_str = ''

        if not mark_str:
            new_lines += f'{line}\n'
    return new_lines


def convert_all(lines, path):
    # del ddt
    new_lines = lines.replace('@ddt\n', '')

    # add import pytest
    try:
        start_import = new_lines.index('import')
    except ValueError:
        start_import = 9999
    start_import2 = new_lines.index('from')
    _min = min((start_import2, start_import))
    new_imports = 'import pytest\n'
                  # 'from pytest_atf.case import TestCase\n' \
                  # 'from fixtures.parametrize import file_data\n'
    new_lines = new_lines[:_min] + new_imports + new_lines[_min:]

    # new_lines = new_lines.replace('from atf import *\n', '')
    # new_lines = new_lines.replace('from atf.ui import *\n', '')
    for k, v in replace_dict.items():
        new_lines = new_lines.replace(k, v)

    # del run_tests
    try:
        last_index = new_lines.index('if __name__ ==')
        new_lines = new_lines[:last_index].strip() + '\n'
    except ValueError:
        new_lines = new_lines.strip() + '\n'
        print('Not found run_tests', path)

    return new_lines


def add_param_to_func(def_func, param):
    match2 = func_param.search(def_func)
    if not match2:
        value = def_func.replace('(self)', f'(self, {param})')
    else:
        value = def_func.replace('(self,', f'(self, {param},')
    return value


def convert_subtests(file_str):
    if 'self.subTest' not in file_str:
        return file_str

    new_lines = ''
    start = end = False
    def_func = ''
    func_body = ''
    for line in file_str.split('\n'):
        line += '\n'

        line_strip = line.strip()

        if def_func and start and end and 'self.subTest' in line and not line_strip.startswith('#'):
            def_func = add_param_to_func(def_func, 'subtests')
            new_lines += def_func + func_body
            start = end = False
            def_func = func_body = ''

        if 'self.subTest' in line and not line_strip.startswith('#'):
            index = line.find('w')
            line = ' ' * index + 'with subtests.test():\n'

        if end and (re_def.search('def') or re_not_space.search(line)):
            start = end = False
            if def_func:
                new_lines += def_func
            if func_body:
                new_lines += func_body
            def_func = func_body = ''

        if start and end:
            func_body += line

        if line_strip.startswith('def test'):
            start = True

        if start and not end:
            def_func += line

            if line_strip.endswith('):'):
                end = True

        if not start:
            new_lines += line

    if def_func:
        new_lines += def_func

    if func_body:
        new_lines += func_body

    return new_lines


def convert_layout(file_str):
    if 'self.capture' not in file_str:
        return file_str

    new_lines = ''
    start = end = False
    def_func = ''
    func_body = ''
    for line in file_str.split('\n'):
        line += '\n'

        line_strip = line.strip()


        if def_func and start and end and 'self.capture' in line and not line.startswith('#'):
            def_func = add_param_to_func(def_func, 'layout')
            new_lines += def_func + func_body
            start = end = False
            def_func = func_body = ''

        if 'self.capture' in line and not line.startswith('#'):
            line = line.replace('self.capture', 'layout.capture')

        if end and (re_def.search(line_strip) or re_not_space.search(line)):
            start = end = False
            if def_func:
                new_lines += def_func
            if func_body:
                new_lines += func_body
            def_func = func_body = ''

        if start and end:
            func_body += line

        if line_strip.startswith('def test'):
            start = True

        if start and not end:
            def_func += line

            if line_strip.endswith('):'):
                end = True

        if not start:
            new_lines += line

    if def_func:
        new_lines += def_func

    if func_body:
        new_lines += func_body

    return new_lines


def convert_file_data(file_str):
    new_lines = ''
    start = end = _def = False
    data_decorator_code = ''
    for line in file_str.split('\n'):
        line += '\n'

        line_strip = line.strip()
        if start and end:
            start = _def = end = False
            data_decorator_code = ''

        if line_strip == '@unpack':
            continue

        if line_strip.startswith('@file_data'):  # or line_strip.startswith('@unpack'):
            start = True

        if start:
            data_decorator_code += line

            if line_strip.startswith('def ') or _def:
                _def = True
            if line_strip.endswith('):'):
                end = True
                # print(data_decorator_code)
                _data, func = data_decorator_code.split('def ')
                _data = _data.strip().replace('@unpack', '')
                match = file_data_params.search(_data)
                params_file_data = match.group(1)
                func = func.replace('\n', '')
                func = re_empty.sub(' ', func)
                match2 = func_param.search(func)
                params = match2.group(1)
                start_params = match2.start(1)
                params_pytest = params.strip().replace('**', '').replace('*', '')
                indent = " " * 4
                decorator = (f'{indent}@file_data("{params_pytest.replace(" ", "")}", '
                             f'{params_file_data})\n'
                             f'{indent}def ' + func[:start_params] + ' ' + params_pytest + '):\n')
                new_lines += decorator
        else:
            new_lines += line
    return new_lines


def convert_data_decorator(file_str):
    new_lines = ''
    start = end = _def = False
    data_decorator_code = others_decorators = ''
    for line in file_str.split('\n'):
        line += '\n'

        line_strip = line.strip()
        if start and end:
            start = _def = end = False
            data_decorator_code = ''
            others_decorators = ''

        if line_strip == '@unpack':
            continue

        if line_strip.startswith('@data'): #or line_strip.startswith('@unpack'):
            start = True

        if start:
            if line_strip.startswith('@') and not line_strip.startswith('@data') or line_strip.startswith('@unpack'):
                others_decorators += line
            else:
                data_decorator_code += line

            if line_strip.startswith('def ') or _def:
                _def = True
            if '):' in line_strip:
                end = True
                # print(data_decorator_code)
                # TODO тут надо еще отслеживать нет ли внутри функции subtest
                #  / capture и добавлять в параметры нужную фикстуру
                _data, func = data_decorator_code.split('def ')
                _data = _data.strip().replace('@unpack', '')
                _data = _data[:_data.rindex(')')]
                _data = _data.replace('@data(', '')
                data2 = ''
                for j in _data.strip().split('\n'):
                    data2 += f'{" " * 8} {j.strip()}\n'
                data2 = data2.replace('**', '').replace('*', '')
                func = func.replace('\n', '')
                func = re_empty.sub(' ', func)
                match = func_param.search(func)
                params = match.group(1)
                start_params = match.start(1)
                params_pytest = params.strip().replace('**', '').replace('*', '')
                params_pytest = ', '.join([i.strip() for i in params_pytest.split(',')])
                indent = " " * 4
                if len(data2.split(',')) > 1:
                    data2 = (f'(\n'
                             f'{data2}'
                             f'{indent})')
                else:
                    data2 = data2.strip()
                decorator = (f'{indent}@pytest.mark.parametrize("{params_pytest.replace(" ", "")}", {data2})\n'
                             f'{others_decorators}'
                             f'{indent}def ' + func[:start_params] + ' ' + params_pytest + '):\n')
                new_lines += decorator
        else:
            new_lines += line
    return new_lines


def convert_file(file_path, override=False):
    with open(file_path, 'r', encoding='utf-8') as file_handler:
        lines = file_handler.read()
        if 'import pytest' not in lines:
            lines = convert_file_data(lines)
            lines = convert_data_decorator(lines)
            lines = convert_subtests(lines)
            lines = convert_layout(lines)
            lines = convert_mark(lines, file_path)
            lines = convert_skip_if(lines)
            lines = convert_all(lines, file_path)
    if not override:
        file_path = os.path.splitext(file_path)[0] + '_2.py'
    with open(file_path, 'w', encoding='utf-8') as file_handler:
        file_handler.write(lines)


def check_file(file_path):
    try:
        folder_name, file_name2 = os.path.split(file_path)
        os.chdir(folder_name)
        module_name = os.path.splitext(file_name2)[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        return True
    except Exception as err:
        print(f'{file_path}\n{err}')
        return err


def main():


    import os
    folder_path = '/Users/ant/work/tests/inside/test-warehouse/mk/**/test_*.py'
    folder_path = 'C:\\Работа\\Репозитории\\api\\**\\test_*.py'
    cfg_files = glob.iglob(folder_path, recursive=True)
    bad_files = []
    for file in cfg_files:
        if 'data_asserts' in file:
            continue
        try:
            convert_file(file, override=True)
        except Exception as err:
            print(file)
            raise err

        # test compile file
        folder, file_name = os.path.split(file)
        config_folder = os.path.join(folder, 'config')

        if os.path.isdir(config_folder):
            cfg_files = os.listdir(config_folder)
            for cfg in cfg_files:
                dst_file = os.path.join(config_folder, cfg)
                # if os.path.exists(config_ini):
                #     os.remove(config_ini)
                # shutil.copyfile(dst_file, config_ini)
                from atf import Config
                Config(dst_file)
                res = check_file(file)
                if res is True:
                    break
            else:
                bad_files.append(file)

    from pprint import pprint
    pprint(bad_files)
#
# check_file('/Users/ant/work/tests/inside/test-messaging/smoke/test_contacts.py')
# convert_file('/Users/ant/work/tests/inside/test-messaging/smoke/test_dialogue_01.py')

if __name__ == '__main__':
    main()