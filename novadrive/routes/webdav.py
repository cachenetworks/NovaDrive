from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, Response, current_app, jsonify, request

from novadrive.extensions import csrf
from novadrive.services.webdav_service import WebDavError, WebDavService

webdav_bp = Blueprint("webdav", __name__, url_prefix="/dav")


def _unauthorized_response() -> Response:
    response = Response(status=HTTPStatus.UNAUTHORIZED)
    response.headers["WWW-Authenticate"] = f'Basic realm="{current_app.config["WEBDAV_REALM"]}"'
    return response


def _dav_capability_headers(response: Response) -> Response:
    response.headers["DAV"] = "1"
    response.headers["MS-Author-Via"] = "DAV"
    response.headers["Allow"] = "OPTIONS, PROPFIND, GET, HEAD, PUT, DELETE, MKCOL, MOVE"
    return response


@webdav_bp.route("/", defaults={"resource_path": ""}, methods=["OPTIONS", "PROPFIND", "GET", "HEAD", "PUT", "DELETE", "MKCOL", "MOVE"])
@webdav_bp.route("/<path:resource_path>", methods=["OPTIONS", "PROPFIND", "GET", "HEAD", "PUT", "DELETE", "MKCOL", "MOVE"])
@csrf.exempt
def dispatch(resource_path: str):
    if not current_app.config["WEBDAV_ENABLED"]:
        return jsonify({"ok": False, "error": "WebDAV is disabled."}), 404

    user = WebDavService.authenticate_request()
    if not user:
        return _dav_capability_headers(_unauthorized_response())

    try:
        if request.method == "OPTIONS":
            return _dav_capability_headers(Response(status=HTTPStatus.NO_CONTENT))

        if request.method == "PROPFIND":
            payload = WebDavService.build_propfind_response(user, resource_path, request.headers.get("Depth"))
            response = Response(payload, status=207, mimetype="application/xml")
            return _dav_capability_headers(response)

        if request.method in {"GET", "HEAD"}:
            response = WebDavService.raw_file_response(user, resource_path)
            return _dav_capability_headers(response)

        if request.method == "PUT":
            status_code = WebDavService.put_file(user, resource_path)
            return _dav_capability_headers(Response(status=status_code))

        if request.method == "MKCOL":
            WebDavService.make_collection(user, resource_path)
            return _dav_capability_headers(Response(status=HTTPStatus.CREATED))

        if request.method == "DELETE":
            WebDavService.delete_resource(user, resource_path)
            return _dav_capability_headers(Response(status=HTTPStatus.NO_CONTENT))

        if request.method == "MOVE":
            WebDavService.move_resource(user, resource_path)
            return _dav_capability_headers(Response(status=HTTPStatus.NO_CONTENT))
    except WebDavError as exc:
        return _dav_capability_headers(Response(str(exc), status=exc.status_code, mimetype="text/plain"))
    except ValueError as exc:
        return _dav_capability_headers(Response(str(exc), status=HTTPStatus.BAD_REQUEST, mimetype="text/plain"))

    return _dav_capability_headers(Response(status=HTTPStatus.METHOD_NOT_ALLOWED))
