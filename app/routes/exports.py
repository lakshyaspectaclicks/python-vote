from __future__ import annotations

from flask import Blueprint, Response, flash, redirect, request, session, url_for

from app.repositories.audit_repository import AuditLogRepository
from app.services.export_service import ExportService
from app.services.result_service import ResultService
from app.utils.auth import admin_login_required
from app.utils.exceptions import ElectionStateError, ValidationError

bp = Blueprint("exports", __name__, url_prefix="/admin/elections")
result_service = ResultService()
export_service = ExportService()
audit_repo = AuditLogRepository()


def _audit_export(election_id: int, export_type: str) -> None:
    admin_id = session.get("admin_id")
    audit_repo.log(
        admin_id=int(admin_id) if admin_id else None,
        action="RESULT_EXPORT",
        entity_type="ELECTION",
        entity_id=election_id,
        details=f"Exported results as {export_type}.",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
    )


@bp.route("/<int:election_id>/export/csv")
@admin_login_required
def export_csv(election_id: int):
    try:
        payload = result_service.get_results(election_id, admin_preview=True)
        csv_data = export_service.build_results_csv(payload)
        _audit_export(election_id, "CSV")
        filename = f"election_{election_id}_results.csv"
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except (ValidationError, ElectionStateError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("admin.results", election_id=election_id))


@bp.route("/<int:election_id>/export/pdf")
@admin_login_required
def export_pdf(election_id: int):
    try:
        payload = result_service.get_results(election_id, admin_preview=True)
        pdf_data = export_service.build_results_pdf(payload)
        _audit_export(election_id, "PDF")
        filename = f"election_{election_id}_results.pdf"
        return Response(
            pdf_data,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except (ValidationError, ElectionStateError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("admin.results", election_id=election_id))

