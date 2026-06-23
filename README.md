# Measurement of HLT_IsoMu24 Trigger Efficiency Using Tag-and-Probe Method

Undergraduate thesis project measuring the CMS HLT_IsoMu24 trigger efficiency in Drell–Yan Z → μμ events using CMS Open Data at √s = 13 TeV.


## Overview

This analysis measures the efficiency of the CMS single-muon trigger path `HLT_IsoMu24` using the Tag-and-Probe (T&P) method applied to Z → μμ events from the Run 2016H data-taking period. The trigger efficiency is measured as a function of muon pT, η, and dimuon invariant mass, and data-to-simulation scale factors are extracted.


## Motivation

Trigger efficiency measurements are a critical component of any CMS physics analysis. Without accurate knowledge of how efficiently the trigger selects events, cross section measurements and other precision results carry uncontrolled systematic uncertainties. The standard technique for measuring trigger efficiency at CMS is the Tag-and-Probe method, but it is typically performed internally by CMS members using proprietary tools and calibrations.

This project explores whether the same measurement can be performed independently using publicly available CMS Open Data. This is non-trivial because the SKNanoAnalyzer framework was not designed for Open Data — it assumes access to CMS-internal era definitions, correction files, and sample databases. Adapting the framework to handle a custom `2016UL_OpenData` era required resolving multiple compatibility issues (see [Troubleshooting](#troubleshooting-cms-open-data-with-sknanoanalyzer)).

The project serves both as an undergraduate thesis and as a practical guide for anyone attempting to use CMS Open Data with existing CMS analysis frameworks.


**Main result:**
```
SF = 0.934 ± 0.001 (stat.) ± 0.002 (syst.)
```


## Data and MC Samples

| Sample | Description | Events |
|--------|-------------|--------|
| SingleMuon Run2016H | CMS Open Data, 8.74 fb⁻¹ | — |
| ZToMuMu (50–120 GeV) | Powheg + Pythia 8, NLO σ = 2116 pb | 2,955,000 |

Data format: NanoAOD v9


## Method

### Tag-and-Probe

| | Definition |
|---|---|
| **Tag** | Tight ID + PF Iso tight + pT > 26 GeV + HLT trigger matched (ΔR < 0.1) |
| **Probe (Tight)** | Tight ID + PF Iso tight + pT > 10 GeV |
| **Probe (Loose)** | Tracker muon + pT > 10 GeV |
| **Pass** | Probe matched to HLT trigger object (ΔR < 0.1, filterBit 1) |
| **Mass window** | \|m_μμ − 91.2\| < 10 GeV |
| **Pair separation** | ΔR(tag, probe) > 0.3 |


### Trigger Object Matching

Since `Muon::TriggerMatched()` is not available in NanoAOD, trigger matching is performed using the `TrigObj` collection:
- Muon trigger object (|pdgId| = 13)
- HLT filter bit set (bit 1)
- pT > 24 GeV
- ΔR < 0.1 (CMS standard for HLT matching)


## Results

### Trigger Efficiency (Tight Probe)

| Variable | Data ε | MC ε | SF |
|----------|--------|------|-----|
| Overall (86–96 GeV) | 0.757 ± 0.001 | 0.811 ± 0.001 | 0.934 ± 0.001 ± 0.002 |


### Systematic Uncertainties

| Source | ΔSF |
|--------|-----|
| Mass window variation (±5 to ±20 GeV) | 0.002 |
| ΔR matching cone (0.05 to 0.20) | < 0.001 |
| **Total** | **0.002** |


## Project Structure

```
.
├── Analyzers/
│   ├── Probe.cc               # Main T&P analysis code
│   └── Probe.h                # Header file
├── Tools/                               
│   ├── SF_pt.py                         # Efficiency & SF plotting (pT, η, mass)
│   └── SF_eta.py              
│   └── SF_mass.py
│   └── mass.py                          # Systematic uncertainty & mass distribution
├── figures/
├── download.sh                          # download the data
├── thesis.pdf                           
└── README.md
```

## Key Files

### `Probe.cc`
The main analysis code implementing the Tag-and-Probe method. Inherits from `AnalyzerCore` in the SKNanoAnalyzer framework.

Key functions:
- `executeEventFromParameter()` — Event selection, weight calculation, T&P call
- `measIsoMu24TrigEff()` — Tag-and-Probe logic with histogram filling
- `PassIsoMuTrigger()` — HLT trigger object matching (ΔR < 0.1, bit 1)
- `PassIsoMuTriggerDR()` — Variable ΔR matching for systematic studies


### `SF_*.py`
Generates efficiency vs pT, η, and mass bin plots with Data/MC comparison and scale factor ratio panels.


### `mass.py`
Generates the invariant mass distribution plot (background estimation) and computes systematic uncertainty tables (mass window and ΔR variations).

## Framework

- **SKNanoAnalyzer** — C++ / ROOT-based analysis framework for CMS NanoAOD ([GitHub](https://github.com/CMSSNU/SKNanoAnalyzer))
- **ROOT** — Data analysis framework ([root.cern](https://root.cern/))
- **CMS Open Data** — [opendata.cern.ch](http://opendata.cern.ch)

## Running the Analysis

### Prerequisites
- SKNanoAnalyzer framework installed and configured
- CMS Open Data files (SingleMuon Run2016H, ZToMuMu MC)
- ROOT 6.x with Python bindings

### Execution
```bash
# Run the data by SKNanoAnalyzer

# Plot results
python Tools/SF_*.py
python Tools/mass.py
```

## MC Weight Configuration

The MC sample JSON must have correct `sumW` and `sumsign` values computed from the ROOT files' `Runs` tree. With `sumsign = 0` (default), `MCweight()` returns `inf`.

```json
{
    "name": "ZToMuMu_OpenData",
    "xsec": 2116.0,
    "nmc": 2955000,
    "sumsign": 2897028,
    "sumW": 6252423770.16
}
```

## Troubleshooting: CMS Open Data with SKNanoAnalyzer

SKNanoAnalyzer was designed for CMS internal use, not for Open Data. Several issues arise when running Open Data through this framework. Below is a summary of all problems encountered and their solutions.

---

### 1. MyCorrection crash: `unordered_map::at` error

**Symptom:**
```
terminate called after throwing an instance of 'std::out_of_range'
what(): unordered_map::at
```

**Cause:** The `MyCorrection` constructor initializes lookup maps (`LUM_keys`, `EGM_keys`, `JME_JER_GT`, etc.) for known eras like `2016preVFP`, `2016postVFP`, `2017`, `2018`, etc. The custom era `2016UL_OpenData` is not registered in these maps, so any function that accesses them (e.g., `GetPUWeight()`, `GetMuonRECOSF()`) throws `unordered_map::at`.

**Solution:** Add entries for `2016UL_OpenData` in `MyCorrection.cc`:
```cpp
LUM_keys["2016UL_OpenData"] = "Collisions16_UltraLegacy_goldenJSON";
EGM_keys["2016UL_OpenData"] = "2016postVFP";
JME_JER_GT["2016UL_OpenData"] = "Summer20UL16_JRV3_MC_######_AK4PFchs";
JME_vetomap_keys["2016UL_OpenData"] = "Summer19UL16_V1";
JME_PILEUP_keys["2016UL_OpenData"] = "PUJetID_eff";
// MC block:
JME_JES_GT["2016UL_OpenData"] = "Summer19UL16_V7_MC_######_AK4PFchs";
```

**Why Data didn't crash:** Data takes simpler code paths in Rochester correction (`kScaleDT`) that don't access these maps. MC takes different paths (`kSpreadMC`/`kSmearMC`) that do.

---

### 2. Rochester correction: preVFP vs postVFP

**Symptom:** MC efficiency is systematically off compared to expectations.

**Cause:** `GetEraConfig()` in `MyCorrection.cc` had `2016UL_OpenData` mapped to `2016preVFP` correction files. But Run2016H is **postVFP** (the VFP issue occurred mid-2016; Runs F(late)–H are postVFP).

**Solution:** Change the `2016UL_OpenData` block in `GetEraConfig()` to use `2016postVFP` files:
```cpp
} else if (era == "2016UL_OpenData") {
    config.json_muon += "/2016postVFP_UL/muon_Z.json.gz";       // was preVFP
    config.json_puWeights += "/2016postVFP_UL/puWeights.json.gz"; // was preVFP
    config.txt_roccor += "/RoccoR2016bUL.txt";                    // was RoccoR2016aUL.txt
    // ... change all paths from preVFP to postVFP
}
```

---

### 3. MC crash in `GetAllMuons()`: segmentation violation

**Symptom:**
```
#5 MyCorrection::GetMuonScaleSF()
#6 AnalyzerCore::GetAllMuons()
```

**Cause:** `GetAllMuons()` internally calls `myCorr->GetMuonScaleSF()` for Rochester correction. If `myCorr` initialization failed (due to issue #1 above), this is a nullptr dereference. Even if you comment out `myCorr = new MyCorrection(...)` in your own code, `GetAllMuons()` still calls it from the compiled `AnalyzerCore` library.

**Solution:** Fix issue #1 first. The `MyCorrection` object must be properly initialized before `GetAllMuons()` is called.

---

### 4. MCweight() returns `inf` → histograms filled with `nan`

**Symptom:** All MC histograms have `nan` values. `MCweight()` returns `inf`.

**Cause:** The MC sample JSON file has `sumsign: 0` and `sumW: 0`:
```json
"nmc": 0,
"sumsign": 0,
"sumW": 0,
```
Since `MCweight() = sign(genWeight) × xsec / sumSign`, dividing by zero gives `inf`.

**Solution:** Compute `sumW`, `sumsign`, and `nmc` from the actual ROOT files:
```python
import ROOT, glob
files = glob.glob('/path/to/MC/*.root')
sumW = 0.; nmc = 0; sumSign = 0
for f in files:
    tf = ROOT.TFile.Open(f)
    for entry in tf.Get('Runs'):
        sumW += entry.genEventSumw
        nmc += entry.genEventCount
    for ev in tf.Get('Events'):
        if ev.genWeight > 0: sumSign += 1
        elif ev.genWeight < 0: sumSign -= 1
    tf.Close()
print(f'nmc = {nmc}, sumW = {sumW:.2f}, sumSign = {sumSign}')
```
Then update the JSON file with the computed values.

**Important:** After updating the JSON, you must **re-submit jobs** via `SKNano.py`. The `sumSign` value is baked into the `job_*.cc` files at submission time, so old jobs still use `sumSign = 0`.

---

### 5. Luminosity mismatch

**Symptom:** `GetTriggerLumi("Full")` returns 16812 pb⁻¹ instead of ~8740 pb⁻¹.

**Cause:** The trigger JSON at `$SKNANO_DATA/2016UL_OpenData/Trigger/HLT_Path.json` was copied from `2016postVFP`, which includes the full postVFP luminosity (Runs F–H). Open Data only uses Run2016H.

**Solution:** Update the luminosity in `HLT_Path.json`:
```json
"HLT_IsoMu24": {
    "lumi": 8740.119304,
    "active": true
}
```

**Note:** For Tag-and-Probe efficiency measurements, the luminosity cancels in the efficiency ratio (AfterTrig/BeforeTrig), so this doesn't affect the SF. But it matters for cross section measurements or MC normalization plots.

---

### 6. Trigger matching: `TriggerMatched()` not available

**Symptom:** `Muon::TriggerMatched()` method doesn't exist in SKNano for NanoAOD v9.

**Solution:** Use the `TrigObj` collection to perform manual matching:
```cpp
bool PassIsoMuTrigger(const Muon &mu, const RVec<TrigObj> &trigObjs) {
    for (const auto &trigObj : trigObjs) {
        if (!trigObj.isMuon()) continue;
        if (trigObj.DeltaR(mu) > 0.1) continue;   // HLT: dR < 0.1
        if (!trigObj.hasBit(1)) continue;           // HLT filter bit
        if (trigObj.Pt() < 24.) continue;           // HLT_IsoMu24 threshold
        return true;
    }
    return false;
}
```

The ΔR < 0.1 cone size follows the CMS recommendation for HLT matching (validated by checking the ΔR distribution peaks at 0.01–0.03).

---

### 7. Efficiency of MC exceeds 1

**Symptom:** This did not happen on this project, but this would happen on measuring the efficiency.

**Cause:** Since some MC events have negative weight, the number of events after cut increases and that makes the efficiency bigger than 1.

**Solution:** Make the bin bigger on big mass region that has few events and usually has negative event weight.

---

### 8. Missing branches in Open Data NanoAOD

**Symptom:** Warnings during initialization:
```
[SKNanoGenLoader::Init] Warning: Branch Electron_scEta not found
[SKNanoGenLoader::Init] Warning: Branch Tau_genPartidDeepTau2017v2p1VSe not found
```

**Cause:** Open Data NanoAOD v9 may not contain all branches expected by SKNano (which targets the latest NanoAOD versions).

**Solution:** These warnings are harmless for muon-based analyses. They can be safely ignored as long as you don't use the missing branches.

---

### Summary of files that need modification

| File | Change |
|------|--------|
| `MyCorrection.cc` (constructor) | Add `2016UL_OpenData` to all key maps |
| `MyCorrection.cc` (`GetEraConfig`) | Change `2016UL_OpenData` paths from `preVFP` → `postVFP` |
| `ZToMuMu_OpenData.json` | Set correct `nmc`, `sumsign`, `sumW` values |
| `HLT_Path.json` | Set correct luminosity for Run2016H |
| `Probe.cc` | Implement manual `TrigObj` matching |

## References

1. CMS Collaboration, "Performance of the CMS muon trigger system in proton-proton collisions at √s = 13 TeV," JINST 16 (2021) P07001 ([arXiv:2102.04790](https://arxiv.org/abs/2102.04790))
2. S. D. Drell and T.-M. Yan, "Massive Lepton-Pair Production in Hadron-Hadron Collisions at High Energies," Phys. Rev. Lett. 25 (1970) 316

## Author

**Siun Kim**
Department of Physics, Sungkyunkwan University
---

*This work uses CMS Open Data released under CERN's Open Data policy.*
