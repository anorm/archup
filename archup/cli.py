import click

from .schema import load_workspace
# from .markdown import generate_markdown
from .project import create_new_project


@click.group()
def main():
    """
    Archup command line utility
    """

    pass


@main.command()
@click.argument("name")
def new(name):
    """
    Create a new architecture project
    """

    create_new_project(name)


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

    load_workspace(filename)
    print("OK")


@datamodel.command()
@click.argument("filename", type=click.File("r"))
def generate():
    """
    Generate markdown from a datamodel
    """
    pass


if __name__ == "__main__":
    main()
