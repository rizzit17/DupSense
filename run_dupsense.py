import streamlit.web.cli as stcli
import sys
import os

if __name__ == "__main__":
    # Points to your app.py
    script_path = os.path.join(os.path.dirname(__file__), "app.py")
    sys.argv = ["streamlit", "run", script_path, "--global.developmentMode=false", "--server.port=8502"]
    sys.exit(stcli.main())
