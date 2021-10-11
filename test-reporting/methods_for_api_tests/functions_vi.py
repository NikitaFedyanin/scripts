# coding=utf-8
from atf import *
from data import Data
from methods_for_api_tests.functions import *
from methods_for_api_tests.functions_edo import create_signature_for_base_64


def sbis_write_doc(client, attacments, data_doc, id_doc, contractor, our_org,
                           note="", type_doc="ДокОтгрИсх", code=200, error=False):
    """
    Создает черновик
    :param client: экземпляр класса Client
    :param attacments: подготовленный список вложений
    :param data_doc: дата документа
    :param id_doc: идентификатор пакета документов
    :param contractor: объект Контрагент {"СвЮЛ": {"ИНН": Data._RECEIVER_UL_INN,
                                          "КПП": Data._RECEIVER_UL_KPP}}
    :param our_org: объект НашаОрганизация {"СвЮЛ": {"ИНН": Data._SENDER_UL_INN,
                                            "КПП": Data._SENDER_UL_KPP}}
    :param note: Примечание
    :param type_doc: Тип
    """
    params = {"Документ": {
              "Вложение": attacments,
              "Дата": data_doc,
              "Идентификатор": id_doc,
              "Контрагент": contractor,
              "НашаОрганизация": our_org,
              "Примечание": note,
              "Тип": type_doc,
              }}
    return client.call("СБИС.ЗаписатьДокумент", code=code, error=error, **params)
            
            
def get_attacment_object(name, id_att, data_att, sign=False, cont_name=None):
    """
    Создает объект вложение - для использования методом СБИС.ЗаписатьДокумент
    (элементы списка attacments для sbis_write_doc создаются этой функцией)
    :param name: название вложения
    :param id_att: идентификатор вложения
    :param data_att: содержание вложения(формат base_64)
    :param sign: если необходимо создать и приложить подписть под вложением
    (если True, то необходимо указать имя контейнера с сетрификатом для подписи)
    :param cont_name: имя контейнера в котором находится сетификат
    """
    att = {"Идентификатор": id_att,
           "Файл": {"ДвоичныеДанные": data_att, "Имя": name}}
    if sign:
        data_sign = create_signature_for_base_64(data_att, cont_name=cont_name)
        obj_file = {"ДвоичныеДанные": data_sign, "Имя": "%s.sgn" % name}
        att["Подпись"] = [{"Файл": obj_file}]
    return att


def perform_action(client, id_doc, cert=None, code=200, error=False):
    """СБИС.ВыполнитьДействие"""
    params = {
            "Документ": {
                "Идентификатор": id_doc,
                "Этап": {
                    "Название": "Отправка",
                    "Действие": {
                        "Название": "Отправить",
                        "Сертификат": cert
                    }
                }
            }
        }
    return client.call("СБИС.ВыполнитьДействие", code=code, error=error, **params)


def prepare_action(client, id_doc, stage, code=200, error=False):
    """СБИС.ПодготовитьДействие"""
    params = {
        "Документ": {
            "Идентификатор": id_doc,
            "Этап": stage
        }
    }
    return client.call("СБИС.ПодготовитьДействие", code=code, error=error, **params)


def perform_action_stage(client, id_doc, stage, code=200, error=False):
    """СБИС.ВыполнитьДействие"""
    params = {
            "Документ": {
                "Идентификатор": id_doc,
                "Этап": stage
            }
        }
    return client.call("СБИС.ВыполнитьДействие", code=code, error=error, **params)










