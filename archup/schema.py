import yaml
import schema
from typing import TextIO


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


def load_workspace(filestream: TextIO):
    workspace = yaml.safe_load(filestream)
    try:
        workspace_schema.validate(workspace)
        return workspace
    except schema.SchemaError as e:
        raise e
