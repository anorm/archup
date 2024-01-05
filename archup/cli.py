import click

from .datamodel import Datamodel
# from .markdown import generate_markdown
from .project import create_new_project, Project


class OrderCommands(click.Group):
    def list_commands(self, ctx: click.Context) -> list[str]:
        return list(self.commands)


@click.group(cls=OrderCommands)
def main():
    """
    Archup command line utility
    """

    pass


@main.group()
def project():
    """
    Commands to work with projects
    """
    pass


@project.command()
@click.argument("name")
@click.option("-f", "--force",
              is_flag=True,
              help="Create the project even though the directory already "
                   "exists")
def new(name, force):
    """
    Create a new architecture project
    """

    create_new_project(name, force)


@main.group()
def datamodel():
    """
    Commands to work with a YAML datamodel
    """

    pass


@datamodel.command()
@click.argument("filename", type=click.File("r"))
def validate(filename):
    """
    Validates a datamodel workspace YAML file
    """

    Datamodel(filename)
    print("OK")


@main.command()
@click.option("-p", "--project", "project_filename",
              type=click.File("r"),
              default="./archup.conf", show_default=True)
def build(project_filename):
    """
    Build project
    """
    p = Project(project_filename)
    p.build()


if __name__ == "__main__":
    main()
