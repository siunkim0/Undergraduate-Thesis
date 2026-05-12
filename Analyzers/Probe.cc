#include "Probe.h"

//==== Constructor and Destructor
Probe::Probe() {}
Probe::~Probe() {}
void Probe::initializeAnalyzer() {

    RunSyst = HasFlag("RunSyst");

    MuonIDs.clear();
    MuonIDs.push_back(Muon::MuonID::POG_TIGHT);
    MuonIDs.push_back(Muon::MuonID::POG_PFISO_TIGHT);

    //==== Trigger settings
    if (DataEra == "2016UL_OpenData") {
        IsoMuTriggerName = "HLT_IsoMu24";
        TriggerSafePtCut = 26.;
    } else if (DataEra == "2017") {
        IsoMuTriggerName = "HLT_IsoMu27";
        TriggerSafePtCut = 29.;
    } else if (DataEra == "2018") {
        IsoMuTriggerName = "HLT_IsoMu24";
        TriggerSafePtCut = 26.;
    } else if (DataEra == "2022" || DataEra == "2022EE") {
        IsoMuTriggerName = "HLT_IsoMu24";
        TriggerSafePtCut = 26.;
    } else if (DataEra == "2023" || DataEra == "2023BPix") {
        IsoMuTriggerName = "HLT_IsoMu24";
        TriggerSafePtCut = 26.;
    } else {
        cerr << "[Probe::initializeAnalyzer] DataEra is not set properly: " << DataEra << endl;
        exit(EXIT_FAILURE);
    }

    myCorr = new MyCorrection(DataEra, DataPeriod, IsDATA ? DataStream : MCSample, IsDATA);

    string SKNANO_HOME = getenv("SKNANO_HOME");
    if (IsDATA) {
        systHelper = std::make_unique<SystematicHelper>(SKNANO_HOME + "/docs/noSyst.yaml", DataStream, DataEra);
    } else {
        systHelper = std::make_unique<SystematicHelper>(SKNANO_HOME + "/docs/ExampleSystematic.yaml", MCSample, DataEra);
    }
}

void Probe::executeEvent() {
    AllMuons = GetAllMuons();
    AllTrigObjs = GetAllTrigObjs();
    for (const auto &syst_dummy : *systHelper) {
        executeEventFromParameter();
    }
}

void Probe::executeEventFromParameter() {
    const TString this_syst = systHelper->getCurrentSysName();
    Event ev = GetEvent();
    float weight = 1.0;
    FillHist(this_syst + "/CutFlow", 1, 1, 10, 0, 10);

    //==== Trigger
    if (!ev.PassTrigger(IsoMuTriggerName)) return;
    FillHist(this_syst + "/CutFlow", 2, 1, 10, 0, 10);

    //==== Object Definition
    RVec<Muon> looseMuons;
    RVec<Muon> tightMuons;
    for (const auto &mu : AllMuons) {
        if (mu.Pt() < 10. || fabs(mu.Eta()) > 2.4) continue;
        looseMuons.push_back(mu);
        if (mu.PassID(Muon::MuonID::POG_TIGHT) && mu.PassID(Muon::MuonID::POG_PFISO_TIGHT)) {
            tightMuons.push_back(mu);
        }
    }

    if (tightMuons.size() < 1 || looseMuons.size() < 2) return;
    FillHist(this_syst + "/CutFlow", 3, 1, 10, 0, 10);

    sort(tightMuons.begin(), tightMuons.end(), PtComparing);
    sort(looseMuons.begin(), looseMuons.end(), PtComparing);

    //==== Event weight
    if (!IsDATA) {
        weight *= MCweight();
        weight *= ev.GetTriggerLumi("Full");
        weight *= GetL1PrefireWeight();
        weight *= myCorr->GetPUWeight(ev.nTrueInt());
    }

    //==== Tag-and-Probe
    measIsoMu24TrigEff(tightMuons, looseMuons, weight, this_syst);
}

void Probe::measIsoMu24TrigEff(RVec<Muon> &tightMuons, RVec<Muon> &looseMuons,
                                float weight, const TString &this_syst) {
    // ════════════════════════════════════════════════════════
    //  Tag-and-Probe: IsoMu24 Trigger Efficiency
    //
    //  Tag:   Tight ID + PFIso tight + pt > TriggerSafePtCut + HLT trigger-matched
    //  Probe: (1) TightProbe: Tight ID + PFIso tight
    //         (2) LooseProbe: loose muon
    //  Pass:  dR < 0.1 to HLT trigger object (bit 3)
    //  Mass window: |Mll - 91.2| < 10 GeV (nominal)
    //
    //  Systematic variations:
    //    - Mass window: ±5, ±10 (nominal), ±15, ±20 GeV
    //    - dR matching: 0.05, 0.1 (nominal), 0.15, 0.2
    // ════════════════════════════════════════════════════════

    const Muon &tag = tightMuons.at(0);

    //==== Tag muon must pass HLT trigger matching
    if (!PassIsoMuTrigger(tag, AllTrigObjs)) return;

    //==== Tag muon kinematic cuts
    if (tag.Pt() < TriggerSafePtCut) return;

    //==== Common T&P fill logic
    auto fillTnP = [&](const Muon &probe, const TString &prefix) {
        if (&probe == &tag) return;
        if (tag.Charge() + probe.Charge() != 0) return;

        double Mll = (tag + probe).M();
        if (tag.DeltaR(probe) < 0.3) return;

        // ──── Invariant mass distribution (for background estimation) ────
        // Wide window (60-120 GeV) to show signal purity
        if (Mll > 60. && Mll < 120.) {
            FillHist(this_syst + "/" + prefix + "_Mass_BeforeTrig", Mll, weight, 120, 60, 120);
            if (PassIsoMuTrigger(probe, AllTrigObjs)) {
                FillHist(this_syst + "/" + prefix + "_Mass_AfterTrig", Mll, weight, 120, 60, 120);
            }
        }

        // ──── Systematic: Mass window variations (before nominal mass cut) ────
        // Tight probe only, overall pT, for systematic uncertainty estimation
        if (prefix.Contains("TightProbe")) {
            const bool probePassTrigSyst = PassIsoMuTrigger(probe, AllTrigObjs);
            const float massWindows[] = {5., 15., 20.};  // nominal (10) done after mass cut
            for (float hw : massWindows) {
                if (fabs(Mll - 91.2) < hw) {
                    TString tag_mw = Form("MW%.0f", hw);
                    FillHist(this_syst + "/" + prefix + "_" + tag_mw + "_Overall_Pt_BeforeTrig",
                             probe.Pt(), weight, 100, 0, 200);
                    if (probePassTrigSyst) {
                        FillHist(this_syst + "/" + prefix + "_" + tag_mw + "_Overall_Pt_AfterTrig",
                                 probe.Pt(), weight, 100, 0, 200);
                    }
                }
            }
        }

        // ──── Apply nominal mass window ────
        if (fabs(Mll - 91.2) > 10.) return;

        const bool probePassTrig = PassIsoMuTrigger(probe, AllTrigObjs);

        // ──── HLT Trigger Efficiency (nominal) ────

        //==== Probe Pt (turn-on curve)
        FillHist(this_syst + "/" + prefix + "_Pt_BeforeTrig", probe.Pt(), weight, 100, 0, 200);
        if (probePassTrig) {
            FillHist(this_syst + "/" + prefix + "_Pt_AfterTrig", probe.Pt(), weight, 100, 0, 200);
        }

        //==== Probe Eta (plateau region)
        if (probe.Pt() > TriggerSafePtCut) {
            FillHist(this_syst + "/" + prefix + "_Eta_BeforeTrig", probe.Eta(), weight, 48, -2.4, 2.4);
            if (probePassTrig) {
                FillHist(this_syst + "/" + prefix + "_Eta_AfterTrig", probe.Eta(), weight, 48, -2.4, 2.4);
            }
        }

        //==== Overall (86-96 GeV)
        if (Mll >= 86. && Mll < 96.) {
            FillHist(this_syst + "/" + prefix + "_Overall_Pt_BeforeTrig", probe.Pt(), weight, 100, 0, 200);
            if (probePassTrig) {
                FillHist(this_syst + "/" + prefix + "_Overall_Pt_AfterTrig", probe.Pt(), weight, 100, 0, 200);
            }
        }

        //==== Mass bin (1 GeV bins: 86-96 GeV)
        int mass_bin = (int)Mll;
        if (mass_bin >= 86 && mass_bin < 96) {
            TString hname_before = Form("%s/%s_MassBin%d_%d_Pt_BeforeTrig",
                                        this_syst.Data(), prefix.Data(), mass_bin, mass_bin + 1);
            TString hname_after  = Form("%s/%s_MassBin%d_%d_Pt_AfterTrig",
                                        this_syst.Data(), prefix.Data(), mass_bin, mass_bin + 1);
            FillHist(hname_before, probe.Pt(), weight, 100, 0, 200);
            if (probePassTrig) {
                FillHist(hname_after, probe.Pt(), weight, 100, 0, 200);
            }
        }

        // ──── Systematic: dR matching cone variation ────
        // Tight probe only, for systematic uncertainty estimation
        if (prefix.Contains("TightProbe") && Mll >= 86. && Mll < 96.) {
            const float dRCuts[] = {0.05, 0.15, 0.2};  // nominal (0.1) already done above
            for (float dRcut : dRCuts) {
                bool passDRVar = PassIsoMuTriggerDR(probe, AllTrigObjs, dRcut);
                TString tag_dr = Form("dR%.0f", dRcut * 100);  // e.g. dR5, dR15, dR20
                FillHist(this_syst + "/" + prefix + "_" + tag_dr + "_Overall_Pt_BeforeTrig",
                         probe.Pt(), weight, 100, 0, 200);
                if (passDRVar) {
                    FillHist(this_syst + "/" + prefix + "_" + tag_dr + "_Overall_Pt_AfterTrig",
                             probe.Pt(), weight, 100, 0, 200);
                }
            }
        }
    };

    //==== 1) Tight probe (CMS standard: Tight ID + PFIso tight)
    for (const auto &probe : tightMuons) {
        fillTnP(probe, "TrigEff_TightProbe");
    }

    //==== 2) Loose probe (inclusive)
    for (const auto &probe : looseMuons) {
        fillTnP(probe, "TrigEff_LooseProbe");
    }
}

bool Probe::PassIsoMuTrigger(const Muon &mu, const RVec<TrigObj> &trigObjs) {
    const float trig_pt_cut = (DataEra == "2016UL_OpenData") ? 27. : 24.;

    for (const auto &trigObj : trigObjs) {
        if (!trigObj.isMuon()) continue;
        if (trigObj.DeltaR(mu) > 0.1) continue;
        if (!trigObj.hasBit(3)) continue;
        if (trigObj.Pt() < trig_pt_cut) continue;
        return true;
    }
    return false;
}

bool Probe::PassIsoMuTriggerDR(const Muon &mu, const RVec<TrigObj> &trigObjs, float dRcut) {
    const float trig_pt_cut = (DataEra == "2016UL_OpenData") ? 27. : 24.;

    for (const auto &trigObj : trigObjs) {
        if (!trigObj.isMuon()) continue;
        if (trigObj.DeltaR(mu) > dRcut) continue;
        if (!trigObj.hasBit(3)) continue;
        if (trigObj.Pt() < trig_pt_cut) continue;
        return true;
    }
    return false;
}
