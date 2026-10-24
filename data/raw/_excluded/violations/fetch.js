// Save a fresh copy of this Hackachusetts starter source.
// Run with: node fetch.js
const fs = require("node:fs/promises");

const url = "https://data.boston.gov/api/3/action/datastore_search_sql?sql=SELECT%20case_no%2Cstatus_dttm%2Cstatus%2Ccode%2Cvalue%2Cdescription%2Cviolation_city%2Cviolation_zip%2Cward%20FROM%20%22800a2663-1d6a-46e7-9356-bedb70f5332c%22%20WHERE%20status_dttm%20%3E%3D%20%272024-01-01%27%20ORDER%20BY%20status_dttm%20DESC%20LIMIT%20100";

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
