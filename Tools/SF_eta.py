import ROOT
import os
ROOT.gROOT.SetBatch(True)



# set global variables
era = "2016UL_OpenData"
histkey_before = "Central/TrigEff_LooseProbe_Eta_BeforeTrig"
histkey_after = "Central/TrigEff_LooseProbe_Eta_AfterTrig"
Data = "SingleMuon_OpenData_H"
MCs = "ZToMuMu_OpenData"

# set config
config = {
    "xTitle": "Probe Muon #eta",
    "yTitle": "Trigger Efficiency",
    "xRange": [-2.4, 2.4],
    "yRange": [0.6, 1.1],
    "sfRange": [0.8, 1.2],
    "era": era
}

LumiInfo = {
    "2016UL_OpenData": 8.74,
    "2018": 59.83
}

# get histograms
def get_hist(sample, histkey):
    era = "2016UL_OpenData"
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

# get efficiency histogram (AfterIso / BeforeIso)
def get_efficiency(sample):
    h_before = get_hist(sample, histkey_before)
    h_after = get_hist(sample, histkey_after)

    h_eff = h_after.Clone(f"{sample}_eff")
    h_eff.Divide(h_after, h_before, 1, 1, "B")

    return h_eff

# Plot Isolation Efficiency
print("=" * 50)
print("Plotting SubleadMuon_Pt Isolation Efficiency & Scale Factor")
print("=" * 50)

# Get data efficiency
data_eff = get_efficiency("data")

# Get MC efficiency (sum all MC samples first, then divide)
mc_before_total = None
mc_after_total = None
for mc in MCs:
    h_before = get_hist(mc, histkey_before)
    h_after = get_hist(mc, histkey_after)
    if mc_before_total is None:
        mc_before_total = h_before.Clone("mc_before_total")
        mc_after_total = h_after.Clone("mc_after_total")
    else:
        mc_before_total.Add(h_before)
        mc_after_total.Add(h_after)

mc_eff = mc_after_total.Clone("mc_eff")
mc_eff.Divide(mc_after_total, mc_before_total, 1, 1, "B")

for i in range(1, mc_before_total.GetNbinsX() + 1):
    b = mc_before_total.GetBinContent(i)
    a = mc_after_total.GetBinContent(i)
    if b > 0 and a/b > 1:
        print(f"Bin {i}: before={b:.1f}, after={a:.1f}, ratio={a/b:.4f}")

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
c.SaveAs("/Trigger_eta_SF.pdf")

print("=" * 50)
print("Done! Created:")
print("  - Trigger_eta_SF.pdf")
print("=" * 50)
