# -*- coding: utf-8 -*-
from atf import *
import postgresql
import time
from .functions import read_file
import json
from urllib.parse import *

def get_count_records(client, name_method, params):
    res = client.call(name_method, return_record=True, **params).record
    if not isinstance(res, list):
        count_record = 1
    else:
        count_record = len(res)
    return count_record

def get_id_doc(docflow_id, time_wait=300):
    """
    :param docflow_id: Документ.Идентификатор
    """
    start = time.time()
    sql_script = '''
    select "ИдентификаторВИ" from "ДокументРасширение"
                    where "@Документ" in(select "Документ" from "Событие" where "кодСобытия" = '{0}')
    '''.format(docflow_id)
    db = postgresql.open(Config().get('DB'))
    res = None
    while True:
        if time.time() < start + time_wait:
            res = db.prepare(sql_script)()
            if not res:
                time.sleep(5)
            else:
                break
        else:
            msg = "Выполнялся запрос:\n{query}\nОжидали получить одну запись - вернулось{res}"
            raise Exception(msg.format(query=sql_script, res=res))

    return res[0][0]

def requirement_attach_list(client, key_complect, count_record, return_record=True):
    """Вызов метода Requirement.AttachList
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param key_complect: идентификатор комплекта
    :param count_record: количество записей в ответе
    """
    params = {
            "ДопПоля": [],
            "Фильтр": {"s": [{"n": "docId", "t": "Строка"},
                             {"n": "onlyMainDocs", "t": "Число целое"},
                             {"n": "search", "t": "Строка"}],
                       "d": [str(key_complect), 1, ""],
                       "_type": "record"},
            "Сортировка": None,
            "Навигация": {"s": [{"n": "ЕстьЕще", "t": "Логическое"},
                                {"n": "РазмерСтраницы", "t": "Число целое"},
                                {"n": "Страница", "t": "Число целое"}],
                          "d": [True, 20, 0],
                          "_type": "record"}}
    assert_that(lambda: len(client.call("Requirement.AttachList", return_record=True, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("Requirement.AttachList", return_record=True, **params).record


def doc_info_about_state(client, key_complect, count_record, return_record=True):
    """Вызов метода Документ.ИнформацияОСостоянии
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param key_complect: идентификатор комплекта
    :param count_record: количество записей в ответе
    """
    params = {"Документ": key_complect, "Событие": None}
    assert_that(lambda: len(client.call("Документ.ИнформацияОСостоянии", return_record=True, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("Документ.ИнформацияОСостоянии", return_record=True, **params).record


def requirement_command_get(client, key_complect, count_record, return_record=True):
    """Вызов метода Requirement.КомандыПолучить
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param key_complect: идентификатор комплекта
    :param count_record: количество записей в ответе
    """
    params = {"ИдО": str(key_complect)}
    assert_that(lambda: len(client.call("Requirement.КомандыПолучить", return_record=True, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("Requirement.КомандыПолучить", return_record=True, **params).record


def requirement_list_folder_decl(client, id_, count_record, return_record=True):
    """Вызов метода Requirement.ListFoldersDecl
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_: идентификатор
    :param count_record: количество записей в ответе
    """
    params = {
		"ДопПоля": [],
		"Фильтр": {
			"d": ["%s" % id_],
			"s": [{
				"n": "ИдТребования",
				"t": "Строка"
			}]
		},
		"Сортировка": None,
		"Навигация": None
	}
    assert_that(lambda: len(client.call("Requirement.ListFoldersDecl", return_record=True, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("Requirement.ListFoldersDecl", return_record=True, **params).record


def complect_list_dispatch(client, key_complect, count_record, return_record=True):
    """Вызов метода Комплект.СписокОтправок
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param key_complect: идентификатор комплекта
    :param count_record: количество записей в ответе
    """
    log('Комплект.СписокОтправок')
    params = {"ДопПоля": [],
             "Фильтр": {"d": [key_complect], "s": [{"n": "ИдКомплекта", "t": "Строка"}]},
             "Сортировка": None,
             "Навигация": None}
    assert_that(lambda: len(client.call("Комплект.СписокОтправок", return_record=True, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("Комплект.СписокОтправок", return_record=True, **params).record


def requirement_list_invoices_folders(client, id_, count_record, return_record=True, wait=180):
    """Вызов метода Requirement.ListInvoicesFolders
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_: идентификатор
    :param count_record: количество записей в ответе
    """
    params = {
		"ДопПоля": [],
		"Фильтр": {
			"d": ["%s" % id_],
			"s": [{
				"n": "ИдТребованияСверкиНДС",
				"t": "Строка"
			}]
		},
		"Сортировка": None,
		"Навигация": {
			"s": [{
				"n": "Страница",
				"t": "Число целое"
			}, {
				"n": "РазмерСтраницы",
				"t": "Число целое"
			}, {
				"n": "ЕстьЕще",
				"t": "Логическое"
			}],
			"d": [0, 15, False]
		}
	}
    assert_that(lambda: len(client.call("Requirement.ListInvoicesFolders", return_record=True, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait(wait))
    if return_record:
        res = client.call("Requirement.ListInvoicesFolders", return_record=True, **params).record
    else:
        res = client.call("Requirement.ListInvoicesFolders", return_record=False, **params)
    return res

def edo_search_package_id(client, id_package, count_record):
    """ЭДО.НайтиПакетПоИдентификатору
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :id_package id_: идентификатор пакета
    :param count_record: количество записей в ответе
    """
    params = {
		"ИдПакета": id_package
	}
    assert_that(lambda: len(client.call("ЭДО.НайтиПакетПоИдентификатору", return_record=True, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("ЭДО.НайтиПакетПоИдентификатору", return_record=True, **params).record


def delivery_eo_list(client, id_doc, count_record, return_record=True):
    """Вызов метода РассылкаЭО.Список
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_doc: идентификатор документа @Документ(из ответа метода ЭДО.НайтиПакетПоИдентификатору)
    :param count_record: количество записей в ответе
    """
    params = {"ДопПоля": [],
             "Фильтр": {"d": ["%s" % id_doc], "s": [{"n": "ИдДокумента", "t": "Строка"}]},
             "Сортировка": None,
             "Навигация": None}
    assert_that(lambda: len(client.call("РассылкаЭО.Список", return_record=True, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("РассылкаЭО.Список", return_record=True, **params).record


def foreign_doc_print(client, id_foreign_doc):
    """Вызов метода ВнешнийДокумент.ОтобразитьДокументыНаПечать
    :param client: клиент экземпляр класса
    :param id_foreign_doc: идентификатор внешнего документа (значение ключа РП.ВнешнийДокумент из ответа
    метода РассылкаЭО.Список)
    """
    params = {"МассивИД": [id_foreign_doc]}
    return client.call("ВнешнийДокумент.ОтобразитьДокументыНаПечать", return_record=False, **params)


def doc_list_attachments_get(client, id_doc, count_record, return_record=True):
    """Вызов метода Документ.СписокВложенийПолучить
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_doc: идентификатор документа @Документ(из ответа метода ЭДО.НайтиПакетПоИдентификатору)
    :param count_record: количество записей в ответе
    """
    params = {
		"ИдОбъекта": "%s" % id_doc,
		"Фильтр": {
			"d": [],
			"s": []
		}
	}
    assert_that(lambda: len(client.call("Документ.СписокВложенийПолучить", return_record=True, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("Документ.СписокВложенийПолучить", return_record=True, **params).record


def complect_retro_list_attacments(client, id_doc, count_record, return_record=True):
    """Вызов метода КомплектРетро.СписокВложений
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_doc: идентификатор документа @Документ(из ответа метода ЭДО.НайтиПакетПоИдентификатору)
    :param count_record: количество записей в ответе
    """
    params = {"ДопПоля": [],
             "Фильтр": {"d": ["%s" % id_doc], "s": [{"n": "ИдО", "t": "Строка"}]},
             "Сортировка": None,
             "Навигация": None}
    assert_that(lambda: len(client.call("КомплектРетро.СписокВложений", return_record=True, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("КомплектРетро.СписокВложений", return_record=True, **params).record


def complect_retro_read_for_show(client, id_doc, count_record, return_record=True):
    """Вызов метода КомплектРетро.ПрочитатьДляПоказа
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_doc: идентификатор документа @Документ(из ответа метода ЭДО.НайтиПакетПоИдентификатору)
    :param count_record: количество записей в ответе
    """
    params = {"ИдО": id_doc, "ИмяМетода": "КомплектРетро.СписокРетро"}
    assert_that(lambda: get_count_records(client, "КомплектРетро.ПрочитатьДляПоказа", params), equal_to(count_record),
                'Должно вернуться %s запись(ей)' % count_record, and_wait())
    if return_record:
        res = client.call("КомплектРетро.ПрочитатьДляПоказа", return_record=True, **params).record
    else:
        res = client.call("КомплектРетро.ПрочитатьДляПоказа", return_record=False, **params)
    return res


def complect_retro_get_answer(client, id_doc, count_record, return_record=True):
    """Вызов метода КомплектРетро.ПолучитьОтвет
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_doc: идентификатор документа @Документ(из ответа метода ЭДО.НайтиПакетПоИдентификатору)
    :param count_record: количество записей в ответе
    """
    params = {"ИдО": id_doc}
    assert_that(lambda: get_count_records(client, "КомплектРетро.ПолучитьОтвет", params),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("КомплектРетро.ПолучитьОтвет", return_record=True, **params).record

def complect_read(client, id_doc, count_record, return_record=True):
    """Вызов метода Комплект.Прочитать
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_doc: идентификатор документа @Документ(из ответа метода ЭДО.НайтиПакетПоИдентификатору)
    :param count_record: количество записей в ответе
    """
    params = {"ИдО": id_doc, "ИмяМетода": ""}
    assert_that(lambda: get_count_records(client, "Комплект.Прочитать", params), equal_to(count_record),
                'Должно вернуться %s запись(ей)' % count_record, and_wait())
    if return_record:
        res = client.call("Комплект.Прочитать", return_record=True, **params).record
    else:
        res = client.call("Комплект.Прочитать", return_record=False, **params)
    return res

def contractor_read(client, id_doc, count_record, return_record=True):
    """Вызов метода Контрагент.Прочитать
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_doc: идентификатор документа @Документ(из ответа метода ЭДО.НайтиПакетПоИдентификатору)
    :param count_record: количество записей в ответе
    """
    params = {"ИдО": id_doc, "ИмяМетода": ""}
    assert_that(lambda: get_count_records(client, "Контрагент.Прочитать", params), equal_to(count_record),
                'Должно вернуться %s запись(ей)' % count_record, and_wait())
    if return_record:
        res = client.call("Контрагент.Прочитать", return_record=True, **params).record
    else:
        res = client.call("Контрагент.Прочитать", return_record=False, **params)
    return res

def requirement_list_doc_decl(client, id_, count_record, return_record=True):
    """Вызов метода Requirement.ListDocDecl
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_: идентификатор
    :param count_record: количество записей в ответе
    """
    params = {
		"ДопПоля": [],
		"Фильтр": {
			"d": ["%s" % id_],
			"s": [{
				"n": "ИдПапки",
				"t": "Строка"
			}]
		},
		"Сортировка": None,
		"Навигация": None
	}
    assert_that(lambda: len(client.call("Requirement.ListDocDecl", return_record=True, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("Requirement.ListDocDecl", return_record=True, **params).record


def requirement_list_files(client, id_, count_record, return_record=True):
    """Вызов метода Requirement.ListFiles
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_: идентификатор
    :param count_record: количество записей в ответе
    """
    params = {
		"ДопПоля": [],
		"Фильтр": {
			"d": ["%s" % id_],
			"s": [{
				"n": "Требование",
				"t": "Строка"
			}]
		},
		"Сортировка": None,
		"Навигация": {
			"s": [{
				"n": "Страница",
				"t": "Число целое"
			}, {
				"n": "РазмерСтраницы",
				"t": "Число целое"
			}, {
				"n": "ЕстьЕще",
				"t": "Логическое"
			}],
			"d": [0, 25, False]
		}
	}
    assert_that(lambda: len(client.call("Requirement.ListFiles", return_record=return_record, **params).record),
                    equal_to(count_record), 'Должно вернуться %s запись(ей)' % count_record, and_wait())
    return client.call("Requirement.ListFiles", return_record=return_record, **params).record


def session_load_add_file(client, id_doc, disk_ver, file_name, file_size, id_session=""):
    """Вызов метода СессияЗагрузки.ДобавитьФайл
    :param client: клиент экземпляр класса rtl.JsonRpcClient
    :param id_doc: ИдентификаторДискДокумент
    :param disk_ver: версия документа
    :param file_name: имя файла
    :param file_size: размер файла(Content-Length)
    """
    params = {
		"ИдСессии": id_session,
		"Параметры": {
			"s": [{
				"t": "UUID",
				"n": "ИдентификаторДискДокумент"
			}, {
				"t": "Строка",
				"n": "ИдентификаторДискВерсияДокумента"
			}, {
				"t": "Строка",
				"n": "ИмяФайла"
			}, {
				"t": "Число целое",
				"n": "Размер"
			}],
			"d": [id_doc, disk_ver, file_name, file_size],
			"_mustRevive": True,
			"_type": "record"
		}
	}
    return client.call("СессияЗагрузки.ДобавитьФайл", return_record=False, **params)

def send_file_sbis_disk(client, url, path_file, name_file, encoding="1251"):
    """Загружаем файл в сбис диск"""
    read_f = read_file(path_file, encoding=encoding).encode(encoding=encoding)
    size_file = str(len(read_f))
    sid = client.sid
    name_file = quote(u'%s' % name_file)  # чтобы не ругался на русские названия
    headers = {'Content-Disposition': "attachment;filename*=UTF-8''" + name_file,
               'X-SBISSessionID': sid, 'Content-Type': 'text/xml', 'Content-Length': size_file}
    res = client.post(_site=url, body=read_f, headers=headers)
    data = json.loads(res[0].decode())
    data["size_file"] = size_file
    return data

def session_download(client, id_session):
    """Дожидаемся загрузки сессии"""
    res = client.call("СессияЗагрузки.Загрузить", **{"ИдСессии": id_session})
    result = False
    if not res:
        time.sleep(5)
    else:
        result = True
    return result

def session_get_result(client, id_session):
    """Дожидаемся загрузки сессии"""
    res = client.call("СессияЗагрузки.ПолучитьРезультат", **{"ИдСессии": id_session})
    result = False
    if not res :#and isinstance(res, dict) and not res.get("loadedFiles")
        time.sleep(5)
    else:
        result = True
    return result