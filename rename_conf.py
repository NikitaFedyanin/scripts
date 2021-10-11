import re
import os


def quot(matcher):
    return '"' + matcher[0].strip() + '"'


def get_encoding(template_path):
    charsets = ['UTF-8', 'windows-1251']
    for i in charsets:
        try:
            with open(template_path, 'r', encoding=i) as f:
                f.read()
                return i
        except UnicodeDecodeError:
            pass


def refractor_template(template_path):
    tmp = None
    charset = get_encoding(template_path)
    with open(template_path, 'r', encoding=charset) as f:
        try:
            tmp = f.read()
        except:
            print(template_path)
    if tmp:
        with open(template_path.replace('ios_fix_inside', 'ios_communicator_fix'), 'w', encoding=charset) as f:
            f.write(tmp)
        os.remove(template_path)


def replace_var_in_dir(path_dir):
    files = os.listdir(path_dir)
    for i in files:
        if 'git' not in i:
            is_file = os.path.isfile(path_dir + '\\' + i)
            if not is_file:
                replace_var_in_dir(path_dir + '\\' + i)
            elif is_file and i == 'ios_fix_inside.ini':
                refractor_template(path_dir + '\\' + i)


replace_var_in_dir('C:\Autotests-mobile\ios_apps')
