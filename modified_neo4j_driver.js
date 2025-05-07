const puppeteer = require('puppeteer');

async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function runCypherQueries(uids) {
    const browser = await puppeteer.connect({
        browserURL: 'http://localhost:9222'
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    await page.goto('http://localhost:7474');

    await page.waitForSelector('textarea.inputarea');
    // console.log("Selector wait complete");

    for (const uid of uids) {
        const queryLines = [
            `MATCH (target {uid: '${uid}'})`,
            `OPTIONAL MATCH pathUp = (root)-[:INFLUENCES*]->(target)`,
            `WITH CASE`,
            `    WHEN pathUp IS NULL THEN target`,
            `    ELSE head(nodes(pathUp))`,
            `END AS root`,
            `MATCH tree = (root)-[:INFLUENCES*0..]->(descendants)`,
            `RETURN tree`
        ];

        // Clear existing input (Ctrl+A, Backspace)
        await page.click('textarea.inputarea');
        await page.keyboard.down('Control');
        await page.keyboard.press('A');
        await page.keyboard.up('Control');
        await page.keyboard.press('Backspace');

        // Type each line with Shift+Enter except the last
        for (let i = 0; i < queryLines.length; i++) {
            await page.type('textarea.inputarea', queryLines[i]);
            if (i < queryLines.length - 1) {
                await page.keyboard.down('Shift');
                await page.keyboard.press('Enter');
                await page.keyboard.up('Shift');
            }
        }

        // Ensure focus and press Enter to run the full query
        await page.click('textarea.inputarea'); // refocus the input
        await delay(100); // small delay for safety
        await page.keyboard.down('Control');
        await page.keyboard.press('Enter');
        await page.keyboard.up('Control');

        // console.log(`Executed query for UID: ${uid}`);
        await delay(500); // wait 1 second before next UID
    }

    // Optional: await browser.close();
    process.exit(0);
}

const uids = process.argv.slice(2);
if (uids.length === 0) {
    console.error("Please pass a list of UIDs as arguments.");
    process.exit(1);
}

runCypherQueries(uids);
