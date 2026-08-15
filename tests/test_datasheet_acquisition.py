from pathlib import Path
import tempfile
import unittest
from urllib.error import URLError

from datasheet_acquisition import (
    HttpFetchResult,
    acquire_datasheet,
    candidate_manufacturer_urls,
    looks_like_pdf,
    verify_manufacturer_url,
)


PDF_A = b"%PDF-1.4\nmanufacturer document A\n"
PDF_B = b"%PDF-1.4\nmanufacturer document B\n"
HTML = b"<html><body>not a pdf</body></html>"


def fetch_result(
    requested_url,
    *,
    final_url=None,
    body=PDF_A,
    status=200,
    content_type="application/pdf",
):
    return HttpFetchResult(
        requested_url=requested_url,
        final_url=final_url or requested_url,
        status_code=status,
        content_type=content_type,
        content_disposition="",
        body=body,
        redirect_chain=(),
    )


class FakeFetcher:
    def __init__(self, mapping):
        self.mapping = mapping
        self.calls = []

    def __call__(self, url, *, timeout=20.0):
        self.calls.append(url)
        value = self.mapping[url]
        if isinstance(value, Exception):
            raise value
        return value


class DatasheetAcquisitionTests(unittest.TestCase):
    def test_pdf_magic_is_accepted_even_without_pdf_content_type(self):
        result = fetch_result(
            "https://example.test/doc",
            content_type="application/octet-stream",
            body=PDF_A,
        )
        self.assertTrue(looks_like_pdf(result))

    def test_html_response_is_rejected(self):
        result = fetch_result(
            "https://example.test/doc",
            content_type="text/html",
            body=HTML,
        )
        self.assertFalse(looks_like_pdf(result))

    def test_manufacturer_candidate_from_final_redirect_url(self):
        candidates = candidate_manufacturer_urls(
            discovery_url="https://disti.test/abc",
            final_url="https://mfg.test/docs/abc.pdf",
            manufacturer_domains=["mfg.test"],
        )
        self.assertEqual(candidates, ["https://mfg.test/docs/abc.pdf"])

    def test_manufacturer_candidate_from_embedded_redirect_target(self):
        candidates = candidate_manufacturer_urls(
            discovery_url=(
                "https://disti.test/redirect?"
                "url=https%3A%2F%2Fmfg.test%2Fdocs%2Fabc.pdf"
            ),
            final_url="https://disti.test/cache/abc.pdf",
            manufacturer_domains=["mfg.test"],
        )
        self.assertEqual(candidates, ["https://mfg.test/docs/abc.pdf"])

    def test_verify_manufacturer_url_requires_recognised_domain(self):
        fetcher = FakeFetcher({})
        result = verify_manufacturer_url(
            "https://unknown.test/abc.pdf",
            manufacturer_domains=["mfg.test"],
            fetcher=fetcher,
        )
        self.assertIsNone(result)
        self.assertEqual(fetcher.calls, [])

    def test_verify_manufacturer_url_rejects_html(self):
        url = "https://mfg.test/abc.pdf"
        fetcher = FakeFetcher({
            url: fetch_result(
                url,
                body=HTML,
                content_type="text/html",
            )
        })
        self.assertIsNone(
            verify_manufacturer_url(
                url,
                manufacturer_domains=["mfg.test"],
                fetcher=fetcher,
            )
        )

    def test_acquisition_prefers_verified_manufacturer_document(self):
        discovery = "https://disti.test/abc"
        mfg = "https://mfg.test/docs/abc.pdf"
        fetcher = FakeFetcher({
            discovery: fetch_result(
                discovery,
                final_url=mfg,
                body=PDF_A,
            ),
            mfg: fetch_result(
                mfg,
                body=PDF_A,
            ),
        })

        with tempfile.TemporaryDirectory() as tmp:
            result = acquire_datasheet(
                discovery_url=discovery,
                discovered_via="Example Disti",
                discovery_source_type="DISTI",
                manufacturer_name="Example MFG",
                manufacturer_domains=["mfg.test"],
                mpn="ABC123",
                archive_root=Path(tmp) / "datasheets",
                retrieved_date="2026-08-15",
                fetcher=fetcher,
            )

            self.assertEqual(result.status, "Manufacturer Evidence Archived")
            self.assertIsNotNone(result.evidence)
            self.assertTrue(result.evidence.manufacturer_url_verified)
            self.assertEqual(
                result.evidence.active_source_url,
                "https://mfg.test/docs/abc.pdf",
            )
            self.assertTrue(Path(result.archive_file).exists())
            self.assertIn("__MFG__", Path(result.archive_file).name)

    def test_acquisition_retains_distributor_when_no_mfg_url_exists(self):
        discovery = "https://disti.test/abc.pdf"
        fetcher = FakeFetcher({
            discovery: fetch_result(discovery, body=PDF_A)
        })

        with tempfile.TemporaryDirectory() as tmp:
            result = acquire_datasheet(
                discovery_url=discovery,
                discovered_via="Example Disti",
                discovery_source_type="DISTI",
                manufacturer_name="Example MFG",
                manufacturer_domains=["mfg.test"],
                mpn="ABC123",
                archive_root=Path(tmp) / "datasheets",
                retrieved_date="2026-08-15",
                fetcher=fetcher,
            )

            self.assertEqual(result.status, "Evidence Archived")
            self.assertFalse(result.evidence.manufacturer_url_verified)
            self.assertEqual(
                result.evidence.active_source_url,
                "https://disti.test/abc.pdf",
            )
            self.assertIn("__DISTI__", Path(result.archive_file).name)

    def test_acquisition_rejects_product_page_html(self):
        discovery = "https://disti.test/product/abc"
        fetcher = FakeFetcher({
            discovery: fetch_result(
                discovery,
                body=HTML,
                content_type="text/html",
            )
        })

        with tempfile.TemporaryDirectory() as tmp:
            result = acquire_datasheet(
                discovery_url=discovery,
                discovered_via="Example Disti",
                discovery_source_type="DISTI",
                manufacturer_name="Example MFG",
                manufacturer_domains=["mfg.test"],
                mpn="ABC123",
                archive_root=Path(tmp) / "datasheets",
                retrieved_date="2026-08-15",
                fetcher=fetcher,
            )

            self.assertEqual(result.status, "Not a PDF")
            self.assertIsNone(result.evidence)

    def test_acquisition_failure_is_returned_not_raised(self):
        discovery = "https://disti.test/missing.pdf"
        fetcher = FakeFetcher({
            discovery: URLError("offline")
        })

        with tempfile.TemporaryDirectory() as tmp:
            result = acquire_datasheet(
                discovery_url=discovery,
                discovered_via="Example Disti",
                discovery_source_type="DISTI",
                manufacturer_name="Example MFG",
                manufacturer_domains=["mfg.test"],
                mpn="ABC123",
                archive_root=Path(tmp) / "datasheets",
                retrieved_date="2026-08-15",
                fetcher=fetcher,
            )

            self.assertEqual(result.status, "Acquisition Failed")
            self.assertIsNone(result.evidence)
            self.assertTrue(result.error)


if __name__ == "__main__":
    unittest.main()
