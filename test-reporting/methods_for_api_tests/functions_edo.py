# coding=utf-8
from atf import *
from data import Data
from methods_for_api_tests.functions import *
import os
import subprocess
from datetime import datetime
import time
from hashlib import md5
import postgresql
config = Config()
import base64


def get_link_docs(res):
    docs = res["result"]["Вложение"]
    temp_list = []
    for doc_i in docs:
        doc_i_file = doc_i["Файл"]
        temp_list.append([doc_i_file["Имя"], doc_i_file["Ссылка"]])
    return temp_list


def get_hash(path, name):
    real_path = os.path.join(path, name)
    if os.path.isfile(real_path):
        log("Определяем ХЭШ файла по адресу %s" % real_path)
        with open(real_path, mode='rb') as f:
            data = f.read()
            data_new = data.replace(b"\n", b"").replace(b"\r", b"").replace(b" ", b"")
            #return (hashlib.md5(data_new).hexdigest(), data, data_new)
            return md5(data_new).hexdigest()

def create_file(client, name, link, path):
        """по ссылке взятой из ответа метода подготовить действие, берется ссылка на документ
         - документ выкачивается"""
        path_to_file = os.path.join(path, name)
        data_file = client.get(link)
        with open(path_to_file, 'bw') as f:
            f.write(data_file)
            return path_to_file

def analysis_link_old(client, list_link, dir_to_files):
    error = []
    real_path_to_dir = os.path.realpath(dir_to_files)
    for file_name in os.listdir(real_path_to_dir):
        if file_name == "Description.xml":  # Description.xml ПРОПУСКАЕМ
            continue
        file_lost = True
        for i in list_link:
            file_name_link = i[0]
            link = i[1]
            if file_name_link != file_name:
                continue
            file_lost = False  # НАЙДЕН ФАЙЛ В СПИСКЕ ДЛЯ СКАЧИВАНИЯ
            hash_file = get_hash(real_path_to_dir, file_name)
            log("Скачиваем файл %s по ссылке %s " % (file_name, link))
            data_i = client.get(link).replace(b"\n", b"").replace(b"\r", b"").replace(b" ", b"")
            hash_get_link = md5(data_i).hexdigest()
            if hash_file != hash_get_link:
                log("Хэш файла %s и хэш ответа полученного по ссылке %s отличаются" % (file_name, link))
                error.append(i)
        if file_lost:
            msg = "НЕ найден файл %s в ответе метода СБИС.ПрочитатьДокумент" % file_name
            raise Exception(msg)
    if error:
        msg_list = ["Содержимое файла %s и ответа полученного по ссылке %s отличаются \n" % (x[0], x[1]) for x in error]
        msg = " ".join(msg_list)
        raise Exception(msg)


def analysis_link(client, list_link, dict_send_files):
    error = []
    for file_name, data in dict_send_files.items():
        if file_name == "Description.xml":
            continue
        file_lost = True
        for i in list_link:
            file_name_link = i[0]
            link = i[1]
            if file_name_link != file_name:
                continue
            file_lost = False  # НАЙДЕН ФАЙЛ В СПИСКЕ ДЛЯ СКАЧИВАНИЯ
            data_file = data.replace(b"\n", b"").replace(b"\r", b"").replace(b" ", b"")
            hash_file = md5(data_file).hexdigest()
            log("Скачиваем файл %s по ссылке %s " % (file_name, link))
            data_i = client.get(link).replace(b"\n", b"").replace(b"\r", b"").replace(b" ", b"")
            hash_get_link = md5(data_i).hexdigest()
            if hash_file != hash_get_link:
                log("Хэш файла %s и хэш ответа полученного по ссылке %s отличаются" % (file_name, link))
                error.append(i)
        if file_lost:
            msg = "НЕ найден файл %s в ответе метода СБИС.ПрочитатьДокумент" % file_name
            raise Exception(msg)
    if error:
        msg_list = ["Содержимое файла %s и ответа полученного по ссылке %s отличаются \n" % (x[0], x[1]) for x in error]
        msg = " ".join(msg_list)
        raise Exception(msg)


def get_data_file(path):
    log("Читаем файл %s" % path)
    with open(path, "rb") as f:
       return f.read()


def send_doc(client, list_, encoding="cp1251", path_res="/cstorage/elo"):
    dict_send_files = {}
    for path, name_for_data, name_file_for_send, replace in list_:
        if replace:
            data = read_file(path, encoding).encode(encoding)
        else:
            data = get_data_file(path)
        temp_link = client.put(data, name_file_for_send, bin=True, path=path_res)
        setattr(Data, name_for_data, temp_link)
        log("Ссылка на загруженный файл %s %s " % (name_file_for_send, temp_link))
        dict_send_files[name_file_for_send] = data
    return dict_send_files


def read_me_test(self, msg):
    log("\n####################################"
        "\nОПИСАНИЕ ТЕСТА"
        "\nСценарий соответствует пункту плана - %s\n"
        "с планом можно ознакомиться по ссылке  - %s"
        "\n####################################" % (msg, self.config.LINK_TEST_PLAN))


def genetate_p7s(list_for_sign, cont_name="mongush", i=1):
    """Создаем подписи по данным из структуры list_for_sign
    :param cont_name: название контейнера в TrueCrypt в контейнере находится сетрификат которым
     и будут подписываться вложения по-умолчанию используется mongush - в нем лежет серт основной организации БУЯНА
    """
    for info_doc in list_for_sign:
        log("\n##################################\n")
        name_doc = info_doc['file_name']
        hash_doc = info_doc['file_hash']
        name_p7s = "_DATA_P7S_%s" % i
        i+=1
        data_p7s = create_signature(hash_doc, cont_name=cont_name)
        setattr(Data, name_p7s, data_p7s)
        log("Вложинию %s соответствует подпись $%s" % (name_doc, name_p7s))
        log("\n##################################\n")

def genetate_p7s_2(list_for_sign, cont_name="mongush", i=1):
    """Создаем подписи по данным из структуры list_for_sign
    :param cont_name: название контейнера в TrueCrypt в контейнере находится сетрификат которым
     и будут подписываться вложения по-умолчанию используется mongush - в нем лежет серт основной организации БУЯНА
    """
    for info_doc in list_for_sign:
        log("\n##################################\n")
        name_doc = info_doc["Файл"]["Имя"]
        hash_doc = info_doc["Файл"]["Хеш"]
        name_p7s = "_DATA_P7S_%s" % i
        i+=1
        data_p7s = create_signature(hash_doc, cont_name=cont_name)
        setattr(Data, name_p7s, data_p7s)
        log("Вложинию %s соответствует подпись $%s" % (name_doc, name_p7s))
        log("\n##################################\n")

def generate_name_attachment(prefix_name, data="20160404", ul=True, inn_kpp=None):
    # ul True - ЮРИДИЧЕСКОЕ ЛИЦО - ИМЕЕТ ИНН И КПП
    # ul False - ФИЗИЦЕСКОЕ ЛИЦО ИМЕЕТ ТОЛЬКО ИНН
    if ul:
        if inn_kpp:
            inn = inn_kpp[0] + inn_kpp[1]
        else:
            inn = Data._SENDER_UL_INN + Data._SENDER_UL_KPP
    else:
        if inn_kpp:
            inn = inn_kpp[0]
        else:
            inn = Data._SENDER_IP_INN
    temp_dict = {"prefix_name": prefix_name,
                 "FINITE_REC": Data._FINITE_RECIPIENT_GOS_INSP_CODE,
                 "REC_CODE": Data._RECIPIENT_GOS_INSP_CODE,
                 "INNKPP": inn,
                 "DATA": data,
                 "GUID": generate_guid()}
    name = "{prefix_name}_{REC_CODE}_{FINITE_REC}_{INNKPP}_{DATA}_{GUID}".format(**temp_dict)
    return name


def create_xml_signature(path_to_in_xml, path_to_out_xml, cont_name=None):
    """
    Подписать XML

    :param path_to_in_xml: путь к входящему файлу
    :param path_to_out_xml: путь к выходящему файлу
    :param cont_name: имя контейнера

    """

    log("Процесс запускается под пользователем %s" % os.getlogin())
    log("Время начала генерации подписи - %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S+03'))
    path_to_root = os.path.dirname(os.getcwd())
    path_crypto_exe = os.path.join(path_to_root, "sbis-crypto-util\sbis-crypto-util.exe")
    assert_that(os.path.exists(path_to_in_xml), is_(True), 'Входящий XML не существует!')
    assert_that(cont_name, not_equal(None), 'Не передано имя контейнера с ключами')
    command_list = [path_crypto_exe, '--sign_xml', '--in_file', path_to_in_xml,
                    '--out_file', path_to_out_xml, '--cont_name', cont_name]
    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(timeout=30)
    exit_code = process.returncode

    log('Код возврата {}'.format(exit_code))
    if exit_code != 0:
        result = stderr.decode('cp1251')
        raise Exception('При генерации подписи XML возникла ошибка - {}'.format(result))


def create_signature(hash_or_path, cont_name="UL1AutoTestVI", is_file=False):
    """Генерирует подпись по переданному хэшу или по содержимому файла - путь которог

    :param hash_or_path: значения либо хэш файла или путь до файла для которого нужно сгенерировать подпись
    :param cont_name: имя контейнера
    :param is_file: по-умолчанию(False) считается что hash_or_path принимае хэш, если указать True,
     то считается что hash_or_path принимает путь к файлу
    """
    log("Процесс запускается под пользователем %s" % os.getlogin())
    log("Время начала генерации подписи - %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S+03'))
    # Проверяем может есть sbis-crypto-util.exe в текущем каталоге, если нет поищем уровнем выше
    path_crypto_exe = os.path.join(os.getcwd(), r"sbis-crypto-util\sbis-crypto-util.exe")
    if not os.path.isfile(path_crypto_exe):
        path_crypto_exe = os.path.join(os.path.split(os.getcwd())[0], r"sbis-crypto-util\sbis-crypto-util.exe")
    commands = [path_crypto_exe, '--out_bytes', '--cont_name', cont_name]
    if is_file:
        commands.extend(['--create_detached_sign', '--in_file', hash_or_path])
    else:
        commands.extend(['--create_sign_on_hash', '--in_bytes', hash_or_path])
    process = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #process.wait(180)
    stdout, stderr = process.communicate()
    if stdout:
        result = stdout.translate(None, b'\n\r\t ').decode()
    else:
        raise Exception("При генерации подписи возникла ошибка\n%s" % stderr.decode())
    return result


def create_signature_for_base_64(data_base_64, cont_name="UL1AutoTestVI"):
    """Генерирует подпись по переданному хэшу или по содержимому файла - путь которог

    :param hash_or_path: значения либо хэш файла или путь до файла для которого нужно сгенерировать подпись
    :param cont_name: имя контейнера
    :param is_file: по-умолчанию(False) считается что hash_or_path принимае хэш, если указать True,
     то считается что hash_or_path принимает путь к файлу
    """
    log("Процесс запускается под пользователем %s" % os.getlogin())
    log("Время начала генерации подписи - %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S+03'))
    path_crypto_exe = os.path.join(os.getcwd(), r"sbis-crypto-util\sbis-crypto-util.exe")
    if not os.path.isfile(path_crypto_exe):
        path_crypto_exe = os.path.join(os.path.split(os.getcwd())[0], r"sbis-crypto-util\sbis-crypto-util.exe")
    commands = [path_crypto_exe, '--out_bytes', '--cont_name', cont_name]
    commands.extend(['--create_detached_sign', '--in_bytes', data_base_64])
    process = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stdout:
        result = stdout.translate(None, b'\n\r\t ').decode()
    else:
        raise Exception("При генерации подписи возникла ошибка\n%s" % stderr.decode())
    return result


def check_signature(data_sign, data_file):
    """Проверяет валидность отсоединенной подписи

    :param data_sign: данные в формате base_64 подписи
    :param data_file: данные в формате base_64 документа (для которого была сгенерирована подпись)
    """
    log("Процесс запускается под пользователем %s" % os.getlogin())
    log("Время начала генерации подписи - %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S+03'))
    path_crypto_exe = os.path.join(os.path.split(os.getcwd())[0], "sbis-crypto-util\\sbis-crypto-util.exe")
    commands = [path_crypto_exe, '--is_valid_detached_sign', '--in_bytes', data_sign, '--in_bytes2', data_file]
    process = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait(30)
    stdout, stderr = process.communicate()
    if stdout:
        result = stdout.decode("cp1251").replace('\r', '').replace('\n', '')
    else:
        raise Exception("При проверке подписи возникла ошибка\n%s" % stderr.decode("cp1251"))
    return result

def get_uuil(client, tmp_path):
    uuil = False
    temp_res = send_json_and_assert(client, tmp_path)['result']
    if temp_res:
        uuil = True
    else:
        time.sleep(3)
    return uuil


def attachments_for_signature(json_obj):
    phase = json_obj['result']['Этап']
    count_phase = len(phase)
    info = {}
    for i in range(count_phase):
        info[i] = {}  # верхний уровень номер этапа
        phase_i = phase[i]
        phase_name = phase_i['Название']
        info[i][phase_name] = temp_list = []
        investing_list = phase[i]['Вложение']
        count_investing_list = len(investing_list)
        for j in range(count_investing_list):
            temp_dict = {}
            investing_j = investing_list[j]
            temp_dict['doc_name'] = investing_j['Название']
            file_dict = investing_j['Файл']
            temp_dict['id'] = investing_j['Идентификатор']
            temp_dict['file_hash'] = file_dict['Хеш']
            temp_dict['file_link'] = file_dict['Ссылка']
            temp_dict['file_name'] = file_dict['Имя']
            temp_list.append(temp_dict)
    return info


def get_info_for_attachment(obj, name, search_name=False):
    """Ищет вложение по названию
        :param obj: объект возвращаемый функцией attachments_for_signature
         (собирает информацию о вложения отданных методом СБИС.ПодготовитьДействие)
        :param name: имя вложения (Файл.Имя)
        :param search_name: имя Название
        """
    not_search = True
    if search_name:
        for i in obj:
            if i["Название"] == name:
                return i
    else:
        for i in obj:
            if i["Файл"]["Имя"] == name:
                return i
    if not_search:
        raise Exception("Не найдено вложение с именем %s" % name)


def generate_many_signature(obj_for_search, obj_for_generate_sign, cont_name=getattr(Data,"_NAME_CONTAINER_SERT_UL", None)):
    for att_i in obj_for_generate_sign:
        name_attachment = att_i[0]
        hash_attachement = get_info_for_attachment(obj_for_search, name_attachment)["Файл"]["Хеш"]
        signature = create_signature(hash_attachement, cont_name)
        msg = "В Data добавлен атрибут {name} содержащий подпись для вложения {name_attach}"
        log(msg.format(name=att_i[1], name_attach=att_i[0]))
        setattr(Data, att_i[1], signature)


def get_attachments(json_obj):
    """Получение списка вложений из ответа, из вложений берутся только интересующие ключи
    На выходе список вложений.
    Интересующие ключи: 'Название', 'Файл', 'Идентификатор', 'Хеш', 'Ссылка', 'Имя'
    """

    interesting_keys = ('Название', 'Файл', 'Идентификатор', 'Хеш', 'Ссылка', 'Имя')
    stage_list = json_obj['result']['Этап']
    result = []
    for stage in stage_list:
        for attachment in stage['Вложение']:
            filter_dict = {key: value for key, value in attachment.items() if key in interesting_keys}
            filter_dict['НазваниеЭтапа'] = stage['Название']
            result.append(filter_dict)
    return result


def get_uuid_set(client, _uuid, time_wait=180):
    start = time.time()
    while True:
        result = client.call("Комплект.НайтиПоUUID", UUID=_uuid)
        if result:
            break
        elif time.time() > start + time_wait:
            raise Exception('Не удалось дождаться целочисленного ключа комплекта с uuid: %s\n' \
                   'Результат: %s' % (_uuid, result))
        else:
            time.sleep(5)
    return result


def check_time_to_sync(json_rpc, key_set, wait_result=None):
    start = time.time()
    while True:
        try:
            result = json_rpc.call("Комплект.ПрочитатьДляПоказа", return_record=True,
                                   ИдО=key_set, ИмяМетода="Комплект.Список")
            if result.record.get("@Документ"):
                return result
            if time.time() > start + 120:
                raise AssertionError('Не дождались ответа %s' % json_rpc.call("Комплект.ПрочитатьДляПоказа",
                                   ИдО=key_set, ИмяМетода="Комплект.Список"))
            time.sleep(3)
        except:
            if time.time() > start + 120:
                raise AssertionError('Не дождались ответа %s' % json_rpc.call("Комплект.ПрочитатьДляПоказа",
                                   ИдО=key_set, ИмяМетода="Комплект.Список"))
            time.sleep(3)


def diff_dict(dict1: dict, dict2: dict, msg: str):
    """Ищем что в dict2 будут все ключи из dict 1 и значения будут совпадать"""

    errors = ''

    for key, value in dict1.items():
        if key not in dict2.keys():
            errors += 'Ключ "{0}" отсутствует в ответе'.format(key)
        if dict2[key] != value:
            errors += 'Ключ: {0}; Эталон {1} != {2} текущему значению\n'.format(
                key, value, dict2[key]
            )
    assert not errors, msg + '\n' + errors if msg else errors


def is_equal_file(file1: str, file2: str, client):
    """Сравнивает, что файл на локальном диске, равен файлу по ссылке
    file1: эталонный файл, байтовая строка
    file2: ссылка на файл взятая из запроса
    client: авторизованный экземпляр atf.rpc.Client или rtl.JsonRpcClient
    """

    def calc_hash(_str):
        replace_char = b'\n\r\t '
        return md5(_str.translate(None, replace_char)).hexdigest()

    hash1 = calc_hash(file1)
    hash2 = calc_hash(client.get(file2))
    return hash1 == hash2


def get_attachment_by_id(result_record, id_attach):
    """Получить из записи результата вложение по его названию

    :param result_record: запись результата
    :param id_attach: id вложения

    """

    for attach in result_record:
        if attach['Идентификатор'] == id_attach:
            break
    else:
        attach = None

    return attach


def execute_prepare_db_script(note_us):
    """

    :param note_us: Документ.Идентификатор

    """
    sql_script = '''select "кодСобытия" from "Событие"
        where "Раздел@" is true and "Документ" in (
           select "@Документ" from "ДокументРасширение"
           where "ДокументРасширение"."ИдентификаторВИ" = '{0}'
    )'''.format(note_us)
    db = postgresql.open(Config().get('DB'))
    return db.prepare(sql_script)()


####################################################################

def wait_stage(client, time_wait=300, count_doc=1, id_doc=None, filter=None, all=False, filter_doc=None):
    """
    Дожидаемся служебок
    client
    :param client: экземпляр класса rtl.JsonRpcClient или Client
    :param time_wait: время ожидания на все служебки
    :param count_doc: общее количество ожидаемых служебок
    :param id_doc: идентификатор пакета документов (указывается в методе СБИС.ЗаписатьКомплект)
    :filter: фильтр
    :all: вернуть все служебные этапы(бывает нужно)
    """

    id_doc = id_doc if id_doc else Data._ID_SUITE
    num_page = 0
    if filter:
        filter = dict(filter)
        filter["Навигация"] = {"Страница": "%s" % num_page, "РазмерСтраницы": "150"}
        filter["Блокировать"] = "Нет"
        params = {"Фильтр": filter}
    else:
        params = {"Фильтр": {"ИдентификаторДокумента": id_doc,
                             "Навигация": {"Страница": "%s" % num_page, "РазмерСтраницы": "150"},
                             "Блокировать": "Нет"}}
    start = time.time()
    wait_doc = count_doc
    # Служебки приходят несинхронно поэтому нужно дожидаться
    # пока общее количестово полученных служебок достингнет count_doc - складывем полученные служебки в список
    list_stage = []
    list_name_stage = []  # сохраняем уникальные названия этапов в случае фильтрации по идентификатору документа

    def filter_(filter: dict, doc: dict):
        for key, value in filter.items():
            if key not in doc.keys():
                errors += 'Ключ "{0}" отсутствует в ответе'.format(key)
            if isinstance(doc[key], dict):
                filter(filter[key], doc[key])
            if doc[key] != value:
                return False
        return True

    while True:
        res_ = client.call("СБИС.СписокСлужебныхЭтапов", return_record=False, **params)
        res = res_.get("Документ", False)
        if all:
            # собираем все что приходит
            list_stage.extend(res)
        else:
            if filter_doc:
                res_temp = []
                for doc_i in res:
                    x = filter_(filter_doc, doc_i)
                    if x:
                        res_temp.append(doc_i)
                res = res_temp
            count_stage = len(res)
            if count_stage == wait_doc:
                list_stage.extend(res)
                return list_stage
            elif count_stage < wait_doc:
                for stage_i in res:
                    if stage_i["Название"] not in list_name_stage:
                        list_stage.append(stage_i)
                        list_name_stage.append(stage_i["Название"])
                        wait_doc -= 1  # будем дожидаться оставшихся служебок
            if time.time() > start + time_wait:
                raise AssertionError("Не дождались служебок ожидали дождаться %s служебок" % count_doc)
        if res_["Навигация"]["ЕстьЕще"] == "Да":
            num_page+=1
            params["Фильтр"]["Навигация"]["Страница"] = "%s" % num_page
        else:
            num_page = 0
            params["Фильтр"]["Навигация"]["Страница"] = "%s" % num_page
            list_name_stage = []
            wait_doc = count_doc
            # если нужно вернуть все документы то выходим, проходим до тех пор пока не дойдем до конца(один раз)
            if all:
                return list_stage
            list_stage = []
        time.sleep(5)


def get_info_stages(result):
    """
    Выбираем необходимые для провки значения из ответа метода СБИС.СписокСлужебныхЭтапов
    :param result: результат выполнения метода СБИС.СписокСлужебныхЭтапов
    """
    list_event = []
    for doc_i in result:
        for stage_i_doc in doc_i["Этап"]:
            temp = {}
            temp["Этап.Название"] = stage_i_doc["Название"]
            temp["Этап.Служебный"] = stage_i_doc["Служебный"]
            temp["Этап.Идентификатор"] = stage_i_doc["Идентификатор"]
            temp["Документ.Тип"] = doc_i["Тип"]
            temp["Документ.Идентификатор"] = doc_i["Идентификатор"]
            temp["Документ.Редакция.Идентификатор"] = doc_i["Редакция"][0]["Идентификатор"]
            for action_stage in stage_i_doc["Действие"]:
                temp["Этап.Действие.ТребуетРасшифровки"] = action_stage["ТребуетРасшифровки"]
                temp["Этап.Действие.ТребуетПодписания"] = action_stage["ТребуетПодписания"]
                temp["Этап.Действие.ТребуетКомментария"] = action_stage["ТребуетКомментария"]
                temp["Этап.Действие.Название"] = action_stage["Название"]
                temp["Этап.Действие.Сертификат"] = action_stage["Сертификат"]
            list_event.append(temp)
    return list_event


def get_attachments_2(json_obj):
    """
    Расширенная версия функции get_attachments(для полного документооборота)
    Получение списка вложений из ответа, из вложений берутся только интересующие ключи
    На выходе список вложений.
    Интересующие ключи: 'Название', 'Файл', 'Идентификатор', 'Хеш', 'Ссылка', 'Имя'
    :param json_obj: ответ метода СБИС.ПодготовитьДействие
    """

    interesting_keys = ('Название', 'Файл', 'Идентификатор', 'Хеш', 'Ссылка', 'Имя')
    stage_list = json_obj['Этап']
    result = []
    for stage in stage_list:
        temp_info_stage = {}
        temp_info_stage["Документ.Идентификатор"] = json_obj["Идентификатор"]
        temp_info_stage["Этап.Название"] = stage['Название']
        temp_info_stage["Этап.Идентификатор"] = stage['Идентификатор']
        temp_info_stage['Документ.Редакция.Идентификатор'] = json_obj["Редакция"][0]["Идентификатор"]
        temp_info_stage["Вложение"] = []
        assert_that(stage.get('Вложение'), is_not(None), "Отсутствует 'Вложение' в этапе {0}".format(stage))
        for attachment in stage['Вложение']:
            filter_dict = {key: value for key, value in attachment.items() if key in interesting_keys}
            temp_info_stage["Вложение"].append(filter_dict)
        result.append(temp_info_stage)
    if len(result) == 1:
        result = result[0]
    return result


def prepare_action(client, list_cerv_stage, sert):
    """
    Фуккция вызывает метода СБИС.ПодготовитьДействие
    :param client: экземпляр класса Client
    :param list_cerv_stage: данные о вложении результат функции - get_info_stages
    :param sert: сертификат используемый для подписи
    """
    log("Вызывается метод СБИС.ПодготовитьДействие для этапа %s " % list_cerv_stage["Этап.Название"])
    sert = json.loads(sert)
    params_1 = {
                "Документ": {
                    "Идентификатор":  Data._ID_SUITE,
                    "Тип":  list_cerv_stage["Документ.Тип"],
                    "Редакция": {"Идентификатор": list_cerv_stage["Документ.Редакция.Идентификатор"]},
                    "Этап": {
                        "Название":  list_cerv_stage["Этап.Название"],
                        "Идентификатор":  list_cerv_stage["Этап.Идентификатор"],
                        "Действие": {
                            "Название": "Обработать служебное",
                            "Сертификат": sert
                        }
                    }
                }
            }
    res_1 = client.call("СБИС.ПодготовитьДействие", **params_1)
    return get_attachments_2(res_1)


def perform_action(client, attachment, sign=True, link=True, cont_name=None, id_doc=None):
    """
    СБИС.ВыполнитьДействие для переданного вложения
    :param client: - инстанс клиента
    :param attachment: - вложение для которого выполняем действие
    :param sign: - подписывать серификатом или нет
    :param link: - это ссылка в файловое хринилище, по-умолчанию при вызове
    СБИС.ВыполнитьДействие прикладываеются ссылки, а не base_64
    :param cont_name: имя контейре в котором лежит сертификат для подписывания документов
    :param id_doc: идентификатор пакета документов (указывается в методе СБИС.ЗаписатьКомплект)
    :return: ответ метода СБИС.ВыполнитьДействие
    """
    #from ctt.crypto import decrypt
    cont_name = cont_name if cont_name else Data._NAME_CONTAINER_SERT_UL
    id_doc = id_doc if id_doc else Data._ID_SUITE

    params = {
            "Документ": {
                "Идентификатор": attachment["Документ.Идентификатор"],
                "Тип": "",
                "Редакция": {
                    "Идентификатор": attachment['Документ.Редакция.Идентификатор']
                },
                "Этап": [{
                    "Идентификатор": attachment['Этап.Идентификатор'],
                    "Название": attachment['Этап.Название'],
                    "Действие": [{
                        "Название": "Обработать служебное",
                        "Комментарий": ""
                    }],
                    "Вложение": None
                }]
            }
        }
    if sign:
        log("Создаем список вложений")
        list_attachments = []
        for att_i in attachment['Вложение']:
            temp_att = {}
            temp_att["Идентификатор"] = att_i["Идентификатор"]
            temp_att["Название"] = att_i["Название"]
            hash_att = att_i["Файл"]["Хеш"]
            data_p7s = create_signature(hash_att, cont_name=cont_name)  # cont_name=Data._NAME_CONTAINER_SERT_UL
            temp_att["Подпись"] = [{"Тип": "Отсоединенная",
                                    "Файл": {"Имя": att_i["Файл"]["Имя"]+".p7s",
                                             "ДвоичныеДанные": data_p7s}}]
            list_attachments.append(temp_att)
        params["Документ"]["Этап"][0]["Вложение"] = list_attachments
    elif link:
        # прикладываем ссылки на вложения
        params["Документ"]["Этап"][0]["Вложение"] = attachment["Вложение"]
    else:
        # если попали сюда, значит нужно прикладывать вложения в формате ДвоичныеДанные
        att_all = []
        for att in attachment["Вложение"]:
            data_bin = client.get(att["Файл"]["Ссылка"])
            #data_bin = decrypt(client.get(att["Файл"]["Ссылка"]))
            data_base_64 = base64.b64encode(data_bin).decode()
            att_all.append({"Ссылка": "", "Имя": att["Файл"]["Имя"], "ДвоичныеДанные": data_base_64})
        params["Документ"]["Этап"][0]["Вложение"] = att_all
    return client.call("СБИС.ВыполнитьДействие", **params)


def prepare_action(client, list_cerv_stage, sert, id_doc=None):
    """
    Фуккция вызывает метода СБИС.ПодготовитьДействие
    :param client: экземпляр класса Client
    :param list_cerv_stage: данные о вложении результат функции - get_info_stages
    :param sert: сертификат используемый для подписи
    :param id_doc: идентификатор пакета документов (указывается в методе СБИС.ЗаписатьКомплект)
    """
    id_doc = id_doc if id_doc else Data._ID_SUITE
    log("Вызывается метод СБИС.ПодготовитьДействие для этапа %s " % list_cerv_stage["Этап.Название"])
    sert = json.loads(sert)
    params_1 = {
                "Документ": {
                    "Идентификатор":  id_doc,
                    "Тип":  list_cerv_stage["Документ.Тип"],
                    "Редакция": {"Идентификатор": list_cerv_stage["Документ.Редакция.Идентификатор"]},
                    "Этап": {
                        "Название":  list_cerv_stage["Этап.Название"],
                        "Идентификатор":  list_cerv_stage["Этап.Идентификатор"],
                        "Действие": {
                            "Название": "Обработать служебное",
                            "Сертификат": sert
                        }
                    }
                }
            }
    res_1 = client.call("СБИС.ПодготовитьДействие", **params_1)
    return get_attachments_2(res_1)


def sbis_list_change(client, id_doc, id_event, count_doc=None, org_ul=True, data_our_org=None, id_billing=None,
                     wait_event_list=None, wait_time=300, log_out=False):
    """
    Ищет документы(служебки) для отправленного документа с фильтрацией по идентификатору события
    :param client:  экземпляр класса Client
    :param id_doc: идентификатор пакета документов (указывается в методе СБИС.ЗаписатьКомплект)
    :param id_event: идентификатор события берется из ответа метода СБИС.ВыполнитьДействие
    (["result"]["Событие"][0]["Идентификатор"])
    :param count_doc: количество документов
    :param org_ul: тип отправителя юридиское лицо или физическое(по умолчанию юридическое = True),
     False - физическое лицо
     Внимание чтобы не усложнять код - если указывается org_ul=False(физ лицо),
     требуется явно передать объект data_our_org И id_billing

    :param data_our_org: сведения об отправителе - СЛОВАРЬ содержащий информацию об отправителе (инн кпп) например
    {"ИНН": Data._SENDER_UL_INN, "КПП": Data._SENDER_UL_KPP}}
    :param id_billing: идентификатор билинга
    :wait_event_list: список событий(которых дожидаемся)
    """
    if not count_doc and not wait_event_list:
        msg = "Для использования функции необходимо передать count_doc(число-количество событий например count_doc=1) ИЛИ" \
              "wait_event_list - список ожидаемых событий"
        raise Exception(msg)
    start = time.time()
    id_billing = id_billing if id_billing else Data._ID_BILLING
    params = \
        {"Фильтр": {"ИдентификаторДокумента": id_doc,
                    "ИдентификаторСобытия": id_event,
                    "ТолькоОтчетность": "Да",
                    "ТолькоЭДО": "Нет",
                    "НашаОрганизация": {
                        "ИдентификаторБиллинга": id_billing},
                    "Навигация": {"Страница": "0",
                                  "РазмерСтраницы": "200"}}}
    if org_ul:
        # юридическое лицо
        if data_our_org:
            # если переданы данные об отправителе
            params["Фильтр"]["НашаОрганизация"]["СвЮЛ"] = data_our_org
        else:
            # по умолчанию считаем отправку стандартной
            params["Фильтр"]["НашаОрганизация"]["СвЮЛ"] = {"ИНН": Data._SENDER_UL_INN, "КПП": Data._SENDER_UL_KPP}
    else:
        # физическое лицо
        params["Фильтр"]["НашаОрганизация"]["СвФЛ"] = data_our_org

    def _search_docs(params, count_doc):
        i = 0
        params["Фильтр"]["Навигация"]["Страница"] = str(i)
        list_doc = []
        search = False
        while True:
            res = client.call("СБИС.СписокИзменений", log_out=log_out, **params)
            for doc in res["Документ"]:
                if doc["Идентификатор"] == id_doc:
                    if wait_event_list:
                        # на тот случай если отбираем документы и по идентификатору и событию(если входим в список)
                        if doc["Событие"][0]["Название"] in wait_event_list:
                            list_doc.append(doc)
                    else:
                        list_doc.append(doc)
            if len(list_doc) == count_doc:
                search = True
                break
            elif res["Навигация"]["ЕстьЕще"] == "Да":
                # уменьшим счетчик на количестово найденных документов, и делам повторный запрос чтобы найти остальные
                count_doc -= len(list_doc)
                i += 1
                params["Фильтр"]["Навигация"]["Страница"] = str(i)
            else:
                # дошли до конца но всех домуентов так и не дождались
                break
        return search, list_doc

    while True:
        if wait_event_list:
            count_doc = len(wait_event_list)
        res_serch, docs = _search_docs(params, count_doc)
        if res_serch or time.time() > start + wait_time:
            break
        else:
            time.sleep(15)
            continue
    client.call("СБИС.СписокИзменений", log_out=True, **params)
    return docs


def simple_res_read_doc(result, name_attacment=False):
    """
    Выбирает из res(ответ метода СБИС.ПрочитатьДокумент) необходимые ключи
    :param res: ответ метода СБИС.ПрочитатьДокумент
    """
    keys = ["Название", "Направление", "Примечание", "Вложение", "Событие", "Состояние", "Тип", "Расширение"]
    keys_att = ["ВерсияФормата", "Зашифрован", "Модифицирован", "Название", "Направление", "ПодверсияФормата",
                "Подтип", "Служебный", "Тип", "Удален", "УдаленКонтрагентом"]
    keys_event = ["Вложение", "Группа", "Название"]
    keys_group = ["Код", "Название", "Описание", "Приоритет"]
    temp_ = {}

    def get_name_file(name_file):
        """Ищем название вложения в Data"""
        for key, value, in Data.__dict__.items():
            if value == name_file:
                return "$%s" % key
        return name_file  # не нашли совпадиний - пусть остается таким

    def _att_list(att_list):
        """
        Преобразует список вложений - остаются только нужные ключи
        """
        att_temp_ = []
        if name_attacment:
            keys_att.append("Файл")  # добавляем дополнительный ключ
            for att_i in att_list:
                att_temp_dict = {}
                for key, value in att_i.items():
                    if key in keys_att:
                        if key == "Файл":
                            att_temp_dict[key] = {"Имя": get_name_file(value["Имя"])}
                        else:
                            att_temp_dict[key] = value
                att_temp_.append(att_temp_dict)
        else:
            for att_i in att_list:
                att_temp_.append({key: value for key, value in att_i.items() if key in keys_att})
        att_temp_.sort(key=lambda x: x["Название"])
        return att_temp_

    def _event_list(event_list):
        """
        :param event_list: список вложений из ответа метода СБИС.ПрочитатьДокумент
        возвращается упрощенная версия - только ключи из списка keys_event
        """
        event_list_temp_ = []
        for event_i in event_list:
            # перебираем список событий
            event_temp_ = {}
            for key, value in event_i.items():
                # анализируем событие - выбираем только нужные ключи
                if key in keys_event:
                    if key == "Вложение":
                        event_temp_["Вложение"] = _att_list(value)
                    elif key == "Группа":
                        group = {key: value for key, value in value.items() if key in keys_group}
                        event_temp_["Группа"] = group
                    else:
                        event_temp_[key] = value
            event_list_temp_.append(event_temp_)
        event_list_temp_.sort(key=lambda x: x["Название"])
        return event_list_temp_

    result = result.get("result", result)
    for key, value in result.items():
        if key in keys:
            if key == "Вложение":
                # выбираем из вложений только нужные ключи из списка keys_att
                temp_["Вложение"] = _att_list(value)
            elif key == "Событие":
                temp_["Событие"] = _event_list(value)
            else:
                temp_[key] = value
    return {"result": temp_}


def simple_res_read_doc_accounting(result, get_att=True, get_event=True, name_attacment=False, add_keys_doc=None,
                                   add_event_keys=None):
    """
    Выбирает из res(ответ метода СБИС.ПрочитатьДокумент) необходимые ключи
    :param result: ответ метода СБИС.ПрочитатьДокумент
    :name_attacment: возвращать объект Файл
    :get_att: возвращать вложения
    :get_event: возвращать события
    :add_keys_doc: СПИСОК дополнительных ключей документа
    :add_event_keys: СПИСОК дополнительных ключей событий
    """
    keys_doc = ["Название", "Направление", "Примечание", "Вложение", "Событие", "Состояние", "Тип", "Расширение"]
    keys_att = ["ВерсияФормата", "Зашифрован", "Модифицирован", "Название", "Направление", "ПодверсияФормата",
                "Подтип", "Служебный", "Тип", "Удален", "УдаленКонтрагентом"]
    keys_event = ["Вложение", "Группа", "Название"]
    keys_group = ["Код", "Название", "Описание", "Приоритет"]
    temp_ = {}
    if add_keys_doc:
        # расширяем список ключей документа
        keys_doc.extend(add_keys_doc)

    if add_event_keys:
        # расширяем список ключей документа
        keys_event.extend(add_event_keys)

    def get_name_file(name_file):
        """Ищем название вложения в Data"""
        for key, value, in Data.__dict__.items():
            if value == name_file:
                return "$%s" % key
        return name_file  # не нашли совпадиний - пусть остается таким

    def _att_list(att_list):
        """
        Преобразует список вложений - остаются только нужные ключи
        """
        att_temp_ = []
        if name_attacment:
            keys_att.append("Файл")  # добавляем дополнительный ключ
            for att_i in att_list:
                att_temp_dict = {}
                for key, value in att_i.items():
                    if key in keys_att:
                        if key == "Файл":
                            att_temp_dict[key] = {"Имя": value["Имя"]}
                        else:
                            att_temp_dict[key] = value
                att_temp_.append(att_temp_dict)
        else:
            for att_i in att_list:
                att_temp_.append({key: value for key, value in att_i.items() if key in keys_att})
        att_temp_.sort(key=lambda x: x["Название"])
        return att_temp_

    def _event_list(event_list):
        """
        :param event_list: список вложений из ответа метода СБИС.ПрочитатьДокумент
        возвращается упрощенная версия - только ключи из списка keys_event
        """
        event_list_temp_ = []
        for event_i in event_list:
            # перебираем список событий
            event_temp_ = {}
            for key, value in event_i.items():
                # анализируем событие - выбираем только нужные ключи
                if key in keys_event:
                    if key == "Вложение":
                        event_temp_["Вложение"] = _att_list(value)
                    elif key == "Группа":
                        group = {key: value for key, value in value.items() if key in keys_group}
                        event_temp_["Группа"] = group
                    else:
                        event_temp_[key] = value
            event_list_temp_.append(event_temp_)
        event_list_temp_.sort(key=lambda x: x["Название"])
        return event_list_temp_

    result = result.get("result", result)
    for key, value in result.items():
        if key in keys_doc:
            if key == "Вложение":
                # выбираем из вложений только нужные ключи из списка keys_att
                if get_att:  # только если нужно, по умолчанию возвращаем
                    temp_["Вложение"] = _att_list(value)
            elif key == "Событие":
                if get_event: # только если нужно, по умолчанию возвращаем
                    temp_["Событие"] = _event_list(value)
            else:
                temp_[key] = value
    return {"result": temp_}

def get_read_doc(client, id_doc, filter_add_filds=None, get_result=True, list_event=None, wait_time=180):
    """
    Возвращаем события по документу, а также общую информацию - замена метода СписокИзменений
    :client: экземпляр калсса Client
    :id_doc: идентификатор документа
    :filter_add_filds: дополнительные поля для вызова метода СБИС.ПрочитатьДокумент - СТРОКА
    (например: Получатель,Плательщик,КраткийСертификатЭП)
    :list_event: СПИСОК названий событий - ожидаем их
    :get_result: КОСТЫЛЬ НЕОБХОДИМ ДЛЯ СОВМЕСТИМОСТИ
    """
    params = {"Документ": {"Идентификатор": id_doc}}
    if filter_add_filds:
        params["Документ"]["ДопПоля"] = filter_add_filds
    # if list_event:
    #     while True:
    #         for event_i in list_event:
    #
    #         res_read = client.call("СБИС.ПрочитатьДокумент", **params)


    res_read = client.call("СБИС.ПрочитатьДокумент", **params)
    if get_result:
        res_read = {"result": res_read}
    return res_read

def get_info_list_change(docs, add_key_doc=None, ign_list_event_att=None):
    """
    Функция преобразует ответ метода СБИС.СписокИзменений в удобный объект(для дальнейшего анализа)
    :param docs: ответ метода СБИС.СписокИзменений
    """
    temp_list_events = []
    for doc in docs:
        temp_doc = {}
        if add_key_doc:
            temp_doc = {key: value for key, value in doc.items() if key in add_key_doc}

        for event_i in doc["Событие"]:
            if ign_list_event_att and event_i["Название"] in ign_list_event_att:
                # todo лучше не придумал пока
                continue
            temp = {}
            temp["Событие.Название"] = event_i["Название"]
            group_keys = ('Название', 'Описание', 'Код')
            temp["Событие.Группа"] = {key: value for key, value in event_i["Группа"].items()
                                      if key in group_keys}
            temp["Событие.Вложение"] = []
            interesting_keys = ('Подтип', 'Название', 'Направление', 'Тип', 'ВерсияФормата', 'Зашифрован',
                                'Служебный', 'ПодверсияФормата')
            for attachment_i in event_i["Вложение"]:
                filter_dict = {key: value for key, value in attachment_i.items() if key in interesting_keys}
                temp["Событие.Вложение"].append(filter_dict)
            temp["Событие.Вложение"].sort(key=lambda x: x["Название"])
            temp_doc.update(temp)
        temp_list_events.append(temp_doc)
    # Для удобства работы предстваим результа ввиде словаря - для дальнейшего использования модуля json
    temp_list_events.sort(key=lambda x: x["Событие.Название"])
    return {"result": temp_list_events}



def info_perform_action_2(res, add_doc_key=None, add_att_keys=None, add_event_key=None, ign_list_event_att=None):
    """
    Функция выбирает из ответа метода СБИС.ВыполнитьДействие
    только то, что необходимо проверять в плане тестирования
    :param res: результат метода СБИС.ВыполнитьДействие
    :param add_att_keys: СПИСОК дополнительных ключей
    """
    obj = {"Состояние": res["Состояние"], "Событие": []}
    group_keys = ["Название", "Описание", "Код"]
    group_att_keys = ["Служебный", "Подтип", "Тип", "Название", "Категория"]
    file_keys = ["Имя"]
    if add_att_keys:
        group_att_keys.extend(add_att_keys)
    if add_doc_key:
        for key in add_doc_key:
          obj[key] = res[key]

    for event_i in res["Событие"]:
        # проходим по списку "Событие"
        if ign_list_event_att and event_i["Название"] in ign_list_event_att:
            # todo лучше не придумал пока
            continue
        group = {key: value for key, value in event_i["Группа"].items() if key in group_keys}
        temp_event = {"Группа": group, "Вложение": [], "Название": event_i["Название"]}
        for att_i in event_i["Вложение"]:
            # проходим по вложениям события
            att_temp_dict = {}
            for key, value in att_i.items():
                if key in group_att_keys:
                    if key == "Файл":
                        att_temp_dict[key] = {key: value for key, value in att_i["Файл"].items() if key in file_keys}
                    else:
                        att_temp_dict[key] = value
            temp_event["Вложение"].append(att_temp_dict)
        # собираем объект - берем только то, что нужно
        temp_event["Вложение"].sort(key=lambda x: x["Название"])
        obj["Событие"].append(temp_event)
    return obj


def info_perform_action(res, add_doc_key=None, add_att_keys=None, add_event_key=None, ign_list_event_att=None):
    """
    Функция выбирает из ответа метода СБИС.ВыполнитьДействие
    только то, что необходимо проверять в плане тестирования
    :param res: результат метода СБИС.ВыполнитьДействие
    :param add_att_keys: СПИСОК дополнительных ключей
    """
    obj = {"Состояние": res["Состояние"], "Событие": []}
    group_keys = ["Название", "Описание", "Код"]
    group_att_keys = ["Служебный", "Подтип", "Тип", "Название", "Категория"]
    file_keys = ["Имя"]
    if add_att_keys:
        group_att_keys.extend(add_att_keys)

    for event_i in res["Событие"]:
        # проходим по списку "Событие"
        if ign_list_event_att and event_i["Название"] in ign_list_event_att:
            # todo лучше не придумал пока
            continue
        group = {key: value for key, value in event_i["Группа"].items() if key in group_keys}
        # не у всех событий есть вложения
        temp_event = {"Группа": group}
        if event_i.get("Вложение"):
            temp_event = {"Группа": group, "Вложение": []}

            for att_i in event_i["Вложение"]:
                # проходим по вложениям события
                att_temp_dict = {}
                for key, value in att_i.items():
                    if key in group_att_keys:
                        if key == "Файл":
                            att_temp_dict[key] = {key: value for key, value in att_i["Файл"].items() if key in file_keys}
                        else:
                            att_temp_dict[key] = value
                temp_event["Вложение"].append(att_temp_dict)

            # собираем объект - берем только то, что нужно
            temp_event["Вложение"].sort(key=lambda x: x["Название"])
        obj["Событие"].append(temp_event)
    return obj

def perform_action_decrypt(client, res_prep, link=True, id_doc=None, cont_name=None):
    """
    Функция принимает информацию о служебке которую нужно обработать (СБИС.ПодготовитьДействие
    СБИС.ВыполнитьДействие)
    СБИС.ВыполнитьДействие - вложения не подписываются а прикладываются ссылка на расшифрованный файл
    Фуккция вызывает метода СБИС.ПодготовитьДействие
    :param client: экземпляр класса Client
    :param cont_name: имя контейре в котором лежит сертификат для подписывания документов
    :param id_doc: идентификатор пакета документов (указывается в методе СБИС.ЗаписатьКомплект)
    :return: ответ метода СБИС.ВыполнитьДействие
    """
    cont_name = cont_name if cont_name else Data._NAME_CONTAINER_SERT_UL
    id_doc = id_doc if id_doc else Data._ID_SUITE
    from ctt.crypto import decrypt
    # подобная функция(испольузующая фрейворк otf) пока одна, поэтому я не стал заводить отдельных модуль
    # для подобных функций - поэтому использую динамический импорт

    list_attachment = []
    for att_i in res_prep["Вложение"]:
        #assert_that(att_0['Этап.Название'], equal_to(name), "Название этапа не отвечает ожиданиям")
        url_file = att_i["Файл"]["Ссылка"]
        file_name = att_i["Файл"]["Имя"]
        data_file = client.get(url_file)
        log("Расшифровываем данные - ключ(инспекции) установлен на машине - "
            "неоходимо уставновить если возникает ошибка при расшифровке")
        data = decrypt(data_file)
        log("Сформировать запрос к методу PUT. Отправить расшифрованный файл в файловое хранилище.")
        if link:
            storage_link = client.put(data, file_name, bin=True)
            i = {"Идентификатор": att_i["Идентификатор"],
            "Название": att_i["Название"],
            "Файл": {"Имя": att_i["Файл"]["Имя"], "Ссылка": storage_link}}
        else:
            data_base_64 = base64.b64encode(data).decode()
            i = {"Идентификатор": att_i["Идентификатор"],
            "Название": att_i["Название"],
            "Файл": {"Имя": att_i["Файл"]["Имя"], "Ссылка": "", "ДвоичныеДанные": data_base_64}}
        list_attachment.append(i)
    res_prep["Вложение"] = list_attachment
    log("СБИС.ВыполнитьДействие для переданного вложения - при вызове указан sign=False, что говорит"
        " что подпись будет приложена ввдиде сслылки(link=storage_link)")
    return perform_action(client, res_prep, sign=False, id_doc=id_doc, cont_name=cont_name)








def processing_declaration(client, stage, name, sert, id_doc=None, cont_name=None):
    """
    Функция принимает информацию о служебке которую нужно обработать (СБИС.ПодготовитьДействие
    СБИС.ВыполнитьДействие)
    СБИС.ВыполнитьДействие - вложения не подписываются а прикладываются ссылка на расшифрованный файл
    Фуккция вызывает метода СБИС.ПодготовитьДействие
    :param client: экземпляр класса Client
    :param stage: объект(словарь - результат вызова функции function_edo.get_info_stages)
    :param name: название ожидаемого этапа
    :param sert: сертификат(словарь) используемый для отправки
    :param cont_name: имя контейре в котором лежит сертификат для подписывания документов
    :param id_doc: идентификатор пакета документов (указывается в методе СБИС.ЗаписатьКомплект)
    :return: ответ метода СБИС.ВыполнитьДействие
    """
    cont_name = cont_name if cont_name else Data._NAME_CONTAINER_SERT_UL
    id_doc = id_doc if id_doc else Data._ID_SUITE
    from ctt.crypto import decrypt
    # подобная функция(испольузующая фрейворк otf) пока одна, поэтому я не стал заводить отдельных модуль
    # для подобных функций - поэтому использую динамический импорт
    log("СБИС.ПодготовитьДействие - служебный этап")
    prepare_action_reception_dec = prepare_action(client, stage, sert, id_doc=id_doc)
    # assert_that(len(prepare_action_reception_dec), equal_to(1), "Ожидалось получить одну запись %s" % name)

    list_attachment = []
    for att_i in prepare_action_reception_dec["Вложение"]:
        #assert_that(att_0['Этап.Название'], equal_to(name), "Название этапа не отвечает ожиданиям")
        url_file = att_i["Файл"]["Ссылка"]
        file_name = att_i["Файл"]["Имя"]
        data_file = client.get(url_file)
        log("Расшифровываем данные - ключ(инспекции) установлен на машине - "
            "неоходимо уставновить если возникает ошибка при расшифровке")
        data = decrypt(data_file)
        log("Сформировать запрос к методу PUT. Отправить расшифрованный файл в файловое хранилище.")
        storage_link = client.put(data, file_name, bin=True)
        i = {"Идентификатор": att_i["Идентификатор"],
         "Название": att_i["Название"],
         "Файл": {"Имя": att_i["Файл"]["Имя"], "Ссылка": storage_link}}
        list_attachment.append(i)
    prepare_action_reception_dec["Вложение"] = list_attachment
    log("Сформировать запрос к методу СБИС.ВыполнитьДействие. В аргументы метода подставить информацию"
        " о этапе (Название= %s) согласно приложенному примеру."
        " В поле Файл.Ссылка подставить ссылку на файловое хранилище, полученную на предыдущем этапе." % stage)
    log("СБИС.ВыполнитьДействие для переданного вложения - при вызове указан sign=False, что говорит"
        " что подпись будет приложена ввдиде сслылки(link=storage_link)")
    return perform_action(client, prepare_action_reception_dec, sign=False, id_doc=id_doc, cont_name=cont_name)


def search_stage_name(list_stage, name_stage):
    """
    Функция ищет нужный этап в списке - список это результам вызова функции get_info_stages
    :param list_stage: список этапов требующих обработки (результат функции get_info_stages)
    :param name_stage: название этапа
    """
    for stage_i in list_stage:
        if stage_i["Этап.Название"] == name_stage:
            return stage_i
    raise Exception("Не найден Этап.Название - %s" % name_stage)


def search_service_doc(list_event, name_event):
    """
    Возвращает информацию о служебке
    :param list_event: результат функции sbis_list_change
    :param name_event: название служебки
    """
    for doc_i in list_event:
        for event_i in doc_i["Событие"]:
            if event_i["Название"] == name_event:
                return event_i
    msg = "Анализировали список событий:" \
          "Ождили найти событие: {name_event}\n" \
          "{list_event}\n"
    raise Exception(msg.format(name_event=name_event, list_event=list_event))


def assert_prepare_action(client, path_req, path_res):
    """
    Выполняет и проверяет ответ метода СБИС.ПодготовитьДействие
    :param client: клиент
    :param path_req: путь к запросу
    :param path_res: путь к ответу
    """
    result = send_json_and_assert(client, path_req)
    result["result"]["Этап"][0]["Вложение"].sort(key=lambda i: (i['Название'], i["Файл"]["Имя"]))
    path_res = json.loads(read_file(path_res))
    path_res["result"]["Этап"][0]["Вложение"].sort(key=lambda i: (i['Название'], i["Файл"]["Имя"]))
    assert_that(path_res, is_in_json(result), "Ответ метода СБИС.ПодготовитьДействие отличается от ожидаемого")
    return result

def get_attachment_from_list(list_doc, key, value):
    """Возвращает вложение значение ключа key которого равно value
    :param list_doc: список вложений(например из ответа метода СБИС.ПрочитатьДокумент)
    :param key: ключ по котрому идет поиск вложения
    :param value: значение ключа для поиска
    """
    list_doc_ = []
    for att in list_doc:
        if att[key] == value:
            list_doc_.append(att)
    return list_doc_

def modification_responce(obj):
    input_file_str = json.dumps(obj, ensure_ascii=False)

    def is_simple_type(obj):
        return not isinstance(obj, (dict, list))

    def replace_value(obj, value, key):
        if type(obj) == dict:
            obj_copy = deepcopy(obj)
            for dict_key, dict_value in obj_copy.items():
                if value == str(dict_value):  # когда целый словарь заменяем строкой
                    obj[dict_key] = '$' + key
                elif not is_simple_type(dict_value):  # когда сложный тип: словарь или список
                    obj[dict_key] = replace_value(dict_value, value, key)
                elif dict_value == value:  # когда просто нашли
                    obj[dict_key] = '$' + key
        elif type(obj) == list:
            obj_copy = deepcopy(obj)
            for index, list_value in enumerate(obj_copy):
                if value == str(list_value):  # когда целый список заменяем строкой
                    obj[index] = '$' + key
                elif not is_simple_type(list_value):  # когда сложный тип: словарь или список
                    obj[index] = replace_value(list_value, value, key)
                elif value == value:  # когда просто нашли
                    obj[index] = '$' + key
        else:
            print('Что то промазал ты с типами')
        return obj

    for _key, _value in Data.__dict__.items():
        if type(_value) == str and _value in input_file_str:
            replace_value(obj, _value, _key)
    return obj

def get_attachment_from_list(list_doc, dict_):
    """Возвращает вложение значение ключа key которого равно value
    :param list_doc: список вложений(например из ответа метода СБИС.ПрочитатьДокумент)
    :param key: ключ по котрому идет поиск вложения
    :param value: значение ключа для поиска
    """
    list_doc_ = []
    keys = dict_.keys()
    for att in list_doc:
        success = True
        for key in keys:
            if att[key] != dict_[key]:
                success = False
        if success:
            list_doc_.append(att)
    return list_doc_
