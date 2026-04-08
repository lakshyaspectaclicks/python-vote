from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.repositories.audit_repository import AuditLogRepository
from app.services.candidate_service import CandidateService
from app.services.election_service import ElectionService
from app.services.position_service import PositionService
from app.services.result_service import ResultService
from app.services.voter_service import VoterService
from app.utils.auth import admin_login_required
from app.utils.exceptions import ElectionStateError, ValidationError

bp = Blueprint("admin", __name__, url_prefix="/admin")

election_service = ElectionService()
position_service = PositionService()
candidate_service = CandidateService()
voter_service = VoterService()
result_service = ResultService()
audit_repo = AuditLogRepository()


def _admin_id() -> int:
    return int(session["admin_id"])


@bp.route("/")
@admin_login_required
def dashboard():
    stats = election_service.dashboard_stats()
    elections = election_service.list_elections()[:8]
    audit_logs = audit_repo.list_logs(limit=12)
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        elections=elections,
        audit_logs=audit_logs,
    )


@bp.route("/elections")
@admin_login_required
def elections():
    return render_template("admin/elections.html", elections=election_service.list_elections())


@bp.route("/elections/create", methods=["GET", "POST"])
@admin_login_required
def election_create():
    if request.method == "POST":
        try:
            election_id = election_service.create_election(
                name=request.form.get("name", ""),
                description=request.form.get("description"),
                start_at=request.form.get("start_at") or None,
                end_at=request.form.get("end_at") or None,
                admin_id=_admin_id(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            flash("Election created.", "success")
            return redirect(url_for("admin.election_edit", election_id=election_id))
        except ValidationError as exc:
            flash(str(exc), "error")
    return render_template("admin/election_form.html", election=None)


@bp.route("/elections/<int:election_id>/edit", methods=["GET", "POST"])
@admin_login_required
def election_edit(election_id: int):
    election = election_service.get_election(election_id)
    if not election:
        flash("Election not found.", "error")
        return redirect(url_for("admin.elections"))

    if request.method == "POST":
        try:
            election_service.update_election(
                election_id=election_id,
                name=request.form.get("name", ""),
                description=request.form.get("description"),
                start_at=request.form.get("start_at") or None,
                end_at=request.form.get("end_at") or None,
                results_visible=bool(request.form.get("results_visible")),
                admin_id=_admin_id(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            flash("Election updated.", "success")
            return redirect(url_for("admin.election_edit", election_id=election_id))
        except (ValidationError, ElectionStateError) as exc:
            flash(str(exc), "error")
    election = election_service.get_election(election_id)
    return render_template("admin/election_form.html", election=election)


@bp.route("/elections/<int:election_id>/delete", methods=["POST"])
@admin_login_required
def election_delete(election_id: int):
    try:
        election_service.delete_election(
            election_id=election_id,
            admin_id=_admin_id(),
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
        flash("Election deleted.", "success")
    except (ValidationError, ElectionStateError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.elections"))


@bp.route("/elections/<int:election_id>/status", methods=["POST"])
@admin_login_required
def election_status(election_id: int):
    next_status = request.form.get("status", "").strip().upper()
    try:
        election_service.change_status(
            election_id=election_id,
            next_status=next_status,
            admin_id=_admin_id(),
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
        flash(f"Election moved to {next_status}.", "success")
    except (ValidationError, ElectionStateError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.election_edit", election_id=election_id))


@bp.route("/elections/<int:election_id>/positions", methods=["GET", "POST"])
@admin_login_required
def positions(election_id: int):
    election = election_service.get_election(election_id)
    if not election:
        flash("Election not found.", "error")
        return redirect(url_for("admin.elections"))
    if request.method == "POST":
        try:
            position_service.create_position(
                election_id=election_id,
                name=request.form.get("name", ""),
                display_order=int(request.form.get("display_order", "1")),
                admin_id=_admin_id(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            flash("Position created.", "success")
            return redirect(url_for("admin.positions", election_id=election_id))
        except (ValueError, ValidationError) as exc:
            flash(str(exc), "error")
    return render_template(
        "admin/positions.html",
        election=election,
        positions=position_service.list_positions(election_id),
    )


@bp.route("/positions/<int:position_id>/edit", methods=["GET", "POST"])
@admin_login_required
def position_edit(position_id: int):
    position = position_service.get_position(position_id)
    if not position:
        flash("Position not found.", "error")
        return redirect(url_for("admin.elections"))
    election_id = position["election_id"]
    if request.method == "POST":
        try:
            position_service.update_position(
                position_id=position_id,
                name=request.form.get("name", ""),
                display_order=int(request.form.get("display_order", "1")),
                admin_id=_admin_id(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            flash("Position updated.", "success")
            return redirect(url_for("admin.positions", election_id=election_id))
        except (ValueError, ValidationError) as exc:
            flash(str(exc), "error")
    return render_template("admin/position_form.html", position=position)


@bp.route("/positions/<int:position_id>/delete", methods=["POST"])
@admin_login_required
def position_delete(position_id: int):
    position = position_service.get_position(position_id)
    if not position:
        flash("Position not found.", "error")
        return redirect(url_for("admin.elections"))
    election_id = position["election_id"]
    try:
        position_service.delete_position(
            position_id=position_id,
            admin_id=_admin_id(),
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
        flash("Position deleted.", "success")
    except ValidationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.positions", election_id=election_id))


@bp.route("/elections/<int:election_id>/candidates", methods=["GET", "POST"])
@admin_login_required
def candidates(election_id: int):
    election = election_service.get_election(election_id)
    if not election:
        flash("Election not found.", "error")
        return redirect(url_for("admin.elections"))

    positions = position_service.list_positions(election_id)
    if request.method == "POST":
        try:
            candidate_service.create_candidate(
                election_id=election_id,
                position_id=int(request.form.get("position_id", "0")),
                full_name=request.form.get("full_name", ""),
                class_name=request.form.get("class_name", ""),
                gender=request.form.get("gender"),
                bio=request.form.get("bio"),
                photo_file=request.files.get("photo"),
                admin_id=_admin_id(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            flash("Candidate created.", "success")
            return redirect(url_for("admin.candidates", election_id=election_id))
        except (ValueError, ValidationError) as exc:
            flash(str(exc), "error")

    return render_template(
        "admin/candidates.html",
        election=election,
        positions=positions,
        candidates=candidate_service.list_candidates(election_id),
    )


@bp.route("/candidates/<int:candidate_id>/edit", methods=["GET", "POST"])
@admin_login_required
def candidate_edit(candidate_id: int):
    candidate = candidate_service.get_candidate(candidate_id)
    if not candidate:
        flash("Candidate not found.", "error")
        return redirect(url_for("admin.elections"))

    election_id = candidate["election_id"]
    if request.method == "POST":
        try:
            candidate_service.update_candidate(
                candidate_id=candidate_id,
                position_id=int(request.form.get("position_id", "0")),
                full_name=request.form.get("full_name", ""),
                class_name=request.form.get("class_name", ""),
                gender=request.form.get("gender"),
                bio=request.form.get("bio"),
                photo_file=request.files.get("photo"),
                remove_photo=bool(request.form.get("remove_photo")),
                is_active=bool(request.form.get("is_active")),
                admin_id=_admin_id(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            flash("Candidate updated.", "success")
            return redirect(url_for("admin.candidates", election_id=election_id))
        except (ValueError, ValidationError) as exc:
            flash(str(exc), "error")

    return render_template(
        "admin/candidate_form.html",
        candidate=candidate,
        positions=position_service.list_positions(election_id),
    )


@bp.route("/candidates/<int:candidate_id>/delete", methods=["POST"])
@admin_login_required
def candidate_delete(candidate_id: int):
    candidate = candidate_service.get_candidate(candidate_id)
    if not candidate:
        flash("Candidate not found.", "error")
        return redirect(url_for("admin.elections"))
    election_id = candidate["election_id"]
    try:
        candidate_service.delete_candidate(
            candidate_id=candidate_id,
            admin_id=_admin_id(),
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
        flash("Candidate deleted.", "success")
    except ValidationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.candidates", election_id=election_id))


@bp.route("/elections/<int:election_id>/voters", methods=["GET", "POST"])
@admin_login_required
def voters(election_id: int):
    election = election_service.get_election(election_id)
    if not election:
        flash("Election not found.", "error")
        return redirect(url_for("admin.elections"))
    if request.method == "POST":
        try:
            voter_service.create_voter(
                election_id=election_id,
                student_id=request.form.get("student_id", ""),
                full_name=request.form.get("full_name", ""),
                class_name=request.form.get("class_name", ""),
                pin=request.form.get("pin"),
                pin_required=bool(request.form.get("pin_required")),
                admin_id=_admin_id(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            flash("Voter added.", "success")
            return redirect(url_for("admin.voters", election_id=election_id))
        except ValidationError as exc:
            flash(str(exc), "error")

    return render_template(
        "admin/voters.html",
        election=election,
        voters=voter_service.list_voters(election_id),
    )


@bp.route("/voters/<int:voter_id>/edit", methods=["GET", "POST"])
@admin_login_required
def voter_edit(voter_id: int):
    voter = voter_service.get_voter(voter_id)
    if not voter:
        flash("Voter not found.", "error")
        return redirect(url_for("admin.elections"))
    election_id = voter["election_id"]
    if request.method == "POST":
        try:
            pin_value = request.form.get("pin")
            voter_service.update_voter(
                voter_id=voter_id,
                student_id=request.form.get("student_id", ""),
                full_name=request.form.get("full_name", ""),
                class_name=request.form.get("class_name", ""),
                pin=pin_value,
                pin_required=bool(request.form.get("pin_required")),
                is_active=bool(request.form.get("is_active")),
                admin_id=_admin_id(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            flash("Voter updated.", "success")
            return redirect(url_for("admin.voters", election_id=election_id))
        except ValidationError as exc:
            flash(str(exc), "error")
    return render_template("admin/voter_form.html", voter=voter)


@bp.route("/voters/<int:voter_id>/delete", methods=["POST"])
@admin_login_required
def voter_delete(voter_id: int):
    voter = voter_service.get_voter(voter_id)
    if not voter:
        flash("Voter not found.", "error")
        return redirect(url_for("admin.elections"))
    election_id = voter["election_id"]
    try:
        voter_service.delete_voter(
            voter_id=voter_id,
            admin_id=_admin_id(),
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
        flash("Voter deleted.", "success")
    except ValidationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.voters", election_id=election_id))


@bp.route("/elections/<int:election_id>/voters/import", methods=["GET", "POST"])
@admin_login_required
def voter_import(election_id: int):
    election = election_service.get_election(election_id)
    if not election:
        flash("Election not found.", "error")
        return redirect(url_for("admin.elections"))
    summary = None
    if request.method == "POST":
        try:
            summary = voter_service.import_voters_from_csv(
                election_id=election_id,
                file_storage=request.files.get("csv_file"),
                admin_id=_admin_id(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            flash(f"Import complete. Imported {summary['imported']} records.", "success")
        except ValidationError as exc:
            flash(str(exc), "error")
    return render_template("admin/voter_import.html", election=election, summary=summary)


@bp.route("/elections/<int:election_id>/results")
@admin_login_required
def results(election_id: int):
    try:
        payload = result_service.get_results(election_id, admin_preview=True)
        return render_template("admin/results.html", payload=payload)
    except (ValidationError, ElectionStateError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("admin.elections"))


@bp.route("/audit-logs")
@admin_login_required
def audit_logs():
    action = request.args.get("action", "").strip() or None
    admin_id_param = request.args.get("admin_id", "").strip()
    admin_id = int(admin_id_param) if admin_id_param.isdigit() else None
    logs = audit_repo.list_logs(action=action, admin_id=admin_id, limit=300)
    return render_template("admin/audit_logs.html", logs=logs, action=action, admin_id=admin_id_param)

