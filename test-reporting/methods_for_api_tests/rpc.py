# coding=utf-8
from http.client import HTTPConnection, HTTPSConnection, OK
from http.cookies import SimpleCookie
from datetime import datetime, timedelta
import json
from atf.config import Config
from atf.logfactory import log
import os
import sqlite3
import inspect
from urllib import request
import re
from base64 import b64encode
from urllib.parse import *
import socket
import zipfile
from shutil import copyfile


class Wrapper:

    use_methods = {}
    def __init__(self, cls, inst_client):
        self.cls = cls
        self.client = inst_client
        self.db_conn = sqlite3.connect(self.client.config.PATH_TO_BASE)
        self.conn_cursor = self.db_conn.cursor()
        self.table_name = self.client.config.TABLE_NAME
        self.conn_cursor.execute("CREATE TABLE IF NOT EXISTS %s "
                                 "             (name_method TEXT, path_module TEXT, lineno INTEGER);" % self.table_name)


    def con_request(self, method, url, body=None, headers={}):
        try:
            if method == "POST":
                cf = inspect.currentframe()
                out_stack_frames = inspect.getouterframes(cf)
                f_lineno = 0
                try:
                    for frame in out_stack_frames:
                        temp_path = frame[1]
                        temp_path = os.path.normpath(temp_path)
                        module_name = temp_path.rsplit("\\", 1)[1]
                        if module_name.startswith("test"):
                            f_lineno = frame[2]
                            break
                except Exception as e:
                    print(e)
                body_json = json.loads(body)
                method_bl = body_json.get("method", "NOT_METHOD")
                all_info_method_bl = self.use_methods.get(method_bl, "NOT_METHOD")
                duplicate = False  # ОДИН И ТОТ ЖЕ МЕТОД НА ОДНОЙ И ТОЙ ЖЕ СТРОКЕ
                if all_info_method_bl == "NOT_METHOD":
                    # первый раз встечаемся с методом
                    self.use_methods[method_bl] = []
                else:
                    for mod_name, lino in all_info_method_bl:
                        if mod_name == module_name and lino == f_lineno:
                            duplicate = True
                            break
                if not duplicate:
                    self.use_methods[method_bl].append([module_name, f_lineno])
                    self.conn_cursor.execute("INSERT INTO %s VALUES (?, ?, ?)" % self.table_name, (method_bl, module_name, f_lineno))
                    self.db_conn.commit()
        except sqlite3.OperationalError as e:
            print(e)
        return self.request_copy(method, url, body, headers)

    def __call__(self, *args, **kwargs):
        self.instance = self.cls(*args, **kwargs)
        self.request_copy = self.instance.request
        self.instance.request = self.con_request
        return self.instance

def zipdir(ziph_name, file_name, data, path_create_zip="TEMP_ZIP_FILES", del_file=False):
    """
    Создаем архив для отправки - эмулящии 1С
    :param path: путь к каталогу для архивирования(содержимое каталога будет архивироваться)
    :param list_name_files: список файлов в которые необходимо подставить значения
    :param ziph_name: имя файла (архива)
    :param path_create_zip: каталог в корне для создаваемых архивов
    :param del_file: удаляем файл после создания и чтения

    возращает данные архива(бинарные) или путь к созданному архиву
    """
    path_create_zip = os.path.realpath(path_create_zip)
    if not os.path.isdir(path_create_zip):
        os.mkdir(path_create_zip)
    path_create_zip = os.path.join(path_create_zip, ziph_name)
    zipf = zipfile.ZipFile(path_create_zip, 'a', zipfile.ZIP_DEFLATED)
    try:
        if True:
            zipf.writestr("raw\%s" % file_name, data.encode("utf-8"))#cp1251
        else:
            zipf.write(path_to_files, file_name)
    finally:
        zipf.close()
    with open(path_create_zip, "rb") as f:
        data = f.read()
    if del_file:
        os.remove(path_create_zip)
    else:
        # возращаем путь до файла
        return path_create_zip
    return data


class Client:
    """Удалённый вызов методов БЛ"""

    def __set_address(self):
        """Определяем куда будем отправлять запрос"""

        if self.config.get('ADDRESS'):
            address = self.config.ADDRESS
        else:
            address = '/service/'
        return address


    def __init__(self, hostname='', is_https=False, url='', sid=''):
        """Инициализация"""

        if url:
            self.hostname, is_https = self.__init(url)
            self.url = url
        else:
            self.hostname = hostname
            self.url = ("https://" if is_https else "http://") + self.hostname
        self.header = {'Content-type': 'application/json; charset=UTF-8',
                       'X-LogEntireTask': 'true',
                       'user-agent': 'SbisAutotest/1.0.0 ({0})'.format(socket.gethostname())}
        self.timepass = {}
        self.config = Config()
        self.address = self.__set_address()
        self.bl_prefix = self.config.get("BL_PREFIX")
        if not self.bl_prefix:
            self.bl_prefix = "?srv=1"
        self.number_block = 1
        if self.config.get("FIDDLER_DEBUG") == True:
            self.connection = HTTPConnection
        else:
            self.connection = HTTPSConnection if is_https else HTTPConnection
        if self.config.__dict__.get("LOG_REQUESTS"):
            self.connection = Wrapper(self.connection, self)

    @staticmethod
    def __init(url):
        """Вычисление hostname и типа подключения"""

        result = request.urlparse(url)
        is_https = True if(result.scheme == "https") else False
        return result.netloc, is_https

    def auth_group(self, login, password, site, group, bus_logic=False):
        """Авторизация

        :param login: логин
        :param password: пароль

        """
        result = self.call('Auth.LogIntoGroup', '/admin_api', bus_logic=bus_logic, Login=login, Site=site, Group=group)
        self.sid = result
        self.url = self.config.SITE
        self.hostname = self.__init(self.url)[0]
        cookie = SimpleCookie()
        cookie['sid'] = self.sid
        self.header['X-SBISSessionID'] = self.sid
        x_api_version = self.config.get("X-API-VERSION")
        if x_api_version:
            self.header['X-API-Version'] = x_api_version
        url = self.url + "/ver.html"
        try:
            ver = self.get(url)
            var_text = ver.decode()
            datepat = re.compile(r"<.*?>")
            text = datepat.sub("", var_text)
        except:
            text = "Произошла ошибка при обращении к странице %s - " % url
        log("\n###################################\n"
            "Содержание страницы ver.html\n"
            "%s"
            "###################################\n" % text)
        return result


    def auth(self, login, password, bus_logic=False):
        """Авторизация

        :param login: логин
        :param password: пароль
        :param bus_logic: прибавлять(или нет) к адресу значение BL_PREFIX из конфига по умолчанию ?srv=1

        """
        if self.config.get("NAME_GROUP_SERVER"):
            self.url = self.config.PRIVATE_SITE
            self.hostname = self.__init(self.url)[0]
            result = self.call('Auth.LogIntoGroup', '/admin_api', bus_logic=bus_logic, Login=login,
                               Site=self.config.SITE, Group=self.config.NAME_GROUP_SERVER)
            self.url = self.config.SITE
            self.hostname = self.__init(self.url)[0]
        else:
            result = self.call('САП.Аутентифицировать', '/auth', bus_logic=bus_logic, login=login, password=password)
        cookie = SimpleCookie()
        cookie['sid'] = result
        self.sid = result
        log('Авторизовались. SID: %s' % cookie['sid'])
        self.header['Cookie'] = str(cookie)
        self.header['X-SBISSessionID'] = result
        # А нужно ли использовать заголовок X-API-Version (для тестов транспорта отчетности заголовок необходим)
        x_api_version = self.config.get("X-API-VERSION")
        if x_api_version:
            self.header['X-API-Version'] = x_api_version
        url = self.url + "/ver.html"
        try:
            ver = self.get(url)
            var_text = ver.decode()
            datepat = re.compile(r"<.*?>")
            text = datepat.sub("", var_text)
        except:
            text = "Произошла ошибка при обращении к странице %s - " % url
        log("\n###################################\n"
            "Содержание страницы ver.html\n"
            "%s"
            "\n###################################\n" % text)
        return result
    

    def output_message(self, block, status_code, message_type, message_params):
        """Метод для генерации сообщения в логи"""
        prefixes = {"error": "В ОТВЕТЕ ОБНАРУЖЕН - error\n",
                    "bad_result": "В ОТВЕТЕ НЕ ОБНАРУЖЕН - result\n",
                    "bad_status": "КОД ОТВЕТА НЕ СОВПАДАЕТ С ЗАДАННЫМ\n"}
        code = "\nКОД ОТВЕТА: {}\n".format(status_code)

        success_block_start = "\nНАЧАЛО БЛОКА - {0}{1:#<60}".format(block, " ")
        success_block_end = "\nКОНЕЦ БЛОКА - {0}{1:#<60}".format(block, " ")
        error_block_start = "\nНАЧАЛО БЛОКА С ОШИБКОЙ - {0}{1:#<60}".format(block, " ")
        error_block_end = "\nКОНЕЦ БЛОКА С ОШИБКОЙ - {0}{1:#<60}".format(block, " ")

        base_message = "\nЗАПРОС ОТПРАВЛЯЕТСЯ В СЕССИИ - {0}\n" \
                       "\nЗНАЧЕНИЕ ЗАГОЛОВКА X-Uniq-ID - {1}\n" \
                       "\nССЫЛКА НА ЛОГИ ВЫЗОВА - {2}\n" \
                       "\nЗАПРОС:\n    {3}\n" \
                       "\n         **************************************************         \n" \
                       "\nОТВЕТ:\n    {4}\n".format(*message_params)
        if message_type == "success":
            message = success_block_start + code + base_message + success_block_end
        else:
            message = error_block_start + prefixes[message_type] + code + base_message + error_block_end
        return message


    def generate_saz(self, connection, response, _site, body, decode_data):

        str_info_request = "{method} {path} {protocol}".format(method=connection._method, path=_site, protocol=connection._http_vsn_str)
        str_headers_request = "\r\n".join(["{key}: {value}".format(key=key, value=value) for key, value in self.header.items()])
        str_all_request = "{str_info}\r\n{headers}\r\n\r\n{body}".format(str_info=str_info_request, headers=str_headers_request, body=body)
        ziph_name = "xxx.saz" #  "xxx.zip"
        file_name = "%s_c.txt" % self.number_block
        data = str_all_request
        zipdir(ziph_name, file_name, data, path_create_zip="TEMP_ZIP_FILES", del_file=False)

        str_info_res = "{protocol} {code} {reason}".format(protocol=connection._http_vsn_str, code=response.getcode(), reason=response.reason)
        str_headers_res = "\r\n".join(["{key}: {value}".format(key=key, value=value) for key, value in response.getheaders()])
        # работает copyfile(os.path.join(os.getcwd(), r"TEMP_ZIP_FILES\\%s" % ziph_name), r"TEMP_ZIP_FILES\\new_xxx.saz")
        str_all_res = "{str_info}\r\n{headers}\r\n\r\n{body}".format(str_info=str_headers_res, headers=str_headers_res,  body=decode_data)
        file_name = "%s_s.txt" % self.number_block
        data = str_all_res
        zipdir(ziph_name, file_name, data, path_create_zip="TEMP_ZIP_FILES", del_file=False)

    def call(self, method, _site='', time_delta=60, code=200, bus_logic=True, error=False, protocol=3,
             log_out=True, encoding="utf-8", full_response=False, **params):
        """Удалённый вызов метода БЛ

        :param method: название метода БЛ, который вызываем
        :param _site: преффикс сервиса /admin, /auth и тд. Если одновная БЛ, то оставить пустым.
        :param params: параметры json из секции params
        :param bus_logic: прибавлять(или нет) к адресу значение BL_PREFIX из конфига по умолчанию ?srv=1

        """
        if bus_logic:
            _site = _site + self.address + self.bl_prefix
        else:
            _site = _site + self.address
        body_req = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1}
        if protocol:
            body_req["protocol"] = protocol
        body = json.dumps(body_req)
        text_request = str(json.dumps(body_req, ensure_ascii=False))
        time_delta_ = timedelta(seconds=time_delta)
        self.time_start_req = (datetime.now()-time_delta_).strftime('%Y-%m-%d %H:%M:%S.%f')
        note = params.get('params', {}).get('Документ', {}).get('Примечание')
        # запрашиваем
        started = datetime.now()  # замер времени
        if self.config.get("FIDDLER_DEBUG") == True:
            connection = self.connection("127.0.0.1", self.config.get("FIDDLER_PORT"))  # Via fiddler-proxy
            connection.request("POST", self.url + _site, body, self.header)
        else:
            connection = self.connection(self.hostname)
            connection.request("POST", _site, body, self.header)
        response = connection.getresponse()
        passed = (datetime.now() - started).total_seconds()
        data = response.read()
        connection.close()
        decode_data = data.decode(encoding=encoding)

        # generate_saz(self, connection, response, _site, body):
        # self.generate_saz(connection, response, _site, body, decode_data)

        # path = self.url + _site
        # str_info_request = "{method} {path} {protocol}".format(method=connection._method, path=path, protocol=connection._http_vsn_str)
        # temp_header = {"Host": self.hostname}
        # temp_header.update(self.header)
        # str_headers_request = "\r\n".join(["{key}: {value}".format(key=key, value=value) for key, value in temp_header.items()])
        # str_all_request = "{str_info}\r\n{headers}\r\n\r\n{body}".format(str_info=str_info_request, headers=str_headers_request, body=body)
        # ziph_name = "xxx.saz" #  "xxx.zip"
        # file_name = "%s_c.txt" % self.number_block
        # data = str_all_request
        # zipdir(ziph_name, file_name, data, path_create_zip="TEMP_ZIP_FILES", del_file=False)
        #
        # str_info_res = "{protocol} {code} {reason}".format(protocol=connection._http_vsn_str, code=response.getcode(), reason=response.reason)
        # str_headers_res = "\r\n".join(["{key}: {value}".format(key=key, value=value) for key, value in response.getheaders()])
        # # работает copyfile(os.path.join(os.getcwd(), r"TEMP_ZIP_FILES\\%s" % ziph_name), r"TEMP_ZIP_FILES\\new_xxx.saz")
        # str_all_res = "{str_info}\r\n{headers}\r\n\r\n{body}".format(str_info=str_info_res, headers=str_headers_res,  body=decode_data)
        # file_name = "%s_s.txt" % self.number_block
        # data = str_all_res
        # zipdir(ziph_name, file_name, data, path_create_zip="TEMP_ZIP_FILES", del_file=False)




        try:
            answer = json.loads(decode_data)
        except ValueError as e:
            msg = "Произошла ошибка\n" \
                  "%s\n" \
                  "Пытались преобразовать - '%s' в json\n" \
                  "Запрос:\n%s\n" % (e.args[0], decode_data, text_request)
            raise Exception(msg)
        # проверяем
        self.method_req = method
        self.x_uniq_id = response.getheader('X-Uniq-ID')
        x_sbis_session_id = self.header.get('X-SBISSessionID', 'АВТОРИЗУЕМСЯ')
        if self.x_uniq_id:
            msg_x_unig_id = self.x_uniq_id
        else:
            msg_x_unig_id = "не обнаружен заголовок X-Uniq-ID"


        link_cloud = self.get_link(self.hostname, note=note)
        message_data = [x_sbis_session_id, msg_x_unig_id, link_cloud, text_request, decode_data]
        success = True
        message_type="success"


        if error and response.status == code:
            if log_out:
                log(self.output_message(block=self.number_block,
                                        status_code=response.status,
                                        message_type="success",
                                        message_params=message_data))
            return answer
        if response.status != code:
            message_type="bad_status"
            success = False
        if 'error' in answer:
            message_type="error"
            success = False
        if 'result' not in answer:
            message_type="bad_result"
            success = False
        link_cloud = self.get_link(self.hostname, note=note, success=success)
        message_data = [x_sbis_session_id, msg_x_unig_id, link_cloud, text_request, decode_data]
        msg = self.output_message(block=self.number_block, status_code=response.status, message_type=message_type,
                                message_params=message_data)
        self.number_block += 1
        # сохраняем замер времени
        if method not in self.timepass:
            self.timepass[method] = [passed]
        else:
            self.timepass[method].append(passed)

        if success:
            if log_out: log(msg)
        else:
            raise Exception(msg)

        result = answer
        if not full_response:
            result = answer['result']
        return result

    def post(self, _site, body, headers=None):
        """
        :param _site: полностью указываем сервис, например. 1C/service/sbis-rpc-service300.dll/SendMessage
        :param body: тело запроса
        :return: Ответ на POST-запрос """

        connection = self.connection(self.hostname)
        if headers:
            connection.request('POST', _site, body, headers)
        else:
            connection.request('POST', _site, body, self.header)
        response = connection.getresponse()
        data = response.read()
        code = response.code
        connection.close()
        return data, code


    def get_filtet(self, note, success=False):
        """Взависимости от наличия или отсутствия ключа 'Примечание' быдет возвращатся разный фильтр

        :param success: корректно ли завершился
        """
        filter = {
            'Метод': self.method_req,
            'Сессия': self.session,
            'До_Время': self.time_end,
            'От_Время': self.time_start_req,
            'ЧислоЗаписей': 10,
            'Отображение': 0 if success else 4,
            'Пул': -1
        }
        if note:
            filter["СообщФильтр"] = note
        if self.x_uniq_id:
            filter["UUID"] = self.x_uniq_id
        return b64encode(json.dumps(filter, ensure_ascii=False).encode()).decode()

    def get_link(self, site, note, time_delta=60, success=False):
        """Генерируем ссылку в админку если таковая имеется

        :param success: корректно ли завершился
        """
        list_admin = {'dev-inside.tensor.ru': 'https://dev-cloud.sbis.ru',
              'dev-online.sbis.ru': 'https://dev-cloud.sbis.ru',
              'dev-reg.tensor.ru': 'https://dev-reg-cloud.tensor.ru',
              'test-inside.tensor.ru': 'https://test-cloud.sbis.ru',
              'xp-test-online.sbis.ru': 'https://test-cloud.sbis.ru',
              'test-online.sbis.ru': 'https://test-cloud.sbis.ru',
              'test-reg.tensor.ru': 'https://test-reg-cloud.tensor.ru',
              'fix-online.sbis.ru': 'https://fix-cloud.sbis.ru',
              'xp-fix-online.sbis.ru': 'https://fix-cloud.sbis.ru',
              'fix-inside.tensor.ru': 'https://fix-cloud.sbis.ru',
              'fix-reg.tensor.ru': 'https://fix-reg-cloud.tensor.ru',
              'rc-reg.tensor.ru': 'https://rc-reg-cloud.tensor.ru',
              'inside.tensor.ru': 'https://cloud.sbis.ru',
              'xp-online.sbis.ru': 'https://cloud.sbis.ru',
              'online.sbis.ru': 'https://cloud.sbis.ru',
              'reg.tensor.ru': 'https://reg-cloud.tensor.ru',
              'rc-inside.tensor.ru': 'https://rc-cloud.sbis.ru',
              'pre-test-inside.tensor.ru': 'https://pre-test-cloud.sbis.ru',
              'pre-test-online.sbis.ru': 'https://pre-test-cloud.sbis.ru'}

        time_delta_ = timedelta(seconds=time_delta)
        if list_admin.get(site):
            site_admin = list_admin[site]
        else:
            site_admin = site.split("-")[0]
        self.session = self.header.get('X-SBISSessionID')
        self.time_end = (datetime.now() + time_delta_).strftime('%Y-%m-%d %H:%M:%S.%f')
        base_64_filter = self.get_filtet(note, success)
        link_cloud = "{link_cloud}/cloud.html#msid=s1445433684749&ws-nc=cloudAccord=CloudWorkAnalysis;" \
                     "AnalyzeMenuBro=501;AdditionalCloudTemplate=null&filter={base_64_filter}"\
                     .format(link_cloud=site_admin, base_64_filter=base_64_filter)
        return link_cloud


    def send_json(self, test_json, bus_logic=True, _site='', time_delta=60, code=200):
        """Метод посылает json и возвращает ответ проверяя код ответа и ошибки в ответе

        :param test_json: request
        :param _site: преффикс сервиса /admin, /auth и тд. Если основная БЛ, то оставить пустым.
        :param code: эталонный код ответа на запрос
        :param bus_logic: прибавлять(или нет) к адресу значение BL_PREFIX из конфига по умолчанию ?srv=1

        """
        if bus_logic:
            _site = _site + self.address + self.bl_prefix
        else:
            _site = _site + self.address
        time_delta_ = timedelta(seconds=time_delta)
        self.time_start_req = (datetime.now()-time_delta_).strftime('%Y-%m-%d %H:%M:%S.%f')
        json_loads = json.loads(test_json)
        self.method_req = json_loads['method']
        note = None  # Примечание, если есть в запросе
        body = json.dumps(json_loads)
        if self.config.get("FIDDLER_DEBUG") == "True":
            connection = self.connection("127.0.0.1", self.config.get("FIDDLER_PORT"))  # Via fiddler-proxy
            connection.request("POST", self.url + _site, body, self.header)
        else:
            connection = self.connection(self.hostname)
            connection.request("POST", _site, body, self.header)
        response = connection.getresponse()
        data = response.read()
        connection.close()
        x_sbis_session_id = self.header.get('X-SBISSessionID', 'АВТОРИЗУЕМСЯ')
        self.x_uniq_id = response.getheader('X-Uniq-ID')
        if self.x_uniq_id:
            msg_x_unig_id = self.x_uniq_id
        else:
            msg_x_unig_id = "не обнаружен заголовок X-Uniq-ID"
        if len(test_json) / 1024 > 700:
            test_json = "Слишком болшой запрос"
        decode_data = data.decode()
        if len(decode_data) / 1024 > 700:
            decode_data = "Слишком болшой ответ"
        if response.status != code:
            log("Возникла ошибка ")
            link_cloud = self.get_link(self.hostname, note)
            message_data = [x_sbis_session_id, msg_x_unig_id, link_cloud, test_json, decode_data]
            if self.config.get('VERBOSE') in ('Always', 'Error'):
                raise Exception(self.output_message(block=self.number_block,
                                                    status_code=response.status,
                                                    message_type="bad_status",
                                                    message_params=message_data))
            else:
                raise Exception('Не верный код ответа: %s != %s\n' % (response.status, code))
        elif self.config.get('VERBOSE') == 'Always':
            link_cloud = self.get_link(self.hostname, note, success=True)
            message_data = [x_sbis_session_id, msg_x_unig_id, link_cloud, test_json, decode_data]
            log(self.output_message(block=self.number_block,
                                    status_code=response.status,
                                    message_type="success",
                                    message_params=message_data))
        self.number_block += 1
        answer = decode_data
        try:
            answer = json.loads(decode_data)
        except:
            pass
        return answer

    def get(self, url, get_status_code=False, headers=None):
        """GET запрос

        :param url: адрес запроса

        """
        if headers:
            headers = headers
        else:
            headers = self.header
        connection = self.connection(self.hostname)
        connection.request('GET', url, headers=headers)
        response = connection.getresponse()
        data = response.read()
        if get_status_code:
            return data, response.code
        else:
            return data


    def put(self, data, file_name, bin=False, status=201, get_response=False, path="/cstorage/elo"):
        """"""
        connection = self.connection(self.hostname)
        url = self.config.SITE + path
        file_name = quote(u'%s' % file_name)  # чтобы не ругался на русские названия
        headers = {
           'Content-Disposition': "attachment;filename*=UTF-8''" + file_name,
           'X-Delete-After': '259200',
           'X-SBISSessionID': self.header['X-SBISSessionID'],
           'user-agent': 'SbisAutotest/1.0.0 ({0})'.format(socket.gethostname())
        }
        if not bin:
            data = data.encode("cp1251")
        try:
            connection.request('PUT', url, data, headers=headers)
        except:
            raise Exception("Возникла ошибка при отправке данных:\n headers:"
                            " \n{headers}\n data: \n{data}".format(headers=headers, data=data))
        response = connection.getresponse()
        code_status = response.status
        if code_status != status:
            raise Exception("\n Отправляли файл %s"
                            "\nОжидали получить код %s - вернулся %s" % (file_name, status, code_status))
        storage_id = response.getheader('X-Storage-Id')
        # response.getheaders()
        # data = response.read()
        if get_response:
            return storage_id, response
        return storage_id


