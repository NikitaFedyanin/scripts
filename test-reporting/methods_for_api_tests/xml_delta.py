# coding=utf-8
"""Модуль для сравнения двух xml файлов"""
from xml.etree import ElementTree


class DiffXML(object):
    """Класс для сравнения двух xml"""

    def __init__(self, left_xml, right_xml, ignore_tags=None, ignore_attrib=None, with_text=False):
        self.left_xml = self.__set_type(left_xml)
        self.right_xml = self.__set_type(right_xml)
        self.with_text = with_text
        if ignore_tags is None:
            self.ignore_tags = []
        else:
            self.ignore_tags = ignore_tags
        self.ignore_attrib = ignore_attrib
        self.diffs = []

    @staticmethod
    def __set_type(_xml):
        """Устаналивает нужный тип xml

        :param _xml: xml файл/строка/инстанс Element

        """
        if isinstance(_xml, str):
            parser = ElementTree.XMLParser(encoding="utf-8")
            _xml = ElementTree.fromstring(_xml, parser=parser)
        elif isinstance(_xml, ElementTree.ElementTree):
            _xml = _xml.getroot()
        return _xml

    @staticmethod
    def diff_keys(left_dict, right_dict):
        """Сравнивает ключи с словаре

        :param right_dict: словарь для сравнения
        :param left_dict: эталонный словарь
        :return возвращает два множеста: отличия, одинаковые

        """
        left_set = set(left_dict)
        right_set = set(right_dict)
        diff = left_set.difference(right_set)
        overlap = left_set.intersection(right_set)
        return diff, overlap

    def __attrib_ignore(self, tag, attrib):
        """Удаляет из сравнения игнорируемые атрибуты тэга

        Вернёт False, если атрибут найден в списке игнорируемых

        """
        result = False
        if tag in self.ignore_tags:
            result = True
        elif self.ignore_attrib is not None and isinstance(self.ignore_attrib, dict):
            if tag in self.ignore_attrib.keys():
                if attrib in self.ignore_attrib[tag]:
                    result = True
        return result

    def diff_tag(self, left_elm=None, right_elm=None):
        """

        :param left_elm: сравнивает атрибуты тэга
        :param right_elm:
        """

        if left_elm is None and right_elm is None:
            left_elm = self.left_xml
            right_elm = self.right_xml

        if left_elm.tag != right_elm.tag and right_elm.tag not in self.ignore_tags:
            self.diffs.append(right_elm.tag)
        else:
            left_dict = left_elm.attrib
            right_dict = right_elm.attrib
            diff_atr, overlap_atr = self.diff_keys(left_dict, right_dict)
            for atr in diff_atr:
                if not self.__attrib_ignore(right_elm.tag, atr):
                    self.diffs.append([right_elm.tag, atr])
            for key in overlap_atr:
                if left_dict[key] != right_dict[key]:  # Добавить сюда игнорирование значения
                    if not self.__attrib_ignore(right_elm.tag, key):
                        self.diffs.append([right_elm.tag, key, right_dict[key]])

            if self.with_text:
                text_left = [i for i in left_elm.itertext()][0]
                text_right = [i for i in right_elm.itertext()][0]
                if text_left != text_right:
                    self.diffs.append(['tag='+right_elm.tag, 'text='+text_right])
        left_children = left_elm.getchildren()
        right_children = right_elm.getchildren()
        if len(left_children) > 0 and len(left_children) == len(right_children):
            for i in range(len(left_children)):
                self.diff_tag(left_children[i], right_children[i])
        elif len(left_children) > 0 and len(left_children) != len(right_children):
            self.diffs.append([right_elm.tag, "Разное кол-во дочерних тэгов!"])

        return self.diffs


def diff_xml(left_xml, right_xml, ignore_tags=None, ignore_attrib=None, with_text=False):
    """Сравнивает две xml

    :param right_xml: эталонный xml
    :param left_xml: полученный xml
    :param ignore_attrib: игнорируемые атрибуты, задаются словарём, {'тэг': 'атрибут'}
    :param ignore_tags: игнорируемые тэги, задаются списком ['тэг1', 'тэг2']

    """
    _xml = DiffXML(left_xml, right_xml, ignore_tags, ignore_attrib, with_text)
    return _xml.diff_tag()