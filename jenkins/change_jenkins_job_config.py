import re
import os
from urllib.parse import quote_plus
from requests.auth import HTTPBasicAuth
from pymongo import MongoClient
import requests


LOGIN = 'autotest'
API_TOKEN = '11a1c5f10b1e1fc16c4eb14faa754a7411'

RE_NAME = re.compile(r'def builder.+runner_(\w+)')
RE_PARAMS = re.compile(r"builder\.run_jobs\((.+)\)", re.MULTILINE)

template = """
    stage('run jobs') {{
        def script
        fileLoader.withGit('git@git-autotests.sbis.ru:helpers/pipeline.git',
                            'master', env.CREDENTIAL_ID_GIT, env.NODE_NAME) {{
            script = fileLoader.load('runner_{name}.groovy');
            script.run_jobs({params})
        }}
    }}
}}"""


def connect_to_db():
    user = os.environ.get('MONGODB_USER')
    pwd = os.environ.get('MONGODB_PWD')
    uri = "mongodb://{0}:{1}@{2}/{3}".format(quote_plus(user), quote_plus(pwd),
                                             'test-selenium38-unix', 'jenkins_control')
    client = MongoClient(uri)
    db = client.get_database('jenkins_control')
    return db


def write_config(update_url, config_data):
    """Запись конфига"""

    update_url += 'config.xml'
    headers = {'Content-Type': 'application/xml; charset=utf-8'}
    data = config_data.encode()
    response = requests.post(update_url, headers=headers, data=data, auth=HTTPBasicAuth('ns.fedyanin', 'Fedyanin5479'))
    response.raise_for_status()


def get_config(url):
    """Получение конфига"""

    url += "config.xml"
    response = requests.get(url, auth=HTTPBasicAuth('ns.fedyanin', 'Fedyanin5479'))
    response.raise_for_status()
    config_xml = response.content.decode()
    return config_xml


def get_jobs():
    """Получение сборок для обработки"""

    db = connect_to_db()
    cursor = db.jobs.find({'job': {'$regex': '^run \((smoke|приемочные)'}, 'host': 'ci-fix-autotests.sbis.ru'},
                          {'url': 1, 'job': 1, '_id': 0})
    return cursor


def path_config(url):
    config = get_config(url)

    start = config.find('<script>')
    end = config.rfind('</script>')
    pipeline = config[start+8:end]

    result = pipeline.replace('test-mobile1', 'test-mobile-builder1')
    result = result.replace('C:\\\\jenkins\\\\test_environment\\\\pipeline\\\\pipeline_templates\\\\mobile', '/home/jenkins/test_environment/pipeline/pipeline_templates/mobile')
    print(result)

    config_xml = config[:start+8] + result + config[end:]
    write_config(url, config_xml)


def main(url=None):
    if not url:
        cursor = get_jobs()
    else:
        cursor = ({'url': url, 'job': 'test'},)

    for j in cursor:
        try:
            path_config(j['url'])
        except Exception as err:
            print('Не смогли обработать сборку: %s\n%s\n%s\n%s' % (j['job'], j['url'], err, '=*60'))

if __name__ == '__main__':
    # db = connect_to_db()
    file = open('run.txt', 'r')
    for l in file:
        l = l.strip()
        # job_url = db.jobs.find_one({'job': l}, {'_id': 0, 'url': 1})
        # main(job_url['url'])
        main(l)
