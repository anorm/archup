# Archup

## Getting started

Install `archup`:

```
pip3 install git+https://github.com/anorm/archup
```

Create a new project:

```
archup project new foo
```

Enter the project directory

```
cd foo
```

Build and run:

```
archup build
docker compose up
```

Navigate to http://127.0.0.1:8081


## Shell completion

### Bash

Add this to `~/.bashrc`:

```
eval "$(_ARCHUP_COMPLETE=bash_source archup)"
```

### Zsh

Add this to `~/.zshrc`:

```
eval "$(_ARCHUP_COMPLETE=zsh_source archup)"
```

## How it works

```mermaid
flowchart TD
    style datamodel fill:#cde,stroke:#000
    style generated_markdown fill:#cde,stroke:#000
    style workspace fill:#cde,stroke:#000
    style markdown fill:#cde,stroke:#000
    style build fill:#aea,stroke:#000
    style structurizr fill:#aea,stroke:#000
    style architecture fill:#ddd,stroke:#000

    datamodel[<b>src/datamodel.yaml</b>\n<i>Contains the conceptual data model</i>]
    build(archup build)
    generated_markdown[<b>src/docs/landscape/02-concepts.md</b>\n<i>Generated markdown</i>]
    workspace[<b>src/workspace.dsl</b>\n<i>Structurizr architecture description</i>]
    markdown[<b>src/docs/*.md</b>\n<i>Markdown files containing\ngeneral documentation</i>]
    structurizr(structurizr)
    architecture[<b>Architecture documentation</b>\n<i>A complete documentation site containing\ndocumentation, diagrams and the conceptual\ndata model</i>]

    datamodel --> build
    build --> generated_markdown
    generated_markdown --> structurizr
    markdown --> structurizr
    workspace --> structurizr
    structurizr --> architecture
```
