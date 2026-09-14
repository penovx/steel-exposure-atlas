from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pipeline.inspect_xlsx import inspect_workbook, sha256_file


CONTENT_TYPES = """<?xml version='1.0' encoding='UTF-8'?>
<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>
  <Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>
  <Default Extension='xml' ContentType='application/xml'/>
</Types>
"""

WORKBOOK = """<?xml version='1.0' encoding='UTF-8'?>
<workbook xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
          xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'>
  <sheets><sheet name='Data' sheetId='1' r:id='rId1'/></sheets>
</workbook>
"""

RELS = """<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
  <Relationship Id='rId1' Type='worksheet' Target='worksheets/sheet1.xml'/>
</Relationships>
"""

SHARED = """<?xml version='1.0' encoding='UTF-8'?>
<sst xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'>
  <si><t>Name</t></si><si><t>Plant A</t></si>
</sst>
"""

SHEET = """<?xml version='1.0' encoding='UTF-8'?>
<worksheet xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'>
  <dimension ref='A1:B2'/>
  <sheetData>
    <row r='1'><c r='A1' t='s'><v>0</v></c><c r='B1' t='inlineStr'><is><t>Capacity</t></is></c></row>
    <row r='2'><c r='A2' t='s'><v>1</v></c><c r='B2'><v>123.5</v></c></row>
  </sheetData>
</worksheet>
"""


def make_workbook(path: Path) -> None:
    with ZipFile(path, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', CONTENT_TYPES)
        archive.writestr('xl/workbook.xml', WORKBOOK)
        archive.writestr('xl/_rels/workbook.xml.rels', RELS)
        archive.writestr('xl/sharedStrings.xml', SHARED)
        archive.writestr('xl/worksheets/sheet1.xml', SHEET)


class InspectXlsxTests(unittest.TestCase):
    def test_reports_sheet_structure_and_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sample.xlsx'
            make_workbook(path)
            report = inspect_workbook(path, preview_rows=2)

        self.assertEqual(report['file_name'], 'sample.xlsx')
        self.assertEqual(report['sheet_count'], 1)
        self.assertEqual(report['sheets'][0]['name'], 'Data')
        self.assertEqual(report['sheets'][0]['dimension'], 'A1:B2')
        self.assertEqual(report['sheets'][0]['preview_rows'][0][0]['value'], 'Name')
        self.assertEqual(report['sheets'][0]['preview_rows'][1][1]['value'], 123.5)

    def test_sha256_is_stable_for_same_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sample.xlsx'
            make_workbook(path)
            first = sha256_file(path)
            second = sha256_file(path)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)


if __name__ == '__main__':
    unittest.main()
