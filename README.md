# gitlab-python-emothep
usage:
	gitlab-emothep.py command
exportTemplate      Export repository from gitlab specified in the configFile
            importPackage       Import all packages to remote repository
                                1. create one repository by package; 
                                2. Move package in configfile.LOCALREPO repository; 
                                3. Add all files in commit et push on origin master
                                4. Finaly, create symlink in IS instance.
            list                List all project already pushed on remote gitlab
            status              Return all modified files in repository
            statusAll           Return all modified files in all repository