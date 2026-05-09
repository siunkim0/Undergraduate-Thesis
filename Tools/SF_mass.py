import ROOT
import os
import math
ROOT.gROOT.SetBatch(True)



# set global variables
era = "2016UL_OpenData"
mass_bins = [(n, n + 1) for n in range(86, 96)]
Data = "SingleMuon_OpenData_H"
MCs = "ZToMuMu_OpenData"

# set config
config = {
    "xTitle": "Dimuon Mass [GeV]",
    "yTitle": "Trigger Efficiency",
    "xRange": [86, 96],
    "yRange": [0.65, 0.90],
    "sfRange": [0.8, 1.2],
    "era": era
}

LumiInfo = {
    "2016UL_OpenData": 8.74,
    "2018": 59.83
}

# get histograms
def get_hist(sample, histkey):
    era = "2016UL_OpenData_AA"
    if sample == "data":
        fkey = f"/2016UL_OpenData/SingleMuon_OpenData_H.root"
    else:
        fkey = f"/2016UL_OpenData/ZToMuMu_OpenData.root"

    print(f"Opening file: {fkey}")  # debugging

    if not os.path.exists(fkey):
        raise FileNotFoundError(f"File does not exist: {fkey}")

    f = ROOT.TFile.Open(fkey)
    if not f or f.IsZombie():
        raise IOError(f"Cannot open ROOT file: {fkey}")

    h = f.Get(histkey)
    if not h:
        raise ValueError(f"Histogram '{histkey}' not found in {fkey}")

    h.SetDirectory(0)
    f.Close()
    return h

# get efficiency histogram (Integral per mass bin, Binomial error)
def get_efficiency(sample):
    h_eff = ROOT.TH1F(f"{sample}_eff", "", 10, 86, 96)
    for i, (lo, hi) in enumerate(mass_bins):
        h_bef = get_hist(sample, f"Central/TrigEff_LooseProbe_MassBin{lo}_{hi}_Pt_BeforeTrig")
        h_aft = get_hist(sample, f"Central/TrigEff_LooseProbe_MassBin{lo}_{hi}_Pt_AfterTrig")
        N_bef = h_bef.Integral()
        N_aft = h_aft.Integral()
        eff = N_aft / N_bef if N_bef > 0 else 0.0
        err = math.sqrt(eff * (1.0 - eff) / N_bef) if N_bef > 0 else 0.0
        h_eff.SetBinContent(i + 1, eff)
        h_eff.SetBinError(i + 1, err)
    return h_eff

# Plot Trigger Efficiency vs Mass Bin & Scale Factor
print("=" * 50)
print("Plotting Trigger Efficiency vs Mass Bin & Scale Factor")
print("=" * 50)

# Get data efficiency
data_eff = get_efficiency("data")

# Get MC efficiency
mc_eff = get_efficiency(MCs)

for i in range(1, 11):
    d = data_eff.GetBinContent(i)
    m = mc_eff.GetBinContent(i)
    sf_val = d / m if m > 0 else 0
    print(f"  {85+i}-{86+i} GeV | Data={d:.4f}  MC={m:.4f}  SF={sf_val:.4f}")

# Calculate Scale Factor (Data / MC)
sf = data_eff.Clone("sf")
sf.Divide(mc_eff)

# Create canvas with ratio pad
c = ROOT.TCanvas("c", "", 800, 900)
padUp = ROOT.TPad("padUp", "", 0, 0.3, 1, 1)
padUp.SetBottomMargin(0.02)
padUp.SetLeftMargin(0.12)
padUp.SetRightMargin(0.08)
padUp.Draw()

padDown = ROOT.TPad("padDown", "", 0, 0, 1, 0.3)
padDown.SetTopMargin(0.02)
padDown.SetBottomMargin(0.3)
padDown.SetLeftMargin(0.12)
padDown.SetRightMargin(0.08)
padDown.SetGrid(True)
padDown.Draw()

# Upper pad: Efficiency
padUp.cd()

# Style data
data_eff.SetStats(0)
data_eff.SetTitle("")
data_eff.SetMarkerStyle(20)
data_eff.SetMarkerSize(0.8)
data_eff.SetMarkerColor(ROOT.kBlack)
data_eff.SetLineColor(ROOT.kBlack)

# Style MC
mc_eff.SetStats(0)
mc_eff.SetMarkerStyle(21)
mc_eff.SetMarkerSize(0.8)
mc_eff.SetMarkerColor(ROOT.kRed)
mc_eff.SetLineColor(ROOT.kRed)
mc_eff.SetFillColorAlpha(ROOT.kRed, 0.3)

# X axis (hide labels for upper pad)
data_eff.GetXaxis().SetLabelSize(0)
data_eff.GetXaxis().SetTitleSize(0)
data_eff.GetXaxis().SetRangeUser(config["xRange"][0], config["xRange"][1])

# Y axis
data_eff.GetYaxis().SetTitle(config["yTitle"])
data_eff.GetYaxis().SetTitleSize(0.05)
data_eff.GetYaxis().SetTitleOffset(1.0)
data_eff.GetYaxis().SetLabelSize(0.045)
data_eff.GetYaxis().SetRangeUser(config["yRange"][0], config["yRange"][1])

# Draw
data_eff.Draw("E1")
mc_eff.Draw("E2 same")
mc_eff.Draw("E1 same")
data_eff.Draw("E1 same")

# Add labels
lumi = ROOT.TLatex()
lumi.SetTextSize(0.04)
lumi.SetTextFont(42)
lumiString = f"L_{{int}} = {LumiInfo[era]} fb^{{-1}} (13TeV)"
lumi.DrawLatexNDC(0.63, 0.92, lumiString)

cms = ROOT.TLatex()
cms.SetTextSize(0.045)
cms.SetTextFont(61)
cms.DrawLatexNDC(0.15, 0.85, "CMS")

preliminary = ROOT.TLatex()
preliminary.SetTextSize(0.04)
preliminary.SetTextFont(52)
preliminary.DrawLatexNDC(0.15, 0.79, "Open Data")

# Legend
legend = ROOT.TLegend(0.65, 0.70, 0.88, 0.85)
legend.SetFillStyle(0)
legend.SetBorderSize(0)
legend.AddEntry(data_eff, "Data", "lep")
legend.AddEntry(mc_eff, "MC", "lep")
legend.Draw()

# Lower pad: Scale Factor
padDown.cd()

# Style SF
sf.SetStats(0)
sf.SetTitle("")
sf.SetMarkerStyle(20)
sf.SetMarkerSize(0.8)
sf.SetMarkerColor(ROOT.kBlack)
sf.SetLineColor(ROOT.kBlack)

# X axis
sf.GetXaxis().SetTitle(config["xTitle"])
sf.GetXaxis().SetTitleSize(0.1)
sf.GetXaxis().SetTitleOffset(1.0)
sf.GetXaxis().SetLabelSize(0.08)
sf.GetXaxis().SetRangeUser(config["xRange"][0], config["xRange"][1])

# Y axis
sf.GetYaxis().SetTitle("SF (Data/MC)")
sf.GetYaxis().CenterTitle()
sf.GetYaxis().SetTitleSize(0.1)
sf.GetYaxis().SetTitleOffset(0.5)
sf.GetYaxis().SetLabelSize(0.08)
sf.GetYaxis().SetRangeUser(config["sfRange"][0], config["sfRange"][1])
sf.GetYaxis().SetNdivisions(505)

# Draw
sf.Draw("E1")

# Draw line at 1
line = ROOT.TLine(config["xRange"][0], 1, config["xRange"][1], 1)
line.SetLineColor(ROOT.kRed)
line.SetLineStyle(2)
line.Draw()

c.Update()
c.SaveAs("/Trigger_mass_SF.pdf")

print("=" * 50)
print("Done! Created:")
print("  - Trigger_mass_SF.pdf")
print("=" * 50)
