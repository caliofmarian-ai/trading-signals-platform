from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Optional Trading Signals companion application")
    parser.add_argument("command",nargs="?",default="serve",choices=["serve","worker","create-owner","invite"])
    parser.add_argument("--data-dir",type=Path,default=Path(os.getenv("SIGNALS_APP_DATA_DIR",str(Path(__file__).parent/".local"))))
    parser.add_argument("--email")
    parser.add_argument("--subscriber-ref")
    args = parser.parse_args()
    if args.command == "worker":
        from .worker import run
        run(args.data_dir)
        return
    if args.command in {"create-owner","invite"}:
        from .api import email_address
        from .store import Store
        from .service import AppService
        store = Store(args.data_dir)
        email = email_address(args.email or input("Account email: "))
        if args.command == "create-owner":
            store.register(email,getpass.getpass("New owner password (12+ characters): "),role="OWNER")
            print("Application owner account created.")
        else:
            if not args.subscriber_ref:
                parser.error("--subscriber-ref is required")
            AppService(store).verify_subscriber(args.subscriber_ref)
            token = store.invite(email,args.subscriber_ref)
            print(os.environ["SIGNALS_APP_PUBLIC_URL"].rstrip("/")+"/#claim="+token)
        return
    import uvicorn
    from .api import create_app
    child = None
    if os.getenv("SIGNALS_APP_ENGINE_ENABLED") == "1":
        child = subprocess.Popen([sys.executable,"-m","apps.signals_app","worker","--data-dir",str(args.data_dir.resolve())])
    try:
        uvicorn.run(create_app(args.data_dir),host="0.0.0.0",port=int(os.getenv("PORT","8765")),access_log=False)
    finally:
        if child:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
