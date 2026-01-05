# How you use it

## VS Code

1. Install “Dev Containers” extension

2. Open repo → “Reopen in Container”

3. Once it boots, run:

```bash
bash ./test.sh "$TETHYS_MANAGE"
```

## CLI (optional)

If you use devcontainer CLI:

```bash
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . sh -lc './test.sh "$TETHYS_MANAGE"'
```

## Udpate the content

1. Edit a file

2. Run

```bash
devcontainer exec --workspace-folder . sh -lc './test.sh "$TETHYS_MANAGE"'
```

3. See results immediately