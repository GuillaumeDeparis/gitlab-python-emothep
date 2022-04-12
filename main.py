from audioop import tostereo
from importlib.resources import path
from logging import exception
import time
import re
import os
from unicodedata import name
import gitlab
import git
import shutil
import subprocess

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

def gitlab_authentication(gitlaburl, token, api_username, api_password):
    gitlab_url = gitlaburl
    gitlab_token = token
    gitlab_user = api_username
    gitlab_password = api_password
    
    try:
        gitlab_instance = gitlab.Gitlab(url=gitlab_url, private_token=gitlab_token, api_version=4, http_username=gitlab_user, http_password=gitlab_password)
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
        
    
    def delete_project(self, project_name):
        print('delete project')

    def create_or_update_project(self, project_name, namespace ,options):
        changed = False
        project_options = {
            'name' : project_name,
            'description': options['description'],
            'issues_enabled': options['issues_enabled'],
            'merge_requests_enabled': options['merge_requests_enabled'],
            'merge_method': options['merge_method'],
            'wiki_enabled': options['wiki_enabled'],
            'snippets_enabled': options['snippets_enabled'],
            'visibility': options['visibility'],
            'lfs_enabled': options['lfs_enabled'],
            'allow_merge_on_skipped_pipeline': options['allow_merge_on_skipped_pipeline'],
            'only_allow_merge_if_all_discussions_are_resolved': options['only_allow_merge_if_all_discussions_are_resolved'],
            'only_allow_merge_if_pipeline_succeeds': options['only_allow_merge_if_pipeline_succeeds'],
            'packages_enabled': options['packages_enabled'],
            'remove_source_branch_after_merge': options['remove_source_branch_after_merge'],
            'squash_option': options['squash_option'],
            'ci_config_path': options['ci_config_path'],
            'shared_runners_enabled': options['shared_runners_enabled']
        }

        # Because we have already call userExists in main()
        if self.project_object is None:
            project_options.update({
                'path': options['path'],
                'import_url': options['import_url'],
                'http_username':'guillaume.deparis',
                'http_password':'jXZWUAAb1V2Lpbt2TG2e'
            })
            if options['initialize_with_readme']:
                project_options['initialize_with_readme'] = options['initialize_with_readme']
                if options['default_branch']:
                    project_options['default_branch'] = options['default_branch']

            project_options = self.get_options_with_value(project_options)
            project = self.create_project(namespace, project_options)

            # add avatar to project
            if options['avatar_path']:
                try:
                    project.avatar = open(options['avatar_path'], 'rb')
                except IOError as e:
                    print('Cannot open {0}: {1}'.format(options['avatar_path'], e))

            changed = True
        else:
            changed, project = self.update_project(self.project_object, project_options)

        self.project_object = project
        if changed:
            try:
                project.save()
            except Exception as e:
                print("Failed update project: %s " % e)
            return True
        return False


    def create_project(self, namespace, arguments):
       
        arguments['namespace_id'] = namespace.id
        try:
            project = self._gitlab.projects.create(arguments)
        except (gitlab.exceptions.GitlabCreateError) as e:
           print("Failed to create project:", e)

        return project

    def get_options_with_value(self, arguments):
        ret_arguments = dict()
        for arg_key, arg_value in arguments.items():
            if arguments[arg_key] is not None:
                ret_arguments[arg_key] = arg_value

        return ret_arguments

    def update_project(self, project, arguments):
        changed = False

        for arg_key, arg_value in arguments.items():
            if arguments[arg_key] is not None:
                if getattr(project, arg_key) != arguments[arg_key]:
                    setattr(project, arg_key, arguments[arg_key])
                    changed = True

        return (changed, project)

    def delete_project(self):

        project = self.project_object

        return project.delete()

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
            output = self._gitlab.projects.import_project(file=open('C:\git\gitlab-python-emothep\webmethods-assets-is-template.zip', 'rb'),namespace=namespace,path=repositoryName, name=packageName)
            # Get a ProjectImport object to track the import status
            project = self._gitlab.projects.get(output['id'], lazy=True).imports.get()
            while project.import_status != 'finished':
                time.sleep(1)
                project.refresh()
            self.project_object = self._gitlab.projects.get(output['id'])      
            

SAGHOME='C:\SoftwareAG107\IntegrationServer\instances\default\packages'
SAGINSTANCE = 'default'
LOCALREPO = 'C:\SoftwareAG107\localPackages'


#group = gl.groups.get('emothep/run/is-run')
#currentGroup = group.get_id()

#gl.features.set('import_project_from_remote_file', True)

#templateProject = gl.projects.get('emothep/architecture/templates/webmethods-assets-is-template')
#print(templateProject)
#currentHttpUrlRepo = templateProject.__getattr__('http_url_to_repo')

#currentProject = gl.projects.import_project(file='{"url":"'+currentHttpUrlRepo+'","path":"remote-project"}', name='my-new-project', path='my-new-project', namespace='emothep/run/is-run')
#gl.projects.update(d, new_data='{"import_project"=currentHttpUrlRepo'})


#print(group.search(gitlab.const.SEARCH_SCOPE_ISSUES, 'regression'))

#group = gl.projects.list(query_parameters={"full_path":"emothep/run/is-run"})

#gl.search(gitlab.const.SEARCH_SCOPE_PROJECTS)

#gl.features.set('import_project_from_remote_file', False)

def to_emothep_case(s):
    s = re.sub("_", "-",s)
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

#transformer un nom de package en projet gitlab :
def calculateProjectName(package):
    return to_emothep_case(package)

#def checkProject(project):
#    print('checkProject if exist : ', project)
#    try:
        #currentProject = group.full_path+'/'+project
        #print(currentProject)
        #projectExist = gl.projects.get(currentProject)
        #if projectExist:
        #    print('Project Exist')
        #    return True
        #else:
        #    print('Project Not Exist')
        #    return False
#    except:
#        print("Error occureed : ")
#        return False
def createOrUpdateProject(projectName, packageDir, gitlab_instance):
    group_identifier = 42
    project_name = packageDir
    project_path = projectName
    project_description = None
    initialize_with_readme = True
    issues_enabled = False
    merge_requests_enabled = False
    merge_method = 'rebase_merge'
    wiki_enabled = True
    snippets_enabled = True
    visibility = 'private'
    import_url = 'http://10.2.39.18/emothep/architecture/templates/webmethods-assets-is-template.git'
    state = 'present'
    lfs_enabled = False
    username = gitlab_instance.http_username
    allow_merge_on_skipped_pipeline = False
    only_allow_merge_if_all_discussions_are_resolved = False
    only_allow_merge_if_pipeline_succeeds = False
    packages_enabled = True
    remove_source_branch_after_merge = False
    squash_option = None
    ci_config_path = None
    shared_runners_enabled = False
    avatar_path = None
    default_branch = None

    module = dict(
        group_identifier = '42',
        project_name = projectName,
        project_path = None,
        project_description = None,
        initialize_with_readme = True,
        issues_enabled = False,
        merge_requests_enabled = False,
        merge_method = 'rebase_merge',
        wiki_enabled = True,
        snippets_enabled = True,
        visibility = 'private',
        import_url = '',
        state = 'present',
        lfs_enabled = False,
        username = gitlab_instance.http_username,
        allow_merge_on_skipped_pipeline = False,
        only_allow_merge_if_all_discussions_are_resolved = False,
        only_allow_merge_if_pipeline_succeeds = False,
        packages_enabled = True,
        remove_source_branch_after_merge = False,
        squash_option = None,
        ci_config_path = None,
        shared_runners_enabled = False,
        avatar_path = None,
        default_branch = None,
    )

    gitlab_project = GitLabProject(module, gitlab_instance)
    namespace = None
    namespace_id = None
    if group_identifier:
        group = find_group(gitlab_instance, group_identifier)
        if group is None:
            print("Failed to create project: group %s doesn't exists" % group_identifier)

        namespace_id = group.id
    else:
        if username:
            namespace = gitlab_instance.namespaces.list(search=username)[0]
        else:
            namespace = gitlab_instance.namespaces.list(search=gitlab_instance.user.username)[0]
        namespace_id = namespace.id

    if not namespace_id:
        print("Failed to find the namespace or group ID which is required to look up the namespace")

    try:
        namespace = gitlab_instance.namespaces.get(namespace_id)
    except gitlab.exceptions.GitlabGetError as e:
        print("Failed to find the namespace for the given user: ", e )

    if not namespace:
        print("Failed to find the namespace for the project")
    project_exists = gitlab_project.exists_project(namespace, project_path)

    if state == 'absent':
        if project_exists:
            gitlab_project.delete_project()
            print("Successfully deleted project %s" % project_name)
        print("Project deleted or does not exists")
    
    if state == 'present':

        if gitlab_project.create_or_update_project(project_name, namespace, {
            "path": project_path,
            "description": project_description,
            "initialize_with_readme": initialize_with_readme,
            "default_branch": default_branch,
            "issues_enabled": issues_enabled,
            "merge_requests_enabled": merge_requests_enabled,
            "merge_method": merge_method,
            "wiki_enabled": wiki_enabled,
            "snippets_enabled": snippets_enabled,
            "visibility": visibility,
            "import_url": import_url,
            "lfs_enabled": lfs_enabled,
            "allow_merge_on_skipped_pipeline": allow_merge_on_skipped_pipeline,
            "only_allow_merge_if_all_discussions_are_resolved": only_allow_merge_if_all_discussions_are_resolved,
            "only_allow_merge_if_pipeline_succeeds": only_allow_merge_if_pipeline_succeeds,
            "packages_enabled": packages_enabled,
            "remove_source_branch_after_merge": remove_source_branch_after_merge,
            "squash_option": squash_option,
            "ci_config_path": ci_config_path,
            "shared_runners_enabled": shared_runners_enabled,
            "avatar_path": avatar_path,
        }):
                print("Successfully created or updated the project %s" % project_name, project=gitlab_project.project_object._attrs)
    print("No need to update the project %s" % project_name, project=gitlab_project.project_object._attrs)


def checkout_git_project(gitlab_project, projectName):
    repo_user_password = gitlab_project.http_url_to_repo.replace('http://', 'http://guillaume.deparis:jXZWUAAb1V2Lpbt2TG2e@')
    output = subprocess.check_output(["git", "clone", repo_user_password, LOCALREPO+'/'+projectName])
    print(output)

def add_git_project():
    output = subprocess.check_output(["git", "add", "."])
    print(output)

def commit_git_project(message):
    output = subprocess.check_output(["git", "commit", "-m "+message])
    print(output)

def push_git_project():
    output = subprocess.check_output(["git", "push", "origin"])
    print(output)

def findPackage(gitlab_instance):
    module = dict(
        group_identifier = '59',
    )

    gitlab_project = GitLabProject(module, gitlab_instance)
    for packageDir in os.listdir(SAGHOME):
        if not packageDir.startswith('Wm') and not packageDir.startswith('Default'):
            projectName = calculateProjectName(packageDir)

            gitlab_project.import_project('emothep/run/is-run', projectName, packageDir)
            src_path = SAGHOME+'/'+packageDir
            if not os.path.exists(LOCALREPO+'/'+projectName):
                #repo_user_password = gitlab_project.project_object.http_url_to_repo.replace('http://', 'http://guillaume.deparis:jXZWUAAb1V2Lpbt2TG2e@')
                #repo = git.Repo.clone_from(repo_user_password, LOCALREPO+'/'+projectName)
                checkout_git_project(gitlab_project.project_object, projectName)
                dst_path = LOCALREPO+'/'+projectName+'/asset/IS/Packages/'+packageDir
                if not os.path.exists(dst_path):
                    shutil.copytree(src_path, dst_path)
                add_git_project()
                commit_git_project('Ajout du package')
                push_git_project()





def main():
    gitlab_instance = gitlab_authentication('http://10.2.39.18/', 'PHFqULc91MVG7jZnZy2g', 'guillaume.deparis', 'jXZWUAAb1V2Lpbt2TG2e')
    findPackage(gitlab_instance)

main()