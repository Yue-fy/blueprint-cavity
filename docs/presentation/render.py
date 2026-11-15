#!/usr/bin/env python3
"""Print the native 16:9 HTML deck with Playwright Chromium.

Install: python -m pip install playwright && python -m playwright install chromium
Run: python docs/presentation/render.py
An existing browser can be selected with --chromium-path or BROWSER_EXECUTABLE.
"""
from pathlib import Path
import argparse
import json
import os

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PDF = HERE / 'Blueprint-Cavity-Presentation.pdf'


def main(browser_path=None):
    with sync_playwright() as p:
        launch_options = {'headless': True,
            'args': ['--no-sandbox', '--disable-gpu', '--renderer-process-limit=1']}
        if browser_path:
            launch_options['executable_path'] = browser_path
        browser = p.chromium.launch(**launch_options)
        page = browser.new_page(viewport={'width': 1280, 'height': 720}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto((HERE / 'presentation.html').as_uri(), wait_until='load')
        page.evaluate('document.fonts.ready')
        page.locator('img').evaluate_all('(imgs) => Promise.all(imgs.map(img => img.decode()))')
        report = page.evaluate('''() => [...document.querySelectorAll('.slide')].map((slide,i)=>{
          const bounds=slide.getBoundingClientRect();
          const outside=[...slide.querySelectorAll('h1,h2,h3,p,.footer,.legend,.answer,.bar-row,.reward-legend,.closing-links')].filter(el=>{
            const r=el.getBoundingClientRect();return r.left<bounds.left-1||r.top<bounds.top-1||r.right>bounds.right+1||r.bottom>bounds.bottom+1;
          }).map(el=>el.innerText);
          return {page:i+1,title:slide.dataset.title,width:bounds.width,height:bounds.height,outside};
        })''')
        if len(report) != 8 or any(item['outside'] for item in report) or errors:
            raise RuntimeError({'layout': report, 'errors': errors})
        page.pdf(path=str(PDF), prefer_css_page_size=True, print_background=True,
                 display_header_footer=False, tagged=True, outline=True)
        browser.close()
    if PDF.stat().st_size >= 20_000_000:
        raise RuntimeError('Presentation exceeds the 20 MB submission limit')
    (HERE / 'layout-check.json').write_text(json.dumps({'pages': report, 'browser_errors': errors,
        'pdf_bytes': PDF.stat().st_size}, indent=2))
    print(f'{PDF}: 8 pages, 16:9, {PDF.stat().st_size:,} bytes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium-path', default=os.environ.get('BROWSER_EXECUTABLE'),
                        help='Optional existing Chromium executable; defaults to Playwright Chromium')
    main(parser.parse_args().chromium_path)
