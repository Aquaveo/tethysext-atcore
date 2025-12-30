# How you use it

## VS Code

1. Install “Dev Containers” extension

2. Open repo → “Reopen in Container”

3. Once it boots, run:

```bash
bash .devcontainer/run-tests.sh
```

## CLI (optional)

If you use devcontainer CLI:

```bash
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . bash .devcontainer/run-tests.sh
```

## Udpate the content

1. Edit a file

2. Run

```bash
bash .devcontainer/run-tests.sh
```

3. See results immediately