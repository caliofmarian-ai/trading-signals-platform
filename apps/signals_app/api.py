from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import hashlib
import io
import zipfile
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import canonical
from .push import PushDelivery, valid_subscription
from .service import AppService
from .store import Store, token_hash

STATIC = Path(__file__).parent / "static"
ANDROID_RELEASE = Path(__file__).parent / "android" / "releases" / "TradingSignals-0.1.1-test.apk"
COOKIE = "signals_session"


def email_address(value) -> str:
    if not isinstance(value,str) or len(value)>254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",value):
        raise ValueError("Enter a valid email address.")
    return value.strip().casefold()


def create_app(directory: Path | None = None, *, public_url: str | None = None,
               ingest_token: str | None = None, setup_token: str | None = None) -> FastAPI:
    directory = directory or Path(os.getenv("SIGNALS_APP_DATA_DIR",str(Path(__file__).parent/".local")))
    public_url = (public_url or os.getenv("SIGNALS_APP_PUBLIC_URL","http://127.0.0.1:8765")).rstrip("/")
    parsed = urlsplit(public_url)
    if parsed.scheme != "https" and parsed.hostname not in {"localhost","127.0.0.1","testserver"}:
        raise ValueError("Use HTTPS outside local development.")
    ingest_token = ingest_token or os.getenv("SIGNALS_APP_INGEST_TOKEN","")
    setup_token = setup_token or os.getenv("SIGNALS_APP_SETUP_TOKEN","")
    store = Store(directory)
    service = AppService(store)
    push = PushDelivery(service,public_url)

    @asynccontextmanager
    async def lifespan(_app):
        async def notifications():
            while True:
                try:
                    await asyncio.to_thread(push.drain)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    store.audit("PUSH_WORKER_ERROR","APP",type(exc).__name__)
                await asyncio.sleep(1)
        task = asyncio.create_task(notifications())
        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    app = FastAPI(title="Trading Signals App",docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
    app.state.service, app.state.store, app.state.push = service,store,push

    def android_package():
        # A published, versioned test build takes precedence over the legacy volume upload.
        return ANDROID_RELEASE if ANDROID_RELEASE.is_file() else store.directory/"TradingSignals-test.apk"

    @app.middleware("http")
    async def protection(request: Request, call_next):
        if request.method in {"POST","PUT","DELETE","PATCH"}:
            origin = request.headers.get("origin")
            if origin and origin.rstrip("/") != public_url:
                return JSONResponse({"detail":"This request must originate from the application."},status_code=403)
            if request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse({"detail":"Cross-site requests are not allowed."},status_code=403)
            length = request.headers.get("content-length","")
            max_body = 32*1024*1024 if request.url.path == "/api/internal/android-apk" else 2*1024*1024
            if not length.isdigit() or int(length)>max_body:
                return JSONResponse({"detail":"A bounded request body is required."},status_code=413)
        response = await call_next(request)
        response.headers.update({
            "X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY",
            "Referrer-Policy":"no-referrer","Permissions-Policy":"camera=(), microphone=(), geolocation=()",
            "Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; worker-src 'self'; manifest-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        })
        if request.url.path.startswith("/api/") or request.url.path == "/sw.js":
            response.headers["Cache-Control"]="no-store"
        elif request.url.path.startswith("/assets/"):
            response.headers["Cache-Control"]="no-cache"
        if parsed.scheme == "https":
            response.headers["Strict-Transport-Security"]="max-age=31536000"
        return response

    @app.exception_handler(ValueError)
    async def bad_input(_request,exc):
        return JSONResponse({"detail":str(exc)[:250]},status_code=400)

    @app.exception_handler(sqlite3.IntegrityError)
    async def duplicate(_request,_exc):
        return JSONResponse({"detail":"The account or connection already exists."},status_code=409)

    def user(request: Request, mutate: bool = False):
        found = store.session(request.cookies.get(COOKIE))
        if not found:
            raise HTTPException(401,"Sign in to continue.")
        if mutate and not hmac.compare_digest(request.headers.get("x-csrf-token",""),found["csrf"]):
            raise HTTPException(403,"Refresh your session and try again.")
        return found

    def owner(request: Request, mutate: bool = False):
        found = user(request,mutate)
        if found["role"] != "OWNER":
            raise HTTPException(403,"Application owner access is required.")
        return found

    def source(request: Request):
        if len(ingest_token)<32 or not hmac.compare_digest(request.headers.get("authorization",""),"Bearer "+ingest_token):
            raise HTTPException(401,"Source authentication is required.")

    async def body(request: Request):
        raw = await request.body()
        if len(raw)>2*1024*1024:
            raise HTTPException(413,"The request is too large.")
        try:
            result = json.loads(raw)
        except (ValueError,UnicodeError):
            raise HTTPException(400,"Invalid JSON.")
        if not isinstance(result,dict):
            raise HTTPException(400,"A JSON object is required.")
        return result

    def session_response(uid: str):
        token,csrf = store.start_session(uid)
        response = JSONResponse({"ok":True,"csrf":csrf})
        response.set_cookie(COOKIE,token,max_age=7*24*3600,httponly=True,
                            secure=parsed.scheme=="https",samesite="strict",path="/")
        return response

    def rate(request: Request, kind: str, limit: int, window: int = 60):
        host = request.client.host if request.client else "unknown"
        if not store.allow_attempt(kind+":"+token_hash(host),limit,window):
            raise HTTPException(429,"Too many attempts. Please try again shortly.")

    @app.get("/healthz")
    def health():
        return {"status":"ok","surface":"APP"}

    @app.get("/.well-known/assetlinks.json")
    def android_association():
        fingerprints = [value.strip().upper() for value in os.getenv("SIGNALS_APP_ANDROID_SHA256","").split(",") if value.strip()]
        if not fingerprints or any(not re.fullmatch(r"(?:[0-9A-F]{2}:){31}[0-9A-F]{2}",value) for value in fingerprints):
            return []
        return [{"relation":["delegate_permission/common.handle_all_urls"],"target":{
            "namespace":"android_app","package_name":"com.caliof.tradingsignals",
            "sha256_cert_fingerprints":fingerprints}}]

    @app.get("/api/config")
    def config():
        with store.db() as db:
            configured = bool(db.execute("SELECT 1 FROM users WHERE role='OWNER'").fetchone())
        return {"channels":service.channels,"canonical":canonical.manifest(),
                "push_public_key":push.public_key,"owner_configured":configured,
                "android_download": "/download/android" if android_package().is_file() else None,
                "installable":True,"setup_available":bool(setup_token) and not configured}

    @app.post("/api/register")
    async def register(request: Request):
        rate(request,"register",8,3600)
        data = await body(request)
        account = store.register(email_address(data.get("email")),data.get("password"))
        return session_response(account["id"])

    @app.post("/api/setup")
    async def setup(request: Request):
        rate(request,"owner-setup",5)
        data = await body(request)
        supplied = data.get("token","")
        if not isinstance(supplied,str) or len(setup_token)<32 or not hmac.compare_digest(supplied,setup_token):
            raise HTTPException(403,"Invalid application setup key.")
        account = store.register(email_address(data.get("email")),data.get("password"),role="OWNER")
        return session_response(account["id"])

    @app.post("/api/login")
    async def login(request: Request):
        rate(request,"login",10)
        data = await body(request)
        account = store.authenticate(email_address(data.get("email")),data.get("password"))
        if not account:
            raise HTTPException(401,"Email or password is incorrect.")
        return session_response(account["id"])

    @app.post("/api/logout")
    def logout(request: Request):
        account = user(request,True)
        store.logout(request.cookies[COOKIE],account["id"])
        response = JSONResponse({"ok":True})
        response.delete_cookie(COOKIE,path="/")
        return response

    @app.get("/api/session")
    def session(request: Request):
        account = user(request)
        access = service.entitlement(account)
        return {"email":account["email"],"role":account["role"],"csrf":account["csrf"],
                "access":access,"allowed_channels":[ch["id"] for ch in service.channels if service.can_read(account,ch["id"])],
                "status":service.status()}

    @app.get("/api/signals/{channel}")
    def signals(channel: str,request: Request,before: int | None = None):
        account = user(request)
        if not service.can_read(account,channel):
            raise HTTPException(403,"Your current subscription does not grant access to this channel.")
        return {"signals":service.feed(channel,before=before),"server_time":int(time.time()),"status":service.status()}

    @app.post("/api/claim")
    async def claim(request: Request):
        account = user(request,True)
        rate(request,"claim",5)
        data = await body(request)
        token = data.get("token","")
        if not isinstance(token,str) or len(token)>150:
            raise ValueError("Invalid connection link.")
        store.claim(account["id"],account["email"],token,service.verify_subscriber)
        return {"ok":True}

    @app.post("/api/push")
    async def subscribe_push(request: Request):
        account = user(request,True)
        data = valid_subscription(await body(request))
        with store.db() as db:
            # One physical browser endpoint belongs to one signed-in app identity.
            db.execute("INSERT OR REPLACE INTO devices VALUES (?,?,?,?)",
                       (data["endpoint"],account["id"],json.dumps(data),int(time.time())))
        return {"ok":True}

    @app.delete("/api/push")
    def unsubscribe_push(request: Request):
        account = user(request,True)
        with store.db() as db:
            db.execute("DELETE FROM pushes WHERE endpoint IN (SELECT endpoint FROM devices WHERE user_id=?)",(account["id"],))
            db.execute("DELETE FROM devices WHERE user_id=?",(account["id"],))
        return {"ok":True}

    @app.post("/api/feedback")
    async def feedback(request: Request):
        account = user(request,True)
        data = await body(request)
        sid,result = data.get("signal_id"),data.get("result")
        if not isinstance(sid,str) or result not in {"WIN","LOSE","MISSED"}:
            raise ValueError("Invalid personal result.")
        access = service.entitlement(account)
        if access["tier"] != "ELITE" and account["role"] != "OWNER":
            raise HTTPException(403,"Personal result reporting belongs to the Elite channel.")
        with store.db() as db:
            rows = db.execute("SELECT channel,payload FROM signals WHERE signal_id=? AND stage='OPEN_NOW'",(sid,)).fetchall()
            visible = [row for row in rows if service.can_read(account,row["channel"])]
            if not visible or json.loads(visible[0]["payload"])["expires_at"]>time.time():
                raise HTTPException(403,"Wait until your published signal expires before reporting a result.")
            db.execute("INSERT OR REPLACE INTO feedback VALUES (?,?,?,?)",
                       (account["id"],sid,result,int(time.time())))
        return {"ok":True,"truth_domain":"COMMUNITY_SELF_REPORT"}

    @app.get("/api/admin")
    def dashboard(request: Request):
        owner(request)
        from .source import snapshot
        return {"metrics":service.metrics(),"status":service.status(),"canonical":canonical.manifest(),
                "source":snapshot(store)}

    @app.post("/api/admin/invites")
    async def invite(request: Request):
        account = owner(request,True)
        data = await body(request)
        subscriber = data.get("subscriber_ref")
        if not isinstance(subscriber,str) or not 1<=len(subscriber)<=200:
            raise ValueError("A verified subscriber reference is required.")
        service.verify_subscriber(subscriber)
        token = store.invite(email_address(data.get("email")),subscriber)
        store.audit("CONNECTION_LINK_CREATED",account["id"],"15 minute email-bound single-use link")
        return {"url":public_url+"/#claim="+token,"expires_in":900}

    @app.post("/api/internal/subscriptions")
    async def subscriptions(request: Request):
        source(request)
        data = await body(request)
        service.import_subscriptions(data.get("records"),data.get("generated_at"))
        return {"ok":True}

    @app.post("/api/internal/signals")
    async def ingest(request: Request):
        source(request)
        data = await body(request)
        if not isinstance(data.get("candidate"),dict):
            raise ValueError("An existing-engine SignalEvent is required.")
        result = service.publish(data["candidate"],provider=data.get("provider"))
        return result

    @app.post("/api/internal/android-apk")
    async def android_upload(request: Request):
        source(request)
        payload = await request.body()
        if not 1 <= len(payload) <= 32*1024*1024:
            raise HTTPException(413,"Invalid Android package size.")
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as package:
                names = package.namelist()
                if "AndroidManifest.xml" not in names or "classes.dex" not in names:
                    raise ValueError("An Android APK package is required.")
        except zipfile.BadZipFile as exc:
            raise ValueError("An Android APK package is required.") from exc
        target = store.directory/"TradingSignals-test.apk"
        temporary = target.with_suffix(".upload")
        temporary.write_bytes(payload)
        temporary.replace(target)
        digest = hashlib.sha256(payload).hexdigest()
        store.set_meta("android_apk_sha256",digest)
        return {"sha256":digest,"bytes":len(payload),"url":public_url+"/download/android"}

    @app.get("/download/android")
    def android_download():
        target = android_package()
        if not target.is_file():
            raise HTTPException(404,"The Android test package is not available yet.")
        return FileResponse(target,filename=target.name,
            media_type="application/vnd.android.package-archive",headers={"Cache-Control":"no-store"})

    @app.get("/")
    def index():
        return FileResponse(STATIC/"index.html",headers={"Cache-Control":"no-cache"})

    @app.get("/sw.js")
    def service_worker():
        return FileResponse(STATIC/"sw.js",media_type="application/javascript",headers={"Service-Worker-Allowed":"/"})

    app.mount("/assets",StaticFiles(directory=STATIC),name="assets")
    return app
