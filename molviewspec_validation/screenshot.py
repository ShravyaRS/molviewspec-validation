"""Static image export using headless Firefox + Selenium.

Renders MolViewSpec HTML views to HD PNG images for PDF reports.
Uses a fresh browser instance per screenshot to avoid memory issues
with large molecular scenes.
"""

import os
import time
import shutil
import threading
import http.server
import functools
from typing import Optional


def _setup_driver(width=1920, height=1080, pixel_ratio=2.0):
    """Create a headless Firefox WebDriver with HD rendering."""
    os.environ.setdefault('XDG_RUNTIME_DIR', '/tmp/runtime-root')
    os.environ.setdefault('MOZ_ENABLE_WAYLAND', '0')
    os.makedirs(os.environ['XDG_RUNTIME_DIR'], exist_ok=True)

    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service

    options = Options()
    options.add_argument('-headless')
    options.set_preference('layout.css.devPixelsPerPx', str(pixel_ratio))

    firefox_path = shutil.which('firefox')
    if firefox_path:
        options.binary_location = firefox_path

    geckodriver_path = shutil.which('geckodriver')
    service = Service(executable_path=geckodriver_path) if geckodriver_path else Service()

    driver = webdriver.Firefox(service=service, options=options)
    driver.set_window_size(width, height)
    return driver


def screenshot_html(html_path, output_path, wait_seconds=30, driver=None):
    """Render an HTML file to a PNG screenshot.
    
    If no driver is provided, creates and destroys a fresh one
    (recommended for reliability with large scenes).
    """
    close_driver = driver is None
    if close_driver:
        driver = _setup_driver()
    try:
        driver.get(f"file://{os.path.abspath(html_path)}")
        time.sleep(wait_seconds)
        driver.save_screenshot(output_path)
    finally:
        if close_driver:
            try:
                driver.quit()
            except Exception:
                pass
    return output_path


def _start_http_server(directory, port=0):
    """Start a local HTTP server for serving CIF files to Mol*."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=directory
    )
    server = http.server.HTTPServer(('127.0.0.1', port), handler)
    actual_port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, actual_port


def generate_screenshots(pdb_id, emdb_id, output_dir=".",
                         scene_types=None, wait_seconds=35):
    """Generate all HD validation screenshots for an entry.
    
    Uses a fresh browser instance per screenshot for reliability.
    """
    from molviewspec_validation.scenes import generate_all_views

    os.makedirs(output_dir, exist_ok=True)
    if scene_types is None:
        scene_types = ["map_model", "qscore"]

    html_dir = os.path.join(output_dir, "html")
    html_outputs = generate_all_views(pdb_id, emdb_id, output_dir=html_dir,
                                      scene_types=scene_types)

    screenshots = {}
    for html_name, html_path in html_outputs.items():
        png_name = html_name.replace(".html", ".png")
        png_path = os.path.join(output_dir, png_name)
        screenshot_html(html_path, png_path, wait_seconds=wait_seconds)
        screenshots[png_name] = png_path

    return screenshots
