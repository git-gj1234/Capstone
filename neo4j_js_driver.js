const puppeteer = require('puppeteer');

async function runCypherQuery() {
    // Connect to the running browser instance
    const browser = await puppeteer.connect({
        browserURL: 'http://localhost:9222' // The debugging URL
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    await page.goto('http://localhost:7474'); // Neo4j Browser URL

    // Wait for the query input field (adjust selector as needed)
    await page.waitForSelector('textarea.inputarea');
    console.log("selector wait complete")
    await new Promise(resolve => setTimeout(resolve, 500));

    // Send the Cypher query to the Neo4j Browser
    await page.type('textarea.inputarea', 'MATCH p=()-[r:INFLUENCES]->() RETURN p LIMIT 53');
    console.log("type complete")

    // Execute the query by simulating hitting "Enter"
    await page.keyboard.press('Enter');
    console.log("p1 exec complete");

    // // Wait for the results to appear (adjust selector as needed)
    // await page.waitForSelector('.neo4j-results');

    // // Optionally, get the results and print them
    // const results = await page.$eval('.neo4j-results', el => el.textContent);
    // console.log(results);

    // await browser.close();
}

runCypherQuery();
