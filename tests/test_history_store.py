from utils.history_store import HistoryStore


def make_store(tmp_path):
    return HistoryStore(db_path=str(tmp_path / "history.db"))


def test_record_and_list_application(tmp_path):
    store = make_store(tmp_path)

    app_id = store.record_application(
        role_title="Backend Engineer",
        company="Globex",
        match_score=82.5,
        cv_file="output/CV_Globex_Backend_Engineer.docx",
        cover_letter_file="output/CL_Globex_Backend_Engineer.docx",
        analysis={"role_info": {"title": "Backend Engineer"}},
    )

    applications = store.list_applications()
    assert len(applications) == 1
    assert applications[0]["id"] == app_id
    assert applications[0]["company"] == "Globex"
    assert applications[0]["match_score"] == 82.5


def test_get_application_includes_analysis(tmp_path):
    store = make_store(tmp_path)
    app_id = store.record_application(
        role_title="Backend Engineer",
        company="Globex",
        analysis={"role_info": {"title": "Backend Engineer"}},
    )

    application = store.get_application(app_id)

    assert application is not None
    assert application["analysis"]["role_info"]["title"] == "Backend Engineer"


def test_get_application_missing_returns_none(tmp_path):
    store = make_store(tmp_path)
    assert store.get_application(999) is None


def test_delete_application(tmp_path):
    store = make_store(tmp_path)
    app_id = store.record_application(role_title="X", company="Y")

    assert store.delete_application(app_id) is True
    assert store.get_application(app_id) is None
    assert store.delete_application(app_id) is False


def test_list_applications_orders_newest_first(tmp_path):
    store = make_store(tmp_path)
    first_id = store.record_application(role_title="First", company="A")
    second_id = store.record_application(role_title="Second", company="B")

    applications = store.list_applications()

    assert [a["id"] for a in applications] == [second_id, first_id]
