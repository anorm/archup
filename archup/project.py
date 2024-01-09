import jinja2
import os
import requests
import shutil
import yaml
from typing import TextIO

from .datamodel import DataModel
from .markdown import MarkdownGenerator


class TemplatingCopyer:
    def __init__(self, values, template_suffix=".tmpl"):
        self.values = values
        self.template_suffix = template_suffix

    def verbose_copy(self, src: str, dst: str):
        if src.endswith(self.template_suffix):
            real_dst = dst.removesuffix(self.template_suffix)
            print(f"  - {real_dst} [T]")
            with open(src, encoding="utf-8") as f:
                template = jinja2.Template(f.read())
            with open(real_dst, "w", encoding="utf-8") as f:
                f.write(template.render(self.values))
        else:
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

    values = {
        "project": {
            "name": name
        }
    }
    copyer = TemplatingCopyer(values)
    shutil.copytree(template_dir, project_dir,
                    dirs_exist_ok=force,
                    copy_function=copyer.verbose_copy)

    remote_files = {".structurizr-plugins/": "https://github.com/anorm/structurizr-examples/raw/main/dsl/plantuml-and-mermaid/dsl/plugins/plugin-1.0-SNAPSHOT.jar"}
    for path, url in remote_files.items():
        local_filename = os.path.join(project_dir, path, url.split('/')[-1])
        print(f"  - {local_filename}")
        os.makedirs(os.path.join(project_dir, path), exist_ok=True)
        r = requests.get(url, stream=True)
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    print(f"Project created in {project_dir}")


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
