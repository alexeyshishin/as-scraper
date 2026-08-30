from __future__ import annotations

import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from domain.models import CalendarEvent

SCOPES = ["https://www.googleapis.com/auth/calendar"]
logger = logging.getLogger("omsu_sync")


class GoogleCalendarGateway:
    def __init__(self, credentials_path: str, token_path: str, calendar_name: str, timezone: str):
        self._credentials_path = credentials_path
        self._token_path = token_path
        self._calendar_name = calendar_name
        self._timezone = timezone
        self._service = None
        self._calendar_id: str | None = None

    def sync(self, events: list[CalendarEvent]) -> dict[str, int]:
        service = self._get_service()
        calendar_id = self._get_calendar_id()
        existing = self._list_managed_events()
        desired = {event.sync_key: self._to_google_body(event) for event in events}

        stats = {"created": 0, "updated": 0, "deleted": 0, "unchanged": 0}

        for key, body in desired.items():
            ev = existing.get(key)
            if ev is None:
                service.events().insert(calendarId=calendar_id, body=body).execute()
                stats["created"] += 1
            elif not self._content_equal(ev, body):
                service.events().update(calendarId=calendar_id, eventId=ev["id"], body=body).execute()
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1

        for key, ev in existing.items():
            if key not in desired:
                service.events().delete(calendarId=calendar_id, eventId=ev["id"]).execute()
                stats["deleted"] += 1

        return stats

    def _get_service(self):
        if self._service is None:
            self._service = build("calendar", "v3", credentials=self._get_credentials())
        return self._service

    def _get_credentials(self) -> Credentials:
        creds: Credentials | None = None
        if os.path.exists(self._token_path):
            creds = Credentials.from_authorized_user_file(self._token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self._credentials_path):
                    raise FileNotFoundError(
                        f"Не найден {self._credentials_path}. Скачай OAuth client (Desktop app) "
                        "из Google Cloud Console — см. README.md."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self._credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self._token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

        return creds

    def _get_calendar_id(self) -> str:
        if self._calendar_id is not None:
            return self._calendar_id

        service = self._get_service()
        page_token = None
        while True:
            resp = service.calendarList().list(pageToken=page_token).execute()
            for cal in resp.get("items", []):
                if cal.get("summary") == self._calendar_name:
                    self._calendar_id = cal["id"]
                    return self._calendar_id
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        created = service.calendars().insert(
            body={"summary": self._calendar_name, "timeZone": self._timezone}
        ).execute()
        logger.info("Создан новый календарь %r (id=%s)", self._calendar_name, created["id"])
        self._calendar_id = created["id"]
        return self._calendar_id

    def _list_managed_events(self) -> dict[str, dict]:
        service = self._get_service()
        calendar_id = self._get_calendar_id()
        result: dict[str, dict] = {}
        page_token = None
        while True:
            resp = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    privateExtendedProperty="omsu_sync=true",
                    singleEvents=True,
                    maxResults=2500,
                    pageToken=page_token,
                )
                .execute()
            )
            for ev in resp.get("items", []):
                key = ev.get("extendedProperties", {}).get("private", {}).get("omsu_sync_key")
                if key:
                    result[key] = ev
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return result

    @staticmethod
    def _to_google_body(event: CalendarEvent) -> dict:
        tz_name = getattr(event.start.tzinfo, "key", str(event.start.tzinfo))
        body: dict = {
            "summary": event.summary,
            "location": event.location,
            "description": event.description,
            "start": {"dateTime": event.start.isoformat(), "timeZone": tz_name},
            "end": {"dateTime": event.end.isoformat(), "timeZone": tz_name},
            "extendedProperties": {
                "private": {
                    "omsu_sync": "true",
                    "omsu_sync_key": event.sync_key,
                }
            },
        }
        if event.reminders_minutes:
            body["reminders"] = {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": m} for m in event.reminders_minutes],
            }
        return body

    @staticmethod
    def _content_equal(existing: dict, desired_body: dict) -> bool:
        for key in ("summary", "location", "description"):
            if (existing.get(key) or "") != (desired_body.get(key) or ""):
                return False
        for part in ("start", "end"):
            if existing.get(part, {}).get("dateTime") != desired_body.get(part, {}).get("dateTime"):
                return False
        return True
