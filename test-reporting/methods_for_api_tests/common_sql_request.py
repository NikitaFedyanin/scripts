# -*- coding: utf-8 -*-
from atf import *
import postgresql
import time
from datetime import datetime


def get_id_vi(docflow_id, id_billing, time_wait=300):
    """
    :param docflow_id: Документ.Идентификатор
    :param id_billing: идентификатор биллинга
    """
    start = time.time()
    sql_script = '''
    select "ИдентификаторВИ" from "Документ"
    left join "ДокументРасширение" using ("@Документ")
    where "ИдентификаторДокумента" = '{0}'
    and "ДокументНашаОрганизация" in (select "@Лицо" from "Контрагент"
                                      where "Идентификатор" = '{1}')
    '''.format(docflow_id, id_billing)
    log("Выполняется запрос:\n%s" % sql_script)
    db = postgresql.open(Config().get('DB'))
    while True:
        if time.time() < start + time_wait:
            res = db.prepare(sql_script)()
            if not res:
                time.sleep(5)
            else:
                break
        else:
            msg = "Выполнялся запрос:\n{query}\nОжидали получить одну запись - вернулось{res}"
            raise Exception(msg.format(query=sql_script, res=res))
    return res[0][0]


def get_code_event(docflow_id, id_billing, time_wait=300, num_event=1):
    """
    :param docflow_id: Документ.Идентификатор
    :param id_billing: идентификатор биллинга
    """
    start = time.time()
    sql_script = '''
    select "кодСобытия" from "Событие"
    where  "Документ" in (select "@Документ" from "Документ"
    where "ИдентификаторДокумента" = '{0}' and "ДокументНашаОрганизация" in
    (select "@Лицо" from "Контрагент" where "Идентификатор" = '{1}')
    )
    order by "Раздел" nulls last
    '''.format(docflow_id, id_billing)
    log("Выполняется запрос:\n%s" % sql_script)
    db = postgresql.open(Config().get('DB'))
    while True:
        if time.time() < start + time_wait:
            res = db.prepare(sql_script)()
            if not res:
                time.sleep(5)
            else:
                break
        else:
            msg = "Выполнялся запрос:\n{query}\nОжидали получить одну запись - вернулось{res}"
            raise Exception(msg.format(query=sql_script, res=res))
    log("Ответ - %s - возвращаем только res[0][0]" % res)
    return str(res[num_event][0])


def get_id_doc_on_id_vi(id_vi, time_wait=300):
    """ Возвращает идентификатор комплекта
    :param id_vi: идентификатор - Документ.Идентификатор

    """
    start = time.time()
    sql_script = '''
        with ext_docs as (SELECT "@Документ" FROM "ДокументРасширение" WHERE "ИдентификаторВИ" = '{0}'),
        docs as (SELECT "Раздел" FROM "Документ" WHERE "@Документ" = ANY(ARRAY(SELECT "@Документ" FROM ext_docs)))
        SELECT "@Документ" FROM "Комплект" WHERE "@Документ" = ANY(ARRAY(SELECT "Раздел" FROM docs))
       '''.format(id_vi)

    db = postgresql.open(Config().get('DB'))
    while True:
        if time.time() < start + time_wait:
            result = db.prepare(sql_script)()
            log("\nВыполнялся запрос:\n"
                "   {query}\n"
                "Ответ:\n"
                "   {result}\n".format(query=sql_script, result=result))
            if not result:
                time.sleep(5)
            else:
                break
        else:
            msg = "Выполнялся запрос:\n{sql_script}\nОжидали получить одну запись - вернулось{result}"
            raise Exception(msg.format(sql_script=sql_script, res=result))
    return result


def updata_name_file(old_name, new_name):
    sql_script = '''
    with linking_names as (
    select "@ВнешнийДокумент", "@ВерсияВнешнегоДокумента", "Имя", "ИмяФайла" from "ВнешнийДокумент"
    left join "ВерсияВнешнегоДокумента"  on "ВерсияВнешнегоДокумента"."ВнешнийДокумент" = "ВнешнийДокумент"."@ВнешнийДокумент"
    where "Имя" LIKE '{old_name}.%'
    order by "@ВнешнийДокумент" desc limit 1
    ),
   ext_doc_name as (
   --select "ИмяФайла", * from "ВнешнийДокумент"
   update "ВнешнийДокумент"  set "ИмяФайла" = '{new_name}'
   where "@ВнешнийДокумент" = any (select "@ВнешнийДокумент" from  linking_names )
   )
   --select "Имя", * from "ВерсияВнешнегоДокумента"
   update "ВерсияВнешнегоДокумента" set "Имя" = '{new_name}'
   where "@ВерсияВнешнегоДокумента" = any (select "@ВерсияВнешнегоДокумента" from  linking_names )
   '''.format(old_name=old_name, new_name=new_name)
    db = postgresql.open(Config().get('DB'))
    res = db.prepare(sql_script)()
    return res

def blocking_api(inn):
    base = Config().get('DB')
    db = postgresql.open(base)
    sql_script_1 = '''
                   delete from "Параметр"
                   WHERE "Название" = 'ВИразрешенныеИНН'
    '''
    log("Выполняется запрос к базе {base}\n {query}\n".format(base=base, query=sql_script_1))
    res = db.prepare(sql_script_1)()

    sql_script_2 = '''
                   insert into "Параметр" ("Название","Значение","ИдПользователь")
                   values('ВИразрешенныеИНН', '{inn}', -1)
    '''.format(inn=inn)
    log("Выполняется запрос к базе {base}\n {query}\n".format(base=base, query=sql_script_2))
    res_2 = db.prepare(sql_script_2)()
    return res_2

def clearing_db():
    """Чистим базу от всех комплектов старше 14 дней"""
    base = Config().get('DB')
    db = postgresql.open(base)
    log(datetime.now())
    sql_script_1 = '''DELETE FROM "Документ" WHERE "@Документ" IN (SELECT "@Документ" FROM "Комплект" WHERE DATE_PART('day', now() - "Дата"::date) > 14)'''
    # sql_script_1 = '''SELECT "@Документ" FROM "Комплект"'''
    log("Выполняется запрос к базе {base}\n {query}\n".format(base=base, query=sql_script_1))
    res = db.prepare(sql_script_1)()
    log(datetime.now())
    return res