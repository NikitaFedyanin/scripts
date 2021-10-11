import re
import os
count = 0

def quot(matcher):
    print(matcher[0])
    re_comp = re.search('(self\.[a-zA-Z_]*(?:\.[a-zA-Z_]*|))(?:|\s*),(?:\s*|)((?:\'.*\'|\w*))', matcher[0])
    if re_comp:
        custom_list = re_comp.groups()[0]
        value = re_comp.groups()[1]
        result = f'{custom_list}.item(contains_text={value}).should_be(Displayed)'
        global count
        count += 1
    else:
        result = matcher[0]
    return result


def get_encoding(template_path):
    charsets = ['UTF-8', 'windows-1251']
    for i in charsets:
        try:
            with open(template_path, 'r', encoding=i) as f:
                f.read()
                return i
        except UnicodeDecodeError:
            pass


def refractor_file(template_path):
    tmp = None
    charset = get_encoding(template_path)
    with open(template_path, 'r', encoding=charset) as f:
        try:
            tmp = f.read()
            tmp = re.sub('get_item_from_custom_list.*', quot, tmp)
        except:
            print(template_path)
    if tmp:
        with open(template_path, 'w', encoding=charset) as f:
            f.write(tmp)


def replace_var_in_dir(path_dir):
    files = os.listdir(path_dir)
    for i in files:
        if 'git' not in i:
            is_file = os.path.isfile(path_dir + '\\' + i)
            if not is_file:
                replace_var_in_dir(path_dir + '\\' + i)
            elif is_file and i.endswith('.py'):
                refractor_file(path_dir + '\\' + i)


replace_var_in_dir('C:\Autotests-mobile\\retail_android')
print(f'Произведено {count} замен')
