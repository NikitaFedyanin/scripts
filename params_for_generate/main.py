import json


def read_params():
    with open('C:\scripts\params_for_generate\s_d_params.json', encoding='utf-8') as f:
        return json.loads(f.read(), encoding='utf-8')


def generate_params(dict_format=False):
    params = read_params()
    if dict_format:
        result = [f'\"{params["s"][i]["n"]}\": ({v}, \"{params["s"][i]["t"]}\")' for i, v in enumerate(params['d'])]
    else:
        result = [f'{params["s"][i]["n"]}=({v}, \"{params["s"][i]["t"]}\")' for i, v in enumerate(params['d'])]

    result = ',\n\t\t\t\t'.join(result)
    print(f'generate_record({result})')



generate_params(dict_format=False)
