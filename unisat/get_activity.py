import csv
import json
import logging
from cgi import print_arguments

from playwright.sync_api import sync_playwright

addr = "bc1qc0clqxxfjvvquenadlx9rtcqx63c49ef0pfw29"

csv_file = open('./unisat/brc20_sats2.csv', 'a', newline='')
writer = csv.writer(csv_file)
def intercept_response(response):
        # we can extract details from background requests
            #print(response.request.url)
            if response.request.url.startswith('https://api.unisat.io/query-v4/address'):
                #print(response.headers.get('cookie'))
                result = json.loads(response.text())
                print(result['data']['detail'])
                for item in result['data']['detail']:
                    row = [item['type'], item['valid'], item['txid'], item['inscriptionNumber'], item['inscriptionId'], item['from'], item['to'], item['amount'], item['availableBalance'],item['overallBalance'],item['transferBalance']]
                    writer.writerow(row)
            # print('response:',response.url)
            return response
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.on("response", intercept_response)
    page.goto('https://unisat.io/brc20?q=' + addr + '&tick=sats')
    
    for i in range(1800):
        try:
            print(i)
            page.wait_for_selector('#__next > div.main-container.brc-20 > div > div:nth-child(2) > table > tbody > tr:nth-child(1) > td.to')
            next_page = page.query_selector_all('.ant-pagination-item-link')[-1]
            next_page.hover()
            next_page.click()
        except Exception as e:
            logging.exception('循环报错',e)
    
    page.close()
    context.close()
    browser.close()
    csv_file.close()
    
    
    