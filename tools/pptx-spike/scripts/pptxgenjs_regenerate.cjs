const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

async function main() {
  const target = process.argv[2];
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "AuditFlow AI Spike";
  pptx.subject = "pptxgenjs regeneration";
  pptx.company = "AuditFlow AI";
  pptx.theme = {
    headFontFace: "Aptos Display",
    bodyFontFace: "Aptos",
    lang: "en-US",
  };

  const cover = pptx.addSlide();
  cover.background = { color: "FFFFFF" };
  cover.addText("FY2026 Audit Committee", {
    x: 0.75,
    y: 1.0,
    w: 10.5,
    h: 0.7,
    fontFace: "Aptos Display",
    fontSize: 34,
    bold: true,
    color: "1F4E79",
  });
  cover.addText("Regenerated current-year deck | Confidential", {
    x: 0.75,
    y: 1.85,
    w: 8.5,
    h: 0.4,
    fontSize: 17,
    color: "666666",
  });
  cover.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 6.8,
    w: 13.333,
    h: 0.35,
    fill: { color: "1F4E79" },
    line: { color: "1F4E79" },
  });
  if (typeof cover.addNotes === "function") {
    cover.addNotes("Speaker note: pptxgenjs can write new notes, but cannot preserve source notes by parsing an existing deck.");
  }

  const summary = pptx.addSlide();
  summary.addText("Executive Summary", {
    x: 0.55,
    y: 0.35,
    w: 9.0,
    h: 0.5,
    fontFace: "Aptos Display",
    fontSize: 28,
    bold: true,
    color: "1F4E79",
  });
  summary.addText(
    [
      { text: "Audit scope completed across core financial controls.", options: { bullet: { type: "ul" } } },
      { text: "Two high-priority findings remain open.", options: { bullet: { type: "ul" } } },
      { text: "Management remediation cadence improved quarter over quarter.", options: { bullet: { type: "ul" } } },
      { text: "Committee attention requested for access governance.", options: { bullet: { type: "ul" } } },
    ],
    { x: 0.75, y: 1.2, w: 5.7, h: 4.7, fontSize: 18, breakLine: false, fit: "shrink" }
  );
  summary.addTable(
    [
      ["Risk", "Open", "Closed"],
      ["High", "2", "3"],
      ["Medium", "6", "6"],
      ["Low", "3", "9"],
    ],
    {
      x: 7.0,
      y: 1.25,
      w: 5.3,
      h: 2.0,
      border: { type: "solid", color: "D9E2F3", pt: 1 },
      fill: { color: "FFFFFF" },
      fontSize: 12,
      color: "222222",
    }
  );
  summary.addChart(pptx.ChartType.bar, [
    { name: "Open", labels: ["High", "Medium", "Low"], values: [2, 6, 3] },
    { name: "Closed", labels: ["High", "Medium", "Low"], values: [3, 6, 9] },
  ], {
    x: 7.05,
    y: 3.65,
    w: 5.1,
    h: 2.5,
    showLegend: true,
    legendPos: "b",
    catAxisLabelFontFace: "Aptos",
    valAxisLabelFontFace: "Aptos",
  });
  if (typeof summary.addNotes === "function") {
    summary.addNotes("Speaker note: Regenerated from normalized findings.");
  }

  const finding = pptx.addSlide();
  finding.addText("Finding Detail | Access Governance", {
    x: 0.55,
    y: 0.35,
    w: 10.5,
    h: 0.5,
    fontFace: "Aptos Display",
    fontSize: 28,
    bold: true,
    color: "1F4E79",
  });
  finding.addText(
    "Condition: Quarterly access reviews lacked consistent evidence.\nRisk: Unauthorized access may persist beyond acceptable timeframes.\nRecommendation: Standardize evidence capture and escalation.",
    { x: 0.75, y: 1.25, w: 11.0, h: 3.0, fontSize: 18, fit: "shrink", valign: "top" }
  );

  fs.mkdirSync(path.dirname(target), { recursive: true });
  await pptx.writeFile({ fileName: target });
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

