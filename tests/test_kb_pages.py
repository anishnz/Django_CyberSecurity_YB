"""
test_kb_pages.py - Knowledge Base pages, navigation tab, English-only and DOM checks
====================================================================================

No call to the RAG service is made by the pages themselves (the JS does that), so
nothing needs mocking here except where noted.
"""

from __future__ import annotations

import re

from django.test import Client
from django.urls import reverse

from .kb_support import BASE_DIR, CJK, ROLES, STAFF, KbTestCase, client_for

NAV_ACTIVE = r'<a class="nav-link active" href="/kb/"><i class="bi bi-book"></i> Knowledge Base</a>'
NAV_PLAIN = r'<a class="nav-link" href="/kb/"><i class="bi bi-book"></i> Knowledge Base</a>'


class PageTests(KbTestCase):
    """The Ask and Manage pages open for the right roles."""

    def test_anonymous_users_are_redirected_to_login(self):
        for name in ("kb:ask", "kb:manage"):
            with self.subTest(page=name):
                response = Client().get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn("/accounts/login/", response["Location"])

    def test_ask_page_renders_for_every_role(self):
        for role in ROLES:
            with self.subTest(role=role):
                response = client_for(role).get(reverse("kb:ask"))
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertIn('id="kb-ask-form"', html)
                self.assertIn("Ask</button>", html)
                self.assertIn("Your question", html)
                # The link to the Manage page is only for roles that may use it.
                self.assertEqual(f'href="{reverse("kb:manage")}"' in html, role in STAFF)

    def test_manage_page_is_for_staff_only(self):
        for role in ROLES:
            with self.subTest(role=role):
                response = client_for(role).get(reverse("kb:manage"))
                self.assertEqual(response.status_code, 200 if role in STAFF else 403)

    def test_manage_page_shows_only_what_the_role_may_use(self):
        teacher = client_for("teacher").get(reverse("kb:manage")).content.decode()
        self.assertIn('data-can-delete="0"', teacher)
        self.assertIn('id="kb-quiz-form"', teacher)
        self.assertIn('id="kb-upload-form"', teacher)
        self.assertNotIn("kb-model-form", teacher)
        self.assertNotIn("data-model-url", teacher)

        school_admin = client_for("school_admin").get(reverse("kb:manage")).content.decode()
        self.assertIn('data-can-delete="1"', school_admin)
        self.assertNotIn("kb-model-form", school_admin)

        boss = client_for("super_admin").get(reverse("kb:manage")).content.decode()
        self.assertIn('data-can-delete="1"', boss)
        self.assertIn('id="kb-model-form"', boss)
        self.assertIn(f'data-model-test-url="{reverse("kb:api_model_test")}"', boss)

    def test_tip_text_does_not_exist(self):
        for role in ("student", "teacher"):
            html = client_for(role).get(reverse("kb:ask")).content.decode()
            self.assertNotIn("Ctrl+Enter", html)
            self.assertNotIn("Tip:", html)
        for path in list((BASE_DIR / "apps/kb").rglob("*.html")) + list((BASE_DIR / "static/js").glob("kb_*.js")):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("Tip: press", text, path)
            self.assertNotIn("Ctrl+Enter", text, path)

    def test_upload_control_uses_english_label_not_the_native_button(self):
        html = client_for("teacher").get(reverse("kb:manage")).content.decode()
        self.assertRegex(html, r'<input id="kb-file" class="d-none" type="file"')
        self.assertIn('<label for="kb-file"', html)
        self.assertIn("Choose file</label>", html)
        self.assertRegex(html, r'<span id="kb-file-name"[^>]*>No file chosen</span>')


class NavigationTests(KbTestCase):
    """The Knowledge Base tab appears in every role's menu."""

    def test_tab_is_present_and_active_on_the_ask_page_for_every_role(self):
        for role in ROLES:
            with self.subTest(role=role):
                html = client_for(role).get(reverse("kb:ask")).content.decode()
                self.assertIn(NAV_ACTIVE, html)

    def test_tab_stays_active_on_the_manage_page(self):
        html = client_for("teacher").get(reverse("kb:manage")).content.decode()
        self.assertIn(NAV_ACTIVE, html)

    def test_tab_is_listed_but_not_active_on_other_pages(self):
        response = client_for("student").get(reverse("notifications:list"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn(NAV_PLAIN, html)
        self.assertNotIn(NAV_ACTIVE, html)

    def test_menu_of_every_role_contains_one_knowledge_base_item(self):
        from apps.accounts.roles import role_for

        for role in ROLES:
            with self.subTest(role=role):
                items = [item for item in role_for(role).menu() if item[1] == "kb:ask"]
                self.assertEqual(items, [("Knowledge Base", "kb:ask", "book")])

    def test_public_site_menu_is_unchanged_for_anonymous_visitors(self):
        html = Client().get(reverse("website:features")).content.decode()
        self.assertNotIn("Knowledge Base", html)


class EnglishOnlyAndDomTests(KbTestCase):
    """Pages, scripts and code stay English-only, and the page elements the scripts need exist."""

    def test_rendered_pages_have_no_cjk(self):
        for role in ROLES:
            for name in ("kb:ask", "kb:manage"):
                if name == "kb:manage" and role not in STAFF:
                    continue
                with self.subTest(role=role, page=name):
                    html = client_for(role).get(reverse(name)).content.decode()
                    self.assertFalse(CJK.search(html))

    def test_kb_templates_scripts_and_python_have_no_cjk(self):
        files = list((BASE_DIR / "apps/kb").rglob("*.html")) + list((BASE_DIR / "static/js").glob("kb_*.js"))
        files += list((BASE_DIR / "apps/kb").glob("*.py"))
        files += [BASE_DIR / "apps/accounts/roles.py", BASE_DIR / "templates/base.html"]
        for path in files:
            with self.subTest(file=path.name):
                self.assertFalse(CJK.search(path.read_text(encoding="utf-8")))

    def test_every_dom_id_used_by_the_js_exists_in_the_html(self):
        pages = {"kb_ask.js": ("kb:ask", "super_admin"), "kb_manage.js": ("kb:manage", "super_admin")}
        for js_name, (url_name, role) in pages.items():
            html = client_for(role).get(reverse(url_name)).content.decode()
            script = (BASE_DIR / "static/js" / js_name).read_text(encoding="utf-8")
            ids = set(re.findall(r'getElementById\("([^"]+)"\)', script))
            self.assertGreater(len(ids), 5, js_name)
            for dom_id in ids:
                with self.subTest(js=js_name, id=dom_id):
                    self.assertIn(f'id="{dom_id}"', html)

    def test_data_attributes_used_by_the_js_exist_and_resolve(self):
        ask = client_for("student").get(reverse("kb:ask")).content.decode()
        self.assertIn(f'data-ask-url="{reverse("kb:api_ask")}"', ask)
        self.assertIn("data-csrf=", ask)
        manage = client_for("super_admin").get(reverse("kb:manage")).content.decode()
        expected = {
            "data-documents-url": reverse("kb:api_documents"),
            "data-quiz-url": reverse("kb:api_quiz"),
            "data-model-url": reverse("kb:api_model"),
            "data-model-test-url": reverse("kb:api_model_test"),
        }
        for attr, url in expected.items():
            with self.subTest(attr=attr):
                self.assertIn(f'{attr}="{url}"', manage)
        script = (BASE_DIR / "static/js/kb_manage.js").read_text(encoding="utf-8")
        for dataset_key in ("csrf", "documentsUrl", "quizUrl", "canDelete", "modelUrl", "modelTestUrl"):
            self.assertIn(f"dataset.{dataset_key}", script)

    def test_pages_use_external_scripts_only_because_of_the_csp(self):
        for name, role in (("kb:ask", "student"), ("kb:manage", "teacher")):
            with self.subTest(page=name):
                html = client_for(role).get(reverse(name)).content.decode()
                self.assertNotRegex(html, r"<script>\s*\S")
                sources = re.findall(r'<script src="(/static/js/kb_[a-z_]+\.js)"', html)
                self.assertIn("/static/js/kb_common.js", sources)
                for src in sources:
                    self.assertTrue((BASE_DIR / src.lstrip("/")).exists(), src)

    def test_no_per_school_knowledge_base_in_the_module(self):
        for path in (BASE_DIR / "apps/kb").rglob("*"):
            if path.suffix not in (".py", ".html") or "migrations" in path.parts:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for word in ("school_id", "school=", "filter(school", "request.user.school"):
                self.assertNotIn(word, text, path)
