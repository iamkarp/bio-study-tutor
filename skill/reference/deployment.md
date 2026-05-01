# Deployment to shinyapps.io — recipe with all the gotchas

The Bio app deployed and broke twice during initial setup. Here's the recipe that works.

## Prerequisites

1. A shinyapps.io account (free tier OK).
2. `rsconnect-python` installed: `pip3 install rsconnect-python`.
3. Account configured locally:
   ```
   rsconnect add --account <name> --name <name> --token <TOKEN> --secret <SECRET>
   ```
4. Verify: `rsconnect list` shows your account.

## Recipe

### 1. Pin Python to 3.11

```bash
echo "3.11" > .python-version
```

shinyapps.io does **not** support Python 3.14. Supported: 3.8–3.11.

### 2. Slim requirements.txt

If `pip freeze` was used, the requirements.txt has 500+ packages and slows deployment to a crawl. Replace with the minimal set:

```
shiny>=1.5.0
pyvis>=0.3.2
requests>=2.31.0
pyyaml>=6.0
markdown>=3.5
networkx>=3.1
edge-tts>=6.1.0
```

Add `python-pptx`, `python-docx`, `jsonschema` only if the deployed app needs them at runtime. The print rebuild button does need `python-pptx` etc. through `tools/build_print_version.py` — adjust accordingly.

### 3. Generate the manifest

```bash
rsconnect write-manifest shiny . --overwrite --entrypoint app
```

The `--entrypoint app` is critical. shinyapps.io will `import app` looking for `app.app` (the App instance). The package shim `app/__init__.py` exposes it.

### 4. Patch the manifest

```python
import json
m = json.load(open('manifest.json'))
m['python']['version'] = '3.11.0'
# Strip large source binaries
for f in [k for k in m['files'] if k.endswith(('.pptx', '.docx'))]:
    del m['files'][f]
json.dump(m, open('manifest.json', 'w'), indent=2)
```

### 5. Configure .rscignore

```
Chapter*.pptx
Chapter*.PPTX
Study Guide*.docx
Study Guide*.DOCX
raw/*.pptx
raw/*.docx
__pycache__/
*.pyc
.git/
.DS_Store
rsconnect-python/
```

### 6. Deploy

```bash
rsconnect deploy manifest manifest.json --name <account> --title <App_Title> --new
```

For subsequent deploys, drop `--new` to update in place.

## Common gotchas (and fixes)

### Gotcha 1: "Failed to find application object in module 'app'"

**Symptom**: deploy succeeds but the app crashes on first request with this error.

**Cause**: shinyapps.io imports `app` as a Python package. If both `app.py` (top-level) and `app/__init__.py` exist, the package wins and Python imports the (possibly empty) `__init__.py`.

**Fix**: put the app loader in `app/__init__.py` itself:
```python
import importlib.util as _u
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_DIR))

_spec = _u.spec_from_file_location("_main", _DIR / "app.py")
_mod = _u.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

app = _mod.app
```

### Gotcha 2: Print/graph routes 404 on deployed app

**Symptom**: `/print-static/...` or `/graph-static/...` links return 404 on shinyapps.io but work locally.

**Cause**: shinyapps.io serves your app under a sub-path like `/bio_study_tutor/`. Absolute paths (`href="/print-static/..."`) resolve to the domain root (`karpeles.shinyapps.io/print-static/...`) and miss the sub-path.

**Fix**: use **relative** paths everywhere:
```python
# Good
ui.tags.a("Open print", href="print-static/study-guide.html", target="_blank")
ui.tags.iframe(src=f"graph-static/{filename}")

# Bad (breaks on shinyapps.io)
ui.tags.a("Open print", href="/print-static/study-guide.html", target="_blank")
```

### Gotcha 3: Manifest checksum mismatch on redeploy

**Symptom**: redeploy fails with "Manifest file <path> checksum mismatch".

**Cause**: you edited the source after the manifest was written. The manifest contains hashes of every file.

**Fix**: regenerate the manifest before each redeploy:
```bash
rsconnect write-manifest shiny . --overwrite --entrypoint app
# then re-patch python version + strip pptx/docx as in step 4
rsconnect deploy manifest manifest.json --name <account> --title <App_Title>
```

### Gotcha 4: Free tier sleeps after 15 minutes

**Symptom**: first request after a quiet period takes 15-20 seconds.

**Cause**: shinyapps.io free tier puts containers to sleep. First wakeup spins up the Python env, imports modules, loads wiki/KG into memory.

**Fix**: this is intrinsic to free tier. To eliminate, upgrade to Basic ($9/mo). For free, mention it in your video/docs so users don't think the app is broken.

### Gotcha 5: API keys in deployment

**Don't** ship `.env` to shinyapps.io if it contains secrets. Use the dashboard:

1. Open your app at `<account>.shinyapps.io/<app>`
2. Settings → Environment variables → Add `OPENROUTER_API_KEY`
3. The deployed app reads from `os.environ` first, then falls back to `.env` (which won't be present)

For private/personal study apps where you control the deployment, including `.env` is acceptable but list it in `.rscignore` if you ever push to git.
