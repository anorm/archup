#!env/bin/python
import argparse
import io
import yaml
import requests
import schema
import sys
import traceback


workspace_schema = schema.Schema({
    "datamodel": {
        "description": str,
        "entities": {
            str: {
                "name": str,
                schema.Optional("aka"): [str],
                schema.Optional("shortDescription"): str,
                schema.Optional("description"): str,
                schema.Optional("properties"): {
                    str: {
                        schema.Optional("description"): str,
                        schema.Optional("type"): str,
                        schema.Optional("values"): [str]
                    }
                },
                schema.Optional("examples"): [str],
                schema.Optional("relations"): [{
                    "to": str,
                    schema.Optional("description"): str,
                    schema.Optional("properties"): {
                        str: {
                        }
                    }
                }],
                schema.Optional("tags"): [str]
            }
        }
    },
    "diagrams": [{
        "name": str,
        "type": schema.Or("overview", "details"),
        schema.Optional("description"): str,
        schema.Optional("whitelist"): [str],
        schema.Optional("blacklist"): [str],
        schema.Optional("layout"): {
            str: {
                str: schema.Or("L", "R", "U", "D")
            }
        }
    }]
})


def load_workspace(filename: str):
    with open(filename) as f:
        workspace = yaml.safe_load(f)
    try:
        workspace_schema.validate(workspace)
        return workspace
    except schema.SchemaError as e:
        raise e


def writeline(stream, str=""):
    stream.write(str)
    stream.write("\n")


def reverse_direction(dir):
    if dir == "L":
        return "R"
    if dir == "R":
        return "L"
    if dir == "U":
        return "D"
    if dir == "D":
        return "U"
    return dir


download_cache = {}
def plantuml_include(stream, url):
    global download_cache
    if not url in download_cache:
        r = requests.get(url, allow_redirects=True)
        content = io.StringIO()
        for line in r.content.decode("utf-8").splitlines():
            if line.startswith("!include http"):
                _, suburl = line.split()
                plantuml_include(content, suburl)
            else:
                writeline(content, line)
        download_cache[url] = content.getvalue()
    writeline(stream)
    writeline(stream, download_cache[url])
    writeline(stream)


def generate_diagram(workspace, whitelist=None, blacklist=None, internal=None, external=None, layout={}):
    ret = io.StringIO()
    writeline(ret, "@startuml")
    plantuml_include(ret, "https://raw.githubusercontent.com/anorm/plantuml-ext/main/datamodelling.puml")
    #writeline(ret, "title Data model overview")

    # Output all entities
    visibleEntities = []
    for id, entity in workspace.get("datamodel", {}).get("entities", {}).items():
        whitelisted = False
        if whitelist:
            if id in whitelist:
                whitelisted = True
            else:
                for tag in entity.get("tags", []):
                    if f"#{tag}" in whitelist:
                        whitelisted = True
            if not whitelisted:
                continue

        if blacklist:
            blacklisted = False
            if id in blacklist:
                blacklisted = True
            else:
                for tag in entity.get("tags", []):
                    if f"#{tag}" in blacklist:
                        blacklisted = True
                        break
            if blacklisted:
                continue

        isInternal = True
        if internal and not id in internal:
            isInternal = False
        if external and id in external:
            isInternal = False
        visibleEntities.append(id)
        prefix = "Entity" if isInternal else "Entity_Ext"
        name = entity.get("name", id)
        aka = entity.get("aka", [])
        akaString = "\\n<size:10>(aka " + " / ".join(aka) + ")" if aka else ""
        shortDescription = entity.get("shortDescription", "")
        examples = ", ".join([f"'{e}'" for e in entity.get("examples", [])])
        properties = entity.get("properties", {})
        ret.write(f'{prefix}({id}, "{name}{akaString}", "{shortDescription}", $example="{examples}") {{\n')
        for property,propertyAttr in properties.items():
            writeline(ret, f'  Property("{property}")')
        writeline(ret, "}")
        writeline(ret)

    # Output all relations
    for id, entity in workspace.get("datamodel", {}).get("entities", {}).items():
        relations = entity.get("relations", [])
        for relation in relations:
            description = relation.get("description", "?")
            to = relation["to"]
            properties = relation.get("properties", [])
            propertyString = "|".join( [p for p in properties] )
            if not id in visibleEntities or not to in visibleEntities:
                continue
            direction = ""
            if f"{to}-{id}" in layout:
                direction = "_"+reverse_direction(layout[f"{to}-{id}"])
            if f"{id}-{to}" in layout:
                direction = "_"+layout[f"{id}-{to}"]

            writeline(ret, f'Rel{direction}({id}, "{description}", {to}, {propertyString})')

    writeline(ret, "@enduml")
    return ret.getvalue()


def find_related_entities(workspace, target):
    ret = set()
    for id, entity in workspace.get("datamodel", {}).get("entities", {}).items():
        relations = entity.get("relations", [])
        for relation in relations:
            to = relation["to"]
            if target == id:
                ret.add(to)
            if target == to:
                ret.add(id)
    return list(ret)


def expand_tags(workspace, elements):
    if not elements:
        return []
    ret = set()
    for element in elements:
        if element.startswith("#"):
            tag = element[1:]
            for entity_id,entity in workspace.get("datamodel", {}).get("entities", {}).items():
                if tag in entity.get("tags", []):
                    ret.add(entity_id)
        else:
            ret.add(element)

    return list(ret)

def generate_markdown_overview(workspace, diagram):
    name = diagram.get("name", "Overview")
    description = diagram.get("description", "")
    whitelist = diagram.get("whitelist", None)
    blacklist = diagram.get("blacklist", None)
    layout = diagram.get("layout", {}).get("overview", {})
    ret = io.StringIO()
    writeline(ret, f"### {name}")
    writeline(ret)
    writeline(ret, "```plantuml")
    internal = expand_tags(workspace, whitelist)

    whitelist = list(internal)
    for entity_id in internal:
        whitelist.extend(find_related_entities(workspace, entity_id))
    writeline(ret, generate_diagram(workspace, internal=internal, whitelist=list(set(whitelist)), blacklist=blacklist, layout=layout))
    writeline(ret, "```")
    writeline(ret)
    if description:
        writeline(ret, description)
        writeline(ret)
    return ret.getvalue()


def generate_markdown_details(workspace, diagram, entity_id):
    ret = io.StringIO()
    entity = workspace.get("datamodel", {}).get("entities", {}).get(entity_id, {})
    name = diagram.get("name", entity_id)
    layout = diagram.get("layout", {}).get(entity_id, {})
    entity_name = entity.get("name", entity_id)
    shortDescription = entity.get("shortDescription", "")
    description = entity.get("description", "")
    examples = ", ".join([f"'{e}'" for e in entity.get("examples", [])])
    properties = entity.get("properties", {})
    writeline(ret, f"### {name}: {entity_name}")
    writeline(ret)
    writeline(ret, "```plantuml")
    whitelist = [entity_id]
    whitelist.extend(find_related_entities(workspace, entity_id))
    writeline(ret, generate_diagram(workspace, internal=[entity_id], whitelist=whitelist, layout=layout))
    writeline(ret, "```")
    writeline(ret)
    if description:
        writeline(ret, description)
        writeline(ret)
    return ret.getvalue()



def generate_markdown(workspace) -> str:
    ret = io.StringIO()
    writeline(ret, "<!-- THIS FILE IS GENERATED -->")
    writeline(ret, "## Concepts")
    writeline(ret)
    diagrams = workspace.get("diagrams", [])
    for diagram in diagrams:
        diagram_type = diagram.get("type", "overview")

        if diagram_type == "overview":
            writeline(ret, generate_markdown_overview(workspace, diagram))
        elif diagram_type == "details":
            entities = workspace.get("datamodel", {}).get("entities", {}).keys()
            whitelist = diagram.get("whitelist", [])
            blacklist = diagram.get("blacklist", [])
            for entity in entities:
                if whitelist and not entity in whitelist:
                    continue
                if blacklist and entity in blacklist:
                    continue
                writeline(ret, generate_markdown_details(workspace, diagram, entity))

    return ret.getvalue()


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("workspace")
        args = parser.parse_args()

        workspace = load_workspace(args.workspace)

        markdown = generate_markdown(workspace)
        print(markdown)
    except Exception as e:
        print("## Concepts")
        print("")
        print("### ERROR")
        print("")
        print('<pre style="background-color:red; color: white">')
        print(e)
        print('</pre>')
        print('<pre style="background-color:yellow; color: black">')
        traceback.print_exc(file=sys.stdout)
        print('</pre>')


if __name__ == "__main__":
    main()
