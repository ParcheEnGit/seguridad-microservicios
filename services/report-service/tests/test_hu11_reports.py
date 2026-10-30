
"""Pruebas aisladas de los reportes administrativos de la HU11.

Ejecutar desde services/report-service:
    python -m unittest discover -s tests -p "test_hu11_reports.py" -v

No requieren insertar ni modificar registros en PostgreSQL.
"""

import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID

from fastapi import HTTPException

from app.routes import alerts_report, tickets_report, validate_report_dates


DEVICE_ID = UUID("11111111-1111-4111-8111-111111111111")
ALERT_ID = UUID("22222222-2222-4222-8222-222222222222")
TICKET_ID = UUID("33333333-3333-4333-8333-333333333333")

START_DATE = date(2026, 10, 1)
END_DATE = date(2026, 10, 23)
CREATED_AT = datetime(2026, 10, 10, 14, 30, tzinfo=timezone.utc)


def fake_database(summary, details, timeline):
    """Simula las tres consultas SQL realizadas por cada reporte."""
    db = MagicMock()

    results = []

    for rows in ([summary], details, timeline):
        result = MagicMock()

        result.mappings.return_value.one.return_value = (
            rows[0] if rows else None
        )

        result.mappings.return_value.__iter__.return_value = iter(rows)

        results.append(result)

    db.execute.side_effect = results

    return db


class TestReportDates(unittest.TestCase):

    def test_fechas_validas(self):
        validate_report_dates(START_DATE, END_DATE)

    def test_fecha_inicial_posterior_a_final(self):
        with self.assertRaises(HTTPException) as error:
            validate_report_dates(END_DATE, START_DATE)

        self.assertEqual(error.exception.status_code, 422)

    def test_fechas_futuras(self):
        future = date(2099, 1, 1)

        with self.assertRaises(HTTPException) as error:
            validate_report_dates(START_DATE, future)

        self.assertEqual(error.exception.status_code, 422)
        self.assertIn("futuras", error.exception.detail)


class TestAlertReport(unittest.TestCase):

    def test_reporte_con_registros(self):
        summary = {
            "total": 2,
            "criticas": 1,
            "advertencias": 1,
            "abiertas": 1,
            "revisadas": 1,
            "cerradas": 0,
        }

        details = [
            {
                "id": ALERT_ID,
                "device_id": DEVICE_ID,
                "device_code": "ROUTER-LAB-01",
                "device_name": "Router laboratorio",
                "metric_code": "temperatura",
                "value": Decimal("38.5"),
                "unit": "C",
                "severity": "critica",
                "status": "abierta",
                "created_at": CREATED_AT,
                "reviewed_at": None,
                "resolved_at": None,
            }
        ]

        timeline = [
            {
                "day": date(2026, 10, 10),
                "total": 2,
                "criticas": 1,
                "advertencias": 1,
            }
        ]

        db = fake_database(summary, details, timeline)

        response = alerts_report(
            start_date=START_DATE,
            end_date=END_DATE,
            device_id=DEVICE_ID,
            severity="critica",
            alert_status="abierta",
            db=db,
            _={"role": 0},
        )

        self.assertEqual(response.summary.total, 2)
        self.assertEqual(response.summary.criticas, 1)
        self.assertEqual(response.summary.advertencias, 1)

        self.assertEqual(len(response.alerts), 1)
        self.assertEqual(response.alerts[0].id, ALERT_ID)

        self.assertEqual(response.timeline[0].total, 2)
        self.assertEqual(db.execute.call_count, 3)

        for call in db.execute.call_args_list:
            params = call.args[1]

            self.assertEqual(params["device_id"], str(DEVICE_ID))
            self.assertEqual(params["severity"], "critica")
            self.assertEqual(params["alert_status"], "abierta")

    def test_reporte_sin_registros(self):
        summary = {
            "total": 0,
            "criticas": 0,
            "advertencias": 0,
            "abiertas": 0,
            "revisadas": 0,
            "cerradas": 0,
        }

        db = fake_database(summary, [], [])

        response = alerts_report(
            start_date=START_DATE,
            end_date=END_DATE,
            device_id=None,
            severity=None,
            alert_status=None,
            db=db,
            _={"role": 0},
        )

        self.assertEqual(response.summary.total, 0)
        self.assertEqual(response.alerts, [])
        self.assertEqual(response.timeline, [])


class TestTicketReport(unittest.TestCase):

    def test_reporte_con_registros(self):
        summary = {
            "total": 1,
            "abiertos": 1,
            "en_revision": 0,
            "resueltos": 0,
            "cerrados": 0,
        }

        details = [
            {
                "id": TICKET_ID,
                "ticket_number": 101,
                "device_id": DEVICE_ID,
                "device_code": "ROUTER-LAB-01",
                "device_name": "Router laboratorio",
                "category": "carcasa_rota",
                "description": "Revisar carcasa rota del equipo",
                "status": "abierto",
                "created_by_user_id": 1,
                "assigned_to_user_id": None,
                "resolved_by_user_id": None,
                "resolved_at": None,
                "closed_by_user_id": None,
                "closed_at": None,
                "created_at": CREATED_AT,
                "updated_at": CREATED_AT,
            }
        ]

        timeline = [
            {
                "day": date(2026, 10, 10),
                "total": 1,
                "abiertos": 1,
                "en_revision": 0,
                "resueltos": 0,
                "cerrados": 0,
            }
        ]

        db = fake_database(summary, details, timeline)

        response = tickets_report(
            start_date=START_DATE,
            end_date=END_DATE,
            device_id=DEVICE_ID,
            ticket_status="abierto",
            category="carcasa_rota",
            db=db,
            _={"role": 0},
        )

        self.assertEqual(response.summary.total, 1)
        self.assertEqual(response.summary.abiertos, 1)

        self.assertEqual(len(response.tickets), 1)
        self.assertEqual(response.tickets[0].id, TICKET_ID)
        self.assertEqual(
            response.tickets[0].category,
            "carcasa_rota",
        )

        self.assertEqual(response.timeline[0].abiertos, 1)
        self.assertEqual(db.execute.call_count, 3)

        for call in db.execute.call_args_list:
            params = call.args[1]

            self.assertEqual(params["device_id"], str(DEVICE_ID))
            self.assertEqual(params["ticket_status"], "abierto")
            self.assertEqual(params["category"], "carcasa_rota")

    def test_reporte_sin_registros(self):
        summary = {
            "total": 0,
            "abiertos": 0,
            "en_revision": 0,
            "resueltos": 0,
            "cerrados": 0,
        }

        db = fake_database(summary, [], [])

        response = tickets_report(
            start_date=START_DATE,
            end_date=END_DATE,
            device_id=None,
            ticket_status=None,
            category=None,
            db=db,
            _={"role": 0},
        )

        self.assertEqual(response.summary.total, 0)
        self.assertEqual(response.tickets, [])
        self.assertEqual(response.timeline, [])


if __name__ == "__main__":
    unittest.main()
