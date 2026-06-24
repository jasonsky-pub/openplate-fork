# Fork maintenance and release instructions

This fork publishes:

- PyPI package: `jsopfork`
- Installed CLI command: `openplate`
- Docker image: `jasonskypub/jsopfork`

## First: rebase this fork onto Comcast/OpenPlate

Before preparing a fork release, rebase this repository onto the latest upstream `main` so the fork keeps its extra commits on top of the current `Comcast/OpenPlate` history.
If a prior local release build temporarily changed `src/openplate/__init__.py`, restore that version file before rebasing so the rebase does not pick up a release-only edit.

```bash
cd /run/media/private/skyzero/random/local/jasonsky-pub/openplate-fork

git status --short --branch
git restore src/openplate/__init__.py

if git remote get-url upstream >/dev/null 2>&1; then
  git remote set-url upstream https://github.com/Comcast/OpenPlate
else
  git remote add upstream https://github.com/Comcast/OpenPlate
fi

git fetch --prune upstream
git branch backup/main-pre-upstream-rebase-$(date +%Y%m%d-%H%M) HEAD
git rebase upstream/main
```

If the rebase stops on conflicts, resolve them, then continue:

```bash
git add <resolved-files>
git rebase --continue
```

After the rebase completes, confirm the fork-specific commits still sit above `upstream/main`, then update GitHub with a lease-protected force push:

```bash
git log --oneline --decorate --graph -n 15
git push --force-with-lease origin main
```

## Choose and set the release version

Check the current published PyPI version and the local source version before choosing the next release:

```bash
cd /run/media/private/skyzero/random/local/jasonsky-pub/openplate-fork

python - <<'PY'
import json
import urllib.request
from pathlib import Path

with urllib.request.urlopen("https://pypi.org/pypi/jsopfork/json", timeout=20) as r:
    data = json.load(r)

print("latest_pypi_version =", data["info"]["version"])
print("all_pypi_versions =", ", ".join(sorted(data.get("releases", {}))))

for line in Path("src/openplate/__init__.py").read_text(encoding="utf-8").splitlines():
    if line.startswith("__version__ = "):
        print("local_source_version =", line.split("=", 1)[1].strip().strip('"'))
        break
PY
```

Then set the next release version and update the source version before building.
This version edit is temporary release state only: build from it, then restore it, and do not commit it.

```bash
export VERSION=X.Y.Z
export IMAGE=jasonskypub/jsopfork

python - <<'PY'
from pathlib import Path
import os
import re

version = os.environ["VERSION"]
path = Path("src/openplate/__init__.py")
text = path.read_text(encoding="utf-8")
text = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{version}"', text)
text = re.sub(r'__semver__ = "[^"]+"', f'__semver__ = "{version}"', text)
path.write_text(text, encoding="utf-8")
PY
```

## Build the Python package

```bash
rm -rf dist build *.egg-info
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
ls -1 dist/

# Do not commit the temporary version change used for the package build.
git restore src/openplate/__init__.py
```

## Publish the Python package to PyPI

```bash
export TWINE_USERNAME=__token__
read -rsp 'PyPI token: ' TWINE_PASSWORD && echo && export TWINE_PASSWORD
python -m twine upload dist/*
```

```bash
python -m pip install --upgrade jsopfork
openplate --version
```

## Build the Docker image

```bash
docker login
docker build -f src/docker/Dockerfile . \
  -t ${IMAGE}:latest \
  -t ${IMAGE}:${VERSION} \
  --build-arg SEMANTIC_VERSION=${VERSION}
```

## Publish the Docker image

```bash
docker push ${IMAGE}:${VERSION}
docker push ${IMAGE}:latest
```

## Notes

- Keep the PyPI package version and Docker `SEMANTIC_VERSION` aligned for each release.
- Publishing `jsopfork` does not reserve the PyPI name `openplate`.
- Installing this package still provides the `openplate` executable.
