"""test_learning.py - Question classes, QuestionFactory, content import. Owners: Jihe Qi / Anish Shrestha."""
import json

import pytest

from apps.core.exceptions import ValidationError
from apps.learning.categories import LEVEL_CATEGORIES
from apps.learning.factory import QuestionFactory
from apps.learning.importer import ContentImporter
from apps.learning.models import Question
from apps.learning.questions import MultiSelectQuestion, ScenarioQuestion, SingleChoiceQuestion, normalise_answer


def _data(**extra):
    base = {"level": 1, "category": "PWD", "text": "Is 123456 a good password?", "options": {"A": "Yes", "B": "No"},
            "answer": "B", "feedback": "It is short and easy to guess."}
    base.update(extra)
    return base


def test_factory_returns_the_right_class():
    assert isinstance(QuestionFactory.create("single", _data()), SingleChoiceQuestion)
    multi = QuestionFactory.create("multi_select", _data(options={"A": "a", "B": "b", "C": "c"}, answer=["A", "C"]))
    assert isinstance(multi, MultiSelectQuestion) and multi.allows_many
    scen = QuestionFactory.create("scenario", _data(scenario_text="A message arrives from 'Netflix'..."))
    assert isinstance(scen, ScenarioQuestion) and isinstance(scen, SingleChoiceQuestion)  # inheritance


def test_unknown_type_and_bad_marks_are_rejected():
    with pytest.raises(ValidationError):
        QuestionFactory.create("essay", _data())
    with pytest.raises(ValidationError):
        QuestionFactory.create("single", _data(marks=10))
    with pytest.raises(ValidationError):
        QuestionFactory.create("single", _data(answer=["A", "B"]))       # single needs one answer
    with pytest.raises(ValidationError):
        QuestionFactory.create("scenario", _data(scenario_text=""))


def test_multi_select_is_all_or_nothing():
    q = QuestionFactory.create("multi_select", _data(options={"A": "a", "B": "b", "C": "c", "D": "d"},
                                                     answer=["A", "B", "D"]))
    assert q.marks_for(["A", "B", "D"]) == 5
    assert q.marks_for(["A", "B"]) == 0 and q.marks_for(["A", "B", "C", "D"]) == 0


def test_normalise_answer():
    assert normalise_answer("b, a") == ["A", "B"] and normalise_answer(None) == []


@pytest.mark.django_db
def test_content_loaded_and_every_level_can_build_an_exam():
    assert Question.objects.system().count() == 126
    for level, cats in LEVEL_CATEGORIES.items():
        for code in cats:
            assert Question.objects.system().filter(level__number=level, category=code).count() >= 5


@pytest.mark.django_db
def test_import_twice_adds_nothing():
    assert ContentImporter().import_all()["questions_added"] == 0


@pytest.mark.django_db
def test_import_rejects_category_from_another_level(tmp_path):
    bad = tmp_path / "level9.json"
    bad.write_text(json.dumps({"level": 1, "questions": [{"id": "X1", "category": "LAW", "q_type": "single",
                   "text": "Wrong level question", "options": {"A": "a", "B": "b"}, "answer": "A",
                   "feedback": "Because."}]}))
    with pytest.raises(ValidationError):
        ContentImporter().validate_file(bad)


def test_correct_answers_spread_over_a_b_c_d(settings):
    from pathlib import Path
    counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for path in sorted((Path(settings.BASE_DIR) / "data" / "question_bank").glob("level*.json")):
        for q in json.loads(path.read_text(encoding="utf-8"))["questions"]:
            if q["q_type"] in ("single", "scenario"):
                counts[q["answer"]] += 1
    assert all(c <= sum(counts.values()) * 0.35 for c in counts.values()), counts
