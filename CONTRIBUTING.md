# Contributing

To set up a development copy:

```bash
python -m venv .venv
.venv/bin/pip install -e . -r requirements-dev.txt
```

Then turn on the repository's hooks:

```bash
git config --local core.hooksPath .githooks
```

The hooks stamp the current build version onto the commit subject and reject a
subject that ends up with more than one stamp.

## Checks

CI runs these three on Windows, macOS and Linux, against Python 3.10 and 3.13.
Run them before opening a pull request:

```bash
python -m ruff format --check .
python -m ruff check .
python -m unittest discover
```

The tests don't need any hardware, and a failure means a real bug.

## Commits

Conventional subjects: `type(scope): description`. Keep them to one line unless
the change needs context the subject can't hold.

## Releases

Tag `vYYYY.M.D.N` and push the tag. The release workflow validates the tag,
runs the checks, builds the Windows executable and the Python distributions,
and publishes them with notes built from the commit subjects since the last
release.

```bash
git tag v2026.8.19.0
git push origin v2026.8.19.0
```

A `-beta` suffix publishes a prerelease instead.
