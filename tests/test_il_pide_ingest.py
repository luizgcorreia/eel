"""Unit tests for PideTheoryIngester and PIDE ingestion."""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock

from edel.il.ingest_interface import get_theory_ingester
from edel.il.pide_ingest import PideTheoryIngester


def test_factory_get_theory_ingester():
    ing_ir = get_theory_ingester("ir")
    from edel.il.ir_ingest import IrTheoryIngester
    assert isinstance(ing_ir, IrTheoryIngester)

    ing_pide = get_theory_ingester("pide")
    assert isinstance(ing_pide, PideTheoryIngester)

    with pytest.raises(ValueError):
        get_theory_ingester("invalid_backend")


def test_pide_ingester_list_theories_mock(tmp_path):
    mock_mcp = MagicMock()
    mock_mcp.call_tool.return_value = {
        "content": [{"type": "text", "text": "Session.ThyA\nSession.ThyB\nOther.ThyC"}]
    }

    ingester = PideTheoryIngester(mcp_client=mock_mcp)
    thys = ingester.list_theories("Session")
    assert "Session.ThyA" in thys
    assert "Session.ThyB" in thys
    assert "Other.ThyC" in thys

    # Test filtering with pattern
    thys_filtered = ingester.list_theories("Session", pattern=r"ThyA")
    assert thys_filtered == ["Session.ThyA"]


def test_pide_ingester_aspect_extraction(tmp_path):
    # Create sample theory file
    session_dir = tmp_path / "TestSession"
    session_dir.mkdir(parents=True, exist_ok=True)
    thy_file = session_dir / "TestTheory.thy"

    thy_content = (
        "theory TestTheory\n"
        "  imports Main\n"
        "begin\n\n"
        "definition my_id :: \"'a => 'a\" where\n"
        "  \"my_id x = x\"\n\n"
        "lemma my_id_apply [simp]:\n"
        "  shows \"my_id A = A\"\n"
        "  by (simp add: my_id_def)\n\n"
        "lemma conditional_thm:\n"
        "  assumes \"x > 0\"\n"
        "  shows \"x + 1 > 1\"\n"
        "  proof -\n"
        "    from assms show ?thesis by simp\n"
        "  qed\n\n"
        "end\n"
    )
    thy_file.write_text(thy_content, encoding="utf-8")

    ingester = PideTheoryIngester(afp_thys_dir=tmp_path)
    records = ingester.ingest_theory("TestSession.TestTheory", session="TestSession")

    assert len(records) >= 3

    # 1. Definition check (0-simplex: P = M = F = I)
    def_rec = next(r for r in records if "my_id" in r["title"] and r["keyword"] == "definition")
    assert "my_id x = x" in def_rec["problem"]
    assert def_rec["problem"] == def_rec["method"] == def_rec["finding"] == def_rec["interpretation"]
    assert "arity=1" in def_rec["architecture"]

    # 2. Unconditional lemma check
    simp_rec = next(r for r in records if "my_id_apply" in r["title"])
    assert "equational-normalization" in simp_rec["method"]
    # Abstract method should not contain concrete citations
    assert "my_id_def" not in simp_rec["method"]
    # Finding must contain concrete tactics and citations
    assert "my_id_def" in simp_rec["finding"]
    assert "my_id A = A" in simp_rec["interpretation"]

    # 3. Conditional lemma check (Horn decomposition)
    cond_rec = next(r for r in records if "conditional_thm" in r["title"])
    assert "x > 0" in cond_rec["problem"]
    assert "x + 1 > 1" in cond_rec["interpretation"]
    assert "isar-decomposition" in cond_rec["method"]

    # Verify 0% emptiness on all aspects
    for r in records:
        assert r["problem"].strip() != ""
        assert r["method"].strip() != ""
        assert r["finding"].strip() != ""
        assert r["interpretation"].strip() != ""


def test_pide_ingester_ingest_session(tmp_path):
    session_dir = tmp_path / "DummySession"
    session_dir.mkdir(parents=True, exist_ok=True)
    thy_file = session_dir / "A.thy"
    thy_file.write_text(
        "theory A imports Main begin\n"
        "lemma a_refl: \"a = a\" by simp\n"
        "end\n",
        encoding="utf-8",
    )

    ingester = PideTheoryIngester(afp_thys_dir=tmp_path)
    df = ingester.ingest_session("DummySession")

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df["title"].iloc[0].endswith("a_refl")
    assert "equational-normalization" in df["method"].iloc[0]
