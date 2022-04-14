import argparse
import configfile
import time
import re
import os
import gitlab
import shutil
import subprocess
import sys

class GitEmothepGitlab(object):
    def __init__(self):
        #if __debug__:
        #    self.import_package_gitlab()
        #    print('Debug mode')
        parser = argparse.ArgumentParser(
                    description='Pretends to be git',
                    usage='''git <command> [<args>]
            exportTemplate      Export repository from gitlab specified in the configFile
            importPackage       Import all packages to remote repository
                                1. create one repository by package; 
                                2. Move package in configfile.LOCALREPO repository; 
                                3. Add all files in commit et push on origin master
                                4. Finaly, create symlink in IS instance.
            list                List all project already pushed on remote gitlab
            status              Return all modified files in repository
            statusAll           Return all modified files in all repository
            ''')

        parser.add_argument('command', help='Subcommand to run')
            # parse_args defaults to [1:] for args, but you need to
            # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def status(self):
        parser = argparse.ArgumentParser(
        description='Return status from project passed in parameter')
        parser.add_argument('-p','--projectName')
        parser.add_argument('-a', '--all', action='store_false')
        args = parser.parse_args(sys.argv[2:])
        self.__statusProject(args.projectName, args.all)
    
    def statusAll(self):
        parser = argparse.ArgumentParser(
        description='Return status fo all repository project')
        parser.add_argument('-a', '--all', action='store_false')
        args = parser.parse_args(sys.argv[2:])
        self.__statusAllProject(args.all)

    def list(self):
        parser = argparse.ArgumentParser(
        description='List all repository project')        
        self.__list()
    
    def importPackage(self):
        parser = argparse.ArgumentParser(
        description='Add all packages from current instance to remote repository')
        self.__import_package_gitlab()
    
    def exportTemplate(self):
        parser = argparse.ArgumentParser(
            description="Export template define in configFile")
        self.__export_template()
    
    ###
    # Git Function

    def __checkout_git_project(self, gitlab_project, projectName):
        print('Checkout remote project to local repository dedicated to the package')
        repo_user_password = gitlab_project.http_url_to_repo.replace('http://', 'http://guillaume.deparis:jXZWUAAb1V2Lpbt2TG2e@')
        #repo_user_password = gitlab_project.ssh_url_to_repo
        subprocess.check_output(["git", "clone", repo_user_password, configfile.LOCALREPO+'/'+projectName])

    def __add_git_project(self):
        print('Add all file to init repository')
        subprocess.call(["git", "add", "."])

    def __commit_git_project(self, message):
        print('Commit change with %s'% message)
        subprocess.call(["git", "commit", "-m "+message])

    def __push_git_project(self):
        print('Trying to push on origin')
        subprocess.call(["git", "push", "origin"])
        print('Success!')
    
    def __export_template(self):
        print('Export template : %s'% configfile.TEMPLATEREPO)
        gitlab_instance = self.__connect_to_gitlab()
        gitlab_project = GitLabProject(gitlab_instance)
        gitlab_project.export_project('emothep/architecture/templates/webmethods-assets-is-template')
    
    def __statusProject(self, projectName, all) :
        os.chdir(configfile.LOCALREPO+'/'+projectName)
        output = subprocess.check_output(["git", "status", "-s"])
        if len(output) == 0:
            if not all:
                print("%s: Nothing to do!"%projectName)
        else:
            if not all:
                print('%s:'% projectName)
                print(output.decode())
            else:
                print(projectName)
        os.chdir(configfile.LOCALREPO)
       
    def __statusAllProject(self, all):
        os.chdir(configfile.LOCALREPO)
        for dir in os.listdir():
            self.__statusProject(dir, all),

    def __list(self):
        os.chdir(configfile.LOCALREPO)
        for dir in os.listdir():
            print(dir)

    def __calculate_project_name(self, package):
        s = package
        s = re.sub("_", "-",s)
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', s)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

    def __connect_to_gitlab(self):
        return self.__gitlab_authentication(configfile.GITLAB_URL, configfile.GITLAB_TOKEN)
    
    def __gitlab_authentication(self, gitlaburl, token):
        gitlab_url = gitlaburl
        gitlab_token = token
        try:
            print('Trying to connect to gitLab: %s'% configfile.GITLAB_URL)
            gitlab_instance = gitlab.Gitlab(url=gitlab_url, private_token=gitlab_token, api_version=4)
            gitlab_instance.auth()
            print('Connected!')
        except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabGetError) as e:
            print('Error d''authentification')
        except (gitlab.exceptions.GitlabHttpError) as e:
            print("Failed to connect to GitLab server: %s. \
                GitLab remove Session API now that private tokens are removed from user API endpoints since version 10.2.")

        return gitlab_instance

    def __import_package_gitlab(self):
        gitlab_instance = self.__connect_to_gitlab()
        gitlab_project = GitLabProject(gitlab_instance)
        print('Exclude Wm* & Default packages')
        for packageDir in os.listdir(configfile.SAGHOME):
            if not packageDir.startswith('Wm') and not packageDir.startswith('Default'):
                projectName = self.__calculate_project_name(packageDir)
                gitlab_project.import_project(configfile.NAMESPACE, projectName, packageDir)
                src_path = configfile.SAGHOME+'/'+packageDir
                if not os.path.exists(configfile.LOCALREPO+'/'+projectName):
                    self.__checkout_git_project(gitlab_project.project_object, projectName)
                    os.chdir(configfile.LOCALREPO+'/'+projectName)
                    dst_path = configfile.LOCALREPO+'/'+projectName+configfile.PATH_REPO_PACKAGES+packageDir
                    if not os.path.exists(dst_path):
                        print('Try to move the current package to local package repository')
                        shutil.move(src_path, dst_path)
                        print('Success!')
                        print('Create symlink')
                        os.symlink(dst_path, src_path)
                        print('Success!')
                        self.__add_git_project()
                        self.__commit_git_project('Ajout du package')
                        self.__push_git_project()
                    os.chdir(configfile.LOCALREPO)
                    print('End for the package %s'% packageDir)
                    print('===========================')


class GitLabProject(object):
    def __init__(self, gitlab_instance):
        self._gitlab = gitlab_instance
        self.project_object = None

    def find_group(self, gitlab_instance, identifier):
        try:
            project = gitlab_instance.groups.get(identifier)
        except Exception as e:
            return None

        return project

    def find_project(self, identifier):
        try:
            print('gitLab - find project with name')
            project = self._gitlab.projects.get(identifier)
            print('gitLab - find project')
        except Exception as e:
            print('gitLab - project not find')
            current_user = self._gitlab.user
            try:
                print('gitLab - try to find project in user space')
                project = self.project_object.get(current_user.username + '/' + identifier)
                print('gitLab - project find in user space')
            except Exception as e:
                print('gitLag - exception %s'% e)
                return None

        return project

    def exists_project(self, namespace, path):
        # When project exists, object will be stored in self.project_object.
        project = self.find_project(namespace + '/' + path)
        if project:
            self.project_object = project
            return True
        return False
    
    def export_project(self, project_id):
            project = self.find_project(project_id)
            export = project.exports.create()
            print('gitLab - export in progress')
            export.refresh()
            while export.export_status != 'finished':
                time.sleep(1)
                print('gitLab - export in progress')
                export.refresh()
            with open('./'+project.name+'.zip', 'wb') as f:
                export.download(streamed=True, action=f.write)
                print('gitLab - export finish')
        
    def import_project(self, namespace, repositoryName, packageName):
        print('GitLab - Check if current project exist  to add %s to project %s'% (packageName))
        if not self.exists_project(namespace, repositoryName):
            print('GitLab - Trying to add %s to project %s'% (repositoryName, packageName))
            output = self._gitlab.projects.import_project(file=open(configfile.TEMPLATEREPO, 'rb'),namespace=namespace,path=repositoryName, name=packageName)
            # Get a ProjectImport object to track the import status
            project = self._gitlab.projects.get(output['id'], lazy=True).imports.get()
            while project.import_status != 'finished':
                time.sleep(1)
                project.refresh()
            self.project_object = self._gitlab.projects.get(output['id'])
            print('GitLab - Import status :'% self.project_object.import_status)  
        else:
            print('GitLab - Exist, nothing to do!')

if __name__ == '__main__':
    GitEmothepGitlab()