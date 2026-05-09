import ROOT
import os
import math

ROOT.gROOT.SetBatch(True)

# set global variables
data_file = "/2016UL_OpenData_22/SingleMuon_OpenData_H.root"
mc_file   = "/2016UL_OpenData_22/ZToMuMu_OpenData.root"
out_dir   = "/Tools/RESULTS/"

lumiString = "8.74 fb^{-1} (13TeV)"

# get histogram
def get_hist(filepath, histkey):
    f = ROOT.TFile.Open(filepath)
    if not f or f.IsZombie():
        raise IOError(f"Cannot open ROOT file: {filepath}")
    h = f.Get(histkey)
    if not h:
        raise ValueError(f"Histogram '{histkey}' not found in {filepath}")
    h.SetDirectory(0)
    f.Close()
    return h


# ===========================================================================
# Plot: Invariant Mass Distribution (Background Estimation)
# ===========================================================================
print("=" * 60)
print("Invariant Mass Distribution (Background Estimation)")
print("=" * 60)

h_mass_before = get_hist(data_file, "Central/TrigEff_TightProbe_Mass_BeforeTrig")
h_mass_after  = get_hist(data_file, "Central/TrigEff_TightProbe_Mass_AfterTrig")

c_mass = ROOT.TCanvas("c_mass", "", 800, 600)
c_mass.SetLeftMargin(0.12)
c_mass.SetRightMargin(0.08)
c_mass.SetTopMargin(0.08)
c_mass.SetBottomMargin(0.12)

# style: before trigger (all probes)
h_mass_before.SetStats(0)
h_mass_before.SetTitle("")
h_mass_before.SetLineColor(ROOT.kBlack)
h_mass_before.SetLineWidth(2)
h_mass_before.SetFillColorAlpha(ROOT.kBlue, 0.15)

# style: after trigger (passed probes)
h_mass_after.SetStats(0)
h_mass_after.SetLineColor(ROOT.kRed)
h_mass_after.SetLineWidth(2)
h_mass_after.SetFillColorAlpha(ROOT.kRed, 0.15)

# axes
h_mass_before.GetXaxis().SetTitle("Dimuon Invariant Mass [GeV]")
h_mass_before.GetXaxis().SetTitleSize(0.045)
h_mass_before.GetXaxis().SetLabelSize(0.04)
h_mass_before.GetYaxis().SetTitle("Events / 0.5 GeV")
h_mass_before.GetYaxis().SetTitleSize(0.045)
h_mass_before.GetYaxis().SetTitleOffset(1.2)
h_mass_before.GetYaxis().SetLabelSize(0.04)

# draw
h_mass_before.Draw("HIST")
h_mass_after.Draw("HIST same")

# mass window lines
line_lo = ROOT.TLine(81.2, 0, 81.2, h_mass_before.GetMaximum() * 0.8)
line_hi = ROOT.TLine(101.2, 0, 101.2, h_mass_before.GetMaximum() * 0.8)
line_lo.SetLineColor(ROOT.kGray + 2)
line_hi.SetLineColor(ROOT.kGray + 2)
line_lo.SetLineStyle(2)
line_hi.SetLineStyle(2)
line_lo.SetLineWidth(2)
line_hi.SetLineWidth(2)
line_lo.Draw()
line_hi.Draw()

# labels
lumi = ROOT.TLatex()
lumi.SetTextSize(0.035)
lumi.SetTextFont(42)
lumi.DrawLatexNDC(0.74, 0.93, lumiString)

cms = ROOT.TLatex()
cms.SetTextSize(0.04)
cms.SetTextFont(61)
cms.DrawLatexNDC(0.15, 0.85, "CMS")

preliminary = ROOT.TLatex()
preliminary.SetTextSize(0.035)
preliminary.SetTextFont(52)
preliminary.DrawLatexNDC(0.15, 0.80, "Open Data")

legend = ROOT.TLegend(0.55, 0.70, 0.88, 0.85)
legend.SetFillStyle(0)
legend.SetBorderSize(0)
legend.AddEntry(h_mass_before, "All probes (before trigger)", "f")
legend.AddEntry(h_mass_after, "Passed probes (after trigger)", "f")
legend.AddEntry(line_lo, "Mass window (#pm 10 GeV)", "l")
legend.Draw()

c_mass.Update()
c_mass.SaveAs(out_dir + "mass_distribution.png")
c_mass.SaveAs(out_dir + "mass_distribution.pdf")
print(f"Saved: {out_dir}mass_distribution.png")


# ===========================================================================
# Systematic Uncertainty Summary
# ===========================================================================
print("\n" + "=" * 60)
print("Systematic Uncertainty Summary")
print("=" * 60)

# Helper: compute overall efficiency from Overall_Pt histograms
def get_overall_eff(filepath, histkey_before, histkey_after):
    h_bef = get_hist(filepath, histkey_before)
    h_aft = get_hist(filepath, histkey_after)
    N_bef = h_bef.Integral()
    N_aft = h_aft.Integral()
    if N_bef <= 0:
        return 0., 0.
    eff = N_aft / N_bef
    err = math.sqrt(eff * (1. - eff) / N_bef)
    return eff, err

# Helper: compute SF from data and MC efficiencies
def compute_sf(d_eff, d_err, m_eff, m_err):
    if m_eff <= 0:
        return 0., 0.
    sf = d_eff / m_eff
    rel_err = 0.
    if d_eff > 0:
        rel_err = math.sqrt((d_err / d_eff)**2 + (m_err / m_eff)**2)
    return sf, sf * rel_err

# ── Nominal SF ──
d_eff_nom, d_err_nom = get_overall_eff(data_file,
    "Central/TrigEff_TightProbe_Overall_Pt_BeforeTrig",
    "Central/TrigEff_TightProbe_Overall_Pt_AfterTrig")
m_eff_nom, m_err_nom = get_overall_eff(mc_file,
    "Central/TrigEff_TightProbe_Overall_Pt_BeforeTrig",
    "Central/TrigEff_TightProbe_Overall_Pt_AfterTrig")
sf_nom, sf_nom_err = compute_sf(d_eff_nom, d_err_nom, m_eff_nom, m_err_nom)

print(f"\nNominal (mass window ±10 GeV, dR < 0.1):")
print(f"  Data eff = {d_eff_nom:.4f} ± {d_err_nom:.4f}")
print(f"  MC   eff = {m_eff_nom:.4f} ± {m_err_nom:.4f}")
print(f"  SF       = {sf_nom:.4f} ± {sf_nom_err:.4f}")

# ── Mass window variations ──
print(f"\n{'Mass window':<20} {'Data eff':<15} {'MC eff':<15} {'SF':<15} {'ΔSF':<10}")
print("-" * 75)
print(f"{'±10 GeV (nominal)':<20} {d_eff_nom:<15.4f} {m_eff_nom:<15.4f} {sf_nom:<15.4f} {'---':<10}")

for mw in [5, 15, 20]:
    tag = f"MW{mw}"
    d_eff, d_err = get_overall_eff(data_file,
        f"Central/TrigEff_TightProbe_{tag}_Overall_Pt_BeforeTrig",
        f"Central/TrigEff_TightProbe_{tag}_Overall_Pt_AfterTrig")
    m_eff, m_err = get_overall_eff(mc_file,
        f"Central/TrigEff_TightProbe_{tag}_Overall_Pt_BeforeTrig",
        f"Central/TrigEff_TightProbe_{tag}_Overall_Pt_AfterTrig")
    sf, sf_err = compute_sf(d_eff, d_err, m_eff, m_err)
    delta = sf - sf_nom
    print(f"{'±' + str(mw) + ' GeV':<20} {d_eff:<15.4f} {m_eff:<15.4f} {sf:<15.4f} {delta:<+10.4f}")

# ── dR matching variations ──
print(f"\n{'dR cone':<20} {'Data eff':<15} {'MC eff':<15} {'SF':<15} {'ΔSF':<10}")
print("-" * 75)
print(f"{'0.10 (nominal)':<20} {d_eff_nom:<15.4f} {m_eff_nom:<15.4f} {sf_nom:<15.4f} {'---':<10}")

for dr_int in [5, 15, 20]:
    tag = f"dR{dr_int}"
    d_eff, d_err = get_overall_eff(data_file,
        f"Central/TrigEff_TightProbe_{tag}_Overall_Pt_BeforeTrig",
        f"Central/TrigEff_TightProbe_{tag}_Overall_Pt_AfterTrig")
    m_eff, m_err = get_overall_eff(mc_file,
        f"Central/TrigEff_TightProbe_{tag}_Overall_Pt_BeforeTrig",
        f"Central/TrigEff_TightProbe_{tag}_Overall_Pt_AfterTrig")
    sf, sf_err = compute_sf(d_eff, d_err, m_eff, m_err)
    delta = sf - sf_nom
    dr_val = dr_int / 100.
    print(f"{f'{dr_val:.2f}':<20} {d_eff:<15.4f} {m_eff:<15.4f} {sf:<15.4f} {delta:<+10.4f}")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
