from functions import *
from atf.api import *


class TestHardBaundle(TestCase):
    """Тестируем комплект"""

    doc_id = Config().NDFL_ID
    doc_second_id = Config().NDFL_SECOND_ID
    face_1 = Config().FACE_1
    type_doc = Config().TYPE_DOC
    second_type_doc = Config().SECOND_TYPE_DOC
    doc_our_org = Config().DOC_OUR_ORG
    report_period = Config().REPORT_PERIOD
    bundle_attach_id = Config().BUNDLE_ATTACH_ID

    @classmethod
    def setup_class(cls):
        cls.new_client = JsonRpcClient(cls.config.SITE, verbose_log=2)
        cls.new_client.auth(cls.config.USER_NAME, cls.config.PASSWORD)

    def setup(self):
        self.new_client.type_response = 'value'

    def test_01_is_bundle(self):
        """Проверяем метод Комплект.ЭтоКомплект"""

        params = {"ИдДокумента": self.doc_id}

        result = self.new_client.call_rvalue("Комплект.ЭтоКомплект", **params)

        assert_that(read_file_to_assert('asserts/hard_bundle/test_01_is_bundle.json'), equal_to_json(result.json()),
                    'Ответ на запрос Комплект.ЭтоКомплект не равен эталонному')

    @skip("https://online.sbis.ru/opendoc.html?guid=fefb4383-d272-4831-af73-632368eb9fde")
    def test_02_bundle_read(self):
        """Проверяем метод Комплект.Прочитать"""

        params = {"ИдО": self.doc_id, "ИмяМетода": 'Список'}

        result = self.new_client.call_rrecord("Комплект.Прочитать", **params)

        assert_that(read_file_to_assert('asserts/hard_bundle/test_02_bundle_read.json'), equal_to_json(result.json()),
                    'Ответ на запрос Комплект.ЭтоКомплект не равен эталонному')

    @skip("https://online.sbis.ru/opendoc.html?guid=fefb4383-d272-4831-af73-632368eb9fde")
    def test_03_list_attachment_documents(self):
        """Проверяем метод Документ.Прочитать для сложных комплектов для сложных комплектов"""

        params = {"ИдО": self.doc_second_id, "ИмяМетода": 'Список'}

        result = self.new_client.call_rrecord("Документ.Прочитать", **params)

        assert_that(read_file_to_assert('asserts/hard_bundle/test_03_list_attachment_documents.json'),
                    equal_to_json(result.json()),
                    'Ответ на запрос Документ.Прочитать не равен эталонному')

    @skip("не вызвался на бою два месяца до 07.02.2019")
    def test_04_read_inspection(self):
        """Проверяем метод ГосударственнаяИнспекция.Прочитать"""

        params = {"ИдО": self.face_1, "ИмяМетода": ''}

        result = self.new_client.call_rrecord("ГосударственнаяИнспекция.Прочитать", **params)

        assert_that(read_file_to_assert('asserts/hard_bundle/test_04_read_inspection.json'),
                    equal_to_json(result.json()),
                    'Ответ на запрос ГосударственнаяИнспекция.Прочитать не равен эталонному')

    def test_05_get_document_type(self):
        """Проверяем метод ТипФормализованногоДокумента.Получить"""

        params = {"ТипДокумента": {"s": [{"t": "Строка", "n": "ТипДокумента"}, {"t": "Строка", "n": "ПодТипДокумента"}],
                  "d": [str(self.type_doc), str(self.second_type_doc)]}}

        result = self.new_client.call_rrecord("ТипФормализованногоДокумента.Получить", **params)

        assert_that(read_file_to_assert('asserts/hard_bundle/test_05_get_document_type.json'),
                    equal_to_json(result.json()),
                    'Ответ на запрос ТипФормализованногоДокумента.Получить не равен эталонному')

    @skip("не вызвался на бою два месяца до 07.02.2019")
    def test_06_read_our_ogr(self):
        """Проверяем метод НашаОрганизация.Прочитать"""

        params = {"ИдО": self.doc_our_org, "ИмяМетода": ''}

        result = self.new_client.call_rrecord("НашаОрганизация.Прочитать", **params)

        assert_that(read_file_to_assert('asserts/hard_bundle/test_06_read_our_ogr.json'),
                    equal_to_json(result.json()),
                    'Ответ на запрос НашаОрганизация.Прочитать не равен эталонному')

    def test_07_read_period(self):
        """Проверяем метод ОтчетныйПериод.Прочитать"""

        params = {"ИдО": self.report_period, "ИмяМетода": 'Список'}

        result = self.new_client.call_rrecord("ОтчетныйПериод.Прочитать", **params)

        assert_that(read_file_to_assert('asserts/hard_bundle/test_07_read_period.json'),
                    equal_to_json(result.json()),
                    'Ответ на запрос ОтчетныйПериод.Прочитать не равен эталонному')

    def test_08_get_minutes_left(self):
        """Проверяем метод Requirement.GetMinutesLeft"""

        params = {"req_id": self.doc_id}

        result = self.new_client.call_rrecord("Requirement.GetMinutesLeft", **params)

        assert_that(type(result.result['value']), equal_to(int), 'Вернулось не целое число')

    def test_09_get_mobile_app_data(self):
        """Проверяем метод Комплект.GetMobileAppData"""

        params = {"ИдО": self.doc_id, "ИдОтправки": self.doc_second_id}

        result = self.new_client.call_rrecord("Комплект.GetMobileAppData", **params)

        assert_that(read_file_to_assert('asserts/hard_bundle/test_09_get_mobile_app_data.json'),
                    equal_to_json(result.json()),
                    'Ответ на запрос Комплект.GetMobileAppData не равен эталонному')

    def test_12_e_rep_notice_get_mobile_app_data(self):
        """Проверяем метод ERepNotice.GetMobileAppData"""

        result = self.new_client.call_rrecord("ERepNotice.GetMobileAppData", DocPK=self.config.NDFL_ID,
                                      SendDocPK=self.config.NDFL_SECOND_ID)

        assert_that(read_file_to_assert('asserts/hard_bundle/test_12_e_rep_notice_get_mobile_app_data.json'),
                    equal_to_json(result.json()),
                    'Ответ на запрос ERepNotice.GetMobileAppData не равен эталонному')

if __name__ == "__main__":
    run_tests()