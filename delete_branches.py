"""
Удаление веток в gitlab
"""
import gitlab
from datetime import datetime

token = 'yFttYNfq2fWZMpdYMfoe'


def delete_branches(repo, group, project):
    print('========================================')
    print(f'======     repo: {repo}')
    print(f'======     group: {group}')
    print(f'======     project: {project}')
    git = gitlab.Gitlab(repo, private_token=token, api_version='4')
    now = datetime.now()
    group = git.groups.get(group)
    projects = group.projects.list(search=project)
    deleted = 0
    for p in projects:
        print(p.name)
        project = git.projects.get(p.id)
        project.delete_merged_branches()

        branches = project.branches.list(all=True)
        for branch in branches:
            last_commit = datetime.strptime(branch.commit['committed_date'][:10], '%Y-%m-%d')
            if (branch.name != 'master' and (now - last_commit).days > 30 * 3) or (
                    'update-files' in branch.name or 'mergerator' in branch.name):
                print(branch.name)
                branch.delete()
                deleted += 1
    print(f'удалили: {deleted}')
    print('========================================\n\n\n\n\n')


delete_branches('http://git-autotests.sbis.ru/', 'mobile', 'ios_apps')
delete_branches('http://git-autotests.sbis.ru/', 'mobile', 'android_apps')
delete_branches('http://git-autotests.sbis.ru/', 'autotests', 'api')
