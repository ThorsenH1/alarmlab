# Verification record

The distributed prototype has been exercised through the command-line pipeline, its numerical tests, the executed walkthrough and a local Chromium browser.

## Checks

| Area | Check | Evidence |
|---|---|---|
| Numerical pipeline | Generate data, fit detectors, calibrate, evaluate and export | artifacts/manifest.json and RESULTS.md |
| Data separation | Entire episodes and condition recipes stay in one partition | tests/test_core.py |
| Causality | Future inputs cannot change past features or states | tests/test_core.py |
| Missing evidence | All-missing and unsupported inputs produce REVIEW | tests/test_core.py |
| Alarm timing | Persistence, hysteresis, resets and no backdated detection | tests/test_core.py |
| Provenance | Source/data hashes and metric bookkeeping agree | scripts/verify_artifacts.py |
| Walkthrough | Six notebook cells execute against saved artifacts | notebooks/01_research_walkthrough.ipynb |
| Interface | 63 scenario/domain/model combinations match saved states at the checked timestamp | artifacts/browser_verification.json |
| Interaction | Playback, truth overlay, local log and JSON export | tests/browser.spec.cjs |
| Layout and offline use | Mobile views fit; no JavaScript errors or HTTP requests | Browser verification output and demo screenshots |

The Python suite contains 18 tests. The browser suite contains eight grouped checks, including the 63 state comparisons.

## Running the checks

From an installed source checkout:

```text
python -m unittest discover -s tests -v
python run.py all
python scripts/create_notebook.py
python scripts/verify_artifacts.py
npm ci
npx playwright install chromium
npm run test:browser
```

On Windows, the helper supports Demo, Setup, Run and Test. If interpreter discovery is affected by an isolated environment, supply its absolute path using -PythonPath.

GitHub Actions is configured to run the numerical pipeline on Python 3.11 and 3.13, and browser checks in a separate job. Its actual status is visible in the repository's Actions tab; configuration alone is not evidence that a remote run passed.

## Interpretation

These checks support correctness of the implemented data and software flows. They do not validate the simulator as a physical plant, establish medical or nuclear suitability, or demonstrate improved human decisions.

The measured-data tasks use one rig and a particular condition split. The stress results intentionally include the detector's observed failure. Neither successful tests nor good in-domain metrics remove those limitations.
