import path from "node:path";
import { pathToFileURL } from "node:url";
import { fileURLToPath } from "node:url";
import { chromium } from "file:///C:/Users/Unoh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";


const root = path.dirname(fileURLToPath(import.meta.url));
const input = path.join(root, "운호_BANK는_어디서_공격받을_수_있는가.html");
const executablePath = "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe";

const browser = await chromium.launch({
  headless: true,
  executablePath,
  args: ["--disable-extensions", "--no-first-run"],
});

try {
  for (const preview of [
    { name: "preview-desktop.png", width: 1440, height: 1000 },
    { name: "preview-mobile.png", width: 430, height: 900 },
  ]) {
    const page = await browser.newPage({
      viewport: { width: preview.width, height: preview.height },
      deviceScaleFactor: 1,
    });
    await page.goto(pathToFileURL(input).href, { waitUntil: "load" });
    await page.waitForFunction(() => {
      const mermaid = document.querySelector(".mermaid");
      return mermaid && mermaid.querySelector("svg");
    });
    await page.screenshot({
      path: path.join(root, preview.name),
      fullPage: true,
    });
    await page.close();
  }
} finally {
  await browser.close();
}

console.log("Generated preview-desktop.png and preview-mobile.png");
