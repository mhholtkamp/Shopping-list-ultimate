import pytest

from custom_components.shopping_list_ultimate.barcode import InvalidBarcode, validate_barcode


@pytest.mark.parametrize(
    ("code", "kind"),
    [("4006381333931", "EAN-13"), ("96385074", "EAN-8"), ("036000291452", "UPC-A"), ("04210005", "UPC-E")],
)
def test_valid_barcodes(code, kind):
    assert validate_barcode(code).format == kind


@pytest.mark.parametrize("code", ["4006381333932", "abc", "12345", ""])
def test_invalid_barcodes(code):
    with pytest.raises(InvalidBarcode):
        validate_barcode(code)
