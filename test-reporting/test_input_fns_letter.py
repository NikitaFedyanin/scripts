from functions import *
from atf.api import *
from data import Data


class TestInputFnsLetter(TestCase):
    """Тестируем"""

    doc_id = Config().FNS_ID
    attach_id = Config().FNS_ATTACH_ID

    @classmethod
    def setup_class(cls):
        cls.new_client = JsonRpcClient(cls.config.SITE, verbose_log=2)
        cls.new_client.auth(cls.config.USER_NAME, cls.config.PASSWORD)

    def setup(self):
        self.new_client.type_response = 'record'

    def test_01_is_bundle(self):
        """Проверяем метод Комплект.ЭтоКомплект"""

        params = {"ИдДокумента": self.doc_id}

        result = self.new_client.call_rvalue("Комплект.ЭтоКомплект", **params)

        assert_that(read_file_to_assert('asserts/input_fns_letter/test_01_is_bundle.json'), equal_to_json(result.json()),
                    'Ответ на запрос Комплект.ЭтоКомплект не равен эталонному')

    @skip("https://online.sbis.ru/opendoc.html?guid=fefb4383-d272-4831-af73-632368eb9fde")
    def test_02_document_read(self):
        """Проверяем метод Документ.Прочитать"""

        params = {"ИдО": self.doc_id, "ИмяМетода": ""}
        

        result = self.new_client.call_rrecord("Документ.Прочитать", **params)

        assert_that(read_file_to_assert('asserts/input_fns_letter/test_02_document_read.json'), equal_to_json(result.json()),
                    'Ответ на запрос Документ.Прочитать не равен эталонному')

    def test_03_get_letter_text(self):
        """Проверяем метод Документ.Прочитать РассылкаЭО.ПолучитьТекстПисьма"""

        params = {"ИдО": self.doc_id}

        result = self.new_client.call_rvalue("РассылкаЭО.ПолучитьТекстПисьма", **params)

        assert_that(read_file_to_assert('asserts/input_fns_letter/test_03_get_letter_text.json'),
                    equal_to_json(result.json()),
                    'Ответ на запрос РассылкаЭО.ПолучитьТекстПисьма не равен эталонному')

    def test_04_attach_list(self):
        """Проверяем метод Документ.AttachList"""

        params = {"catalogId": self.doc_id}
        params = generate_record_list(**params)

        result = self.new_client.call_rrecordset("Документ.AttachList", **params)

        assert_that(read_file_to_assert('asserts/input_fns_letter/test_04_attach_list.json'),
                    equal_to_json(result.json()),
                    'Ответ на запрос Документ.AttachList не равен эталонному')

    @skip('Проверяется в требованиях')
    def test_05_read_attachment(self):
        #TODO когда перейдут на ВнешнийДокумент.ReadAttachment(3.18.510) написать новость и перевести последний тест
        """Проверяем метод Документ.ReadAttachment"""

        params = {"ИдО": str(self.attach_id)}

        result = self.new_client.call_rvalue("Документ.ReadAttachment", **params).result

        assert_that(result['ИмяФайла'], equal_to(Data._RA_FILE_NAME),
                    'Ответ на запрос Документ.ReadAttachment не равен эталонному')

if __name__ == "__main__":
    run_tests()
