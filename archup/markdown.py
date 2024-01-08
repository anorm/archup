import io
import requests

from .datamodel import DataModel

class MarkdownGenerator:
    def __init__(self):
        self._download_cache = {}

    def _writeline(self, stream, str=""):
        stream.write(str)
        stream.write("\n")

    def _reverse_direction(self, dir):
        if dir == "L":
            return "R"
        if dir == "R":
            return "L"
        if dir == "U":
            return "D"
        if dir == "D":
            return "U"
        return dir

    def _plantuml_include(self, stream, url):
        if url not in self._download_cache:
            r = requests.get(url, allow_redirects=True)
            content = io.StringIO()
            for line in r.content.decode("utf-8").splitlines():
                if line.startswith("!include http"):
                    _, suburl = line.split()
                    self._plantuml_include(content, suburl)
                else:
                    self._writeline(content, line)
            self._download_cache[url] = content.getvalue()
        self._writeline(stream)
        self._writeline(stream, self._download_cache[url])
        self._writeline(stream)

    def _generate_diagram(self, workspace: DataModel, whitelist=None,
                          blacklist=None, internal=None, external=None,
                          layout={}):
        ret = io.StringIO()
        self._writeline(ret, "@startuml")
        self._plantuml_include(ret, "https://raw.githubusercontent.com/anorm/plantuml-ext/main/datamodelling.puml")
        # writeline(ret, "title Data model overview")

        # Output all entities
        visibleEntities = []
        for id, entity in workspace.datamodel().get("entities", {}).items():
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
            if internal and id not in internal:
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
            for property, propertyAttr in properties.items():
                self._writeline(ret, f'  Property("{property}")')
            self._writeline(ret, "}")
            self._writeline(ret)

        # Output all relations
        for id, entity in workspace.datamodel().get("entities", {}).items():
            relations = entity.get("relations", [])
            for relation in relations:
                description = relation.get("description", "?")
                to = relation["to"]
                properties = relation.get("properties", [])
                propertyString = "|".join([p for p in properties])
                if id not in visibleEntities or to not in visibleEntities:
                    continue
                direction = ""
                if f"{to}-{id}" in layout:
                    direction = "_"+self._reverse_direction(layout[f"{to}-{id}"])
                if f"{id}-{to}" in layout:
                    direction = "_"+layout[f"{id}-{to}"]

                self._writeline(ret, f'Rel{direction}({id}, "{description}", {to}, {propertyString})')

        self._writeline(ret, "@enduml")
        return ret.getvalue()

    def _find_related_entities(self, workspace, target):
        ret = set()
        for id, entity in workspace.datamodel().get("entities", {}).items():
            relations = entity.get("relations", [])
            for relation in relations:
                to = relation["to"]
                if target == id:
                    ret.add(to)
                if target == to:
                    ret.add(id)
        return list(ret)

    def _expand_tags(self, workspace, elements):
        if not elements:
            return []
        ret = set()
        for element in elements:
            if element.startswith("#"):
                tag = element[1:]
                for entity_id, entity in workspace.datamodel().get("entities", {}).items():
                    if tag in entity.get("tags", []):
                        ret.add(entity_id)
            else:
                ret.add(element)

        return list(ret)

    def _generate_markdown_overview(self, workspace, diagram):
        name = diagram.get("name", "Overview")
        description = diagram.get("description", "")
        whitelist = diagram.get("whitelist", None)
        blacklist = diagram.get("blacklist", None)
        layout = diagram.get("layout", {}).get("overview", {})
        ret = io.StringIO()
        self._writeline(ret, f"### {name}")
        self._writeline(ret)
        self._writeline(ret, "```plantuml")
        internal = self._expand_tags(workspace, whitelist)

        whitelist = list(internal)
        for entity_id in internal:
            whitelist.extend(self._find_related_entities(workspace, entity_id))
        self._writeline(ret,
                        self._generate_diagram(workspace,
                                               internal=internal,
                                               whitelist=list(set(whitelist)),
                                               blacklist=blacklist,
                                               layout=layout))
        self._writeline(ret, "```")
        self._writeline(ret)
        if description:
            self._writeline(ret, description)
            self._writeline(ret)
        return ret.getvalue()

    def _generate_markdown_details(self, workspace, diagram, entity_id):
        ret = io.StringIO()
        entity = workspace.datamodel().get("entities", {}).get(entity_id, {})
        name = diagram.get("name", entity_id)
        layout = diagram.get("layout", {}).get(entity_id, {})
        entity_name = entity.get("name", entity_id)
        # shortDescription = entity.get("shortDescription", "")
        description = entity.get("description", "")
        # examples = ", ".join([f"'{e}'" for e in entity.get("examples", [])])
        # properties = entity.get("properties", {})
        self._writeline(ret, f"### {name}: {entity_name}")
        self._writeline(ret)
        self._writeline(ret, "```plantuml")
        whitelist = [entity_id]
        whitelist.extend(self._find_related_entities(workspace, entity_id))
        self._writeline(ret,
                        self._generate_diagram(workspace,
                                               internal=[entity_id],
                                               whitelist=whitelist,
                                               layout=layout))
        self._writeline(ret, "```")
        self._writeline(ret)
        if description:
            self._writeline(ret, description)
            self._writeline(ret)
        return ret.getvalue()

    def generate(self, fs, workspace: DataModel) -> str:
        self._writeline(fs, "<!-- THIS FILE IS GENERATED -->")
        self._writeline(fs, "## Concepts")
        self._writeline(fs)
        diagrams = workspace.diagrams()
        for diagram in diagrams:
            diagram_type = diagram.get("type", "overview")

            if diagram_type == "overview":
                self._writeline(fs,
                                self._generate_markdown_overview(workspace,
                                                                 diagram))
            elif diagram_type == "details":
                entities = workspace.datamodel().get("entities", {}).keys()
                whitelist = diagram.get("whitelist", [])
                blacklist = diagram.get("blacklist", [])
                for entity in entities:
                    if whitelist and entity not in whitelist:
                        continue
                    if blacklist and entity in blacklist:
                        continue
                    self._writeline(fs,
                                    self._generate_markdown_details(workspace,
                                                                    diagram,
                                                                    entity))
