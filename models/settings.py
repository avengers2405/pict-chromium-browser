import json
import os

if os.path.isfile("settings.json"):  # If settings file exists, then open it
    print('here, file found')
    with open("settings.json", "r") as f:
        settings_data = json.load(f)
else:  # If settings not exists, then create a new file with default settings
    json_data = json.loads(
    """
    {
        "defaultSearchEngine": "Google",
        "startupPage": "https://google.com",
        "newTabPage": "https://google.com",
        "homeButtonPage": "https://google.com"
    }
    """
    )
    with open("settings.json", "w") as f:
        json.dump(json_data, f, indent=2)
    with open("settings.json", "r") as f:
        settings_data = json.load(f)