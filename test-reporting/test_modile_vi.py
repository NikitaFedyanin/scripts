# -*- coding: utf-8 -*-
from methods_for_api_tests.functions import *
from methods_for_api_tests.rpc import Client
from data import Data
from atf.api.recordset3 import RecordSet3
from atf.api.helpers import generate_record, generate_record_list
from atf.api import JsonRpcClient


def get_list_cert(client, filter, error=False, code=200, all=False):
    """
    Возвращаем сертификаты
    :param filter: фильтр для поиска
    :param all: если True возвращает все доступные сертификаты
    """
    if all:
        params = {"Фильтр": {}}
    else:
        params = {"Фильтр": {"Сертификат": {"Отпечаток": filter}}}
    return client.call("СБИС.СписокСертификатов", error=error, code=code, **params)


def activate_cert(client, mark, key, error=False, code=200):
    """
    Активирует сертификат по отпечатку и ключу
    через метод СБИС.АктивироватьСертификат
    :param mark: отпечаток сертификата
    :param key: код активации
    """
    params = {"Сертификат": {"Отпечаток": mark, "КодАктивации": key}}
    return client.call("СБИС.АктивироватьСертификат", error=error, code=code, **params)

def activate_cert_edo(client, mark, key, error=False, code=200):
    """
    Активирует сертификат по отпечатку и ключу
    через метод ЭДО.АктивироватьСертификат
    :param mark: отпечаток сертификата
    :param key: код активации
    """
    params = {'Сертификат': generate_record(Отпечаток=mark,
                                            КодАктивации=key)}
    return client.call("ЭДО.АктивироватьСертификат", error=error, code=code, **params)


def get_key_activate_code_cert(client, mark, error=False, code=200):
    """
    Возвращаем код активации сертификата через метод
    СБИС.ПолучитьКодАктивацииСертификата
    :param mark: отпечаток сертификата
    """
    params = {"Сертификат": {"Отпечаток": mark}}
    return client.call("СБИС.ПолучитьКодАктивацииСертификата", error=error, code=code, **params)


def get_key_activate_code_cert_edo(client, mark, error=False, code=200):
    """
    Возвращаем код активации сертификата через метод
    ЭДО.ПолучитьКодАктивацииСертификата
    :param mark: отпечаток сертификата
    """
    return client.call("ЭДО.ПолучитьКодАктивацииСертификата", error=error, code=code, Отпечаток=mark)


def get_last_sms_by_number(client, time, tel_number):
    """Получить смс
    :param client: авторизованный с правами на просмотр СМС пользователь админки
    :param tel_number: Номер телефона
    :param code_only: True возвращает только код из сообщения, False все сообщение
    :param just_result: Сразу вернуть результат запроса без обработки"""

    time = time.strftime('%Y-%m-%d %H:%M:%S+03')
    client.headers['REFERER'] = 'cloud.sbis.ru'

    navigation_params = {"d": [True, 30, "both", None], "s": [{"t": "Логическое", "n": "HaveMore"},
                                                              {"t": "Число целое", "n": "Limit"},
                                                              {"t": "Строка", "n": "Order"},
                                                              {"t": "Строка", "n": "Position"}],
                         "_type": "record"}

    params = generate_record_list(navigation=navigation_params,
                                  **{"PhoneNumber": (str(tel_number), "Строка"),
                                     "Created": ([time, None], {"n": "Массив", "t": "Дата и время"})})

    result = lambda: client.call_rrecordset(method="Message.ListCursor", path='/smsc', **params).result

    assert_that(result, not_equal([]),
                "Сообщения по номеру %s в сервисе смс не найдено" % tel_number, and_wait(30, 2))

    for i in result():
        text = i['TextSms']
        if text.startswith("Подтвердите использование ЭП для СБИС. Одноразовый код"):
            pin = text.split(' ')[-1]
            break
    else:
        msg = "Не удалось получить код подтверждения"
        raise Exception(msg)
    return pin


class TestModileVI(TestCase):
    """Тестирование методов ЭДО"""

    config = Config()
    user = config.USER_NAME_VI
    password = config.PASSWORD_VI
    comment = 'Автотестирование мобильного API'
    Data._COMMENT = comment
    Data._CONTRACTOR = json.dumps({"СвЮЛ": {"ИНН": Data._RECEIVER_UL_INN, "КПП": Data._RECEIVER_UL_KPP}},
                                  ensure_ascii=False)
    Data._OUR_ORG = json.dumps({"СвЮЛ": {"ИНН": Data._SENDER_UL_INN, "КПП": Data._SENDER_UL_KPP}},
                               ensure_ascii=False)
    Data._MainAuthorSender = json.dumps(Data._MainAuthorSender, ensure_ascii=False)

    path_dir = r"test-files\МобильноеАПИ\ЗапускВДокуменооборот"
    Data._TYPE_DOC = "ДокОтгрИсх"

    @classmethod
    def setup_class(cls):
        cls.start_time_case = datetime.now()
        cls.site = cls.config.SITE
        cls.client = Client(url=cls.site)

    def setup(self):
        self.client.auth(self.user, self.password)

    @classmethod
    def teardown_class(cls):
        post_delete_docs_by_comment(cls.client, cls.comment, cls.start_time_case,
                                    user=cls.config.USER_NAME_VI, password=cls.config.PASSWORD_VI, _out=True)
        post_delete_docs_by_comment(cls.client, cls.comment, cls.start_time_case,
                                    user=cls.config.USER_NAME_RECIEVER_VI, password=cls.config.PASSWORD_VI, _in=True)

    def test_01_send_doc(self):
        """Вызываем
        СБИС.ЗаписатьДокумент
        СБИС.ПодготовитьДействие
        СБИС.ВыполнитьДействие
        СБИС.ПрочитатьДокумент
        """
        path_dir = r"test-files\МобильноеАПИ\ЗапускВДокуменооборот"
        Data._ATTACH_ID = generate_guid()
        Data._ID_SUITE = generate_guid()
        log("Создаем черновик - СБИС.ЗаписатьДокумент")
        path_req = os.path.join(path_dir, "01.request.json")
        path_res = os.path.join(path_dir, "01.response.json")
        send_json_and_assert(self.client, path_req, path_res)

        log("СБИС.ПодготовитьДействие")
        path_res_2 = os.path.join(path_dir, "02.response.json")
        temp_json = json.loads(read_file(path_res_2))
        cert = json.loads(Data._SENDER_FULL_CERT)
        params = {"Документ": {"Идентификатор": Data._ID_SUITE,
                               "Этап": {"Действие": {"Название": "Отправить", "Сертификат": cert},
                                        "Название": "Отправка"}}}
        res = self.client.call("СБИС.ПодготовитьДействие", **params)
        # y = modification_responce(res)
        assert_that(temp_json, is_in_json(res), "Ответ метода СБИС.ПодготовитьДействие отличается от ожиданий")

        log("СБИС.ВыполнитьДействие")
        res = self.client.call("СБИС.ВыполнитьДействие", **params)
        path_res_3 = os.path.join(path_dir, "03.response.json")
        temp_json = json.loads(read_file(path_res_3))
        assert_that(temp_json, is_in_json(res), "Ответ метода СБИС.ВыполнитьДействие отличается от ожиданий")

        log("СБИС.ПрочитатьДокумент")
        res = self.client.call("СБИС.ПрочитатьДокумент", **{"Документ": {"Идентификатор":   Data._ID_SUITE}})
        path_res_4 = os.path.join(path_dir, "04.response.json")
        temp_json = json.loads(read_file(path_res_4))
        assert_that(temp_json, is_in_json(res), "Ответ метода СБИС.ПрочитатьДокумент отличается от ожиданий")

    def test_02_list_cert(self):
        """СБИС.СписокСертификатов"""
        path_dir = r"test-files\МобильноеАПИ\ТестированиеСертификатов"
        params = {"Фильтр": {"Сертификат": {"Отпечаток": Data._SENDER_SERVER_CERT}}}
        res = self.client.call("СБИС.СписокСертификатов", **params)
        path_res = os.path.join(path_dir, "01.response.json")
        temp_json = json.loads(read_file(path_res))
        assert_that(temp_json, is_in_json(res), "Ответ метода СБИС.СписокСертификатов отличается от ожиданий")

    def test_03_activate_cert(self):
        """Тестируем метод СБИС.АктивироватьСертификат
        СБИС.АктивироватьСертификат для сертификат с смс-паролем, передав ВЕРНЫЙ пароль
        """
        delay(20, 'смс с одного номера нельзя отправлять чаще, чем раз в 10 секунд')
        log("\nОПИСАНИЕ ТЕСТА\n"
            "Вызвать СБИС.АктивироватьСертификат для сертификат с смс-паролем, передав ВЕРНЫЙ пароль"
            "1.	Вызвать СБИС.СписокСертификатов "
            "2.	Вызвать СБИС.ПолучитьКодАктивации для существующего серверного сертификат с смс-паролем "
            "3.	Полученный в п.1 пароль передать в СБИС.АктивироватьСертификат "
            "4.	Вызывать повторно СБИС.СписокСертификатов")
        mark = Data._NOT_ACTIVATE_SERVER_CERT["Отпечаток"]

        user = self.config.USER_SMS_ACTIVATE_CERT
        password = self.config.PASSWORD_SMS_ACTIVATE_CERT
        log("Логинемся под пользователем имеющим сетрификат для активации %s %s" % (user, password))
        self.client.auth(user, password)

        log("Вызываем СБИС.СписокСертификатов - сетрификат должен быть НЕ АКТИВИРОВАН")
        cert_active = get_list_cert(self.client, mark)["Сертификат"][0]["Ключ"]["Активирован"]
        assert_that(cert_active, equal_to("Нет"), "Сетрификат с отпечатком %s актифирован" % mark)

        log("Получаем код активации")
        self.start = datetime.now()
        delay(1)
        get_key_activate_code_cert(self.client, mark=mark)
        log("Авторизуемся под пользователем с админскими правами в админке")
        user_cloud = self.config.USER_CLOUD_SMSC
        pass_cloud = self.config.PASSWORD_CLOUD_SMSC
        log("Перелогиневаемся под {user}/{pas}".format(user=user_cloud, pas=pass_cloud))
        new_client = JsonRpcClient(url=self.config.SITE_CLOUD, verbose_log=2)
        new_client.auth(user_cloud, pass_cloud)
        delay(5, 'Ждем смс')
        pin = get_last_sms_by_number(new_client, self.start, '+79201274105')

        log("Активируем сертификат используя полученный код активации")
        client = Client(url=self.site)
        client.auth(user, password)
        activate_cert(self.client, mark, pin)
        cert_active = get_list_cert(self.client, mark)["Сертификат"][0]["Ключ"]["Активирован"]
        assert_that(cert_active, equal_to("Да"), "Сетрификат с отпечатком %s актифирован" % mark)
        delay(20, 'смс с одного номера нельзя отправлять чаще, чем раз в 10 секунд')

    def test_04_get_code_activate_cert(self):
        """Тестируем метод СБИС.ПолучитьКодАктивацииСертификата Вызвать метод для серверного сертификата без смс-пароля
        """
        delay(20, 'смс с одного номера нельзя отправлять чаще, чем раз в 10 секунд')
        log("\nОПИСАНИЕ ТЕСТА\n"
            "Тест 4 Вызывать метод для серверного сертификата с смс - паролем")
        user = self.config.USER_SMS_ACTIVATE_CERT
        password = self.config.PASSWORD_SMS_ACTIVATE_CERT
        log("Логинемся под пользователем имеющим сетрификат для активации %s %s" % (user, password))
        self.client.auth(user, password)
        log("Ожидаем что метод завершится без ошибок - 200 ответ")
        get_key_activate_code_cert(self.client, Data._NOT_ACTIVATE_SERVER_CERT["Отпечаток"])
        delay(20, 'смс с одного номера нельзя отправлять чаще, чем раз в 10 секунд')

    def test_05_activate_cert_edo(self):
        """Тестируем метод ЭДО.АктивироватьСертификат и ЭДО.ПолучитьКодАктивацииСертификата
        ЭДО.АктивироватьСертификат для сертификат с смс-паролем, передав ВЕРНЫЙ пароль
        Тест полностью аналогичен тесту № 3, только ипользует методы ЭДО
        """
        delay(20, 'смс с одного номера нельзя отправлять чаще, чем раз в 10 секунд')
        log("\nОПИСАНИЕ ТЕСТА\n"
            "Вызвать СБИС.АктивироватьСертификат для сертификат с смс-паролем, передав ВЕРНЫЙ пароль"
            "1.	Вызвать СБИС.СписокСертификатов "
            "2.	Вызвать СБИС.ПолучитьКодАктивации для существующего серверного сертификат с смс-паролем "
            "3.	Полученный в п.1 пароль передать в СБИС.АктивироватьСертификат "
            "4.	Вызывать повторно СБИС.СписокСертификатов")
        mark = Data._NOT_ACTIVATE_SERVER_CERT["Отпечаток"]

        user = self.config.USER_SMS_ACTIVATE_CERT
        password = self.config.PASSWORD_SMS_ACTIVATE_CERT
        log("Логинемся под пользователем имеющим сетрификат для активации %s %s" % (user, password))
        self.client.auth(user, password)

        log("Вызываем СБИС.СписокСертификатов - сетрификат должен быть НЕ АКТИВИРОВАН")
        cert_active = get_list_cert(self.client, mark)["Сертификат"][0]["Ключ"]["Активирован"]
        assert_that(cert_active, equal_to("Нет"), "Сетрификат с отпечатком %s актифирован" % mark)

        log("Получаем код активации")
        self.start = datetime.now()
        delay(1)
        get_key_activate_code_cert_edo(self.client, mark=mark)
        log("Авторизуемся под пользователем с админскими правами в админке")
        user_cloud = self.config.USER_CLOUD_SMSC
        pass_cloud = self.config.PASSWORD_CLOUD_SMSC
        log("Перелогиневаемся под {user}/{pas}".format(user=user_cloud, pas=pass_cloud))
        new_client = JsonRpcClient(url=self.config.SITE_CLOUD)
        new_client.auth(user_cloud, pass_cloud)
        delay(3, 'Ждем смс')
        pin = get_last_sms_by_number(new_client, self.start, '+79201274105',)

        log("Активируем сертификат используя полученный код активации")
        client = Client(url=self.site)
        client.auth(user, password)
        activate_cert_edo(self.client, mark, pin)
        cert_active = get_list_cert(self.client, mark)["Сертификат"][0]["Ключ"]["Активирован"]
        assert_that(cert_active, equal_to("Да"), "Сетрификат с отпечатком %s актифирован" % mark)
        delay(20, 'смс с одного номера нельзя отправлять чаще, чем раз в 10 секунд')


if __name__ == "__main__":
    run_tests()