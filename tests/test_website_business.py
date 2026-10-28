"""test_website_business.py - Business pages: prices, discount, sustainability, SWOT, proposal, contract.

Owner: Jihe Qi (QA).
"""

from decimal import Decimal

import pytest
from django.test import Client

from apps.licensing.plans import PLAN_CLASSES
from apps.website import business

pytestmark = pytest.mark.django_db

PAGES = [
    "/pricing/",
    "/pricing/discount/",
    "/business/",
    "/business/swot/",
    "/business/proposal/",
    "/business/contract/",
]


@pytest.mark.parametrize("url", PAGES)
def test_every_business_page_opens_without_login(url):
    response = Client().get(url)
    assert response.status_code == 200
    assert "Contract sample" in response.content.decode()  # the shared tabs are on every page


def test_price_table_uses_the_plan_classes():
    rows = {r["code"]: r for r in business.price_table()}
    assert set(rows) == set(PLAN_CLASSES)
    assert rows["STANDARD"]["yearly_gst"] == Decimal("3450.00")  # 250 x 12 x 1.15
    assert rows["STANDARD"]["community_monthly"] == Decimal("125.00")  # 50% off


def test_proposal_budget_matches_the_project_report():
    assert business.proposal_total() == business.BUILD_COST == Decimal("33420.17")


def test_sustainability_needs_more_schools_when_more_get_the_discount():
    model = business.SustainabilityModel(business.RUNNING_COSTS)
    needed = [s.schools_needed for s in model.scenarios()]
    assert needed == sorted(needed) and needed[0] > 0
    assert model.yearly_target == model.running_total + model.payback_per_year
    # enough schools really cover the target
    first = model.scenarios()[0]
    assert first.schools_needed * first.income_per_school >= model.yearly_target


def test_contract_says_it_is_a_sample_and_not_legal_advice():
    html = Client().get("/business/contract/").content.decode()
    assert "Sample only." in html and "not legal advice" in html
    for title, _points in business.CONTRACT_CLAUSES:
        assert title in html


def test_swot_shows_all_four_boxes():
    html = Client().get("/business/swot/").content.decode()
    for title in ("Strengths", "Weaknesses", "Opportunities", "Threats"):
        assert title in html


def test_public_menu_links_to_story_and_business_pages():
    html = Client().get("/").content.decode()
    for url in ["/story/", *PAGES]:
        assert f'href="{url}"' in html
