# -*- coding: utf-8 -*-
from methods_for_api_tests.functions import *
import shutil
import os
import zipfile
import difflib
import hashlib


class WorkZip:

    def __init__(self, name_test, name_zip, client, link, path_to_temp_files):
        self.name_zip = name_zip
        self.client = client
        self.link = link
        self.name_test = name_test
        self.path_to_temp_files = os.path.realpath(path_to_temp_files)

    @staticmethod
    def get_hash(path, name):
        real_path = os.path.join(path, name)
        with open(real_path, mode='rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    @staticmethod
    def diff_files(template, file_in_zip):
        result = template == file_in_zip
        diff_str = None
        if not result:
            diff = difflib.ndiff(template.splitlines(1), file_in_zip.splitlines(1))
            diff_str = "".join(diff)
        return diff_str

    @staticmethod
    def read_file(path, name, encoding='cp1251'):
        real_path = os.path.realpath(os.path.join(path, name))
        with open(real_path, encoding=encoding, mode='r') as f:
            return f.read()

    @staticmethod
    def extract_zip(paht_to_zip, extract_to_path):
        """Извлекает архив"""
        log("Время начала извлечения архива - %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S+03'))
        csp_path = r"C:\Program Files\7-Zip\7z.exe"
        process = subprocess.Popen([
            csp_path, 'x', paht_to_zip, '-r', '-y'], cwd=extract_to_path)
        # 'x', paht_to_zip, '-o./extract', '*.xml',  '-r', '-y'
        # http://www.cyberforum.ru/cmd-bat/thread702837.html - ОПИСАНИЕ КЛЮЧЕЙ
        process.communicate(30)

    @staticmethod
    def filter_files_for_zip(file_name):
        result = True
        if file_name.endswith(".p7s") or file_name.startswith("Дополнительно"):
            result = False
        return result

    def analysis_zip(self, path=None):
        paht_to_zip = os.path.realpath(path)
        assert_that(zipfile.is_zipfile(paht_to_zip), is_(True), "Файл не zip!")
        zip_file = zipfile.ZipFile(paht_to_zip, 'r')
        files_in_zip = zip_file.namelist()
        zip_file.close()
        files_in_zip_norm_name = [name.encode('CP437').decode('CP866') for name in files_in_zip]
        filter_name_files = list(filter(self.filter_files_for_zip, files_in_zip_norm_name))
        log("Анализируем содержимое каталога с этлонными файлами - проверяем наличие нужных файлов в архиве")
        # bytes(files_in_zip[0], 'CP437').decode('CP866')
        lost_files = []
        list_files_template = os.listdir(self.path_to_temp_files)
        self.extract_zip(paht_to_zip, self.path_extract_files)
        list_extract_files = os.listdir(self.path_extract_files)
        # проверяем что архив содержит столько же файлов и с теми же именами что эталонный каталог
        for name_file_i in list_files_template:
            if not name_file_i in filter_name_files:
                lost_files.append(name_file_i)
        if lost_files:
            lost = "\n".join(lost_files)
            text_error = "в архиве не найдены следующие файлы : %s " % lost
            assert_that(lost_files, equal_to(False), text_error)
        # определим разнизу между списками файлов в эталоне и архиве - на тот случай если в архиве находится
        # больше файлов
        diff = set(filter_name_files) - set(list_files_template)
        if diff:
            msg = r"В архиве обнаружены дополнительные файлы %s " % str(diff)
            raise Exception(msg)
        error_list = []  # храним сообщения об ошибках
        for name_file_i in list_files_template:
            if name_file_i.endswith(".xml"):  # not i.endswith(".p7s")
                data_zip_file = self.read_file(self.path_extract_files, name=name_file_i)
                read_temp = self.read_file(self.path_to_temp_files, name=name_file_i)
                result_diff = self.diff_files(read_temp, data_zip_file)
                if result_diff:
                    msg = "Файл %s извлеченный из аржива - не соответствует эталону\n" \
                          "Результат сравнения :\n" \
                          "%s\n" % (name_file_i, result_diff)
                    error_list.append(msg)
            else:
                # в этом блоке анализируются не .xml файлы по хэшу
                hash_temp = self.get_hash(self.path_to_temp_files, name=name_file_i)
                hash_data_zip_file = self.get_hash(self.path_extract_files, name=name_file_i)
                if not hash_temp == hash_data_zip_file:
                    msg = "Hash файлов %s эталона и одноименного файла из архива различаются"
                    error_list.append(msg)
        if error_list:
            all_error_msg = "\n==================\n".join(error_list)
            raise AssertionError("\n" + all_error_msg)

    def create_file_zip(self, name, link, path):
        """создаем физически файл"""
        path_to_file = os.path.join(path, name)
        data_file = self.client.get(link)
        with open(path_to_file, 'bw') as f:
            f.write(data_file)
            return path_to_file

    def generate_zip_files(self, del_folder=True):
        path_to_dir = self.create_folder()
        try:
            path_to_zip = self.create_file_zip(self.name_zip, self.link, path_to_dir)
            self.analysis_zip(path_to_zip)
        finally:
            if del_folder:
                self.delete_folder(path_to_dir)

    def create_folder(self):
        """создает отдельный каталог под тест - в этот каталог пападают файлы извлеченные из архивов"""
        path_to_dir = os.path.realpath('TEMP_ZIP')
        if not os.path.isdir(path_to_dir):
            os.mkdir(path_to_dir)
            folder_to_test_files = os.path.join(path_to_dir, self.name_test)
            if not os.path.isdir(folder_to_test_files):
                os.mkdir(folder_to_test_files)
                path_to_dir = folder_to_test_files
        else:
            folder_to_test_files = os.path.join(path_to_dir, self.name_test)
            if not os.path.isdir(folder_to_test_files):
                os.mkdir(folder_to_test_files)
                path_to_dir = folder_to_test_files
            else:
                path_to_dir = folder_to_test_files
        self.path_extract_files = path_to_dir
        return path_to_dir

    @staticmethod
    def delete_folder(path):
        """удалем каталог и все содержимое каталога"""
        shutil.rmtree(path, ignore_errors=True)
