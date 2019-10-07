import yaml

from pocr.constants import Paths
from pocr.exceptions.project_exceptions import ProjectNameAlreadyExists


class Project(yaml.YAMLObject):
    yaml_tag = u'!Project'

    def __init__(self, project_path=None, name=None, conda_name=None, vcs=None, python=None):
        self.project_path = project_path
        self.name = name
        self.conda_name = conda_name
        self.vcs = vcs
        self.python = python

    def __repr__(self):
        return "{}\t{}\t{}\t{}".format(self.name, self.conda_name, self.vcs, self.python)

    # STATIC

    @staticmethod
    def load_projects():
        with open(Paths.PROJECT_FILE_PATH, 'r') as f:
            return yaml.load_all(f, Loader=yaml.Loader)

    @staticmethod
    def save_projects(projects: list):
        with open(Paths.PROJECT_FILE_PATH, 'r') as f:
            yaml_dict = yaml.safe_load(f) or {}
        yaml_dict.update(projects)
        with open(Paths.PROJECT_FILE_PATH, 'w') as f:
            yaml.dump(yaml_dict, f)

    @staticmethod
    def append_project(project):
        yaml_dict = Project.project_exists(project.name)
        yaml_dict[project.name] = project
        with open(Paths.PROJECT_FILE_PATH, 'a') as f:
            yaml.dump(yaml_dict, f)

    @staticmethod
    def project_exists(project_name: str):
        with open(Paths.PROJECT_FILE_PATH, 'r') as f:
            yaml_dict = yaml.load(f, Loader=yaml.Loader)
        if type(yaml_dict) is not dict:
            return {}
        if project_name in yaml_dict:
            raise ProjectNameAlreadyExists()
        return yaml_dict

    # GETTERS / SETTERS

    @property
    def project_path(self):
        return self._project_path

    @project_path.setter
    def project_path(self, value):
        self._project_path = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def conda_name(self):
        return self._conda_name

    @conda_name.setter
    def conda_name(self, value):
        self._conda_name = value

    @property
    def vcs(self):
        return self._vcs

    @vcs.setter
    def vcs(self, value):
        self._vcs = value

    @property
    def python(self):
        return self._python

    @python.setter
    def python(self, value):
        self._python = value
