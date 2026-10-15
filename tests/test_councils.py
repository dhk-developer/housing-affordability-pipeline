from pipeline.councils import normalise_council_name


def test_case_and_spaces():
    assert normalise_council_name("  Leeds ") == "LEEDS"


def test_double_spaces_inside():
    assert normalise_council_name("North   Warwickshire") == "NORTH WARWICKSHIRE"


def test_ampersand():
    assert normalise_council_name("Brighton & Hove") == normalise_council_name("BRIGHTON AND HOVE")


def test_city_of_prefix_and_suffix():
    assert normalise_council_name("CITY OF BRISTOL") == normalise_council_name("Bristol, City of")


def test_county_of_suffix():
    assert normalise_council_name("Herefordshire, County of") == "HEREFORDSHIRE"


def test_full_stops_and_hyphens():
    assert normalise_council_name("St. Helens") == normalise_council_name("ST HELENS")
    assert normalise_council_name("Stockton-on-Tees") == normalise_council_name("STOCKTON ON TEES")


def test_different_councils_stay_different():
    assert normalise_council_name("Warwick") != normalise_council_name("North Warwickshire")