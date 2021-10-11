# -*- coding: utf-8 -*-
import json


class JsonDiff:

    ignore_values = ['ignore']                  # значения в json которые игнорируются при сравнении
    ignore_tags = ['ignore', 'protocol']        # тэги в json которые игнорируются при сравнении

    def __init__(self, left_json, right_json):
        """Первым задаём ЭТАЛОННЫЙ json! Вторым полученный!"""

        self.left_json = self.check_type(left_json)
        self.right_json = self.check_type(right_json)
        self.diffs = list()

    @staticmethod
    def diff_keys(left_dict, right_dict):
        """Сравнивает ключи с словаре"""

        left_set = set(left_dict)
        right_set = set(right_dict)
        diff = left_set.difference(right_set)
        overlap = left_set.intersection(right_set)
        return diff, overlap

    @staticmethod
    def check_type(tmp_json):
        """Проверяем типы json при инициализации класса"""

        if isinstance(tmp_json, dict):
            pass
        elif isinstance(tmp_json, str):
            tmp_json = json.loads(tmp_json)
        else:
            raise Exception('Не верный тип json')
        return tmp_json

    def diff_dict(self, left_dict, right_dict, tmp_key=None):
        """Сравнение словарей"""

        diff_tags, check_tags = self.diff_keys(left_dict, right_dict)
        for i in diff_tags:
            if not i in self.ignore_tags:
                self.diffs.append([i])
        for key in check_tags:
            if not tmp_key is None:
                tmp = tmp_key + [key]
            else:
                tmp = [key]

            if left_dict[key] != right_dict[key]:
                if not (left_dict[key] in self.ignore_values or key in self.ignore_tags):
                    if not isinstance(left_dict[key], (list, dict)):
                        self.diffs.append([tmp, right_dict[key]])
                    elif not isinstance(left_dict[key], type(right_dict[key])):
                        self.diffs.append([tmp, right_dict[key]])
                    else:
                        self.diff(left_dict[key], right_dict[key], tmp)

    def diff_list(self, left_list, right_list, tmp_key=None):
        """Сравнение списков

        :param left_list: эталонный
        :param right_list: проверяемый
        :param tmp_key: для json path

        """
        if left_list != right_list:
            if len(left_list) != len(right_list):
                self.diffs.append([tmp_key, right_list])
            else:
                for i in range(len(left_list)):
                    tmp = tmp_key + [i]
                    if left_list[i] != right_list[i] and not left_list[i] in self.ignore_values:
                        if not isinstance(left_list[i], (list, dict)):
                            self.diffs.append([tmp, right_list[i]])
                        elif not isinstance(left_list[i], type(right_list[i])):
                            self.diffs.append([tmp, right_list[i]])
                        else:
                            self.diff(left_list[i], right_list[i], tmp)

    def diff(self, left_json=None, right_json=None, key=None):
        """Метод для сравнения json

        :param left_json: эталонный
        :param right_json: проверяемый
        :param key: для совместимости с другими методами

        """
        if left_json is None:
            left_json = self.left_json
        if right_json is None:
            right_json = self.right_json

        if isinstance(left_json, type(right_json)) and type(left_json) is dict:
            self.diff_dict(left_json, right_json, key)
        elif isinstance(left_json, type(right_json)) and type(left_json) is list:
            self.diff_list(left_json, right_json, key)
        return self.diffs


def json_diff(left_json, right_json):
    """Метод сравнивает два json

    :param left_json: эталонный
    :param right_json: проверяемый
    :return: возвращает список списков различий

    """
    tmp_diff = JsonDiff(left_json, right_json)
    return tmp_diff.diff()