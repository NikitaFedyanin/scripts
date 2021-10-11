# -*- coding: utf-8 -*-
import json

json_string = '''

  {"jsonrpc":"2.0","protocol":3,"method":"FileSD.ListFiles","params":{"AuxParams":{"d":[false,true,false,false],"s":[{"t":"Логическое","n":"ReadAllVersions"},{"t":"Логическое","n":"ReadServiceFiles"},{"t":"Логическое","n":"ReadSignRequirements"},{"t":"Логическое","n":"ReadLinkedObjects"}]},"Id":"9edd7de1-e7ad-4963-8c88-52bfd52e5977"},"id":1}

  '''

json_dict = json.loads(json_string)
p = json.dumps(json_dict, sort_keys=True, indent=4, ensure_ascii=False)
print(p)


