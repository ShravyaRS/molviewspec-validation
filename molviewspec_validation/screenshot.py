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
    """Firefox WebDriver via Xvfb on :99.

    Headless Firefox doesn't support WebGL (Mozilla bug 1375585), and
    Mol* needs WebGL for volume rendering. We use Xvfb (a virtual X
    server) so Firefox runs non-headless but invisible.
    """
    os.environ['DISPLAY'] = ':99'
    os.environ.setdefault('XDG_RUNTIME_DIR', '/tmp/runtime-root')
    os.environ.setdefault('MOZ_ENABLE_WAYLAND', '0')
    os.makedirs(os.environ['XDG_RUNTIME_DIR'], exist_ok=True)

    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service

    options = Options()
    options.set_preference('layout.css.devPixelsPerPx', str(pixel_ratio))
    options.set_preference('webgl.force-enabled', True)
    options.set_preference('webgl.disabled', False)
    options.set_preference('layers.acceleration.force-enabled', True)

    firefox_path = shutil.which('firefox')
    if firefox_path:
        options.binary_location = firefox_path

    geckodriver_path = shutil.which('geckodriver')
    service = Service(executable_path=geckodriver_path) if geckodriver_path else Service()

    driver = webdriver.Firefox(service=service, options=options)
    driver.set_window_size(width, height)
    return driver

def screenshot_html(html_path, output_path, wait_seconds=30, driver=None,
                    max_attempts=5, min_size_bytes=500_000):
    """Render HTML -> PNG, retrying up to max_attempts on blank output.

    A blank screenshot (file < min_size_bytes) typically means Mol* finished
    loading before the volume isosurface had been computed. WebGL is now
    working via Xvfb, but timing can still race; a retry with a fresh
    browser session resolves it most of the time.
    """
    import os
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            _do_screenshot_once(html_path, output_path, wait_seconds, driver=None)
        except Exception as e:
            last_err = e
            print(f"  [retry] attempt {attempt} raised {type(e).__name__}: {e}")
            continue
        if os.path.exists(output_path):
            sz = os.path.getsize(output_path)
            if sz >= min_size_bytes:
                if attempt > 1:
                    print(f"  [retry] succeeded on attempt {attempt} ({sz//1024}KB)")
                return
            print(f"  [retry] attempt {attempt}/{max_attempts}: {sz//1024}KB blank, retrying")
    if last_err:
        raise last_err
    print(f"  [retry] all {max_attempts} attempts produced blank output")


def _do_screenshot_once(html_path, output_path, wait_seconds=30, driver=None):
    """Render an HTML file to a PNG screenshot.
    
    If no driver is provided, creates and destroys a fresh one
    (recommended for reliability with large scenes).
    """
    close_driver = driver is None
    if close_driver:
        driver = _setup_driver()
    try:
        driver.get(f"file://{os.path.abspath(html_path)}")
        # Poll for the rendering-complete flag instead of fixed sleep
        from selenium.webdriver.support.ui import WebDriverWait
        try:
            WebDriverWait(driver, wait_seconds).until(
                lambda d: d.execute_script("return window.__rendered === true")
            )
            # Small additional settle time for the final frame
            time.sleep(2)
        except Exception:
            print(f"  [warn] readiness flag never set within {wait_seconds}s, "
                  f"taking screenshot anyway")
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
