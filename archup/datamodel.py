import yaml
import schema
from typing import TextIO


_schema = schema.Schema({
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
        schema.Optional("content"): {str: bool},
        schema.Optional("layout"): {
            str: {
                str: str
            }
        }
    }]
})


class DataModel:
    def __init__(self, filestream):
        self._workspace = self._load_from_file(filestream)

    def _load_from_file(self, filestream: TextIO):
        workspace = yaml.safe_load(filestream)
        try:
            _schema.validate(workspace)
            return workspace
        except schema.SchemaError as e:
            raise e

    def diagrams(self):
        return self._workspace.get("diagrams", [])

    def datamodel(self):
        return self._workspace.get("datamodel", {})
