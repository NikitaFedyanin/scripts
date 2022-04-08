import re
import os

methods_matches = []
all_methods_matches = []
file_counter = 0


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


def find_methods_in_file(template_path, methods, match_mode):
    global file_counter
    tmp = None
    charset = get_encoding(template_path)
    with open(template_path, 'r', encoding=charset) as f:
        try:
            tmp = f.read()
        except:
            pass

    if tmp:
        for method in methods:
            re_method = None
            if match_mode == 'полный':
                re_method = re.compile(f'\"{method.split(".")[0]}\".*(?:\n|).*\"{method.split(".")[1]}\"')
            if match_mode == 'объект':
                re_method = re.compile(f'.*\"{method.split(".")[0]}\".*')
            if match_mode == 'метод':
                re_method = re.compile(f'.*\"{method.split(".")[1]}\".*')
            cpp_method_in_controller = re_method.search(tmp)
            if cpp_method_in_controller:
                methods_matches.append([method, cpp_method_in_controller[0]])
                methods.pop(methods.index(method))
                print('{0:<50}{1}'.format(method, cpp_method_in_controller[0].replace('\n', '')))
            file_counter += 1
            # print(f'Проверено {file_counter} файлов')


def find_methods(path_dir, methods, match_mode='полный'):
    files = os.listdir(path_dir)
    for i in files:
        if 'git' not in i:
            is_file = os.path.isfile(path_dir + '\\' + i)
            if not is_file:
                find_methods(path_dir + '\\' + i, methods, match_mode)
            elif is_file and 'cpp' in i:
                find_methods_in_file(path_dir + '\\' + i, methods, match_mode)


def execute(path_dir):
    global methods_matches
    with open('methods.txt', 'r', encoding='UTF-8') as f:
        methods = list(set(f.read().split('\n')))
    start_len = len(methods)

    print(f'Поиск методов запущен, режим - полный')
    find_methods(path_dir, methods, match_mode='полный')
    print(f'Найдено {len(methods_matches)} совпадений в режиме - полный\n\nНЕ НАЙДЕНЫ:')
    print('\n'.join([i for i in methods]))
    print('\n\n\n\n\n')
    # if methods:
    #     methods_matches = []
    #     print(f'Поиск методов запущен, режим - метод')
    #     find_methods(path_dir, methods, match_mode='метод')
    #     print(f'Найдено {len(methods_matches)} совпадений в режиме метод')
    #     print('\n'.join(['{0:<50}{1}'.format(i[0], i[1].replace('\n', '')) for i in methods_matches]))
    #     print('\n\n\n\n\n')
    # if methods:
    #     methods_matches = []
    #     print(f'Поиск методов запущен, режим - объект')
    #     find_methods(path_dir, methods, match_mode='объект')
    #     print(f'Найдено {len(methods_matches)} совпадений в режиме объект')
    #     # print('\n'.join(['{0:<50}{1}'.format(i[0], i[1].replace('\n', '')) for i in methods_matches]))
    #     print('\n\n\n\n\n')

    print(f'Найдено совпадений: {start_len - len(methods)} из {start_len}')


execute(r'C:\Работа\Controllers\communicator')
