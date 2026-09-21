from utils.document_builder import DocumentBuilder


def test_create_cv_docx_writes_file(tmp_path, sample_profile):
    builder = DocumentBuilder()
    cv_data = {**sample_profile, "summary": sample_profile["summary"]}
    output_path = tmp_path / "cv.docx"

    builder.create_cv(cv_data, str(output_path))

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_create_cv_pdf_writes_file(tmp_path, sample_profile):
    builder = DocumentBuilder()
    output_path = tmp_path / "cv.pdf"

    builder.create_cv_pdf(sample_profile, str(output_path))

    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert output_path.read_bytes().startswith(b"%PDF")


def test_create_cover_letter_docx_writes_file(tmp_path, sample_profile):
    builder = DocumentBuilder()
    output_path = tmp_path / "cl.docx"

    builder.create_cover_letter("Dear Hiring Manager,\n\nBody text.", sample_profile, str(output_path))

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_create_cover_letter_pdf_writes_file(tmp_path, sample_profile):
    builder = DocumentBuilder()
    output_path = tmp_path / "cl.pdf"

    builder.create_cover_letter_pdf("Dear Hiring Manager,\n\nBody text.", sample_profile, str(output_path))

    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF")
