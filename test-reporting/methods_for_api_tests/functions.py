# coding=utf-8
"""
Вспомогательные функции для тестов внешнего интерфейса
"""
import subprocess
import os
from atf import *
from methods_for_api_tests.json_delta import json_diff
from methods_for_api_tests.xml_delta import diff_xml
import uuid
from string import Template
from datetime import datetime
import json
from copy import deepcopy
import re
import tempfile
from atf.assert_that import equal_to_json_ignoring_index
import base64

conf = Config()


def get_data_file_base64(path):
    """возвращает содержимое файла в формате base_64"""
    f = open(path, mode='br')
    data_file = f.read()
    return base64.b64encode(data_file).decode()


def generate_guid():
    """Генерация GUID"""

    return str(uuid.uuid1())


def valid_uuid(uuid):
    regex = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
    match = regex.match(uuid)
    return bool(match)

def assert_xml(xml1, xml2, msg='Ошибка!', ignore_tags=None, ignore_attrib=None,
               tmp_response=None, tmp_request=None, with_text=False):
    """Странение двух xml

    На входе раскодированная из base64 xml

    :param xml1: эталонная xml
    :param xml2: полученная xml
    :param msg: сообщение об ошибке
    :param ignore_attrib: игнорируемые атрибуты, задаются словарём, {'тэг': 'атрибут'}
    :param ignore_tags: игнорируемые тэги, задаются списком ['тэг1', 'тэг2']
    :param tmp_request: запрос, чтобы вывести в лог
    :param tmp_response: ответ, чтобы вывести в лог
    :param with_text: есть ли текст для сравнения вне тега или нет.

    """
    diffs = diff_xml(xml1, xml2, ignore_tags, ignore_attrib, with_text)
    if diffs:
        tmp_str = ''
        for diff in diffs:
            diff = ' '.join(diff)
            tmp_str += 'отличия: %s\n' % diff.strip()
        if conf.get('VERBOSE') in ('Always', 'Error'):
            raise AssertionError('Тест: %s\n%s\n запрос: %s \n ответ: %s'
                                 % (msg.strip(), tmp_str.strip(), tmp_request, tmp_response))
        else:
            raise AssertionError('Тест: %s\n%s' % (msg.strip(), tmp_str.strip()))


def read_file(file_path, encoding=None, delimiter='$', idpattern=None, strip=True):
    """
    :param file_path: отностительный/полный путь к файлу
    :param strip: удалить переносы строк
    :return: возвращает файл одной строкой, удаляя пробелы вначале и конце строки
    """
    from data import Data
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
        tmp = type("MyTemplate", (Template,), {"delimiter": delimiter, "idpattern": idpattern})(tmp_str)
        return tmp.substitute(**Data.__get_var__())


def SignatureToHash(hash, cont_name="UL1AutoTestVI"):
        log("Процесс запускается под пользователем %s" % os.getlogin())
        log("Время начала генерации подписи - %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S+03'))
        path_to_root = os.path.dirname(os.getcwd())
        path_crypto_exe = os.path.join(path_to_root, "sbis-crypto-util\sbis-crypto-util.exe")
        pipe_output = tempfile.TemporaryFile()
        pipe_error = tempfile.TemporaryFile()
        process = subprocess.Popen([
            path_crypto_exe,
            #'--create_detached_sign',
            #'--in_file', path_in,
            #'--out_file', out_file,
            '--create_sign_on_hash',
            '--in_bytes', hash,
            '--out_bytes',
            '--cont_name', cont_name
        ], stdout=pipe_output, stderr=pipe_error)
        process.communicate(30)
        exit_code = process.returncode
        log("Код возврата %s" % exit_code)
        if exit_code != 0:
            name_error = pipe_error.name
            os.path.isfile(name_error)
            pipe_error.seek(0)
            result = pipe_error.read()
            text_error = result.decode("cp1251")
            pipe_error.close()
            raise Exception("При генерации подписи возникла ошибка - %s" % text_error)
        else:
            name = pipe_output.name
            os.path.isfile(name)
            pipe_output.seek(0)
            result = pipe_output.read()
            result_final = str(result).replace("\\r\\n", "")[2:-1]
            pipe_output.close()
        return result_final

def SignatureToFile(path_in, cont_name="UL1AutoTestVI"):
        log("Процесс запускается под пользователем %s" % os.getlogin())
        log("Время начала генерации подписи - %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S+03'))
        path_to_root = os.path.dirname(os.getcwd())
        path_crypto_exe = os.path.join(path_to_root, "sbis-crypto-util\sbis-crypto-util.exe")
        pipe_output = tempfile.TemporaryFile()
        pipe_error = tempfile.TemporaryFile()
        process = subprocess.Popen([
            path_crypto_exe,
            '--create_detached_sign',
            '--in_file', path_in,
            #'--out_file', out_file,
            #'--create_sign_on_hash',
            '--out_bytes',
            '--cont_name', cont_name
        ], stdout=pipe_output, stderr=pipe_error)
        process.communicate(30)
        exit_code = process.returncode
        log("Код возврата %s" % exit_code)
        if exit_code != 0:
            name_error = pipe_error.name
            os.path.isfile(name_error)
            pipe_error.seek(0)
            result = pipe_error.read()
            text_error = result.decode("cp1251")
            pipe_error.close()
            raise Exception("При генерации подписи возникла ошибка - %s" % text_error)
        else:
            name = pipe_output.name
            os.path.isfile(name)
            pipe_output.seek(0)
            result = pipe_output.read()
            result_final = str(result).replace("\\r\\n", "")[2:-1]
            pipe_output.close()
        return result_final

def copy_with_change(path1, path2):
    """
    :param path1: Берем файл отсюда и файл и копируем его с замененными данными
    :param path2: Путь к файлу, куда переносим данные с изменениями
    """

    from data import Data
    file1 = open(path1, 'r')
    file2 = open(path2, 'w')
    while True:
        line = file1.readline()
        if not line:
            line = file1.readline()
            if not line:
                break
        tmp = Template(line)
        file2.write(tmp.substitute(**Data.__get_var__()))
    file1.close()
    file2.close()


def assert_json(response1, response2, msg='', tmp_request=''):
        """Сравнивает 2 json.

        В json игнорируются значения 'ignore'.

        :param response1: эталонный ответ
        :param response2: пришедший ответ
        :param msg: сообщение об ошибке
        :param tmp_request: запрос, выводится в лог при включенной в конфиге опции VERBOSE

        """
        diffs = list()
        if response1 != response2:
            diffs = json_diff(response1, response2)

        if diffs:
            tmp_str = ''
            for diff in diffs:
                tmp_str += 'отличия %s\n' % diff
            if conf.get('VERBOSE') in ('Always', 'Error'):
                raise AssertionError('Тест: %s\n%s\nзапрос: %s\nответ: %s' %
                                     (msg.strip(), tmp_str, tmp_request, response2))
            else:
                raise AssertionError('Тест: %s\n%s\n' % (msg.strip(), tmp_str))


def get_password_from_sms(tel_number, when):
    """Получаем пароль для активации сертификата из СМС-сервиса"""

    import methods_for_api_tests.rpc
    client = methods_for_api_tests.rpc.Client('test-sms.inner.tensor.ru', is_https=False)
    client.auth('тест', "тест")
    #datetime.now().strftime('%Y-%m-%d %H:%M:%S+03')

    params = {
        "ДопПоля": [],
        "Фильтр":  {"d": ["23", when, tel_number],
                    "s": [{"n": "Агрегатор", "t": "Строка"},
                          {"n": "ДатаНач", "t": "Строка"},
                          {"n": "Адресат", "t": "Строка"}
                          ]},
        "Сортировка": None,
        "Навигация": {"s": [{"n": "Страница", "t": "Число целое"},
                            {"n": "РазмерСтраницы", "t": "Число целое"},
                            {"n": "ЕстьЕще", "t": "Логическое"}],
                      "d": [0, 20, False]}
    }

    result = client.call(method='ЖурналСтатусов.Список', _site='', **params)
    texts = str(result).split('\'')
    for text in texts:
        if 'Использование ключа ЭП на сервере. Пароль для подтверждения операции' in text:
            pin = text[-5:]
            break
    else:
        log("В журнале сообщений не найдено наше с пин-кодом")
        return
    log("Выловили код из текста сообщения - %s" % pin)
    return pin


def __check_option_true_crypt():
    """Проверка задания опций в конфиге"""

    options = ['PROGRAM_PATH', 'IMAGE_PATH', "DRIVE", "IMAGE_PASSWORD"]
    for option in options:
        if not conf.get(option):
            raise Exception('Не задана недоходимая настройка в конфиге: %s' % option)


def mount_image():
    """Монтируем образ в диск согласно настройкам в config.ini"""

    __check_option_true_crypt()
    program_path = os.path.abspath(conf.PROGRAM_PATH)
    image_path = os.path.abspath(conf.IMAGE_PATH)
    password = conf.PASSWORD
    drive = conf.DRIVE

    log('Монтируем образ %s в диск %s в программе TrueCrypt' % image_path, drive)

    subprocess.call([program_path, '/volume',  image_path, '/mountoption', 'removable', '/history',
                     'n', '/letter', drive, '/password', password, '/quit'], timeout=60)


def dismount_image():
    """Размонтируем образ"""

    program_path = os.path.abspath(conf.PROGRAM_PATH)
    drive = conf.DRIVE

    log('Размонтируем диск %s программе TrueCrypt' % drive)

    subprocess.call([program_path, '/beep', '/dismount', drive, '/force', '/quit',
                     'background', '/silent', '/wipecache'], timeout=60)


def time_out_and_relogin(client, login_password):
    """ Перелогиниваемся под другим пользователем """

    if login_password != '':
        login = login_password.split('/')[0]
        password = login_password.split('/')[1]
        log('Логинимся под %s' % login_password)
        client.call("САП.Выход", "/auth")
        client.auth(login, password)
        log('Теперь запросы выполняются под этим сидом = "%s"' % client.header.get('X-SBISSessionID'))


def relogin(client, login, password):
    """ Перелогиниваемся под другим пользователем """

    log('Логинимся под %s/%s' % (login, password))
    client.call("САП.Выход", "/auth")
    sid =client.auth(login, password)
    log('Теперь запросы выполняются под этим сидом = "%s"' % client.header.get('X-SBISSessionID'))
    return sid


def get_id_for_receiver(client, comment, type_doc="ДокОтгрВх", count_doc=1, wait_iter=50):
    """ Получаем идентификатор документа в аккаунте с клиентом client
    :param client: экземпляр класса atf.rpc.Client
    :param type_doc: тип документа для поиска
    :param comment: - маска для поиска документа
    :return: - идентификатор нужного документа у получателя
    """

    start = datetime.now()
    params = {"Фильтр": {"Тип": type_doc, "Маска": "%s" % comment}}# {"Фильтр": {"Маска": "%s" % comment}}
    for i in range(wait_iter):
        delay(2.5)
        result = client.call(method='СБИС.СписокДокументов', _site='', **params)
        docs = result["Документ"]
        if docs:
           if len(docs) != count_doc:
               continue
           elif len(docs) == 1:
               return docs[0]["Идентификатор"]
           else:
               return docs
        else:
            log("Документ пока еще не дошел до получателя")

        # try:
        #     return result["Документ"][0]["Идентификатор"]
        # except IndexError:
        #     log("Документ пока еще не дошел до получателя")
    delta = (datetime.now() - start).seconds
    assert_that(True, is_(False), "Документ (%s) так и не дошел до получателся за %d секунд" % (comment, delta))


def create_base64(path):
    import base64
    f = open(path, mode='br')
    file = f.read()
    return str(base64.encodestring(file)).replace(r'\n', '')


def create_string_of_base64(path):
    import base64
    f = open(path, mode='br')
    file = f.read()
    f.close()
    b64 = str(base64.encodestring(file)).replace(r'\n', '')
    return str(b64[2:-1])


def sign_file(path_in, path_out, fio):
    """
    :param path_in: Путь до файла, который хотим подписать
    :param path_out: Полный путь до файла подписи, который генерируем
    :param fio: ФИО владельца сертификата
    :return: Генерируем файл подписи по указанному пути
    """

    cur_path = os.getcwd()
    os.chdir('C:\Program Files\Crypto Pro\CSP')
    command = 'csptest.exe -sfsign -sign -detached -add -in "%s" -base64 -my ' \
              % path_in + '"%s"' % fio + ' -out "%s"' % path_out
    os.system(command)
    log('Появился ли файл подписи - ' + str(os.path.exists(path_out)))
    os.chdir(cur_path)

def compare_pdf(file_old, file_new):
    """ Сравнивем два файла .pdf по двоичным совпадениям внутри stream-endstream. На вход идут две двоичные строки,
        возвращается количество стримов, внутри которых данные у файлов различаются"""

    count = file_new.count(b'endstream')
    count_old = file_old.count(b'endstream')
    log('Количество двоичных stream\'ов у эталона = %d, а у полученного по ссылке = %d '
        '(Они должна совпадать)' % (count_old, count))
    stream_new = end_stream_new = old_stream = old_end_stream = 0

    errors = []
    for streams in [1, file_new.count(b'endstream') + 1]:
        stream_new = file_new.find(b'stream', stream_new)   # запоминаем границы стримов в обоих файлах
        end_stream_new = file_new.find(b'endstream', end_stream_new)
        old_stream = file_old.find(b'stream', old_stream)
        old_end_stream = file_old.find(b'endstream', old_end_stream)

        _new_pdf_stream = file_new[stream_new:end_stream_new]
        _old_pdf_stream = file_old[old_stream:old_end_stream]
        if _new_pdf_stream != _old_pdf_stream:
            errors.append(streams)
        stream_new += 10  # Определяем теги stream для последующего поиска
        end_stream_new += 10
        old_end_stream += 10
        old_stream += 10
    return errors


def check_datetime(test_time, _from=datetime(1987, 1, 1), _to=datetime(2222, 1, 1)):
    """ Принимаем три datetime - тестовое время, время С и время По.
    Проверяем, что нужное время лежит между этими двумя крайними значениями"""

    if _from <= test_time <= _to:
        return True
    else:
        return False


def universal_list_tests_change_file(file, new_file, list_method):
    """
    :param file: Передаем путь к файлу, где лежат базовые запросы-ответы
    :param list_method: Список методов, которые должны быть добавлены в новый файл для запуска тестов
    :param new_file: Путь к новому файлу с добавленными методами
    :return:
    """

    base_file = open(file)
    new_file_w = open(new_file, mode='w')

    for line in base_file:
        for method in list_method:
            new_file_w.write(line.replace('МетодДляЗамены', method))
    base_file.close()
    new_file_w.close()
    return new_file


def set_data_type_by_list_method(method):
    """ В зависимости от списочного метода определяем данные, которые он возвращает """

    if method == 'СБИС.СписокИзменений' or method == 'СБИС.СписокДокументов':
        return 'Документ', ""
    elif method == 'СБИС.СписокНашихОрганизаций':
        return 'НашаОрганизация', ""
    elif method == 'СБИС.СписокДокументовПоСобытиям':
        return "Реестр", '"ТипРеестра": "Входящие",'


def assert_field(response, field, code, value, message, details):
    """
    :param response: Ответ сервера
    :param field: Поле, которые должны проверять
    :param value: Предполагаемый ответ (Если заранее оно не известно, но должно быть непустое, указываем value=Непустое)
    :param code: код ответа
    :param message: Описание ошибки
    :param details: Детализация ошибки
    """

    if code == '500':
        assert_that('error', is_in(response), "Сервер должен был вернуть ошибку")
        assert_that(response.get('error').get('message'), equal_to(message),
                    "Сервер вернул неверное значение message при ошибке")
        assert_that(response.get('error').get('details'), equal_to(details),
                    "Сервер вернул неверное значение details при ошибке")

    elif code == '200':
        key_list = field.split('.')
        response = response.get('result')
        for key in key_list:
            if type(response) == dict:
                response = response.get(key)
            elif type(response) == list:
                response = response[0]
        if value == "Непустое":
            assert_that(response, not_equal(''), "Вернулось пустое значение " + field)
            return response
        else:
            assert_that(response, equal_to(value), "Ответ (%s) не совпал с ожидаемым (%s)" % (response, value))
            return response


def sort_event_and_investing(obj_json, ignoge_elements_=None):
    """Сортирует Вложение и Событие чтобы гарантировать одинаковй порядок следования"""
    ignoge_elements = []
    if ignoge_elements_:
        ignoge_elements = ignoge_elements_ #  'Утверждение', 'Подтверждение отправки электронного документа оператором',
                          #'Товарная накладная (титул покупателя)' 'Утверждение',

    if type(obj_json['result']) is dict:
        if obj_json['result'].get('Вложение'):
            list_investing = obj_json['result']['Вложение']
            if type(list_investing) is list:
                list_investing.sort(key=lambda i: i.get('Название', ' '))
                index_for_delete = []
                for i in range(len(list_investing)):
                    name = list_investing[i].get('Название', 'нет названия')
                    print(name)
                    if name in ignoge_elements:
                        index_for_delete.append(i)
                if index_for_delete:
                    index_for_delete.sort(reverse=True)
                    for index in index_for_delete:
                        list_investing.pop(index)

        print("######### События ##########")
        if obj_json['result'].get('Событие'):
            list_event = obj_json['result']['Событие']
            if type(list_event) is list:
                copy_list_event = deepcopy(list_event)
                # проверим - событие входит в список ignoge_elements
                count_event = len(copy_list_event)
                index_for_delete = []
                for event_i in range(count_event):
                    if copy_list_event[event_i]['Название'] in ignoge_elements:
                        index_for_delete.append(event_i)
                if index_for_delete:
                    index_for_delete.sort(reverse=True)
                    for index in index_for_delete:
                        copy_list_event.pop(index)
                copy_list_event.sort(key=lambda i: i['Название'])
                obj_json['result']['Событие'] = copy_list_event
                # в событиях присутствует массив вложений - отсортирует по названия вложений
                count_event = len(list_event)
                for event_i in range(count_event):  # проходим по всем событиям
                    investing_event = obj_json['result']['Событие'][event_i].get("Вложение")
                    if investing_event:  # если  у события есть вложение и объект список (не ignore)
                        if type(investing_event) is list:
                            investing_event.sort(key=lambda i: i['Название'])  # отсортировали вложения в событии
                            # проверим вложения события на предмет игнорируемых
                            count_event_investing = len(investing_event)
                            # создаем копию списка вложений для события - из которого будут удалены некоторые вложения
                            delete_index_investing_event = []
                            for x in range(count_event_investing):
                                if investing_event[x]['Название'] in ignoge_elements:
                                    delete_index_investing_event.append(x)
                            if delete_index_investing_event:
                                delete_index_investing_event.sort(reverse=True)
                                for i in delete_index_investing_event:
                                    investing_event.pop(i)


                for j in range(count_event):
                    print(list_event[j]['Название'])
                    if list_event[j].get("Вложение") and type(list_event[j].get("Вложение")) is list:
                        for k in range(len(list_event[j].get("Вложение"))):
                            print("      %s" % list_event[j]["Вложение"][k]['Название'])
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

def sort_and_delete_investing(obj_json, responce, sub_attr='Событие', add_sort=None):
    """Сортирует Вложение и Событие чтобы гарантировать одинаковй порядок следования"""
    def get_list_names(list_dicts):
        temp = []
        if list_dicts:
            for elm in list_dicts:
                name = elm.get('Название')
                if name:
                    temp.append(name)
        return temp

    def print_elm(list_event_responce, sub_attr='Событие'):
        list_event = list_event_responce[sub_attr]
        count = len(list_event_responce[sub_attr])
        for j in range(count):
            print(list_event[j]['Название'])
            if list_event[j].get("Вложение") and type(list_event[j].get("Вложение")) is list:
                for k in range(len(list_event[j].get("Вложение"))):
                    print("      %s" % list_event[j]["Вложение"][k]['Название'])
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    def sort_(list_event_template):
        for event_i in list_event_template:  # проходим по всем событиям
            investing_event = event_i.get("Вложение")
            if investing_event:  # если  у события есть вложение и объект список (не ignore)
                if type(investing_event) is list:
                    fun_sort = lambda i: (i['Название'], i['Направление'])
                    if add_sort:
                        fun_sort = lambda i: (i['Название'], i['Направление'], i[add_sort])
                    investing_event.sort(key=fun_sort)  # отсортировали вложения в событии
                    event_i["Вложение"] = investing_event

    if obj_json.get(sub_attr) and responce.get(sub_attr):
        list_event_template = obj_json[sub_attr]
        list_event_responce = responce[sub_attr]
        copy_responce = deepcopy(list_event_responce)
        if type(list_event_template) is list:
            list_arrt = get_list_names(list_event_template)
            if list_arrt:
                delete_elements = []
                for index, val in enumerate(copy_responce):
                    name = val.get('Название')
                    if name not in list_arrt:
                        delete_elements.append(index)
                        log("###### DEL %s - %s ######" % (sub_attr, name))
                if delete_elements:
                    delete_elements.sort(reverse=True)
                    for i in delete_elements:
                        list_event_responce.pop(i)
                if sub_attr == 'Вложение':
                    fun_sort = lambda i: (i['Название'], i['Направление'])
                    if add_sort:
                        fun_sort = lambda i: (i['Название'], i['Направление'], i[add_sort])
                    list_event_template.sort(key=fun_sort)
                    list_event_responce.sort(key=fun_sort)
                else:
                    list_event_template.sort(key=lambda i: i['Название'])
                    sort_(list_event_template)
                    list_event_responce.sort(key=lambda i: i['Название'])
                    sort_(list_event_responce)
        else:
            list_event_responce = 'ignore'

    return obj_json, responce

def send_json_and_assert(client, request_path, response_path='', code=200, equal=False,
                         equal_index_ignore=False, log_events=False, sort_=True, ignore=None):
    """ Отправляем запрос на сервер и проверяем ответ, если это нужно.
    :param client: клиент
    :param request_path:  путь до файла с запросом. Обязательный параметр!
    :param response_path: путь  до файла с эталонным ответом, с которым хотим сравнивать полученный от сервера ответ
    :param equal: Передаем True, если хотим проверять идентичность ответов, по умолчанию делается проверка вхождения
    :param log_events: Передаем тру, чтобы залогировать перед проверкой список пришедших событий и вложений
    """
    tmp_request = read_file(os.path.join(request_path))
    result = client.send_json(test_json=tmp_request, code=code)
    # log('\n############################################################\n'
    #     'ЗАПРОС ОТПРАВЛЯЕТСЯ В СЕССИИ - %s'
    # '\nЗАПРОС:\n      %s\n'
    # '\n############################################################\n'
    # 'ОТВЕТ:\n    %s\n' % (client.header.get('X-SBISSessionID'), tmp_request, result))
    # log('Готовим запрос (%s) .  Они выполняются под этой сессией - %s'
    #     % (tmp_request, client.header.get('X-SBISSessionID')))
    if log_events:
        log('Список вложений:')
        for doc in result.get('result').get('Вложение'):
            print(doc.get('Название'), end='\n')
        log('Список событий: \n')
        for event in result.get('result').get('Событие'):
            print(event.get('Название'), end='\n')
    if response_path:
        tmp_response = read_file(response_path)
        tmp_response = json.loads(tmp_response)
        if sort_:
            sort_event_and_investing(tmp_response, ignore)
            sort_event_and_investing(result, ignore)
        if equal_index_ignore:
            assert_that(tmp_response, equal_to_json_ignoring_index(result),
                        "Ответ не совпал с эталонным при проверке с игнорированием порядка (%s)" % response_path)
        elif equal:
            assert_that(tmp_response, equal_to_json(result), "Ответ не совпал с эталонным (%s)" % response_path)
        else:
            assert_that(tmp_response, is_in_json(result),
                        "Джейсон ответа не включается в себя эталонный ответ (%s)" % response_path)
    return result


def assert_json_perform(request_path, response_path='', code=200, equal=False, log_events=False, reload=False):

    def delete_(tmp_response, responce):
        tmp_response, responce = sort_and_delete_investing(tmp_response, responce, sub_attr='Вложение')
        return tmp_response, responce
    tmp_response, responce = delete_(request_path, response_path)
    if equal:
            assert_that(tmp_response, equal_to_json(responce), "Ответ не совпал с эталонным (%s)" % response_path)
    else:
        assert_that(responce, is_in_json(tmp_response),
                        "Ответ не включается в себя эталонный ответ (%s)" % response_path)


def debug_send_json_and_assert(client, request_path, response_path='', code=200, equal=False, log_events=False, reload=False, add_sort=None):
    """ Отправляем запрос на сервер и проверяем ответ, если это нужно.
    :param client: клиент
    :param request_path:  путь до файла с запросом. Обязательный параметр!
    :param response_path: путь  до файла с эталонным ответом, с которым хотим сравнивать полученный от сервера ответ
    :param equal: Передаем True, если хотим проверять идентичность ответов, по умолчанию делается проверка вхождения
    :param log_events: Передаем тру, чтобы залогировать перед проверкой список пришедших событий и вложений
    :return:
    """
    if isinstance(request_path, dict):
        responce = request_path
    else:
        tmp_request = read_file(request_path)
        responce = client.send_json(test_json=tmp_request, code=code)

    def delete_(tmp_response, responce):
        result_responce = responce.get('result')
        result_tmp_response = tmp_response.get('result')
        if result_responce and result_tmp_response:
            tmp_response['result'], responce['result'] = sort_and_delete_investing(result_tmp_response, result_responce, add_sort=add_sort)
            tmp_response['result'], responce['result'] = sort_and_delete_investing(result_tmp_response, result_responce, sub_attr='Вложение', add_sort=add_sort)

    if response_path:
        tmp_response = read_file(response_path)
        tmp_response = json.loads(tmp_response)
        delete_(tmp_response, responce)
        if reload:
            def update(obj_mat):
                delay(5)
                responce_new = client.send_json(test_json=tmp_request, code=code)
                delete_(tmp_response, responce_new)
                obj_mat.item2 = responce_new
                return tmp_response
            if equal:
                matches = equal_to_json(responce)
                assert_that(lambda: update(matches), matches, "Ответ не совпал с эталонным (%s)" % response_path, and_wait(20))
            else:
                matches = is_in_json(responce)
                assert_that(lambda: update(matches), matches,
                            "Ответ не включается в себя эталонный ответ (%s)" % response_path, and_wait(20))
        else:
            if equal:
                assert_that(tmp_response, equal_to_json(responce), "Ответ не совпал с эталонным (%s)" % response_path)
            else:
                assert_that(tmp_response, is_in_json(responce),
                            "Ответ не включается в себя эталонный ответ (%s)" % response_path)
    return responce


#from atf.api.recordset3 import RecordSet3

def post_delete_docs_by_comment(client, comment, start_time_case, user=None, password=None, _out=False, _in=False):
    """
    :param comment: маска для поиска документов
    :param start_time: время начала выполнения тест кейсов
    :param user: логин
    :param password: пароль
    :param client: передаем клиента
    :param _out: True, если нужно удалять исходящие документы
    :param _in: True, если нужно удалять входящие документы
    """
    # --USER_OPTIONS DELETE=True
    conf = Config()
    if conf.get("DELETE_DOC") == 1:
        log("Документы не удаляются - сборка запущена с параметром NOT_DELETE_DOC")
        return

    if user is None and password is None:
        log('Готовимся удалять документы по по маске "%s"' % comment)
    else:
        relogin(client, user, password)
        log('Удаляем документы по маске "%s"' % comment)
    params = {
        "ДопПоля": [],
        "Фильтр": {
            "d": [False, "-1", "-1", "Все", "-1", "-3", comment, "Нет"],
            "s": [{"n": "ФильтрУдаленные", "t": "Логическое"},
                  {"n": "ФильтрАвторИлиОтвОтдел", "t": "Строка"},
                  {"n": "ФильтрАвторИлиОтветственный", "t": "Строка"},
                  {"n": "ФильтрВладелец", "t": "Строка"},
                  {"n": "ФильтрКонкретныйИсполнительID", "t": "Строка"},
                  {"n": "ТипДокумента", "t": "Строка"},
                  {"n": "ФильтрПоМаске", "t": "Строка"},
                  {"n": "ФильтрИзСписка", "t": "Строка"}
            ]
        },
        "Сортировка": None,
        "Навигация": {
            "s": [
                {"n": "Страница", "t": "Число целое"}, {"n": "РазмерСтраницы", "t": "Число целое"},
                {"n": "ЕстьЕще", "t": "Логическое"}
            ],
            "d": [0, 50, True]
        }
    }
    method = ''
    if _out:
        method = "РеестрИсходящих.СписокСобытий"
    if _in:
        method = "РеестрВходящих.СписокСобытий"
    if method:
        table = client.call(method, **params)
        # xxx = RecordSet3(table).record
        # id = xxx[0]["ИдентификаторДокумента"]
        # xxx_30 = xxx[0] ["Дата"]
        for doc in table.get('d'):
            _id = int(doc[1])
            if conf.get("DELETE_DOC") == 0:
                # Удалим документы только для запущенной сборки
                print('doc={0}'.format(doc))
                try:
                    time_doc = datetime.strptime(doc[3][:-3], "%Y-%m-%d %H:%M:%S")
                    if time_doc < start_time_case:
                        continue
                except:
                    log("Ошибка преобразования даты - %s\ n Идентификатор документа %s "
                        % (doc[3], _id))
                    continue
            log('Удаляем документ с ИДО = %d' % _id)
            try:
                client.call('Документ.НаУдалить', ИдО=_id)
                log('Документ с ИДО=%d удален' % _id)
            except Exception as error:
                log('Не удалось удалить документ - %s' % error)

def log_description(path):
    """Логируется в начале теста его описание, путь до которого передается в path"""

    file = open(path, 'r')
    print('========================= ОПИСАНИЕ ТЕСТА =========================')
    for line in file:
        print(line.replace('\n', ''))
    path = path.replace('\\', '/')
    http_path = Config().SVN_PATH + '/' + path
    print('Путь до файла описания теста - ' + http_path)
    print('==================================================================')


def sign_service_doc_by_server_cert(client, id_doc, cert):
    """
    :param client: Передаем клиента для выполнения запросов
    :param id_doc: идентификатор документа
    :param cert: Передаем полные данные о серверном сертификате, который испольуется в подписании документов
    :return: Возвращаем количество подписанных этапов
    """

    result = client.call('СБИС.СписокСлужебныхЭтапов', Фильтр={"ИдентификаторДокумента": id_doc})
    docs = 0
    for phase in result.get("Документ"):
        phase_id = phase.get('Этап')[0].get('Идентификатор')
        phase_name = phase.get('Этап')[0].get('Название')
        log('Подпишем служебный документ с названием %s' % phase_name)
        json1 = '{"jsonrpc": "2.0","method": "СБИС.ПодготовитьДействие", "params": {"Документ": {"Идентификатор": ' \
                '"%s","Этап": {"Действие": {"Название": "Обработать служебное","Сертификат": %s},' \
                '"Идентификатор": "%s","Название": "%s"}}},"id": 0}' % (id_doc, cert, phase_id, phase_name)
        json2 = '{"jsonrpc": "2.0","method": "СБИС.ВыполнитьДействие","params": {"Документ": {"Идентификатор": ' \
                '"%s","Этап": [{"Действие": [{"Комментарий": "","Название": "Обработать служебное","Сертификат": ' \
                '%s,"ТребуетКомментария": "Нет", "ТребуетПодписания": "Да","ТребуетРасшифровки": ' \
                '"Нет"}],"Идентификатор": "%s","Название": "%s","Служебный": "Нет"}]}},"id": 0}' % (
                id_doc, cert, phase_id, phase_name)
        client.send_json(json1, code=200)
        client.send_json(json2, code=200)
        docs += 1
    return docs


def close_all_service_docs_after_sending(client, sender_id_doc, comment, doc_type="ДокОтгрИсх"):
    """ Этот метод дожидается появление всех служебок и закрывает их серверным сертификаторм (используются логин-пароли
     из конфига и данные    по сертификатам отправителя и получателя из класса Data).
    Вызывать этот метод имеет смысл сразу после отправки.
    Важно: работает не для всех регламентов. Применять для ДокОтгрИсх.
    Ссылка на схему - "https://help.sbis.ru/resources/help/images/Edo/shema_ch.jpg"

    :param client: клиент для выполнения пост-запросов
    :param sender_id_doc: идентификатор отправленного документа у отправителя
    :param comment: примечание документа, по которму будем искать его на стороне получателя
    :return: Возвращаем идентификатор документа на стороне получателя. Клиент остается залогиненным под получателем!
    """

    from data import Data
    #cert1, cert2 = Data._SENDER_SERVER_CERT, Data._RECEIVER_SERVER_CERT
    cert1, cert2 = Data._SENDER_FULL_CERT, Data._RECEIVER_FULL_CERT
    sender_login, sender_password, receiver_login, receiver_password = \
        Config().USER_NAME, Config().PASSWORD, Config().USER_2_NAME, Config().PASSWORD

    log('Ждем и подписываем Подтверждение получения документа оператором на стороне отправителя')
    assert_that(lambda: sign_service_doc_by_server_cert(client, sender_id_doc, cert1),
                    equal_to(1), "Не дождались появления служебки от оператора после отправки документа", and_wait(180, 10))

    log('Переходим на получателя')
    relogin(client, receiver_login, receiver_password)
    receiver_id = get_id_for_receiver(client, comment, doc_type.replace('Исх', "Вх"))
    event2 = "Подтверждение отправки электронного документа оператором"
    event = "Подтверждение даты отправки"
    assert_that(event, is_in(lambda: str(client.call("СБИС.ПрочитатьДокумент",
                                                     **{"Документ": {"Идентификатор":  receiver_id}}))),
                "Не пришло событие %s от оператора" % event, and_wait(50, 10))
    assert_that(event2, is_in(lambda: str(client.call("СБИС.ПрочитатьДокумент",
                                                      **{"Документ": {"Идентификатор":  receiver_id}}))),
                "Не пришло событие %s от оператора" % event2, and_wait(50, 10))
    assert_that(lambda: len(client.call('СБИС.СписокСлужебныхЭтапов',
                            Фильтр={"Блокировать": "Нет", "ИдентификаторДокумента": receiver_id}).get('Документ')),
                    equal_to(2), "Не дождались получения двух активных этапов у получателя", and_wait(180, 10))

    assert_that(sign_service_doc_by_server_cert(client, receiver_id, cert2),
                equal_to(2), "Должны были подписать сразу две служебки")
    assert_that(lambda: sign_service_doc_by_server_cert(client, receiver_id, cert2),
                equal_to(1), "Не сгенерировалась еще одна служебка после подписания Извещения о получении",
                and_wait(180, 10))

    log('Идем на отправителя и проверяем, что документ доставлен')
    relogin(client, sender_login, sender_password)
    assert_that(lambda: client.call("СБИС.ПрочитатьДокумент",
                                    **{"Документ": {"Идентификатор": sender_id_doc}}).get('Состояние').get('Код'),
                    equal_to('4'), "Документ должен быть доставлен (Состояние.Код = 4)", and_wait(30, 5))
    relogin(client, receiver_login, receiver_password)
    return receiver_id  















