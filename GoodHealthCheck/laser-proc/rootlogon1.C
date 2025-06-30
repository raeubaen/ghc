{
   TStyle *myStyle  = new TStyle("MyStyle","My Root Styles");

   // from ROOT plain style
   myStyle->SetCanvasBorderMode(0);
   myStyle->SetPadBorderMode(0);
   myStyle->SetPadColor(0);
   myStyle->SetCanvasColor(0);
   myStyle->SetTitleColor(1);
   myStyle->SetStatColor(0);

   myStyle->SetLabelSize(0.03,"xyz"); // size of axis values

   myStyle->SetHistLineWidth(2);
   myStyle->SetHistLineColor(kBlack);

   myStyle->SetLineWidth(1);
   myStyle->SetMarkerStyle(20);
   myStyle->SetMarkerSize(0.8);


   myStyle->SetFuncColor(kRed+1);
   myStyle->SetFuncWidth(3);

   myStyle->SetTitleFont(62, "X");
   myStyle->SetTitleFont(62, "Y");
   myStyle->SetTitleFont(62, "Z");


   myStyle->SetLabelSize(0.06, "X");
   myStyle->SetTitleSize(0.06, "X");

   myStyle->SetLabelSize(0.06, "Y");
   myStyle->SetTitleSize(0.06, "Y");

   myStyle->SetLabelSize(0.06, "Z");
   myStyle->SetTitleSize(0.06, "Z");

   myStyle->SetTitleOffset(1.0, "X");
   myStyle->SetTitleOffset(0.70, "Z");

   // default canvas positioning
   myStyle->SetCanvasDefX(900);
   myStyle->SetCanvasDefY(20);

   myStyle->SetPadBottomMargin(0.14);
   myStyle->SetPadTopMargin(0.1);
   myStyle->SetPadLeftMargin(0.14);
   myStyle->SetPadRightMargin(0.1);
   myStyle->SetPadTickX(1);
   myStyle->SetPadTickY(1);
   myStyle->SetFrameBorderMode(0);

   myStyle->SetTitleBorderSize(0);
   myStyle->SetOptTitle(0); //messo a 1

   // Din letter
   myStyle->SetPaperSize(21, 38);

   myStyle->SetStatBorderSize(0);

   myStyle->SetStatX(0.85); 
   myStyle->SetLineWidth(1);
   myStyle->SetLineColor(kBlue+2);
   myStyle->SetStatY(0.85);
   myStyle->SetStatFont(42);

   myStyle->SetOptStat(0);    // (1110)Show overflow and underflow as well

   myStyle->SetOptFit(0111); //(1111) con chi e prob
   myStyle->SetPalette(1);

   // apply the new style
   gROOT->SetStyle("MyStyle"); //uncomment to set this style
   gROOT->ForceStyle(); // use this style, not the one saved in root files

   printf("\n Beginning new ROOT session with private TStyle \n");

}
