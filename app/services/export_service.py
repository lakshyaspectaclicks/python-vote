from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from fpdf import FPDF
from flask import current_app


class ExportService:
    def build_results_csv(self, result_payload: dict) -> bytes:
        election = result_payload["election"]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "election_name",
                "position_name",
                "candidate_name",
                "candidate_class",
                "vote_count",
                "status",
            ]
        )
        for position in result_payload["positions"]:
            for candidate in position["candidates"]:
                writer.writerow(
                    [
                        election["name"],
                        position["position_name"],
                        candidate["candidate_name"],
                        candidate["candidate_class"],
                        candidate["vote_count"],
                        candidate["status"],
                    ]
                )
        return output.getvalue().encode("utf-8")

    def build_results_pdf(self, result_payload: dict) -> bytes:
        election = result_payload["election"]
        totals = result_payload["totals"]
        generated_at = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, current_app.config.get("SCHOOL_NAME", "School Election"), ln=True)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, f"Election: {election['name']}", ln=True)
        pdf.cell(0, 8, f"Status: {election['status']}", ln=True)
        pdf.cell(0, 8, f"Generated: {generated_at}", ln=True)
        pdf.ln(2)
        pdf.cell(0, 8, f"Registered voters: {totals['registered_voters']}", ln=True)
        pdf.cell(0, 8, f"Ballots cast: {totals['ballots_cast']}", ln=True)
        pdf.cell(0, 8, f"Turnout: {totals['turnout_percent']}%", ln=True)
        pdf.ln(5)

        for position in result_payload["positions"]:
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 8, f"Position: {position['position_name']}")
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(70, 8, "Candidate", border=1)
            pdf.cell(30, 8, "Class", border=1)
            pdf.cell(25, 8, "Votes", border=1)
            pdf.cell(50, 8, "Status", border=1, ln=True)
            pdf.set_font("Helvetica", "", 11)
            for candidate in position["candidates"]:
                pdf.cell(70, 8, candidate["candidate_name"][:34], border=1)
                pdf.cell(30, 8, candidate["candidate_class"][:14], border=1)
                pdf.cell(25, 8, str(candidate["vote_count"]), border=1)
                pdf.cell(50, 8, candidate["status"][:24], border=1, ln=True)
            pdf.ln(4)

        return bytes(pdf.output(dest="S"))

