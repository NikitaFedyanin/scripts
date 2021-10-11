"""
https://online.sbis.ru/opendoc.html?guid=6df2bd92-e12a-4836-906c-2d9bb9fba277
"""
from functions import *
from atf import *
from atf.api import *


class TestPrivatePersonGetPhoto(TestCase):

    person_id = Config().get('PERSON_ID')

    @classmethod
    def setup_class(cls):
        cls.client = JsonRpcClient(url=cls.config.SITE, verbose_log=2)
        cls.client.auth(cls.config.USER_NAME, cls.config.PASSWORD)

    def test_01_private_person_get_photo(self):
        """ЧастноеЛицо.ПолучитьФото"""

        log('получает фото частного лица (файл) по ID (лицо) пользователя')
        # ID Биллинга
        response = self.client.call_rvalue("ЧастноеЛицо.ПолучитьФото", ИдО=1)
        assert_that(read_file_to_assert('asserts/private_person/ЧастноеЛицо.ПолучитьФото.json'),
                    equal_to_json(response.json()),
                    'Ответ на вызов метода ЧастноеЛицо.ПолучитьФото не равен эталонному')
        # response.should_be(BodyEqualToSample('asserts/private_person/ЧастноеЛицо.ПолучитьФото.json'),
        #                    msg='Ответ на вызов метода ЧастноеЛицо.ПолучитьФото не равен эталонному')

    def test_02_private_person_get_work(self):
        """
        ЧастноеЛицо.MainPositionOnDateMass
        Получение основной действующей должности по частному лицу, контрагенту (необязательное), на дату.
        :return:
        """

        params = generate_record(faces=([self.person_id], {"n": "Массив", "t": "Число целое"}),
                                 withDocs=False, withSchedule=False)
        result = self.client.call_rrecordset('ЧастноеЛицо.MainPositionOnDateMass', params=params)
        assert_that(read_file_to_assert('asserts/private_person/ЧастноеЛицо.MainPositionOnDateMass.json'),
                    equal_to_json(result.json()),
                    'Ответ на вызов метода ЧастноеЛицо.MainPositionOnDateMass не равен эталонному')

    def test_03_private_person_basic_information(self):
        """ЧастноеЛицо.ОсновнаяИнформация
        Получение основной информации о лицах. В параметрах может быть любой тип частного лица
        """

        response = self.client.call_rrecordset("ЧастноеЛицо.ОсновнаяИнформация", Лица=[self.person_id])
        assert_that(read_file_to_assert('asserts/private_person/ЧастноеЛицо.ОсновнаяИнформация.json'),
                    equal_to_json(response.json()),
                    'Ответ на вызов метода ЧастноеЛицо.ОсновнаяИнформация не равен эталонному')


if __name__ == "__main__":
    run_tests()