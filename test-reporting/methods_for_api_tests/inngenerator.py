# coding=utf-8
"""
Модуль для генерации валидного ИНН
"""
__author__ = 'boychenkoio'


from random import randrange


def new_inn(for_person=True):
    """
    Генерация случайного ИНН

    :param for_person: генерировать ИНН для физлица (ИП)
    :return: str
    """

    inn = ''
    if not for_person:
        multipliers = (2, 4, 10, 3, 5, 9, 4, 6, 8)
        inn_arr = [randrange(0, 9) for i in range(0, 9)]
        num_2 = 0
        for i in range(0, 9):
            num_2 += inn_arr[i] * multipliers[i]
        num_3 = num_2 // 11
        num_4 = num_3 * 11
        num_5 = abs(num_2 - num_4)
        if num_5 == 10:
            num_5 = 0
        inn_arr.append(num_5)
        for sym in inn_arr:
            inn += str(sym)
    else:
        multipliers = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
        inn_arr = [randrange(0, 9) for i in range(0, 10)]
        num_2 = 0
        for i in range(0, 10):
            num_2 += inn_arr[i] * multipliers[i]
        num_3 = num_2 // 11
        num_4 = num_3 * 11
        num_5 = abs(num_2 - num_4)
        if num_5 == 10:
            num_5 = 0
        inn_arr.append(num_5)

        multipliers_2 = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
        num_7 = 0
        for i in range(0, 11):
            num_7 += inn_arr[i] * multipliers_2[i]
        num_8 = num_7 // 11
        num_9 = num_8 * 11
        num_10 = abs(num_7 - num_9)
        if num_10 == 10:
            num_10 = 0
        inn_arr.append(num_10)

        for sym in inn_arr:
            inn += str(sym)

    if inn.startswith('00'):
        inn = new_inn(for_person)

    return inn


def generate_snils():
    snins_num = [randrange(0, 9) for _ in range(0, 9)]
    str_snils = [str(n) for n in snins_num]
    #x = [(9-i[0], i[1]) for i in enumerate(snins_num)]
    x2 = [(9-i[0])*i[1] for i in enumerate(snins_num)]
    sum_x = sum(x2)
    while True:
        if sum_x < 100:
            if sum_x < 10:
                zz = "0%s" % sum_x
            else:
                zz = str(sum_x)
            break
        elif sum_x == 100 or sum_x == 101:
            zz = "00"
            break
        else:
            sum_x = sum_x % 101
    print("СНИЛС - %s" % "".join(str_snils)+"    "+zz)
    return "".join(str_snils)+zz



#generate_snils()
print()