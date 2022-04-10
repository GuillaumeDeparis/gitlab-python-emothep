from audioop import tostereo
import re
import os
import gitlab


gl = gitlab.Gitlab(url='http://10.2.39.18/', private_token='osNiwSvXf2qQJhxUck6y') #expire le 30/04/2022


group = gl.groups.get('emothep/run/is-run')
currentGroup = group.get_id()

gl.features.set('import_project_from_remote_file', True)

templateProject = gl.projects.get('emothep/architecture/templates/webmethods-assets-is-template')
#print(templateProject)
currentHttpUrlRepo = templateProject.__getattr__('http_url_to_repo')
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
    print(package, "-" ,to_emothep_case(package))