from __future__ import annotations

from infrastructure.distabit_api import REPORT_ID_RE, DistabitEnrollmentClient

parse = DistabitEnrollmentClient.parse_report_body


def test_summary_line_and_enrolled_count():
    body = """
    <html><body>
    <table>
      <tr><td>Иванов</td><td>Зачислен</td></tr>
      <tr><td>Петров</td><td>Зачислен</td></tr>
      <tr><td>Сидоров</td><td>Зачислен</td></tr>
    </table>
    <p>Количество мест: 50 , из них зачислено: 49</p>
    </body></html>
    """
    places, enrolled, summary = parse(body)
    assert places == 50
    assert summary == 49
    assert enrolled == 3


def test_zachislen_disambiguation():
    body = "<td>Зачислен</td> Зачислено зачисленных <td>Зачислен</td>"
    _, enrolled, _ = parse(body)
    assert enrolled == 2


def test_target_quota_places_without_summary():
    body = "количество мест: 2 <td>Зачислен</td> количество мест: 3"
    places, enrolled, summary = parse(body)
    assert places == 5
    assert enrolled == 1
    assert summary is None


def test_empty_body():
    places, enrolled, summary = parse("")
    assert places is None
    assert enrolled == 0
    assert summary is None


def test_script_and_style_stripped():
    body = "<script>Зачислен Зачислен</script><style>Зачислен</style><td>Зачислен</td>"
    _, enrolled, _ = parse(body)
    assert enrolled == 1


def test_html_entities_unescaped():
    body = "Количество&nbsp;мест: 10 , из них зачислено: 7"
    places, _, summary = parse(body)
    assert places == 10
    assert summary == 7


def test_report_id_regex_matches():
    rid = "a" * 32
    assert REPORT_ID_RE.findall(f"...reportId={rid}&x=1") == [rid]


def test_report_id_regex_none():
    assert REPORT_ID_RE.findall("no id here") == []


def test_report_id_regex_multiple():
    rid1, rid2 = "a" * 32, "b" * 32
    assert REPORT_ID_RE.findall(f"reportId={rid1} reportId={rid2}") == [rid1, rid2]
