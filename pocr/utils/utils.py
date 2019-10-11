import os
import shutil
import subprocess
import json
import sys

from PyInquirer import prompt
from github import Github, GithubException, UnknownObjectException

from pocr.conf.config import Config
from pocr.project import Project
from pocr.utils.constants import Texts, Structures, Paths
from pocr.utils.exceptions import CondaAlreadyExists, ProjectNameAlreadyExists, RepoAlreadyExists


def get_object_from_list_by_name(filter_str, input_list):
    return next(filter(lambda x: filter_str in x.name, input_list), None)


def build_question(interface_type: str, message: str, name: str, iter_list: list):
    question = {
        'type': interface_type,
        'name': name,
        'message': message,
    }

    if interface_type == 'list':
        if type(iter_list[0]) == str:
            choices = iter_list
        else:
            choices = [item.name for item in iter_list]
        question['choices'] = choices

    return question


def ask_questions(types: list, messages: list, names: list, iter_list: list):
    questions = [build_question(t, m, n, l) for t, m, n, l in zip(types, messages, names, iter_list)]
    return prompt(questions)


def check_env_exists(name):
    # execute command
    envs = subprocess.check_output(['conda', 'env', 'list', '--json']).decode('utf-8')
    # create a dict
    envs = json.loads(envs.replace('\n', ''))['envs']
    # just get the basename of the conda env path
    envs = [os.path.basename(e) for e in envs]
    if name in envs:
        raise CondaAlreadyExists()


def dialog_username_password():
    # username and password
    username_password = ask_questions(['input', 'password'],
                                      [Texts.USERNAME_TEXT, Texts.PASSWORD_TEXT],
                                      ['username', 'password'],
                                      [[], []])
    username = username_password['username']
    password = username_password['password']
    github = Github(login_or_token=username, password=password)
    return github, username, password


def user_password_dialog(error=None):
    if error is None:
        error = {}
    try:
        if not error:
            github, username, password = dialog_username_password()
        else:
            if error['key'] == 0:
                print(error['message'])
                github, username, password = dialog_username_password()
                auth = github.get_user().create_authorization(scopes=Structures.AUTH_SCOPES,
                                                              note='pocr')

            if error['key'] == 1:
                print(error['message'])
                github, username, password = error['cred']
                tfa = ask_questions(['input'], [Texts.TFA_TEXT], ['tfa'], [[]])['tfa']
                auth = github.get_user().create_authorization(scopes=Structures.AUTH_SCOPES,
                                                              onetime_password=tfa,
                                                              note='pocr')

            sec = auth.token or ""
            github = Github(sec)

        # to test if the github object has a correct authentication
        github.get_user().id

        Config.getInstance().username = username
        Config.getInstance().sec = sec
    except GithubException as e:
        error_msg = {}
        if e.status == 422:
            error_msg['message'] = Texts.TOKEN_ALREADY_EXISTS_TEXT
            error_msg['key'] = 1
        if e.status == 401:
            if e.data['message'] == 'Bad credentials':
                error_msg['key'] = 0
            else:
                error_msg['key'] = 1
            error_msg['message'] = e.data['message']
        error_msg['cred'] = (github, username, password)
        return error_msg


def duplication_check(project_name, github_user, git_check=True, conda_check=True):
    # Check if project name already exists
    try:
        # project check
        Project.project_exists(project_name)
        if git_check:
            # github check
            check_repo_exists(project_name, github_user)
        if conda_check:
            # conda check
            check_env_exists(project_name)
    except ProjectNameAlreadyExists:
        print("Project name is already in use")
        sys.exit(1)
    except RepoAlreadyExists:
        print(
            "The Github user {} already has a repository named {}".format(Config.getInstance().username, project_name))
        sys.exit(1)
    except CondaAlreadyExists:
        print("There exists already a conda environment named {}".format(project_name))
        sys.exit(1)


def check_repo_exists(name, github_user):
    try:
        github_user.get_repo(name)
    except UnknownObjectException:
        return
    raise RepoAlreadyExists


def create_files_folders():
    # create folder
    os.mkdir(Paths.POCR_FOLDER)

    # create conf file
    open(Paths.CONF_FILE_PATH, 'a').close()
    # Config.getInstance().write_into_yaml_file(Constants.CONF_FILE_PATH, **Constants.CONF_DICT)
    # project file {'TestProject': {infos}}
    open(Paths.PROJECT_FILE_PATH, 'a').close()


def check_requirements():
    if shutil.which("conda") is None:
        raise Exception(
            "Conda is not installed! https://docs.conda.io/projects/conda/en/latest/user-guide/install/")
    if sys.version_info[0] < 3 and sys.version_info[1] < 5:
        raise Exception("The default python version is lower then 3.5. Please update!")


def first_usage():
    """
    Checks if the pocr config file is existing.
    If this file is existing we know that it is not first usage and so the function returns false.
    Else vise versa.

    :return:
        boolean: if its first usage or not
    """
    return not os.path.exists(Paths.POCR_FOLDER)