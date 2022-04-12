import time
import re
import os
import gitlab
import shutil
import subprocess

SAGHOME='C:\SoftwareAG107\IntegrationServer\instances\default\packages'
SAGINSTANCE = 'default'
TEMPLATEREPO = 'C:\git\gitlab-python-emothep\webmethods-assets-is-template.zip'
LOCALREPO = 'C:\SoftwareAG107\localPackages'
NAMESPACE = 'emothep/run/is-run'
PATH_REPO_PACKAGES = '/assets/IS/Packages/'


#https://github.com/ansible-collections/community.general/blob/main/plugins/module_utils/gitlab.py
#https://github.com/ansible-collections/community.general/blob/7e6a2453d0786052b1640c5c602e6ac152c75947/plugins/modules/source_control/gitlab/gitlab_project.py#L259

def find_group(gitlab_instance, identifier):
    try:
        project = gitlab_instance.groups.get(identifier)
    except Exception as e:
        return None

    return project

def find_project(gitlab_instance, identifier):
    try:
        project = gitlab_instance.projects.get(identifier)
        
    except Exception as e:
        current_user = gitlab_instance.user
        try:
            project = gitlab_instance.projects.get(current_user.username + '/' + identifier)
        except Exception as e:
            return None

    return project

def gitlab_authentication(gitlaburl, token):
    gitlab_url = gitlaburl
    gitlab_token = token
    
    try:
        gitlab_instance = gitlab.Gitlab(url=gitlab_url, private_token=gitlab_token, api_version=4)
        gitlab_instance.auth()
    except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabGetError) as e:
        print('Error d''authentification')
    except (gitlab.exceptions.GitlabHttpError) as e:
       print("Failed to connect to GitLab server: %s. \
            GitLab remove Session API now that private tokens are removed from user API endpoints since version 10.2.")

    return gitlab_instance

class GitLabProject(object):
    def __init__(self, module, gitlab_instance):
        self._gitlab = gitlab_instance
        self._module = module
        self.project_object = None

    def exists_project(self, namespace, path):
        # When project exists, object will be stored in self.project_object.
        project = find_project(self._gitlab, namespace + '/' + path)
        if project:
            self.project_object = project
            return True
        return False
    
    def export_project(self, project_id):
            project = find_project(self._gitlab, project_id)
            export = project.exports.create()
            
            export.refresh()
            while export.export_status != 'finished':
                time.sleep(1)
                export.refresh()
            with open('./'+project.name+'.zip', 'wb') as f:
                export.download(streamed=True, action=f.write)
        
    def import_project(self, namespace, repositoryName, packageName):
        if not self.exists_project(namespace, repositoryName):
            output = self._gitlab.projects.import_project(file=open(TEMPLATEREPO, 'rb'),namespace=namespace,path=repositoryName, name=packageName)
            # Get a ProjectImport object to track the import status
            project = self._gitlab.projects.get(output['id'], lazy=True).imports.get()
            while project.import_status != 'finished':
                time.sleep(1)
                project.refresh()
            self.project_object = self._gitlab.projects.get(output['id'])      

###
# Git Function
def checkout_git_project(gitlab_project, projectName):
    repo_user_password = gitlab_project.http_url_to_repo.replace('http://', 'http://guillaume.deparis:jXZWUAAb1V2Lpbt2TG2e@')
    #repo_user_password = gitlab_project.ssh_url_to_repo
    subprocess.check_output(["git", "clone", repo_user_password, LOCALREPO+'/'+projectName])

def add_git_project():
    subprocess.call(["git", "add", "."])

def commit_git_project(message):
    subprocess.call(["git", "commit", "-m "+message])

def push_git_project():
    subprocess.call(["git", "push", "origin"])

##
# E-Mothep Function
# Transformer un nom de package en projet gitlab :
def calculate_project_name(package):
    s = package
    s = re.sub("_", "-",s)
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

def find_package(gitlab_instance):
    module = dict(
        group_identifier = '59',
    )

    gitlab_project = GitLabProject(module, gitlab_instance)
    for packageDir in os.listdir(SAGHOME):
        if not packageDir.startswith('Wm') and not packageDir.startswith('Default'):
            projectName = calculate_project_name(packageDir)

            gitlab_project.import_project(NAMESPACE, projectName, packageDir)
            src_path = SAGHOME+'/'+packageDir
            if not os.path.exists(LOCALREPO+'/'+projectName):
                checkout_git_project(gitlab_project.project_object, projectName)
                os.chdir(LOCALREPO+'/'+projectName)
                dst_path = LOCALREPO+'/'+projectName+PATH_REPO_PACKAGES+packageDir
                if not os.path.exists(dst_path):
                    shutil.move(src_path, dst_path)
                    os.symlink(dst_path, src_path)
                    add_git_project()
                    commit_git_project('Ajout du package')
                    push_git_project()
                os.chdir(LOCALREPO)





def main():
    gitlab_instance = gitlab_authentication('http://10.2.39.18/', 'PHFqULc91MVG7jZnZy2g')
    find_package(gitlab_instance)

main()