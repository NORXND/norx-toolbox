import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

from quart import Quart, abort, jsonify, redirect, render_template, request, send_file

from norx_toolbox.bot.handlers.convert import escape_md
from norx_toolbox.coverters.providers import ffmpeg, pillow_conv
from norx_toolbox.coverters.registry import convert_file
from norx_toolbox.db import get_db
from norx_toolbox.delivery.deliver import deliver_to_chat
from norx_toolbox.delivery.storage import get_crop_session, get_upload_session, pop_upload_session, resolve_download

if TYPE_CHECKING:
    from norx_toolbox.bot.handlers.download import TaskManager

class QuartWithTaskManager(Quart):
    task_manager: 'TaskManager'

    """A Quart subclass that has a reference to the task manager instance, for use in routes."""
    def __init__(self, task_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_manager = task_manager
        self.template_folder=str(Path(__file__).parent / "templates")

    def set_task_manager(self, task_manager):
        self.task_manager = task_manager

app = QuartWithTaskManager(None, __name__)

@app.route("/")
async def root_redirect():
    me = await app.task_manager.bot.get_me()
    return redirect(f"https://t.me/{me.username}")

@app.route("/health")
async def health_check():
    return "OK!"

# --- CROP  ---

@app.route("/workspace/crop/<token>")
async def crop_page(token: str):
    session = get_crop_session(token)
    if session is None:
        abort(404)
    return await render_template(
        "crop.html",
        token=token,
        is_video=session.is_video,
        file_url=f"/workspace/crop/{token}/source",
    )


@app.route("/workspace/crop/<token>/source")
async def crop_source_file(token: str):
    session = get_crop_session(token)
    if session is None:
        abort(404)
    return await send_file(session.file_path)


@app.route("/workspace/crop/<token>/submit", methods=["POST"])
async def crop_submit(token: str):
    session = get_crop_session(token)
    if session is None:
        abort(404)

    data = await request.get_json()
    x, y, w, h = data["x"], data["y"], data["w"], data["h"]
    resize_w, resize_h = data.get("resize_w"), data.get("resize_h")

    output_path = session.file_path.parent / f"cropped_{session.file_path.name}"

    if session.is_video:
        result_path = await ffmpeg.crop_and_resize(session.file_path, output_path, x, y, w, h, resize_w, resize_h)
    else:
        result_path = await pillow_conv.crop_and_resize(session.file_path, output_path, x, y, w, h, resize_w, resize_h)

    await deliver_to_chat(app.task_manager.bot, session.chat_id, result_path)
    return {"status": "ok"}


# --- DOWNLOADS  ---

@app.route("/downloads/<token>/<filename>")
async def download_file(token: str, filename: str):
    path = resolve_download(token, filename)
    if path is None:
        abort(404)
    return await send_file(path, as_attachment=True)


@app.route("/go/<token>")
async def go_redirect(token: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT target_url, expires_at FROM short_links WHERE token = ?", (token,)
        ).fetchone()
        if row is None:
            abort(404)
        if row["expires_at"] is not None and row["expires_at"] < time.time():
            abort(404)
        conn.execute("UPDATE short_links SET hits = hits + 1 WHERE token = ?", (token,))
    return redirect(row["target_url"])


@app.route("/share/<token>/<filename>")
async def share_file(token: str, filename: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT path, expires_at FROM files WHERE token = ?", (token,)
        ).fetchone()
        if row is None or row["expires_at"] < time.time():
            abort(404)
    return await send_file(row["path"], as_attachment=True)


@app.route("/workspace/dashboard/<dash_token>")
async def dashboard(dash_token: str):
    with get_db() as conn:
        user_row = conn.execute("SELECT user_id FROM users WHERE dashboard_token = ?", (dash_token,)).fetchone()
        if user_row is None:
            abort(404)
        user_id = user_row["user_id"]

        links = conn.execute(
            "SELECT token, target_url, created_at, expires_at, hits FROM short_links "
            "WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        files = conn.execute(
            "SELECT token, filename, created_at, expires_at FROM files "
            "WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()

    return await render_template(
        "dashboard.html", dash_token=dash_token,
        links=[dict(r) for r in links], files=[dict(r) for r in files],
    )


@app.route("/api/dashboard/<dash_token>/links/<token>", methods=["DELETE"])
async def delete_link(dash_token: str, token: str):
    with get_db() as conn:
        user_row = conn.execute("SELECT user_id FROM users WHERE dashboard_token = ?", (dash_token,)).fetchone()
        if user_row is None:
            abort(404)
        conn.execute(
            "DELETE FROM short_links WHERE token = ? AND user_id = ?", (token, user_row["user_id"])
        )
    return jsonify({"status": "ok"})


@app.route("/api/dashboard/<dash_token>/files/<token>", methods=["DELETE"])
async def delete_file(dash_token: str, token: str):
    with get_db() as conn:
        user_row = conn.execute("SELECT user_id FROM users WHERE dashboard_token = ?", (dash_token,)).fetchone()
        if user_row is None:
            abort(404)
        row = conn.execute(
            "SELECT path FROM files WHERE token = ? AND user_id = ?", (token, user_row["user_id"])
        ).fetchone()
        if row:
            Path(row["path"]).parent.parent  # careful: don't rmtree beyond the token dir if you reuse layout
            import shutil
            shutil.rmtree(Path(row["path"]).parent, ignore_errors=True)
        conn.execute("DELETE FROM files WHERE token = ? AND user_id = ?", (token, user_row["user_id"]))
    return jsonify({"status": "ok"})

# --- DOWNLOADS ---


@app.route("/workspace/upload/<token>")
async def upload_page(token: str):
    session = get_upload_session(token)
    if session is None:
        abort(404)
    return await render_template(
        "upload.html", token=token, kind=session.kind, params=session.params
    )


@app.route("/workspace/upload/<token>/submit", methods=["POST"])
async def upload_submit(token: str):
    session = pop_upload_session(token)  # one-shot — consumed on use
    if session is None:
        abort(404)

    files = await request.files
    uploaded = files.get("file")
    if uploaded is None:
        return {"error": "no file provided"}, 400

    workdir = Path(tempfile.mkdtemp(prefix="upload_"))
    local_path = workdir / uploaded.filename
    await uploaded.save(local_path)

    try:
        if session.kind == "convert":
            result_path = await convert_file(
                local_path, session.params["format"], workdir
            )
        elif session.kind == "trim":
            output_path = workdir / "trimmed.mp4"
            result_path = await ffmpeg.trim(
                local_path, output_path, session.params["start"], session.params["end"]
            )
        else:
            return {"error": "unknown session kind"}, 400

        await deliver_to_chat(
            app.task_manager.bot,
            session.chat_id,
            result_path,
        )
        return {"status": "ok"}
    except Exception as e:
        await app.task_manager.bot.send_message(session.chat_id, escape_md(f"Job failed: {str(e)}"))
        return {"error": str(e)}, 500
