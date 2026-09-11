import subprocess
import os
import time

views = [
    ("citizen", "screenshot_citizen.png"),
    ("dispatch", "screenshot_dispatch.png"),
    ("timeline", "screenshot_timeline.png"),
    ("report", "screenshot_report.png"),
    ("responder", "screenshot_responder.png")
]

temp_dir = os.environ.get("TEMP", ".")
chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

for tab, filename in views:
    out_temp = os.path.join(temp_dir, f"temp_{filename}")
    if os.path.exists(out_temp):
        os.remove(out_temp)
    url = f"http://127.0.0.1:8000/?demo=admin&tab={tab}"
    args = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--window-size=1400,900",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=3000",
        f"--screenshot={out_temp}",
        url
    ]
    subprocess.run(args)
    if os.path.exists(out_temp):
        target = os.path.join("c:\\Users\\PREMTEJA\\OneDrive\\Desktop\\resqagent", filename)
        if os.path.exists(target):
            os.remove(target)
        os.replace(out_temp, target)
        print(f"[OK] Captured {filename} ({os.path.getsize(target)} bytes)")
    else:
        print(f"[FAIL] Could not capture {filename}")
