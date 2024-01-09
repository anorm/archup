workspace {
    !identifiers hierarchical
    !impliedRelationships true

    name "Foo system landscape"
    description "All Foo software systems"

    !docs docs/landscape/

    model {
        user = person "User"
        mySoftwareSystem = softwareSystem "My Software System"

        user -> mySoftwareSystem "Uses"
    }

    views {
        systemLandscape "landscape" {
            include *
            autoLayout
        }

        systemContext mySoftwareSystem "Diagram1" {
            include *
        }

        styles {
            element "Database" {
                shape Cylinder
            }
            element "External" {
                background #999999
                color #ffffff
            }
        }

        theme default
    }

    !plugin plantuml.PlantUMLEncoderPlugin
}
