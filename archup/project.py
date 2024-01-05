import os
import shutil
import yaml
from typing import TextIO

from .datamodel import Datamodel
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
        with open(self._config["datamodel"]["filename"]) as f:
            self.datamodel = Datamodel(f)

    def build(self):
        generator = MarkdownGenerator()
        with open(self.config["datamodel"]["markdown"], "w") as f:
            generator.generate(f, self.datamodel)
