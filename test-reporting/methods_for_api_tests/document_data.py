# coding=utf-8
import json
from copy import deepcopy
import os
from methods_for_api_tests.functions import *
from base64 import b64encode
from data import Data


class DataDocs:

    def __init__(self, id_att, type_doc, id_sender, id_receiver, path_dir_files, new_atrib_xml=None,
                 out_keys_responce=None, encoding="cp1251"):
        self.id_att = id_att
        self.type_doc = type_doc
        self.organizations_id = {"id_sender": id_sender, "id_receiver": id_receiver}
        path_desc = os.path.join(path_dir_files, r"documents_data\Description.json")
        # ДЛЯ XML есть возможность менять значения атрибутов Дата, Номер, Сумма
        with open(path_desc) as f:
            obj_docs = json.loads(f.read())
        self.docs = obj_docs[type_doc]

        if isinstance(new_atrib_xml, dict):
            self.docs["res"].update(new_atrib_xml)
        Data._DataDocs_NUM_DOC = self.docs["res"]["Номер"]
        Data._DataDocs_DATA_DOC = self.docs["res"]["Дата"]
        Data._DataDocs_SUM_DOC = self.docs["res"]["Сумма"]

        if self.docs["path"]:
            path_to_xml = os.path.join(path_dir_files, "documents_data", self.docs["path"])
            xml_text = read_file(path_to_xml, encoding=encoding)
            self.docs["data"] = b64encode(xml_text.encode(encoding)).decode(encoding)
        else:
            self.docs["data"] = ""

        if isinstance(out_keys_responce, dict):
            self.docs["res"].update(out_keys_responce)
        self.data_file = self.docs["data"]
        self.docs["name"] = self.docs["name"].format(**self.organizations_id)
        self.name_file = self.docs["name"]

    def get_data_file(self):
        return self.docs["data"]

    def get_attacmemt(self, direction, redaction=1, certs=None, get_json=True, get_file=True):
        redaction = str(redaction)
        obj = deepcopy(self.docs)
        obj_res = obj["res"]
        obj_res["Идентификатор"] = self.id_att
        obj_res["Направление"] = direction
        obj_res["Редакция"]["Номер"] = redaction
        obj_res["Файл"]["Имя"] = obj["name"]
        if not get_file:
            obj_res["Файл"].pop("Имя")
        if certs:
            obj_res["Подпись"] = self.generate_sign(certs, get_file=get_file)
        if get_json:
            obj_res = json.dumps(obj_res, ensure_ascii=False)
        return obj_res

    def generate_sign(self, obj, get_file):
        temp = []
        for i in obj:
            temp_i = {"Файл": {"Имя": "", "Ссылка": "ignore"}}
            temp_i["Тип"] = i.get("Тип", "Отсоединенная")
            if get_file:
                temp_i["Файл"]["Имя"] = self.name_file + i["Имя"]
            else:
                temp_i["Файл"]["Имя"] = "ignore"
            temp_i["Сертификат"] = i["Сертификат"]
            temp.append(temp_i)
        return temp

    def get_key_doc(self, key):
        return self.docs["res"].get(key, "Переданный ключ не обнаружен - проверьте название ключа")