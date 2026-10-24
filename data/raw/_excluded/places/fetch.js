// Save a fresh copy of this Hackachusetts starter source.
// Run with: node fetch.js
const fs = require("node:fs/promises");

const url = "https://data.cdc.gov/resource/swc5-untb.json?$select=year,locationname,measure,data_value,low_confidence_limit,high_confidence_limit,totalpopulation&$where=stateabbr%3D%27MA%27%20AND%20measure%20in(%27Obesity%20among%20adults%27,%27Diagnosed%20diabetes%20among%20adults%27,%27Visits%20to%20doctor%20for%20routine%20checkup%20within%20the%20past%20year%20among%20adults%27,%27Frequent%20mental%20distress%20among%20adults%27,%27Current%20cigarette%20smoking%20among%20adults%27)%20AND%20data_value_type%3D%27Crude%20prevalence%27&$limit=500";

async function main() {
  const response = await fetch(url, { headers: { "User-Agent": "HackachusettsKit" } });
  if (!response.ok) throw new Error("Request failed: " + response.status);
  const bytes = Buffer.from(await response.arrayBuffer());
  const type = response.headers.get("content-type") || "";
  let name = "fresh.json";
  if (url.includes(".csv") || type.includes("csv")) name = "fresh.csv";
  if (url.endsWith(".txt")) name = "fresh.txt";
  await fs.writeFile(name, bytes);
  console.log("wrote " + name + " (" + bytes.length + " bytes)");
}

main();
