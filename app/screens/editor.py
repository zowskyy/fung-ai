from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QThread, Qt, Signal, QStringListModel
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QInputDialog,
    QCompleter,
    QWidget,
)

from ai import get_backend, settings, CyclingBackend
from app.notifications import notify_complete
from app.paths import templates_dir
from app.widgets import ContextPanel, build_field_form
from app.widgets.diff_view import DiffView
from app.widgets.markdown import MarkdownView
from app.widgets.tool_view import ToolExecutionView
from core.field_models import FieldValidationError
from core.template_engine import Template, TemplateError, discover_templates
from repo.git_manager import GitError, RepoManager
from runners import NoRunnerForLanguage, get_runner
from sandbox.snapshots import take_snapshot
from sandbox.workspace import Project


class RunWorker(QThread):
    line = Signal(str)
    finished_run = Signal(int)

    def __init__(self, runner, cwd, script, parent=None):
        super().__init__(parent)
        self.runner = runner
        self.cwd = cwd
        self.script = script

    def run(self) -> None:
        try:
            code = self.runner.start_and_stream(self.cwd, self.script, self.line.emit)
        except Exception as exc:
            self.line.emit(f"Error: {exc}")
            code = 1
        self.finished_run.emit(code)


class AIWorker(QThread):
    delta = Signal(str)
    done = Signal(str)

    def __init__(self, backend, system, user, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.system = system
        self.user = user

    def run(self) -> None:
        try:
            reply = self.backend.complete(
                self.system, [{"role": "user", "content": self.user}], self.delta.emit
            )
        except Exception as exc:
            reply = f"Error: {exc}"
            self.delta.emit(reply)
        self.done.emit(reply)


class InsightsWorker(QThread):
    """Streams a few helpful, related ideas while the main answer is gathered.

    This is the friendly 'distraction' that keeps a client engaged and quietly
    surfaces possibilities (and, softly, other things Creator can do) without
    ever touching the user's files.
    """

    delta = Signal(str)
    done = Signal(str)

    def __init__(self, backend, system, user, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.system = system
        self.user = user

    def run(self) -> None:
        try:
            reply = self.backend.complete(
                self.system, [{"role": "user", "content": self.user}], self.delta.emit
            )
        except Exception as exc:
            self.delta.emit(f"(ideas unavailable: {exc})")
            reply = ""
        self.done.emit(reply)


EDIT_RE = re.compile(r"%%EDIT\s+([^\n]+)\n(.*?)%%END", re.DOTALL)


class EditorScreen(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.project: Project | None = None
        self.template: Template | None = None
        self.field_validate = None
        self.run_worker: RunWorker | None = None
        self.ai_worker: AIWorker | None = None
        self.insights_worker: InsightsWorker | None = None
        self._ai_raw = ""
        self._ai_edit_mode = False
        self._pending = 0
        self._open_tabs: dict[int, Project] = {}
        self._tab_counter = 0
        self._undo_stack: list[dict] = []
        self._redo_stack: list[dict] = []
        self._attached_files: set[str] = set()
        self._thinking = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.session_tabs = QTabBar()
        self.session_tabs.setTabsClosable(True)
        self.session_tabs.setMovable(True)
        self.session_tabs.tabCloseRequested.connect(self._close_tab)
        self.session_tabs.currentChanged.connect(self._on_tab_changed)
        self.session_tabs.setStyleSheet(
            "QTabBar { background: #0a0f0a; border-bottom: 1px solid #0b3d22; padding-left: 8px; }"
            "QTabBar::tab { padding: 8px 16px; border: none; border-right: 1px solid #0b3d22; "
            "background: #0a0f0a; color: #4f6b57; font-size: 12px; "
            "font-family: Consolas, 'Courier New', monospace; }"
            "QTabBar::tab:selected { background: #050805; color: #00ff66; font-weight: 600; }"
            "QTabBar::tab:hover { background: #0b3d22; }"
        )
        layout.addWidget(self.session_tabs)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 16, 24, 24)
        content_layout.setSpacing(10)

        header = QHBoxLayout()
        home_btn = QPushButton("Home")
        home_btn.clicked.connect(window.show_home)
        self.title_label = QLabel()
        self.title_label.setObjectName("title")
        header.addWidget(home_btn)
        header.addWidget(self.title_label)
        header.addStretch()

        self.mode_btn = QPushButton("Build")
        self.mode_btn.setCheckable(True)
        self.mode_btn.setChecked(True)
        self.mode_btn.setMinimumWidth(80)
        self.mode_btn.setStyleSheet(
            "QPushButton { border-radius: 6px; padding: 6px 14px; font-weight: 600; "
            "background: #00ff66; color: #050805; border: none; "
            "font-family: Consolas, 'Courier New', monospace; }"
            "QPushButton:hover { background: #1aff77; }"
            "QPushButton:checked { background: #ff2e44; color: #050805; }"
            "QPushButton:checked:hover { background: #ff5a6e; }"
        )
        self.mode_btn.toggled.connect(self._on_mode_toggled)
        header.addWidget(self.mode_btn)

        content_layout.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_edit_tab(), "Edit")
        self.tabs.addTab(self._build_run_tab(), "Run")
        self.tabs.addTab(self._build_versions_tab(), "Versions")
        self.tabs.addTab(self._build_ai_tab(), "Ask AI")
        content_layout.addWidget(self.tabs, stretch=1)

        layout.addWidget(content, stretch=1)

    def set_project(self, project: Project) -> None:
        for idx, proj in self._open_tabs.items():
            if proj.root == project.root:
                self.session_tabs.setCurrentIndex(idx)
                return
        self._tab_counter += 1
        idx = self._tab_counter
        self._open_tabs[idx] = project
        self.session_tabs.addTab(project.name)
        self.session_tabs.setTabData(idx, project.root)
        self.session_tabs.setCurrentIndex(idx)
        self._load_project(project)

    def _load_project(self, project: Project) -> None:
        self.project = project
        self.title_label.setText(project.name)
        for template in discover_templates(templates_dir()):
            if template.manifest.get("id") == project.data.get("template"):
                self.template = template
                break
        self._build_edit_form()
        self._refresh_versions()
        self.output.clear()
        self._refresh_ai_status()
        self._attached_files.clear()
        self._update_attached_files_label()
        if hasattr(self, "context_panel"):
            self.context_panel.update_context(project, self.template)
        self.tabs.setCurrentIndex(0)
        self.window.current_project = project
        if hasattr(self.window, "sidebar"):
            self.window.sidebar.highlight_project(project)
        self._set_status_mode("build" if self.mode_btn.isChecked() else "plan")

    def _close_tab(self, idx: int) -> None:
        if idx not in self._open_tabs:
            return
        del self._open_tabs[idx]
        self.session_tabs.removeTab(idx)
        remaining = list(self._open_tabs.values())
        if remaining:
            new_idx = self.session_tabs.currentIndex()
            if new_idx >= 0 and new_idx in self._open_tabs:
                self._load_project(self._open_tabs[new_idx])
        else:
            self.project = None
            self.template = None
            self.title_label.setText("")
            self.window.show_home()

    def _on_tab_changed(self, idx: int) -> None:
        if idx >= 0 and idx in self._open_tabs:
            self._load_project(self._open_tabs[idx])

    def _build_edit_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.edit_form_container = QWidget()
        layout.addWidget(self.edit_form_container)
        self.edit_status = QLabel("")
        self.edit_status.setWordWrap(True)
        layout.addWidget(self.edit_status)
        save_btn = QPushButton("Update project")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._save_edits)
        layout.addWidget(save_btn)
        return tab

    def _build_edit_form(self) -> None:
        container = self.edit_form_container
        old = container.layout()
        if old is not None:
            while old.count():
                item = old.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            old.deleteLater()

        layout = QVBoxLayout(container)
        container.setLayout(layout)
        if self.template is None or self.project is None:
            layout.addWidget(
                QLabel("This project's template could not be found in templates/.")
            )
            self.field_validate = None
            return
        values = dict(self.project.data.get("fields", {}))
        form_widget, self.field_validate, _ = build_field_form(
            self.template.fields, values
        )
        layout.addWidget(form_widget)
        layout.addStretch()

    def _save_edits(self) -> None:
        if self.template is None or self.project is None or self.field_validate is None:
            return
        try:
            values = self.field_validate()
        except FieldValidationError as exc:
            self.edit_status.setStyleSheet("color: #c62828;")
            self.edit_status.setText(str(exc))
            return
        try:
            self.template.materialize(self.project.files_dir, values)
        except TemplateError as exc:
            self.edit_status.setStyleSheet("color: #c62828;")
            self.edit_status.setText(str(exc))
            return
        self.project.save_fields(values)
        self.edit_status.setStyleSheet("color: #00ff66;")
        self.edit_status.setText("Saved. Go to Run to try it, or Versions to keep this moment.")

    def _build_run_tab(self) -> QWidget:
        tab = QWidget()
        self._run_tab = tab
        layout = QVBoxLayout(tab)
        self.run_status = QLabel("")
        self.run_status.setWordWrap(True)
        layout.addWidget(self.run_status)
        buttons = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.run_btn.setObjectName("primary")
        self.run_btn.clicked.connect(self._run)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_run)
        buttons.addWidget(self.run_btn)
        buttons.addWidget(self.stop_btn)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.tool_view = ToolExecutionView()
        layout.addWidget(self.tool_view, stretch=1)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Output from your creation will appear here.")
        self.output.setMaximumHeight(150)
        layout.addWidget(self.output)
        return tab

    def _run(self) -> None:
        if self.project is None or self.template is None:
            return
        is_build = self.mode_btn.isChecked()
        if not is_build:
            reply = QMessageBox.question(
                self,
                "Permission required",
                "You are in Plan mode. Running executes the project's code.\n"
                "Allow this run?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.run_status.setText("Run cancelled (Plan mode permission denied).")
                return
        window = self.window
        if hasattr(window, "status_bar"):
            window.status_bar.set_status("Running...")
        cmd = self.template.run_command()
        script = cmd[1] if len(cmd) > 1 else "game.py"
        try:
            runner = get_runner(self.template.language)
        except NoRunnerForLanguage as exc:
            self.output.appendPlainText(str(exc))
            return
        self.output.clear()
        self.tool_view.clear()
        self._run_card = self.tool_view.add_execution(" ".join(cmd))
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.run_worker = RunWorker(runner, self.project.files_dir, script, self)
        self.run_worker.line.connect(self._on_run_line)
        self.run_worker.finished_run.connect(self._run_finished)
        self.run_worker.start()
        if hasattr(self.window, "status_bar"):
            self.window.status_bar.set_status(f"Running: {' '.join(cmd)}")

    def _on_run_line(self, line: str) -> None:
        self.output.appendPlainText(line)
        if hasattr(self, "_run_card") and self._run_card is not None:
            self._run_card.append_line(line)

    def _run_finished(self, code: int) -> None:
        if hasattr(self, "_run_card") and self._run_card is not None:
            self._run_card.finish(code)
            self._run_card = None
        self.output.appendPlainText("")
        self.output.appendPlainText(f"Finished (exit code {code}).")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if hasattr(self.window, "status_bar"):
            self.window.status_bar.set_status(f"Finished (exit {code})")
        notify_complete(self)

    def _stop_run(self) -> None:
        if self.run_worker is not None:
            self.run_worker.runner.stop()

    def _build_versions_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        hint = QLabel("Every version is saved safely, so you can always go back.")
        hint.setObjectName("muted")
        layout.addWidget(hint)
        note_row = QHBoxLayout()
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("What did you change? (e.g. Made the sky purple)")
        save_ver_btn = QPushButton("Save a version")
        save_ver_btn.setObjectName("primary")
        save_ver_btn.clicked.connect(self._save_version)
        note_row.addWidget(self.note_edit, stretch=1)
        note_row.addWidget(save_ver_btn)
        layout.addLayout(note_row)

        self.versions_list = QListWidget()
        layout.addWidget(self.versions_list, stretch=1)

        actions = QHBoxLayout()
        restore_btn = QPushButton("Restore this version")
        restore_btn.clicked.connect(self._restore_version)
        changed_btn = QPushButton("What changed?")
        changed_btn.clicked.connect(self._what_changed)
        actions.addWidget(restore_btn)
        actions.addWidget(changed_btn)
        export_btn = QPushButton("Export...")
        export_btn.clicked.connect(self._export_session)
        actions.addWidget(export_btn)
        actions.addStretch()
        layout.addLayout(actions)

        self.version_status = QLabel("")
        self.version_status.setWordWrap(True)
        layout.addWidget(self.version_status)

        self.diff_view = DiffView()
        layout.addWidget(self.diff_view)

        return tab

    def _save_version(self) -> None:
        if self.project is None:
            return
        note = self.note_edit.text().strip() or "Saved a version"
        take_snapshot(self.project, note)
        try:
            repo = RepoManager(self.project.files_dir)
            repo.ensure()
            repo.save_version(note)
        except GitError:
            pass
        self.version_status.setStyleSheet("color: #00ff66;")
        self.version_status.setText("Version saved. You can always come back to it.")
        self._refresh_versions()

    def _refresh_versions(self) -> None:
        self.versions_list.clear()
        if self.project is None:
            return
        try:
            versions = RepoManager(self.project.files_dir).list_versions()
        except GitError:
            versions = []
        for version in versions:
            item = QListWidgetItem(f"{version['hash']}  {version['message']}")
            item.setData(Qt.UserRole, version["hash"])
            self.versions_list.addItem(item)
        if not versions:
            self.versions_list.addItem("No versions saved yet. Click \u201cSave a version\u201d.")

    def _restore_version(self) -> None:
        if self.project is None:
            return
        item = self.versions_list.currentItem()
        if item is None:
            self.version_status.setText("Pick a version first, then click Restore.")
            return
        revision = item.data(Qt.UserRole)
        if not revision:
            return
        confirm = QMessageBox.question(
            self,
            "Restore version",
            f"Put your project back to version {revision}? This overwrites your current files.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            RepoManager(self.project.files_dir).restore(revision)
        except GitError as exc:
            self.version_status.setStyleSheet("color: #c62828;")
            self.version_status.setText(str(exc))
            return
        self.version_status.setStyleSheet("color: #00ff66;")
        self.version_status.setText(f"Restored version {revision}.")

    def _what_changed(self) -> None:
        if self.project is None:
            return
        item = self.versions_list.currentItem()
        if item is None:
            self.version_status.setText("Pick a version first, then click What changed.")
            return
        revision = item.data(Qt.UserRole)
        if not revision:
            return
        try:
            repo = RepoManager(self.project.files_dir)
            changed_files = repo.changed_files(revision)
            if not changed_files:
                self.diff_view.show_diff("changes", "", "(no changes)")
                return
            for filename in changed_files:
                try:
                    old_text = repo.show_file(revision + "~1", filename) if revision != list(RepoManager(self.project.files_dir).list_versions())[0]["hash"] else ""
                    new_text = repo.show_file(revision, filename)
                    self.diff_view.show_diff(filename, old_text, new_text)
                except (GitError, IndexError):
                    pass
        except GitError as exc:
            self.version_status.setStyleSheet("color: #c62828;")
            self.version_status.setText(str(exc))

    def _export_session(self) -> None:
        if self.project is None:
            return
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Session", f"{self.project.name}.json",
            "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        import json
        data = {
            "project": self.project.name,
            "template": self.project.data.get("template", ""),
            "fields": self.project.data.get("fields", {}),
            "created": self.project.data.get("created", ""),
        }
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.version_status.setStyleSheet("color: #00ff66;")
        self.version_status.setText(f"Session exported to {path}")

    def _build_ai_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.ai_status = QLabel("")
        self.ai_status.setWordWrap(True)
        layout.addWidget(self.ai_status)

        top_row = QHBoxLayout()
        self.allow_edits_check = QCheckBox(
            "Let the AI edit my files (experimental, undoable via Versions)"
        )
        self.allow_edits_check.setChecked(settings.allow_ai_edits())
        self.allow_edits_check.toggled.connect(self._on_allow_edits_toggled)
        top_row.addWidget(self.allow_edits_check)
        top_row.addStretch()

        self.attach_btn = QPushButton("Attach File")
        self.attach_btn.setToolTip("Attach a project file to the conversation")
        self.attach_btn.clicked.connect(self._attach_file)
        top_row.addWidget(self.attach_btn)

        self.undo_btn = QPushButton("Undo")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self._undo_edit)
        top_row.addWidget(self.undo_btn)

        self.redo_btn = QPushButton("Redo")
        self.redo_btn.setEnabled(False)
        self.redo_btn.clicked.connect(self._redo_edit)
        top_row.addWidget(self.redo_btn)

        self.thinking_check = QCheckBox("Reasoning")
        self.thinking_check.setToolTip("Show the model's reasoning blocks (/thinking)")
        self.thinking_check.toggled.connect(self._on_thinking_toggled)
        top_row.addWidget(self.thinking_check)

        layout.addLayout(top_row)

        self.attached_files_label = QLabel("")
        self.attached_files_label.setWordWrap(True)
        self.attached_files_label.setStyleSheet("color: #4f6b57; font-size: 11px; font-family: Consolas, 'Courier New', monospace;")
        layout.addWidget(self.attached_files_label)

        split = QHBoxLayout()
        chat_col = QVBoxLayout()
        self.chat_log = MarkdownView()
        chat_col.addWidget(self.chat_log, stretch=1)
        prompt_row = QHBoxLayout()
        self.prompt_edit = QLineEdit()
        self.prompt_edit.setPlaceholderText(
            "e.g. Suggest three fun hero names  (type # to attach, @ for mode, / for commands)"
        )
        self.prompt_edit.returnPressed.connect(self._send_prompt)
        self._completer = QCompleter(self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.prompt_edit.setCompleter(self._completer)
        self.prompt_edit.textChanged.connect(self._update_completer)
        self.ai_send_btn = QPushButton("Send")
        self.ai_send_btn.setObjectName("primary")
        self.ai_send_btn.clicked.connect(self._send_prompt)
        prompt_row.addWidget(self.prompt_edit, stretch=1)
        prompt_row.addWidget(self.ai_send_btn)
        chat_col.addLayout(prompt_row)
        split.addLayout(chat_col, stretch=3)

        insights_col = QVBoxLayout()
        insights_header = QLabel("Ideas you might not have thought of")
        insights_header.setObjectName("muted")
        insights_col.addWidget(insights_header)
        self.insights_view = QPlainTextEdit()
        self.insights_view.setReadOnly(True)
        self.insights_view.setPlaceholderText(
            "Connect an AI helper to see live ideas while your answer loads."
        )
        insights_col.addWidget(self.insights_view, stretch=1)
        split.addLayout(insights_col, stretch=1)

        self.context_panel = ContextPanel()
        self.context_panel.set_file_click_callback(self._attach_file_from_panel)
        split.addWidget(self.context_panel, stretch=1)

        layout.addLayout(split, stretch=1)
        return tab

    def _system_prompt(self) -> str:
        fields = ""
        if self.project is not None:
            fields = str(self.project.data.get("fields", {}))
        template_name = self.template.name if self.template else "unknown"
        is_build = self.mode_btn.isChecked()
        mode_desc = "Build" if is_build else "Plan"
        prompt = (
            f"You are the friendly AI helper inside Creator, an app for people who "
            f"do not write code. They make projects from kits. Be warm, clear, and "
            f"short. Give concrete suggestions they can type into the form. "
            f"Current kit: {template_name}. Current answers: {fields}. "
            f"You are currently in {mode_desc} mode."
        )
        if self._attached_files:
            prompt += "\n\nAttached files (for context):"
            for rel_path in sorted(self._attached_files):
                try:
                    full_path = self.project.files_dir / rel_path
                    if full_path.exists():
                        content = full_path.read_text(encoding="utf-8")
                        prompt += f"\n--- {rel_path} ---\n{content}\n"
                except (OSError, UnicodeDecodeError):
                    pass
        if is_build and settings.allow_ai_edits():
            prompt += (
                "\nWhen you want to change a project file, output the new file inside "
                "an edit block placed after your explanation, exactly like this:\n"
                "%%EDIT <relative/path/to/file>\n<the full new contents of that file>\n%%END\n"
                "Only edit files that already exist in the project. Do not edit the manifest."
            )
        elif not is_build:
            prompt += (
                "\nYou are in Plan mode. You must NOT edit any files. "
                "Analyze the code and suggest improvements, but do not output %%EDIT blocks."
            )
        if self._thinking:
            prompt += "\nShow your reasoning step by step before the final answer."
        return prompt

    def _insights_system(self) -> str:
        return (
            "You are a creative product coach for non-coders using Creator, a no-code "
            "app builder. Given the user's request, reply with exactly 3 short, concrete "
            "feature or improvement ideas they may not have considered. One idea per line. "
            "Each line at most 12 words. No numbering, no markdown, no code. Be encouraging "
            "and mention other kinds of projects or kits when relevant."
        )

    def _attach_file(self) -> None:
        if not self.project:
            return
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Attach File", str(self.project.files_dir), "All Files (*)"
        )
        if file_path:
            self._add_attached_file(file_path)

    def _attach_file_from_panel(self, file_path: str) -> None:
        self._add_attached_file(file_path)

    def _add_attached_file(self, file_path: str) -> None:
        if not self.project:
            return
        try:
            full_path = Path(file_path).resolve()
            base = self.project.files_dir.resolve()
            if base not in full_path.parents and full_path != base:
                return
            rel_path = str(full_path.relative_to(base))
            self._attached_files.add(rel_path)
            self._update_attached_files_label()
            self.chat_log.append_markdown(f"Attached **{rel_path}** to the conversation.")
        except (OSError, ValueError):
            pass

    def _update_attached_files_label(self) -> None:
        if self._attached_files:
            files = ", ".join(sorted(self._attached_files))
            self.attached_files_label.setText(f"Attached: {files}")
        else:
            self.attached_files_label.setText("")

    def _on_mode_toggled(self, checked: bool) -> None:
        if checked:
            self.mode_btn.setText("Build")
            self.mode_btn.setStyleSheet(
                "QPushButton { border-radius: 6px; padding: 6px 14px; font-weight: 600; "
                "background: #00ff66; color: #050805; border: none; "
                "font-family: Consolas, 'Courier New', monospace; }"
                "QPushButton:hover { background: #1aff77; }"
            )
            settings.set_allow_edits(True)
            self.allow_edits_check.setChecked(True)
            self._set_status_mode("build")
        else:
            self.mode_btn.setText("Plan")
            self.mode_btn.setStyleSheet(
                "QPushButton { border-radius: 6px; padding: 6px 14px; font-weight: 600; "
                "background: #ff2e44; color: #050805; border: none; "
                "font-family: Consolas, 'Courier New', monospace; }"
                "QPushButton:hover { background: #ff5a6e; }"
            )
            settings.set_allow_edits(False)
            self.allow_edits_check.setChecked(False)
            self._set_status_mode("plan")

    def set_mode(self, mode: str) -> None:
        self.mode_btn.setChecked(mode.strip().lower() != "plan")

    def _set_status_mode(self, mode: str) -> None:
        window = self.window
        if hasattr(window, "status_bar"):
            window.status_bar.set_mode(mode)

    def run_current(self) -> None:
        self.tabs.setCurrentWidget(self._run_tab)
        self._run()

    def rename_current(self) -> None:
        project = self.project
        if project is None:
            return
        current = project.name
        new_name, ok = QInputDialog.getText(
            self, "Rename session", "New display name:", text=current
        )
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()
        project.data["name"] = new_name
        project.save_fields(project.data.get("fields", {}))
        self.title_label.setText(new_name)
        idx = self.session_tabs.currentIndex()
        if idx >= 0:
            self.session_tabs.setTabText(idx, new_name)
        window = self.window
        if hasattr(window, "sidebar"):
            window.sidebar.refresh()
            window.sidebar.highlight_project(project)
        if hasattr(window, "status_bar"):
            window.status_bar.set_status(f"Renamed to {new_name}")

    def shutdown(self) -> None:
        for attr in ("ai_worker", "insights_worker", "run_worker"):
            worker = getattr(self, attr, None)
            if worker is not None and worker.isRunning():
                worker.quit()

    def _on_allow_edits_toggled(self, checked: bool) -> None:
        settings.set_allow_edits(bool(checked))

    def _on_thinking_toggled(self, checked: bool) -> None:
        self._thinking = bool(checked)
        self.chat_log.append_markdown(
            f"_Reasoning {'on' if self._thinking else 'off'}._"
        )

    def _project_file_list(self) -> list[str]:
        if self.project is None:
            return []
        files_dir = self.project.files_dir
        if not files_dir.exists():
            return []
        result = []
        for path in files_dir.rglob("*"):
            if path.is_file():
                result.append(str(path.relative_to(files_dir)))
        return sorted(result)

    def _slash_commands(self) -> list[str]:
        return [
            "help", "new", "sessions", "models", "themes",
            "share", "undo", "compact", "details", "thinking",
        ]

    def _update_completer(self, text: str) -> None:
        before = text[: self.prompt_edit.cursorPosition()]
        match = re.search(r"([@#/])(\w*)$", before)
        if match is None:
            self._completer.popup().hide() if self._completer.popup() is not None else None
            return
        trigger, partial = match.group(1), match.group(2)
        if trigger == "#":
            opts = [f"#{f}" for f in self._project_file_list()]
        elif trigger == "@":
            opts = ["@Build", "@Plan"]
        else:
            opts = [f"/{c}" for c in self._slash_commands()]
        opts = [o for o in opts if o.lower().startswith((trigger + partial).lower())]
        self._completer.setModel(QStringListModel(opts))
        self._completer.setCompletionPrefix(trigger + partial)
        if opts:
            self._completer.complete()

    def _send_prompt(self) -> None:
        user = self.prompt_edit.text().strip()
        if not user:
            if get_backend() is None:
                self.chat_log.append_markdown(
                    "AI is not connected. Set an API key in ~/.creator/auth.json "
                    "(bring your own key) or point at a local server like Ollama "
                    "via the ai/ module, then try again."
                )
            return
        if user.startswith("/"):
            self.prompt_edit.clear()
            self._handle_slash(user)
            return
        backend = get_backend()
        if backend is None:
            self.chat_log.append_markdown(
                "AI is not connected. Set an API key in ~/.creator/auth.json "
                "(bring your own key) or point at a local server like Ollama "
                "via the ai/ module, then try again."
            )
            return
        self.chat_log.append_markdown(f"**You:** {user}")
        self.prompt_edit.clear()
        self.ai_send_btn.setEnabled(False)
        self._ai_raw = ""
        self._ai_edit_mode = settings.allow_ai_edits()
        self._pending = 2

        self.insights_view.clear()
        self.ai_worker = AIWorker(backend, self._system_prompt(), user, self)
        self.ai_worker.delta.connect(self._ai_delta)
        self.ai_worker.done.connect(self._ai_done)
        self.ai_worker.start()

        self.insights_worker = InsightsWorker(backend, self._insights_system(), user, self)
        self.insights_worker.delta.connect(self._insights_delta)
        self.insights_worker.done.connect(self._insights_done)
        self.insights_worker.start()

    def _handle_slash(self, command: str) -> None:
        cmd = command.strip().lstrip("/").split()[0].lower() if command.strip() != "/" else ""
        if cmd in ("help", ""):
            self.chat_log.append_markdown(
                "**Commands**\n"
                "- `/help` — show this list\n"
                "- `/new` — clear the conversation\n"
                "- `/models` — show the active model/backend\n"
                "- `/themes` — list UI theme info\n"
                "- `/sessions` — go to the session/project list\n"
                "- `/undo` — revert the last AI edit\n"
                "- `/compact` — clear the visible conversation\n"
                "- `/details` — toggle showing tool run details\n"
                "- `/thinking` — toggle the model's reasoning blocks\n"
            )
        elif cmd == "new":
            self.chat_log.clear()
            self.chat_log.append_markdown("_New conversation started._")
        elif cmd == "sessions":
            self.window.show_home()
            self.chat_log.append_markdown("_Switched to the session list._")
        elif cmd == "models":
            self._refresh_ai_status()
            self.chat_log.append_markdown(
                f"**Model:** {self.window.status_bar.model_label.text()}"
            )
        elif cmd == "themes":
            self.chat_log.append_markdown(
                "**Theme:** fungai terminal (black / neon-green / red). "
                "This is the only bundled theme."
            )
        elif cmd == "share":
            self.chat_log.append_markdown(
                "Sharing is not enabled in this build. Export the session from "
                "the **Versions** tab to save a copy."
            )
        elif cmd == "undo":
            self._undo_edit()
        elif cmd == "compact":
            self.chat_log.clear()
            self.chat_log.append_markdown("_Conversation compacted._")
        elif cmd == "details":
            self.chat_log.append_markdown(
                "Tool run details are always shown in the **Run** tab."
            )
        elif cmd == "thinking":
            self._thinking = not self._thinking
            self.thinking_check.setChecked(self._thinking)
        else:
            self.chat_log.append_markdown(
                f"Unknown command `/{cmd}`. Type `/help` for the list."
            )

    def _ai_delta(self, text: str) -> None:
        if self._ai_edit_mode:
            self._ai_raw += text
        else:
            self.chat_log.append_markdown(text)

    def _ai_done(self, reply: str) -> None:
        if self._ai_edit_mode:
            cleaned = EDIT_RE.sub("", reply).strip()
            if cleaned:
                self.chat_log.append_markdown(cleaned)
            self._apply_edits(reply)
        self.chat_log.appendPlainText("")
        self._pending -= 1
        self._maybe_finish()

    def _insights_delta(self, text: str) -> None:
        self.insights_view.appendPlainText(text)

    def _insights_done(self, _reply: str) -> None:
        suggestions_text = self.insights_view.toPlainText().strip()
        if suggestions_text and hasattr(self, "context_panel"):
            for line in suggestions_text.splitlines():
                if line.strip():
                    self.context_panel.add_suggestion(line.strip())
        self._pending -= 1
        self._maybe_finish()

    def _maybe_finish(self) -> None:
        if self._pending <= 0:
            self.ai_send_btn.setEnabled(True)

    def _apply_edits(self, reply: str) -> None:
        if self.project is None:
            return
        files_dir = self.project.files_dir
        applied = 0
        edit_record: dict[str, str] = {}
        for match in EDIT_RE.finditer(reply):
            rel = match.group(1).strip().lstrip("/\\")
            content = match.group(2).strip("\n")
            target = (files_dir / rel).resolve()
            base = files_dir.resolve()
            if target != base and base not in target.parents:
                self.chat_log.append_markdown(
                    f"Refused an edit to {rel} (it is outside the project)."
                )
                continue
            if target.exists():
                edit_record[rel] = target.read_text(encoding="utf-8")
            else:
                edit_record[rel] = ""
            note = f"Before AI edit to {rel}"
            try:
                take_snapshot(self.project, note)
                repo = RepoManager(files_dir)
                repo.ensure()
                repo.save_version(note)
            except (GitError, OSError):
                pass
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            applied += 1
            self.chat_log.append_markdown(
                f"Applied an edit to {rel}. Undo it any time from the Versions tab."
            )
        if applied:
            self._undo_stack.append(edit_record)
            self._redo_stack.clear()
            self._update_undo_redo_buttons()
            self._refresh_versions()

    def _undo_edit(self) -> None:
        if not self._undo_stack or self.project is None:
            return
        edit_record = self._undo_stack.pop()
        restore_record: dict[str, str] = {}
        files_dir = self.project.files_dir
        for rel, old_content in edit_record.items():
            target = (files_dir / rel).resolve()
            if target.exists():
                restore_record[rel] = target.read_text(encoding="utf-8")
            else:
                restore_record[rel] = ""
            if old_content:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(old_content, encoding="utf-8")
            elif target.exists():
                target.unlink()
        self._redo_stack.append(restore_record)
        self._update_undo_redo_buttons()
        self._refresh_versions()
        self.chat_log.append_markdown("**Undo:** Reverted the last AI edit.")

    def _redo_edit(self) -> None:
        if not self._redo_stack or self.project is None:
            return
        restore_record = self._redo_stack.pop()
        undo_record: dict[str, str] = {}
        files_dir = self.project.files_dir
        for rel, content in restore_record.items():
            target = (files_dir / rel).resolve()
            if target.exists():
                undo_record[rel] = target.read_text(encoding="utf-8")
            else:
                undo_record[rel] = ""
            if content:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            elif target.exists():
                target.unlink()
        self._undo_stack.append(undo_record)
        self._update_undo_redo_buttons()
        self._refresh_versions()
        self.chat_log.append_markdown("**Redo:** Re-applied the AI edit.")

    def _update_undo_redo_buttons(self) -> None:
        self.undo_btn.setEnabled(len(self._undo_stack) > 0)
        self.redo_btn.setEnabled(len(self._redo_stack) > 0)

    def _refresh_ai_status(self) -> None:
        window = self.window
        backend = get_backend()
        if backend is None:
            self.ai_status.setText(
                "AI is off (works fine without it). Bring your own key or use a local "
                "model server to turn it on."
            )
            self.allow_edits_check.setEnabled(False)
            self.insights_view.setPlainText(
                "Connect an AI helper to see live ideas while your answer loads."
            )
            if hasattr(window, "status_bar"):
                window.status_bar.set_model("no backend")
        elif isinstance(backend, CyclingBackend):
            providers = backend._get_available_providers()
            if providers:
                current = providers[0] if backend._current_index == 0 else providers[-1]
                self.ai_status.setText(
                    f"AI is on — auto-cycling through {len(providers)} free models. "
                    f"Current: {current.name}"
                )
                if hasattr(window, "status_bar"):
                    window.status_bar.set_model(f"cycling: {current.name}")
            else:
                self.ai_status.setText(
                    "AI cycling enabled but no providers available (check API keys)."
                )
                if hasattr(window, "status_bar"):
                    window.status_bar.set_model("cycling: none")
            self.allow_edits_check.setEnabled(True)
        else:
            self.ai_status.setText(f"AI is on \u2014 connected via {backend.name}.")
            self.allow_edits_check.setEnabled(True)
            if hasattr(window, "status_bar"):
                window.status_bar.set_model(backend.name)
