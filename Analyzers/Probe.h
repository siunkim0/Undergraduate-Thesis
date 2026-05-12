#ifndef Probe_h
#define Probe_h

#include "AnalyzerCore.h"
#include "SystematicHelper.h"

class Probe : public AnalyzerCore {
public:
    Probe();
    ~Probe();

    void initializeAnalyzer();
    void executeEvent();
    void executeEventFromParameter();

    // Analysis flags
    bool RunSyst;

    // Trigger settings
    TString IsoMuTriggerName;
    float TriggerSafePtCut;

    // Object ID settings
    RVec<Muon::MuonID> MuonIDs;

    // Physics objects
    RVec<Muon> AllMuons;
    RVec<TrigObj> AllTrigObjs;

    // Systematic helper
    unique_ptr<SystematicHelper> systHelper;

    // Tag-and-Probe methods
    void measIsoMu24TrigEff(RVec<Muon> &tightMuons,
                            RVec<Muon> &looseMuons,
                            float weight,
                            const TString &this_syst);

    // Helper functions
    bool PassIsoMuTrigger(const Muon &mu, const RVec<TrigObj> &trigObjs);
    bool PassL1Trigger(const Muon &mu, const RVec<TrigObj> &trigObjs);
    bool PassIsoMuTriggerDR(const Muon &mu, const RVec<TrigObj> &trigObjs, float dRcut);
};

#endif
