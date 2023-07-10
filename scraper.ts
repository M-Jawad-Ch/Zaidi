import Chromium from "@sparticuz/chromium";
import puppeteer from "puppeteer-core";

export const scrape = async (urls: string[]) => {
    const browser = await puppeteer.launch({
        executablePath: await Chromium.executablePath(),
        headless: Chromium.headless,
        ignoreHTTPSErrors: true,
        defaultViewport: Chromium.defaultViewport,
        args: [...Chromium.args, "--hide-scrollbars", "--disable-web-security"]
    })
    const page = await browser.newPage()

    await page.setExtraHTTPHeaders({
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'upgrade-insecure-requests': '1',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9,en;q=0.8'
    });

    const data: { url: string, text: string, image: string }[] = []

    for (let i = 0; i < urls.length; i++) {
        const url = urls[i]

        try {
            await page.goto(url)

            const text = await page?.evaluate(() => (document.getElementsByTagName("BODY")[0] as any).innerText)
            const image = await page.evaluate(() => {
                const metas = document.getElementsByTagName('meta')
                for (let i = 0; i < metas.length; i++) {
                    if (metas[i].getAttribute('property') as string == 'og:image') {
                        return metas[i].getAttribute('content')
                    }
                }
            }) as string;

            data.push({ url, text, image })
            console.log('DONE')
        } catch (err) {
            console.log(err)
            continue
        }
    }

    await page.close()
    await browser.close()

    return data
}


// await scrape(["https://awstip.com/how-to-run-puppeteer-on-aws-lambda-using-layers-b1583ebd7120"])