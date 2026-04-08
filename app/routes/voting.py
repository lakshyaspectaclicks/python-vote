from __future__ import annotations

import secrets

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.voting_service import VotingService
from app.utils.exceptions import DuplicateVoteError, ElectionStateError, ValidationError

bp = Blueprint("voting", __name__, url_prefix="/vote")
voting_service = VotingService()


def _clear_vote_session() -> None:
    for key in [
        "vote_election_id",
        "vote_voter_id",
        "vote_voter_name",
        "vote_pending",
        "vote_token",
    ]:
        session.pop(key, None)


@bp.route("/", methods=["GET"])
def index():
    _clear_vote_session()
    election = voting_service.get_active_election()
    return render_template("voting/verify.html", election=election)


@bp.route("/verify", methods=["POST"])
def verify():
    election = voting_service.get_active_election()
    if not election:
        flash("No open election available right now.", "error")
        return redirect(url_for("voting.index"))

    student_id = request.form.get("student_id", "").strip().upper()
    pin = request.form.get("pin", "").strip() or None
    try:
        voter = voting_service.verify_voter(election_id=election["id"], student_id=student_id, pin=pin)
        session["vote_election_id"] = election["id"]
        session["vote_voter_id"] = voter["id"]
        session["vote_voter_name"] = voter["full_name"]
        session["vote_token"] = secrets.token_urlsafe(24)
        return redirect(url_for("voting.ballot"))
    except (ValidationError, DuplicateVoteError, ElectionStateError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("voting.index"))


@bp.route("/ballot", methods=["GET"])
def ballot():
    election_id = session.get("vote_election_id")
    voter_id = session.get("vote_voter_id")
    if not election_id or not voter_id:
        flash("Please verify voter details first.", "error")
        return redirect(url_for("voting.index"))
    ballot_data = voting_service.get_ballot_data(int(election_id))
    if not ballot_data:
        flash("No ballot content found for this election.", "error")
        return redirect(url_for("voting.index"))
    return render_template("voting/ballot.html", ballot_data=ballot_data)


@bp.route("/confirm", methods=["POST"])
def confirm():
    election_id = session.get("vote_election_id")
    if not election_id:
        flash("Voting session expired.", "error")
        return redirect(url_for("voting.index"))

    ballot_data = voting_service.get_ballot_data(int(election_id))
    selections: dict[int, int] = {}
    for position in ballot_data:
        value = request.form.get(f"position_{position['id']}")
        if value and value.isdigit():
            selections[position["id"]] = int(value)
    try:
        validated = voting_service.validate_selections(int(election_id), selections)
        session["vote_pending"] = [{"position_id": pid, "candidate_id": cid} for pid, cid in validated]
        return redirect(url_for("voting.confirm_page"))
    except ValidationError as exc:
        flash(str(exc), "error")
        return redirect(url_for("voting.ballot"))


@bp.route("/confirm", methods=["GET"])
def confirm_page():
    election_id = session.get("vote_election_id")
    pending = session.get("vote_pending")
    token = session.get("vote_token")
    if not election_id or not pending or not token:
        flash("No pending ballot found.", "error")
        return redirect(url_for("voting.index"))

    ballot_data = voting_service.get_ballot_data(int(election_id))
    by_position = {p["id"]: p for p in ballot_data}
    lines = []
    for item in pending:
        position = by_position.get(item["position_id"])
        if not position:
            continue
        candidate = next(
            (c for c in position["candidates"] if c["id"] == item["candidate_id"]),
            None,
        )
        if candidate:
            lines.append(
                {
                    "position_name": position["name"],
                    "candidate_name": candidate["full_name"],
                    "candidate_class": candidate["class_name"],
                }
            )
    return render_template("voting/confirm.html", lines=lines, vote_token=token)


@bp.route("/submit", methods=["POST"])
def submit():
    election_id = session.get("vote_election_id")
    voter_id = session.get("vote_voter_id")
    pending = session.get("vote_pending")
    token = session.get("vote_token")
    submitted_token = request.form.get("vote_token")

    if not election_id or not voter_id or not pending or not token:
        flash("Voting session is invalid or expired.", "error")
        return redirect(url_for("voting.index"))
    if token != submitted_token:
        flash("Invalid submission token.", "error")
        return redirect(url_for("voting.index"))

    selections = {int(item["position_id"]): int(item["candidate_id"]) for item in pending}
    try:
        voting_service.submit_vote(
            election_id=int(election_id),
            voter_id=int(voter_id),
            selections=selections,
            client_ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
    except (ValidationError, DuplicateVoteError, ElectionStateError) as exc:
        flash(str(exc), "error")
        _clear_vote_session()
        return redirect(url_for("voting.index"))

    _clear_vote_session()
    session["vote_success"] = True
    return redirect(url_for("voting.success"))


@bp.route("/success", methods=["GET"])
def success():
    voted = bool(session.pop("vote_success", False))
    return render_template("voting/success.html", voted=voted)

