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
        def _inner(d):
            if d == "L":
                return "R"
            if d == "R":
                return "L"
            if d == "U":
                return "D"
            if d == "D":
                return "U"
            return d
        return "".join(map(_inner, dir))

    def _plantuml_include(self, stream, file_or_url):
        """
        Inlude the contents of a file or url into the plantuml stream,
        caching any includes that are downloaded.
        """
        # Open a stream to the source
        if file_or_url.startswith(("https://", "http://")):
            if file_or_url not in self._download_cache:
                r = requests.get(file_or_url, allow_redirects=True)
                self._download_cache[file_or_url] = r.content.decode("utf-8")
            include_stream = io.StringIO(self._download_cache[file_or_url])
        else:
            include_stream = open(file_or_url, "r", encoding="utf-8")

        # Iterate through the included file, recursing into embedded includes
        for line in include_stream.read().splitlines():
            if line.startswith("!include "):
                _, suburl = line.split()
                self._plantuml_include(stream, suburl)
            elif line.startswith(("@startuml", "@enduml")):
                # skip the file markers
                # TODO: decide if we should only include what's inside the
                #       markers
                pass
            else:
                self._writeline(stream, line)

        include_stream.close()

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
                direction = "-D->"
                if f"{to}-{id}" in layout:
                    direction = self._reverse_direction(layout[f"{to}-{id}"])
                if f"{id}-{to}" in layout:
                    direction = layout[f"{id}-{to}"]

                self._writeline(ret, f'Rel_({id}, "{description}", {to}, "{propertyString}", "{direction}")')

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
        # properties = entity.get("properties", {})

        if diagram.get("content", {}).get("headingPrefix", False):
            prefix = f"{name}: "
        else:
            prefix = ""
        akas = ", ".join([f'"_{a}_"' for a in entity.get("aka", [])])
        if akas and diagram.get("content", {}).get("aka", False):
            self._writeline(ret, f"### {prefix}{entity_name} <small>(aka {akas})</small>")
        else:
            self._writeline(ret, f"### {prefix}{entity_name}")
        self._writeline(ret)

        examples = entity.get("examples", [])
        if examples and diagram.get("content", {}).get("examples", False):
            self._writeline(ret, "Examples:")
            self._writeline(ret)
            for example in examples:
                self._writeline(ret, f'* "_{example}_"')
            self._writeline(ret)

        if diagram.get("content", {}).get("diagrams", False):
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

        description = entity.get("description", "")
        if not description:
            description = entity.get("shortDescription", "")
        if description and diagram.get("content", {}).get("description", False):
            self._writeline(ret, description)
            self._writeline(ret)

        properties = entity.get("properties", [])
        if properties and diagram.get("content", {}).get("properties", False):
            self._writeline(ret, "Properties:")
            self._writeline(ret)
            self._writeline(ret, "| Name | Type | Description |")
            self._writeline(ret, "|------|------|-------------|")
            for name, prop in properties.items():
                desc = prop.get("description", "")
                _type = prop.get("type", "")
                values = prop.get("values", [])
                if values:
                    _type = _type + "(" + ", ".join(values) + ")"
                self._writeline(ret, f"| {name} | {_type} | {desc} |")
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
