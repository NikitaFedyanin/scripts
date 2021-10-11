# -*- coding: utf-8 -*-
import os
from atf import *
from string import Template
from data import Data
import json
from atf.api import *

conf = Config()


def read_file(file_path, encoding=None, delimiter='$_', idpattern=None, strip=True):
    """
    :param file_path: отностительный/полный путь к файлу
    :param strip: удалить переносы строк
    :return: возвращает файл одной строкой, удаляя пробелы вначале и конце строки
    """
    idpattern = idpattern if idpattern else r'([_a-zA-Zа-яА-Я][_a-zA-Zа-яА-Я0-9]*EXIT|[_a-zA-Zа-яА-Я][_a-zA-Zа-яА-Я0-9]*)'

    tmp_str = ''
    file_path = os.path.realpath(file_path)
    if os.path.isfile(file_path):
        if encoding:
            file = open(file_path, encoding=encoding)
        else:
            file = open(file_path)

        if strip:
            f = lambda line: line.strip()
        else:
            f = lambda line: line
        for line in file:
            line = f(line)
            if not line:
                continue
            tmp_str += line
        tmp = type("MyTemplate", (Template,), {"delimiter": delimiter, "idpattern": idpattern})(tmp_str)
        return tmp.substitute(**Data.__get_var__())


def send_notification(site, sid, doc_id, event_id):
    client = JsonRpcClient(site, sid=sid, verbose_log=2)
    client.type_response = 'value'
    client.call_rvalue('ERepNotice.AddNotice', ДокументОтправка=doc_id, Событие=event_id)


def read_file_with_screening(file_path, encoding=None, delimiter='$', idpattern=None, strip=True):
    """
    :param file_path: отностительный/полный путь к файлу
    :param strip: удалить переносы строк
    :return: возвращает файл одной строкой, удаляя пробелы вначале и конце строки
    """
    idpattern = idpattern if idpattern else r'([_a-z][_a-z0-9]*EXIT|[_a-z][_a-z0-9]*)'

    tmp_str = ''
    file_path = os.path.realpath(file_path)
    if os.path.isfile(file_path):
        if encoding:
            file = open(file_path, encoding=encoding)
        else:
            file = open(file_path)

        if strip:
            f = lambda line: line.strip()
        else:
            f = lambda line: line
        for line in file:
            line = f(line)
            if not line:
                continue
            tmp_str += line
        screening_dollar(tmp_str)
        tmp = type("MyTemplate", (Template,), {"delimiter": delimiter, "idpattern": idpattern})(tmp_str)
        return tmp.substitute(**Data.__get_var__())


def record_set_to_json(string):
    string = string.replace('\'None\'', 'None')
    string = string.replace('\'False\'', 'False')
    string = string.replace('\'True\'', 'True')
    string = string.replace('None', 'null')
    string = string.replace('True', 'true')
    string = string.replace('False', 'false')
    string = string.replace('\'', '\"')
    return string


def read_file_to_assert(file_path, encoding='utf-8'):
    string = read_file(file_path, encoding)
    string = record_set_to_json(string)  #
    return json.loads(string)


def read_file_to_assert_with_screening(file_path, encoding=None):
    string = just_read_file(file_path, encoding='UTF-8')
    string = screening_dollar(string)
    string = record_set_to_json(string)
    return json.loads(string)


def print_key_value(dict_item):
    for key in dict_item.keys():
        print(key, dict_item[key])


def just_read_file(file_path, encoding=None, strip=True):
    """
    :param file_path: отностительный/полный путь к файлу
    :param strip: удалить переносы строк
    :return: возвращает файл одной строкой, удаляя пробелы вначале и конце строки
    """
    tmp_str = ''
    file_path = os.path.realpath(file_path)
    if os.path.isfile(file_path):
        if encoding:
            file = open(file_path, encoding=encoding)
        else:
            file = open(file_path)

        if strip:
            f = lambda line: line.strip()
        else:
            f = lambda line: line
        for line in file:
            line = f(line)
            if not line:
                continue
            tmp_str += line
        return tmp_str


def screening_dollar(string):
    """ Экранирование заменяемых значений, для обработки скриптом sccript"""
    i_min_stack = ('$', '\'', '\"')
    j_stack = (',', '}', ']', ' ')
    for i in range(len(string)):
        if string[i] == '$' and string[i + 1] != '$' and string[i - 1] not in i_min_stack:
            for j in range(i + 1, len(string)):
                if string[j] in j_stack:
                    string = string[:i] + "\"" + string[i:j] + "\"" + string[j:]
                    break
    return string


def sccript(dict_sample, dict_answer):
    """ Рекурсивный обход словарей с одинаковой структурой и вывод в консоль значений соотвтетствующих атрибутам начинающимся с $ """
    if type(dict_sample) == dict:
        for key, value in dict_sample.items():
            if type(value) == str and value.startswith('$'):
                type_print(dict_sample[key], dict_answer[key])
            if type(value) == dict or type(value) == list:
                sccript(dict_sample[key], dict_answer[key])
    elif type(dict_sample) == list:
        for i in range(len(dict_sample)):
            if type(dict_sample[i]) == str and dict_sample[i].startswith('$'):
                type_print(dict_sample[i], dict_answer[i])
            elif type(dict_sample[i]) == dict or type(dict_sample[i]) == list:
                sccript(dict_sample[i], dict_answer[i])


def type_print(item_sample, item_answer):
    """ Вывод значений в зависимости от их типов"""
    if type(item_answer) == str:
        print(item_sample[1:], '= \'', end='')
        print(item_answer, end='')
        print('\'')
    else:
        print(item_sample[1:], '=', item_answer)


def get_attribut_for_data(json_answer, path_sample):
    """Вывести значения всех атрибутов из шаблона по адресу 'path_sample' по json ответу"""
    sample = read_file_to_assert_with_screening(path_sample, encoding='UTF-8')
    sccript(sample, json_answer)


def get_requirement_list(client, our_org):
    """Получаем список требований по организации"""
    requirement_list = client.call_rrecordset('Requirement.ListCursor',
                                              **generate_record_list(attachmentsLimit=2,
                                                                     ИдентификаторНашейОрганизации=our_org,
                                                                     ТипыДокументов=[
                                                                         'ИстребованиеФНС',
                                                                         'Истребование'])).result
    requirement_list = [i for i in requirement_list if
                        i['ДокументНашаОрганизация'] == int(our_org) and i['НазваниеОтправителя'] == 'Налоговая 2012']

    return requirement_list


def get_requirement(client, our_org):
    """Проверка, что в списке есть одно нужное требование
    return: требование
    """
    assert_that(lambda: len(get_requirement_list(client, our_org)), equal_to(1),
                'Требование не пришло или есть лишние требования', and_wait(40, 3))

    requirement_list = get_requirement_list(client, our_org)

    return requirement_list[0]


def delete_requirements(client, our_org):
    """Удаление требований"""
    requirement_list = get_requirement_list(client, our_org)

    for i in requirement_list:
        client.call_rvalue('Requirement.DeleteToBin', id=i['@Документ'])
