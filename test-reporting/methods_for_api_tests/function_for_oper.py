# coding=utf-8
from otf import *
from atf import *
from data import Data
from methods_for_api_tests.functions import *
from methods_for_api_tests.functions_edo import *
import os
import subprocess
from datetime import datetime
import time
from hashlib import md5
import postgresql
config = Config()
import base64
from otf.documentrules.reglaments import *
import xmltodict


def analysis_file_desc(id_doc_flow, transaction, path_desc, list_id, key_docs, encoding="cp1251", sort_doc_key=None, list_filter_ignore_docs=None):
    """Анализируем файл описания
    :param id_doc_flow: идентификатор документооботота
    :param transaction: транзация(исходящая)
    :param file_name: путь к файлу packageDescription в формате .json
    :param list_id: список идентификаторов в который будут удалены символы -
    :param sort_doc: список ключей для сортировки
    :param list_ignore_docs: список словарей - если документ будет соотвестовать одному из элементов списка(словорю) - документ удаляется из проверки
    пример для list_filter_ignore_docs = [{"@типДокумента": "описаниеСведений"}, {"@типДокумента": "пачкаИС"}] - удалятся докуметы подоходящие под одну из масок
    """

    log("Анализ файла описания")
    def id_oper(id_list):
        for name_id in id_list:
            setattr(Data, "%s_OPER" % name_id, getattr(Data, name_id).replace("-", ""))

    def sort_(obj):
        return tuple(obj[key] for key in sort_doc_key)

    def filter_doc(filter, doc):
        res = True
        for key, value in filter.items():
            if key not in doc.keys():
                res = False
                break
            if isinstance(value, dict):
                res = filter_doc(value, doc[key])
                break
            if doc[key] != value:
                res = False
                break
        return res

    def find_doc(doc):
        for filter in list_filter_ignore_docs:
            if (filter_doc(filter, doc)):
                return True

    id_oper(list_id)
    fd = TransportCoreDB().download_container(id_doc_flow, container_type=EventType.Primary,
                                              transaction=transaction)
    container = Container(fd)
    # for doc_i in container.package_description.документ():
    #     log(doc_i.to_string())
    #
    # for name, val in  container.documents.items():
    #     print("Название %s" % val.origin_name)
    #     print("Идентификатор документа %s" % val.document_id)
    #     print("Тип документа %s" % val.document_type)
    #     type_doc = val.content_type
    #     print("Тип %s" % type_doc)
    #     compr = val.is_compressed
    #     print("Cжат %s" % compr)
    #     encr_ = val.is_encrypted
    #     print("Закодирован %s" % encr_)
    #     # if compr and type_doc=="xml":
    #     #     data_xml = val.extract().data.decode("cp1251")
    #     #     print(data_xml)
    #     # else:
    #     #     print("не xml")
    #     print("#"*100)



    cont = container.package_description.write(filename='packageDescription.xml', write_dir='output_directory')
    data = cont.data.decode(encoding)
    log("Содержание файла packageDescription.xml\n %s" % data)
    rest_dict = json.loads(json.dumps(xmltodict.parse(data), ensure_ascii=False))
    data_temp = json.loads(read_file(path_desc))

    docs_resp = rest_dict[key_docs]["документ"]
    docp_temp = data_temp[key_docs]["документ"]
    if list_filter_ignore_docs:
        # удаляем вложения
        index_del = []
        for index_i, doc_i in enumerate(docs_resp):
            if find_doc(doc_i):
                index_del.append(index_i)
        if index_del:
            index_del.sort(reverse=True)
            for i in index_del:
                docs_resp.pop(i)
    # y = modification_responce(rest_dict)
    msg = "Файл packageDescription.xml из транзакции %s отличается от ожиданий" % transaction.name
    if sort_doc_key:
        docp_temp.sort(key=sort_)
        docs_resp.sort(key=sort_)
    assert_that(data_temp, equal_to_json(rest_dict), msg)