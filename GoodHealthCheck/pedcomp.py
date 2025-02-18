import ROOT

# from ghc_modules import Data, Plot
# import pfgutils.connection


# noinspection PyProtectedMember,PyPep8Naming
def draw(c, EB, EE2, EE1):
    from pfgutils.plotECAL import _drawEBextra, _drawEEextra
    c.Clear()
    c.Divide(1, 2)

    pad = c.cd(1)
    pad.SetCanvasSize(3600, 1710)
    EB.Draw('colz')
    _drawEBextra(c, 1)

    # Endcap
    pad0 = c.cd(2)
    pad0.Divide(2, 1)

    # Endcap z = -1
    pad1 = pad0.cd(1)
    pad1.SetCanvasSize(1000, 1000)

    EE1.Draw("colz,0")
    _drawEEextra(pad0, 1, -1)
    pad2 = pad0.cd(2)
    pad2.SetCanvasSize(1000, 1000)
    EE2.Draw("colz,0")
    _drawEEextra(pad0, 2, 1)

    for p in (pad, pad1, pad2):
        p.SetGridx(True)
        p.SetGridy(True)

    c.Update()
    ROOT.SetOwnership(EB, False)
    ROOT.SetOwnership(EE1, False)
    ROOT.SetOwnership(EE2, False)


#
# def main():
#     pfgutils.connection.connect(oracle=False, chanstat=True,
#                                 chandb="sqlite3:/home/razumov/Work/ECal/GoodHealthCheck/pfgutils/ecalchannels.db")
#
#     ghc17 = Data.Data('20170506', False)
#     ghc16 = Data.Data('20160525', False)
#
#     plotter17 = Plot.Plotter(ghc17)
#     plotter16 = Plot.Plotter(ghc16)
#
#     c = ROOT.TCanvas("diff", "Difference plot")
#     c.Divide(1, 2)
#
#     f = ROOT.TFile("comp.root", "RECREATE")
#     f.cd()
#
#     for plottype in ('mean', 'RMS'):
#         for g in ("G1", "G6", "G12"):
#             print "Processing", plottype, "for gain", g
#             hdiff_16 = [None, None, None]
#             hdiff_17 = [None, None, None]
#             hdiff = [None, None, None]
#             hon_16 = plotter16.get2DHistogram(key=("PED_ON_{0}_{1}".format(plottype, g)).upper(),
#                                               name="2016 Pedestal {0}, gain {1} ({2})".format(plottype, g, "HV ON"))
#
#             hoff_16 = plotter16.get2DHistogram(key=("PED_OFF_{0}_{1}".format(plottype, g)).upper(),
#                                                name="2016 Pedestal {0}, gain {1} ({2})".format(plottype, g, "HV OFF"))
#
#             for i in range(0, 3):
#                 # hdiff_16[i] = hoff_16[i].Clone("hdiff16_{0}".format(i))
#                 # hdiff_16[i].Add(hon_16[i], -1)
#                 hoff_16[i].Write()
#                 hon_16[i].Write()
#
#             # draw(c, *hdiff_16)
#             # c.SaveAs("20160525_diff_{0}_{1}.png".format(plottype, g))
#
#             hon_17 = plotter17.get2DHistogram(key=("PED_ON_{0}_{1}".format(plottype, g)).upper(),
#                                               name="2017 Pedestal {0}, gain {1} ({2})".format(plottype, g, "HV ON"))
#
#             hoff_17 = plotter17.get2DHistogram(key=("PED_OFF_{0}_{1}".format(plottype, g)).upper(),
#                                                name="2017 Pedestal {0}, gain {1} ({2})".format(plottype, g, "HV OFF"))
#
#             for i in range(0, 3):
#                 # hdiff_17[i] = hoff_17[i].Clone("hdiff17_{0}".format(i))
#                 # hdiff_17[i].Add(hon_17[i], -1)
#                 hoff_17[i].Write()
#                 hon_17[i].Write()
#
#                 # draw(c, *hdiff_17)
#                 # c.SaveAs("20170506_diff_{0}_{1}.png".format(plottype, g))
#
#                 # for i in range(0, 3):
#                 #     hdiff[i] = hdiff_16[i].Clone("hdiff_{0}".format(i))
#                 #     hdiff[i].Add(hdiff_17[i], -1)
#                 #
#                 # draw(c, *hdiff)
#                 # c.SaveAs("diff_{0}_{1}.png".format(plottype, g))
#
#     f.Close()

def main():
    f = ROOT.TFile("diff.root")
    h = ROOT.TFile("outfile.root", "RECREATE")
    h.cd()
    c = ROOT.TCanvas("diff", "Difference plot")

    for plottype in ('mean', 'RMS'):
        for g in ("G1", "G6", "G12"):
            hon_16 = []
            hon_17 = []
            hoff_16 = []
            hoff_17 = []
            hdiff_16 = [None, None, None]
            hdiff_17 = [None, None, None]
            hdiff = [None, None, None]

            print("Processing", plottype, "for gain", g)
            for det in ('EB', 'EEp', 'EEm'):
                hon_16.append(f.Get("GHC 2016 Pedestal {0}, gain {1} ({2})_{3}".format(plottype, g, "HV ON", det)))
                hoff_16.append(f.Get("GHC 2016 Pedestal {0}, gain {1} ({2})_{3}".format(plottype, g, "HV OFF", det)))
                hon_17.append(f.Get("GHC 2017 Pedestal {0}, gain {1} ({2})_{3}".format(plottype, g, "HV ON", det)))
                hoff_17.append(f.Get("GHC 2017 Pedestal {0}, gain {1} ({2})_{3}".format(plottype, g, "HV OFF", det)))

            for i in range(0, 3):
                print("Calculating diff_16 [" + str(i) + ']')
                hdiff_16[i] = hon_16[i].Clone("hdiff16_{0}".format(i))
                hdiff_16[i].Add(hoff_16[i], -1)
                hdiff_16[i].Reset("ICES")
                hdiff_16[i].SetTitle(
                    "GHC 2016 Pedestal {0}, gain {1} |{2} - {3}|".format(plottype, g, "HV ON", "HV OFF"))
                for ix in range(1, hdiff_16[i].GetXaxis().GetNbins() + 1):
                    for iy in range(1, hdiff_16[i].GetYaxis().GetNbins() + 1):
                        value_on = hon_16[i].GetBinContent(ix, iy)
                        value_off = hoff_16[i].GetBinContent(ix, iy)
                        x = hdiff_16[i].GetXaxis().GetBinCenter(ix)
                        y = hdiff_16[i].GetYaxis().GetBinCenter(iy)
                        if value_on != 0 and value_off != 0:
                            # hdiff_16[i].SetBinContent(ix, iy, value_on - value_off)
                            hdiff_16[i].Fill(x, y, abs(value_on - value_off))
                hdiff_16[i].SetName("hist_{0}ped{1}diff_{2}_ghc20160525".format(g, plottype, ('EB', 'EEp', 'EEm')[i]))
                hdiff_16[i].Write()

            draw(c, *hdiff_16)
            c.SaveAs("20160525_diff_{0}_{1}.png".format(plottype, g))

            for i in range(0, 3):
                print("Calculating diff_17 [" + str(i) + ']')
                hdiff_17[i] = hon_17[i].Clone("hdiff17_{0}".format(i))
                hdiff_17[i].Add(hoff_17[i], -1)
                hdiff_17[i].Reset("ICES")
                hdiff_17[i].SetTitle(
                    "GHC 2017 Pedestal {0}, gain {1} |{2} - {3}|".format(plottype, g, "HV ON", "HV OFF"))
                for ix in range(1, hdiff_17[i].GetXaxis().GetNbins() + 1):
                    for iy in range(1, hdiff_17[i].GetYaxis().GetNbins() + 1):
                        value_on = hon_17[i].GetBinContent(ix, iy)
                        value_off = hoff_17[i].GetBinContent(ix, iy)
                        x = hdiff_17[i].GetXaxis().GetBinCenter(ix)
                        y = hdiff_17[i].GetYaxis().GetBinCenter(iy)
                        if value_on != 0 and value_off != 0:
                            # hdiff_17[i].SetBinContent(ix, iy, value_on - value_off)
                            hdiff_17[i].Fill(x, y, abs(value_on - value_off))
                hdiff_17[i].SetName("hist_{0}ped{1}diff_{2}_ghc20170506".format(g, plottype, ('EB', 'EEp', 'EEm')[i]))
                hdiff_17[i].Write()

            # if plottype == "mean" and g == "G12":
            #     hdiff_17[0].SetMaximum(+15)
            # if plottype == "mean" and g == "G6":
            #     hdiff_17[0].SetMaximum(+10)
            # if plottype == "mean" and g == "G1":
            #     hdiff_17[0].SetMaximum(+5)

            draw(c, *hdiff_17)
            c.SaveAs("20170506_diff_{0}_{1}.png".format(plottype, g))

            for i in range(0, 3):
                print("Calculating diff [" + str(i) + ']')
                hdiff[i] = hdiff_17[i].Clone("hdiff_{0}".format(i))
                hdiff[i].Add(hdiff_16[i], -1)
                hdiff[i].SetTitle(
                    "|GHC 2017 - GHC 2016| for Pedestal {0}, gain {1} |{2} - {3}|".format(plottype, g, "HV ON",
                                                                                          "HV OFF"))
                hdiff[i].Reset("ICES")
                for ix in range(1, hdiff[i].GetXaxis().GetNbins() + 1):
                    for iy in range(1, hdiff[i].GetYaxis().GetNbins() + 1):
                        value_on = hdiff_17[i].GetBinContent(ix, iy)
                        value_off = hdiff_16[i].GetBinContent(ix, iy)
                        x = hdiff[i].GetXaxis().GetBinCenter(ix)
                        y = hdiff[i].GetYaxis().GetBinCenter(iy)
                        if value_on != 0 and value_off != 0:
                            # hdiff[i].SetBinContent(ix, iy, value_on - value_off)
                            hdiff[i].Fill(x, y, abs(value_on - value_off))

                hdiff[i].SetName(
                    "hist_{0}ped{1}diff_{2}_ghc20170506-ghc20160525".format(g, plottype, ('EB', 'EEp', 'EEm')[i]))
                hdiff[i].Write()

            # if plottype == "mean" and g == "G12":
            #     hdiff[0].SetMaximum(+15)
            # if plottype == "mean" and g == "G6":
            #     hdiff[0].SetMaximum(+10)
            # if plottype == "mean" and g == "G1":
            #     hdiff[0].SetMaximum(+5)

            draw(c, *hdiff)
            c.SaveAs("diff_{0}_{1}.png".format(plottype, g))

    f.Close()
    h.Close()


if __name__ == "__main__":
    main()
