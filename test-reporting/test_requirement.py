from atf.api import JsonRpcClient
from functions import *
from atf import *
import requests


class TestRequirement(TestCase):
    """Тестируем"""

    doc_type = Data()._КП_ДОКУМЕНТ102
    doc_id = Config().REQUIREMENT_ID
    attach_id = Config().REQUIREMENT_ID_ATTACH
    our_org = Config().get('OUR_ORG')
    requirement_request = Config().get('GET_REQUIREMENT')

    @classmethod
    def setup_class(cls):
        cls.new_client = JsonRpcClient(cls.config.SITE, verbose_log=2)
        cls.new_client.auth(cls.config.USER_NAME, cls.config.PASSWORD)

    def setup(self):
        self.new_client.type_response = 'value'
        delete_requirements(self.new_client, self.our_org)

    def test_01_is_bundle(self):
        """Проверяем метод Комплект.ЭтоКомплект"""

        params = {"ИдДокумента": self.doc_id}

        result = self.new_client.call_rvalue("Комплект.ЭтоКомплект", **params)

        assert_that(read_file_to_assert('asserts/requirement/test_01_is_bundle.json'), equal_to_json(result.json()),
                    'Ответ на запрос Комплект.ЭтоКомплект не равен эталонному')

    @skip("https://online.sbis.ru/opendoc.html?guid=fefb4383-d272-4831-af73-632368eb9fde")
    def test_02_bundle_read(self):
        """Проверяем метод Комплект.Прочитать"""

        params = {"ИдО": self.doc_id, "ИмяМетода": 'Список'}

        result = self.new_client.call_rrecord("Комплект.Прочитать", **params)

        assert_that(read_file_to_assert('asserts/requirement/test_02_bundle_read.json'), equal_to_json(result.json()),
                    'Ответ на запрос Комплект.Прочитать не равен эталонному')

        assert_that(result.result['Документ_'], equal_to(self.doc_type), 'Вернулся некорректный тип документа')

    @skip("https://online.sbis.ru/opendoc.html?guid=fefb4383-d272-4831-af73-632368eb9fde")
    def test_03_list_attachment_documents(self):
        """Проверяем метод Документ.Прочитать для сложных комплектов"""

        params = {"ИдО": self.doc_id, "ИмяМетода": 'Список'}

        result = self.new_client.call_rrecord("Документ.Прочитать", **params)

        assert_that(read_file_to_assert('asserts/requirement/test_03_list_attachment_documents.json'),
                    equal_to_json(result.json()),
                    'Ответ на запрос Документ.Прочитать не равен эталонному')

        assert_that(result.result['Документ_'], equal_to(self.doc_type), 'Вернулся некорректный тип документа')

    def test_04_read_attachment(self):
        """Проверяем метод ВнешнийДокумент.ReadAttachment"""

        params = {"ИдО": str(self.attach_id)}

        result = self.new_client.call_rvalue("ВнешнийДокумент.ReadAttachment", **params).result

        assert_that(result['ИмяФайла'], equal_to(Data._3RA_FILE_NAME),
                    'Ответ на запрос ВнешнийДокумент.ReadAttachment не равен эталонному')

    def test_05_read_requirement(self):
        """Проверяем метод ИстребованиеФНС.ПрочитатьСРПДокумент
        Читает документ - требование
        """
        result = self.new_client.call_rvalue('ИстребованиеФНС.ПрочитатьСРПДокумент', ИдО=str(self.doc_id))

        assert_that(read_file_to_assert('asserts/requirement/ИстребованиеФНС.ПрочитатьСРПДокументt.json'),
                    equal_to_json_rpc(result.json()),
                    'ИстребованиеФНС.ПрочитатьСРПДокумент')

    def test_06_requirement_stop(self):
        """
        Requirement.Stop - Метод помечает требование как завершенное
        Требования создаются по организации "Автотестирование Отчетности"
        1. Отправляем требование через get запрос
        2. Завершаем требование
        3. Проверяем установку флага РП.Завершен
        :return:
        """
        log('Генерируем требование')
        self.new_client.get(self.requirement_request, path_join=False)
        requirement = get_requirement(self.new_client, self.our_org)
        assert_that(requirement['РП.Завершен'], equal_to(False), 'Требование не завершилось')

        log('Завершение требования')
        self.new_client.call_rvalue('Requirement.Stop', ИдДокумента=requirement['@Документ'])

        log('Проверка флага РП.Завершен')
        requirement = get_requirement(self.new_client, self.our_org)
        assert_that(requirement['РП.Завершен'], equal_to(True), 'Требование не завершилось')

    def teardown(self):
        delete_requirements(self.new_client, self.our_org)


if __name__ == "__main__":
    run_tests()
