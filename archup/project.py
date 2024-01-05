import os
import shutil


def create_new_project(name):
    project_dir = name
    template_dir = os.path.join(os.path.dirname(__file__), "template")
    shutil.copytree(template_dir, project_dir)
    print(f"Project created in {project_dir}")
