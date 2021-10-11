# -*- coding: utf-8 -*-
from methods_for_api_tests.functions import *
from data import Data
import base64
import shutil
import time
import os


class LocalSignature:

        def __init__(self, name_test, client, time=30, cert="ТестовыйЮЛПервый Тест Тестович"):
            self.name_test = name_test
            self.client = client
            self.cert = cert
            self.time = time
            self.number = 1

        def create_file(self, name, link, path):
            """по ссылке взятой из ответа метода подготовить действие, берется ссылка на документ
             - документ выкачивается"""
            path_to_file = os.path.join(path, name)
            data_file = self.client.get(link)
            with open(path_to_file, 'bw') as f:
                f.write(data_file)
                # todo добавить дополнительное логирование
                return path_to_file

        @staticmethod
        def get_data_file_base64(path):
            """возвращает содержимое файла в формате base_64"""
            f = open(path, mode='br')
            data_file = f.read()
            return str(base64.encodestring(data_file)).replace(r'\n', '')[2:-1]

        @staticmethod
        def get_data_file(path):
            """возвращает содержимое файла, удаляя символы \n"""
            f = open(path)
            data_file = f.read().replace('\n', '')
            return data_file

        def create_sign(self, in_file, name):
            """создают файл отсоединенной подписи"""
            # name = "ТестовыйЮЛПервый Тест Тестович"
            log("Процесс запускается под пользователем %s" % os.getlogin())
            log("Время начала генерации подписи - %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S+03'))
            out_file = in_file + '.p7s'
            csp_path = r'C:\Program Files (x86)\Crypto Pro\CSP\csptest.exe'
            process = subprocess.Popen([
                csp_path, '-sfsign', '-sign', '-detached', '-add', '-alg', 'GOST', '-addsigtime', '-base64',
                '-in', in_file,
                '-out', out_file,
                '-my', name
            ])  # , stderr=subprocess.PIPE, stdout=subprocess.PIPE
            process.communicate(timeout=self.time)  # wait(self.time)
            # for x in range(3):
            #     if process.poll() == None:
            #         log("Попытка номер - %s" % x)
            #         time.sleep(5)
            #     else:
            #         break
            log("Время окончания генерации подписи - %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S+03'))
            log("КОД ВОЗВРАТА ПРОЦЕССА СОЗДАНИЯ ПОДПИСИ : %s" % process.returncode)
            # if process.stderr.read().decode():
            #     log("ОШИБКА - %s " % process.stderr.read().decode())
            return out_file

        def generate_name_key(self, obj, end_name):
            """по имени файла создает ключ который будет использован в эталоне"""
            split_name = obj['file_name'].replace(".", "_").replace("-", "_").split("_")
            # имя формируется следующим образом: берутся первые два элемента списка + номер
            # + последний элемент списка(расширение файла) + окончание(p7s или file_base_64
            # в зависимости от того какое имя создается для данных подписи или для данных пропатченного файла )
            name_key = "_%s_%s_%s_%s_%s" % (split_name[0], split_name[1], self.number, split_name[-1], end_name)
            self.number += 1
            return name_key

        def create_p7s(self, path, obj):

            name_key_data_p7s = self.generate_name_key(obj, "p7s")
            name_key_data_file_base_64 = self.generate_name_key(obj, "file_base_64")
            doc_name = obj['doc_name']
            log("\n================ Служебная информация =================\n"
                "       Необходимо в запросе 'СБИС.ВыполнитьДействие' во вложении 'Название' - %s, :\n"
                "       в 'Подпись.Файл.ДвоичныеДанные' добавить параметр:\n"
                "       '$%s'\n"
                "       а также в 'Файл.ДвоичныеДанные' добавить параметр(в это место будет подставлено содержимое файла -\n"
                "       (выкаченного по ссылке, взятой из ответа СБИС.ПодготовитьДействие - пропатчинного сервером) в формате base_64):\n"
                "       '$%s'\n"
                "========================================================\n" % (doc_name, name_key_data_p7s, name_key_data_file_base_64))
            path_p7s = self.create_sign(path, self.cert)
            data_p7s = self.get_data_file(path_p7s)
            # создаем атрибут имя которого(для конкретного вложения) будет использоваться в запросе метода
            # СБИС.ВыполнитьДействие ('Подпись.Файл.ДвоичныеДанные' - по этому адресу его нужно подставлять),
            # его значение это - данные(отсоединенная подпись)
            # в формате base_64 сгенерированные
            # по файлу выкаченному по ссылке, взятой из ответа СБИС.ПодготовитьДействие
            setattr(Data, name_key_data_p7s, data_p7s)
            # создаем атрибут имя которого(для конкретного вложения) будет использоваться в запросе метода
            # СБИС.ВыполнитьДействие ('Файл.ДвоичныеДанные' - по этому адресу его нужно подставлять),
            # его значение это - содержимое файла в формате base_64 взятое из выкаченного файла
            data_file = self.get_data_file_base64(path)
            setattr(Data, name_key_data_file_base_64, data_file)
            log("В класс Data был добавлен атрибут:  %s " % name_key_data_p7s)
            log("В класс Data был добавлен атрибут:  %s " % name_key_data_file_base_64)

        def create_folder(self):
            """создает отдельный каталог под тест - в этот каталог пападают файлы вложений
             и файлы отсоединенных подписей"""
            path_to_dir = os.path.realpath('KEYS')
            if not os.path.isdir(path_to_dir):
                os.mkdir(path_to_dir)
            folder_to_test_files = os.path.join(path_to_dir, self.name_test)
            if not os.path.isdir(folder_to_test_files):
                os.mkdir(folder_to_test_files)
                path_to_dir = folder_to_test_files
            return path_to_dir

        @staticmethod
        def delete_folder(path):
            """удалем каталог и все содержимое каталога"""
            shutil.rmtree(path, ignore_errors=True)

        def generate_files(self, obj, del_folder=True):
            path_to_dir = self.create_folder()
            try:
                for key, value in obj.items():
                    print("Номер этапа %s " % key)
                    for key_i, value_i in value.items():
                        print("Название этапа - %s " % key_i)
                        count_doc = len(value_i)
                        for j in range(count_doc):
                            info_doc = value_i[j]
                            file_path = self.create_file(info_doc["file_name"], info_doc["file_link"], path_to_dir)
                            if file_path:
                                log("Генерируем файл подписи для файла %s " % file_path)
                                self.create_p7s(file_path, obj=info_doc)
            finally:
                if del_folder:
                    self.delete_folder(path_to_dir)

        @staticmethod
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