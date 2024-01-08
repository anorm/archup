import os
import shutil
import yaml
from typing import TextIO

from .datamodel import DataModel
from .markdown import MarkdownGenerator


def _verbose_copy(src, dst):
    print(f"  - {dst}")
    shutil.copyfile(src, dst)


def create_new_project(name, force):
    """
    Creates a new project directory on disk by copying
    and possibly templating files from the distributed
    template files contained in this module
    """
    project_dir = name
    template_dir = os.path.join(os.path.dirname(__file__), "template")
    print("Creating project")
    shutil.copytree(template_dir, project_dir,
                    dirs_exist_ok=force,
                    copy_function=_verbose_copy)
    print(f"Project created in {project_dir}")

    # TODO Template expansion


class Project:
    def __init__(self, project_file: TextIO):
        self._config = yaml.safe_load(project_file)
        self.name = self._config.get("name", "Unnamed")
        self.project_dir = os.path.dirname(project_file.name)

        filename = self._resolve_path(self._config["datamodel"]["filename"])
        with open(filename) as f:
            self.datamodel = DataModel(f)

    def _resolve_path(self, relative_path):
        """
        Resolves a path relative to the project configuratino file
        """
        return os.path.join(self.project_dir, relative_path)

    def build(self):
        generator = MarkdownGenerator()
        filename = self._resolve_path(self._config["datamodel"]["markdown"])
        with open(filename, "w") as f:
            generator.generate(f, self.datamodel)
