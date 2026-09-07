import pytest

from bot.database.models.player import TroopType
from bot.services.csv_importer import (
    CsvImporter,
    parse_helios,
    parse_level,
    parse_number,
)


def test_parse_number():
    assert parse_number("165k") == 165_000
    assert parse_number("165K") == 165_000
    assert parse_number("1.5M") == 1_500_000
    assert parse_number("1.5m") == 1_500_000
    assert parse_number("165,000") == 165_000
    assert parse_number("165.000") == 165_000
    assert parse_number("1,250.50") == 1250
    assert parse_number("") is None
    assert parse_number("-") is None
    assert parse_number(None) is None


def test_parse_level():
    assert parse_level("FC 5") == 5
    assert parse_level("fc3") == 3
    assert parse_level("Level 8") == 8
    assert parse_level("lvl 10") == 10
    assert parse_level("T11") == 11
    assert parse_level("30") == 30
    assert parse_level("-") is None
    assert parse_level("") is None


def test_parse_helios():
    assert parse_helios("Yes") == (True, None)
    assert parse_helios("y") == (True, None)
    assert parse_helios("true") == (True, None)
    assert parse_helios("1") == (True, None)
    assert parse_helios("No") == (False, None)
    assert parse_helios("false") == (False, None)
    assert parse_helios("0") == (False, None)
    assert parse_helios("") == (False, None)
    # Quantity entered directly in Helios column
    assert parse_helios("150k") == (True, 150_000)
    assert parse_helios("150,000") == (True, 150_000)


def test_csv_importer_standard_comma(session):
    importer = CsvImporter(session)
    csv_data = """Name,Game ID,March Limit,Discord ID,Infantry FC,Infantry Helios,Lancers FC,Lancers Helios,Marksman FC,Marksman Helios
Vader,1001,165000,discord_1,30,Yes,28,No,29,150k
Luke,1002,150000,,25,No,25,No,25,No
"""
    res = importer.import_text(csv_data)
    assert res.total_rows == 2
    assert res.created == 2
    assert res.updated == 0
    assert res.skipped == 0
    assert len(res.errors) == 0

    p1 = importer.repo.get_by_game_player_id("1001")
    assert p1 is not None
    assert p1.name == "Vader"
    assert p1.march_limit == 165_000
    inf = p1.profile_for(TroopType.INFANTRY)
    assert inf.level == 30
    assert inf.helios is True
    # Helios defaulted to march limit if quantity not provided
    assert inf.helios_quantity == 165_000

    mrk = p1.profile_for(TroopType.MARKSMAN)
    assert mrk.level == 29
    assert mrk.helios is True
    assert mrk.helios_quantity == 150_000


def test_csv_importer_synonym_headers_and_semicolon(session):
    importer = CsvImporter(session)
    # European Excel style with semicolons, 'IGN', 'Governor ID', 'March Capacity', 'Cav FC', 'Archer FC', etc.
    csv_data = """IGN;Governor ID;March Capacity;Discord Tag;Infantry Level;T11 Infantry;Cav FC;Cav Helios;Archer FC;Archer Helios
Gandalf;9901;160k;gandalf#1234;FC 30;120k;FC 28;No;Level 29;Yes
"""
    res = importer.import_text(csv_data)
    assert res.total_rows == 1
    assert res.created == 1
    assert res.skipped == 0

    p = importer.repo.get_by_game_player_id("9901")
    assert p is not None
    assert p.name == "Gandalf"
    assert p.march_limit == 160_000
    cav = p.profile_for(TroopType.LANCERS)
    assert cav.level == 28
    assert cav.helios is False

    inf = p.profile_for(TroopType.INFANTRY)
    assert inf.level == 30
    assert inf.helios is True
    assert inf.helios_quantity == 120_000


def test_csv_importer_tsv_and_bom(session):
    importer = CsvImporter(session)
    # TSV with BOM (copy-pasted from Google Sheets / Excel export)
    tsv_data = "\ufeffPlayer Name\tPlayer ID\tMarch Limit\tInfantry FC\tLancer FC\tMarksman FC\nAragorn\t7701\t175,000\t30\t29\t28\n"
    res = importer.import_text(tsv_data)
    assert res.created == 1
    assert res.skipped == 0

    p = importer.repo.get_by_game_player_id("7701")
    assert p is not None
    assert p.name == "Aragorn"
    assert p.march_limit == 175_000


def test_csv_importer_upsert_existing_player(session):
    importer = CsvImporter(session)
    csv1 = """Name,Game ID,March Limit,Infantry FC,Lancers FC,Marksman FC
Player1,5555,100000,10,10,10
"""
    res1 = importer.import_text(csv1)
    assert res1.created == 1

    # Now update Player1 with new march limit and higher FC levels
    csv2 = """Name,Game ID,March Limit,Infantry FC,Lancers FC,Marksman FC
Player1,5555,150000,20,20,20
"""
    res2 = importer.import_text(csv2)
    assert res2.created == 0
    assert res2.updated == 1

    p = importer.repo.get_by_game_player_id("5555")
    assert p.march_limit == 150_000
    assert p.profile_for(TroopType.INFANTRY).level == 20


def test_csv_importer_google_forms_export(session):
    importer = CsvImporter(session)
    # Exact Google Forms export structure with Timestamp and hero columns
    google_csv = (
        "Timestamp,In-Game Name,Game ID,March Limit,Discord Username,Infantry FC,Infantry Helios,Lancers FC,Lancers Helios,Marksman FC,Marksman Helios,Jessie,Patrick,Jasser,Seoyoon\n"
        "2026/09/07 3:45:12 PM EST,LordVader,10001,165k,vader#0001,FC 30,Yes - 150k,FC 28,No,FC 29,Yes,5 Stars (Max),4 Stars,3 Stars,Not Owned\n"
        "2026/09/07 3:46:01 PM EST,CommanderLuke,,\"150,000\",luke_sky,Level 25,No,Level 25,No,Level 25,No,4 Stars,5 Stars (Max),Not Owned,4 Stars\n"
    )
    res = importer.import_text(google_csv)
    assert res.total_rows == 2
    assert res.created == 2
    assert res.skipped == 0
    assert len(res.errors) == 0

    p1 = importer.repo.get_by_game_player_id("10001")
    assert p1 is not None
    assert p1.name == "LordVader"
    assert p1.march_limit == 165_000
    assert p1.profile_for(TroopType.INFANTRY).level == 30
    assert p1.profile_for(TroopType.INFANTRY).helios is True
    assert p1.profile_for(TroopType.INFANTRY).helios_quantity == 150_000
    assert p1.profile_for(TroopType.LANCERS).helios is False
    assert len(p1.heroes) == 3
    hero_names = {h.hero_name: h.stars for h in p1.heroes}
    assert hero_names["jessie"] == 5
    assert hero_names["patrick"] == 4
    assert hero_names["jasser"] == 3
    assert "seoyoon" not in hero_names  # 'Not Owned' is filtered out

    # Test player 2 where Game ID was blank (auto-generated fallback)
    p2 = importer.repo.get_by_discord_id("luke_sky")
    assert p2 is not None
    assert p2.name == "CommanderLuke"
    assert p2.march_limit == 150_000
    assert p2.profile_for(TroopType.INFANTRY).level == 25

