from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.paths import templates_dir
from app.widgets import build_field_form
from core.field_models import FieldValidationError
from core.template_engine import Template, TemplateError, discover_templates
from repo.git_manager import GitError, RepoManager
from sandbox.snapshots import take_snapshot
from sandbox.workspace import Project, ProjectExistsError


class WizardScreen(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.templates: list[Template] = []
        self.selected: Template | None = None
        self.name_edit: QLineEdit | None = None
        self.field_validate = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        self.header = QLabel()
        self.header.setObjectName("title")
        layout.addWidget(self.header)

        self.body = QScrollArea()
        self.body.setWidgetResizable(True)
        self.content = QWidget()
        self.content_box = QVBoxLayout(self.content)
        self.content_box.setSpacing(10)
        self.body.setWidget(self.content)
        layout.addWidget(self.body, stretch=1)

        footer = QHBoxLayout()
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff2e44; font-family: Consolas, 'Courier New', monospace;")
        self.error_label.setWordWrap(True)
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self._back)
        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("primary")
        self.next_btn.clicked.connect(self._next)
        footer.addWidget(self.error_label, stretch=1)
        footer.addWidget(self.back_btn)
        footer.addWidget(self.next_btn)
        layout.addLayout(footer)

        self.step = 1

    def refresh(self) -> None:
        self.templates = discover_templates(templates_dir())
        self.show_step(1)

    def show_step(self, step: int) -> None:
        self.step = step
        self.error_label.setText("")
        self._clear_content()
        if step == 1:
            self.header.setText("Step 1 of 2 \u2014 What do you want to make?")
            self.back_btn.setText("Home")
            self.next_btn.setText("Next")
            self._build_template_list()
        else:
            self.header.setText("Step 2 of 2 \u2014 Add your details")
            self.back_btn.setText("Back")
            self.next_btn.setText("Create it")
            self._build_details_form()

    def _clear_content(self) -> None:
        while self.content_box.count():
            item = self.content_box.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _build_template_list(self) -> None:
        if not self.templates:
            self.content_box.addWidget(
                QLabel("No templates found in the templates/ folder.")
            )
            return
        for template in self.templates:
            btn = QPushButton()
            btn.setObjectName("card")
            title = QLabel(f"{template.name}   ({template.language})")
            title.setObjectName("card_title")
            desc = QLabel(template.description)
            desc.setWordWrap(True)
            desc.setObjectName("muted")
            wrap = QVBoxLayout(btn)
            wrap.setContentsMargins(12, 10, 12, 10)
            wrap.addWidget(title)
            wrap.addWidget(desc)
            btn.clicked.connect(
                lambda _=False, t=template: self._select(t)
            )
            self.content_box.addWidget(btn)

    def _select(self, template: Template) -> None:
        self.selected = template
        self.show_step(2)

    def _build_details_form(self) -> None:
        template = self.selected
        if template is None:
            return
        self.content_box.addWidget(QLabel("Give your project a name"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. My First Game")
        self.content_box.addWidget(self.name_edit)
        self.content_box.addWidget(QLabel("Now the fun part \u2014 answer these questions:"))
        form_widget, self.field_validate, _ = build_field_form(template.fields, {})
        self.content_box.addWidget(form_widget)

    def _back(self) -> None:
        if self.step == 2:
            self.show_step(1)
        else:
            self.window.show_home()

    def _next(self) -> None:
        if self.step == 1:
            if self.selected is not None:
                self.show_step(2)
            return
        template = self.selected
        if template is None or self.name_edit is None:
            return
        name = self.name_edit.text().strip()
        if not name:
            self.error_label.setText("Please give your project a name first.")
            return
        try:
            values = self.field_validate()
        except FieldValidationError as exc:
            self.error_label.setText(str(exc))
            return
        try:
            project = Project.create(
                self.window.workspace, name, template.manifest.get("id", ""), values
            )
        except ProjectExistsError as exc:
            self.error_label.setText(str(exc))
            return
        try:
            template.materialize(project.files_dir, values)
        except TemplateError as exc:
            self.error_label.setText(str(exc))
            return
        take_snapshot(project, "Initial version")
        try:
            repo = RepoManager(project.files_dir)
            repo.ensure()
            repo.save_version("Started project")
        except GitError:
            pass
        self.window.open_project(project)
