import json
import re
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Label, ListItem, ListView, Markdown, Button, Input
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.events import Click

class ExamSelector(ModalScreen):
    """A simple screen to select from multiple generated exams."""
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Select Exam Set to Load:", id="selector-title"),
            ListView(id="exam-choice-list"),
            Button("Cancel", id="btn-cancel"),
            id="selector-container"
        )

    def on_mount(self) -> None:
        exam_list = self.query_one("#exam-choice-list")
        exams = list(Path("exams").glob("*.json"))
        if Path("exam_data.json").exists(): exams.append(Path("exam_data.json"))
        if not exams:
            exam_list.append(ListItem(Label("No exams found. Please run generator.py"), name=""))
            return
        for path in sorted(exams, reverse=True):
            exam_list.append(ListItem(Label(f"📄 {path.name}"), name=str(path)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.name: self.dismiss(event.item.name)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


class TimerModal(ModalScreen):
    """Modal to input desired exam time in minutes."""
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Set Exam Duration (Minutes):", id="timer-modal-title"),
            Input(placeholder="Enter minutes (e.g., 190)", id="timer-input", type="integer"),
            Horizontal(
                Button("Set", id="btn-set"),
                Button("Cancel", id="btn-cancel"),
                id="timer-modal-buttons"
            ),
            id="timer-modal-container"
        )

    def on_mount(self) -> None:
        self.query_one("#timer-input").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-set": self.submit()
        else: self.dismiss()

    def on_input_submitted(self) -> None:
        self.submit()

    def submit(self) -> None:
        value = self.query_one("#timer-input").value
        if value.isdigit(): self.dismiss(int(value))
        else: self.dismiss()


class ScenarioModal(ModalScreen):
    """Full-screen reading view for the scenario overlay."""
    BINDINGS = [
        Binding("s", "dismiss", "Close Scenario"),
        Binding("escape", "dismiss", "Close"),
        Binding("j", "scroll_down", "Scroll Down", show=False),
        Binding("k", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("up", "scroll_up", "Scroll Up", show=False),
    ]

    def __init__(self, scenario_text, **kwargs):
        super().__init__(**kwargs)
        self.scenario_text = scenario_text

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("SCENARIO REFERENCE", id="scenario-title"),
            ScrollableContainer(Markdown(self.scenario_text, id="scenario-text"), id="scenario-scroll"),
            Label("Press 's' or 'Esc' to close...", id="scenario-close-hint"),
            id="scenario-modal-container"
        )

    def action_dismiss(self) -> None: self.dismiss()
    def action_scroll_down(self) -> None: self.query_one("#scenario-scroll").scroll_relative(y=3, animate=False)
    def action_scroll_up(self) -> None: self.query_one("#scenario-scroll").scroll_relative(y=-3, animate=False)


class RationaleModal(ModalScreen):
    """Zero-border rationale feedback with navigation."""
    BINDINGS = [
        Binding("escape", "dismiss_back", "Back"),
        Binding("j", "scroll_down", "Scroll Down", show=False),
        Binding("k", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("up", "scroll_up", "Scroll Up", show=False),
    ]

    def __init__(self, rationale, is_correct, correct_ans, **kwargs):
        super().__init__(**kwargs)
        self.rationale = rationale
        self.is_correct = is_correct
        self.correct_ans = correct_ans

    def compose(self) -> ComposeResult:
        header_text = "[#3fb950]CORRECT[/#3fb950]" if self.is_correct else f"[#f85149]INCORRECT[/#f85149] - Answer is {self.correct_ans}"
        
        cleaned_rationale = self.rationale.replace("Why this is correct:", f"**Why Option {self.correct_ans} is correct:**")

        yield Vertical(
            Label(header_text, id="status-label"),
            ScrollableContainer(Markdown(cleaned_rationale, id="rationale-text"), id="rationale-scroll"),
            Horizontal(
                Button("Back", id="btn-modal-back"),
                Button("Next", id="btn-modal-next"),
                id="modal-nav-buttons"
            ),
            id="modal-container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def action_dismiss_back(self) -> None: self.dismiss("btn-modal-back")
    def action_scroll_down(self) -> None: self.query_one("#rationale-scroll").scroll_relative(y=3, animate=False)
    def action_scroll_up(self) -> None: self.query_one("#rationale-scroll").scroll_relative(y=-3, animate=False)


class ExamApp(App):
    theme = "textual-dark"
    CSS = """
    Screen { background: #0d1117; scrollbar-color: #30363d; scrollbar-background: transparent; }
    ScenarioModal, RationaleModal, TimerModal, ExamSelector { align: center middle; }
    #main-layout { height: 100%; }
    #sidebar { width: 35; background: #0d1117; border-right: solid #30363d; padding: 1; height: 100%; overflow: hidden; }
    #content-area { padding: 2; height: 100%; }
    #question-scroll { height: 1fr; padding-right: 1; }
    #question-display { margin-bottom: 1; color: #c9d1d9; }
    ListView { background: transparent; border: none; }
    
    #options-list { height: auto; margin-top: 1; margin-bottom: 1; }
    #options-list ListItem { height: auto; padding: 0 1; margin-bottom: 1; background: transparent; border: round #30363d; }
    #options-list Label { height: auto; width: 100%; color: #c9d1d9; }
    #options-list ListItem:hover { background: #161b22; }
    ListView#options-list ListItem.active-opt, ListView#options-list ListItem.--highlight { background: transparent; border: round #58a6ff; }
    ListView#options-list ListItem.active-opt Label, ListView#options-list ListItem.--highlight Label { color: #58a6ff !important; text-style: bold; }
    
    #q-list { margin-top: 1; height: 1fr; border-top: solid #30363d; padding-top: 1; overflow-x: hidden; }
    #q-list ListItem { padding: 1; background: transparent; height: auto; width: 100%; }
    #q-list Horizontal { height: 1; width: 100%; }
    #q-list ListItem:hover { background: #161b22; }
    #q-list ListItem.active-q { background: #21262d; border-left: thick #58a6ff; }
    #q-list ListItem.active-q .q-label { color: #c9d1d9; text-style: bold; }
    
    .bookmark-icon { width: 3; color: #8b949e; text-style: bold; text-align: center; }
    .q-label { width: 1fr; height: 1; color: #8b949e; overflow: hidden; }
    .answered-item .q-label { color: #484f58; text-style: strike; }
    .answered-item .bookmark-icon { color: #484f58; }
    .bookmark-icon.bookmarked { color: #f85149 !important; }
    
    #modal-container { width: 70%; height: auto; background: #161b22; border: round #30363d; padding: 2; }
    #timer-modal-container, #selector-container { width: 70%; height: auto; background: #161b22; border: round #30363d; padding: 2; align-horizontal: center; }
    #selector-container { width: 50%; max-height: 80%; }
    #rationale-scroll { max-height: 50vh; margin-bottom: 1; }
    #scenario-modal-container { width: 80%; height: 80%; background: #161b22; border: round #30363d; padding: 2; }
    #scenario-scroll { height: 1fr; }
    #scenario-title, #timer-modal-title, #selector-title { text-align: center; width: 100%; text-style: bold; margin-bottom: 1; color: #c9d1d9; }
    
    #exam-choice-list { height: 1fr; margin-bottom: 1; }
    #exam-choice-list ListItem { padding: 1; background: transparent; border: round #30363d; margin-bottom: 1; }
    #timer-bar { height: auto; align-horizontal: left; margin-top: 1; }
    #timer-label { text-align: center; text-style: bold; color: #c9d1d9; padding: 0 1; border: round #30363d; }
    #pause-btn, #theme-btn { width: 5; text-align: center; background: transparent; color: #8b949e; margin-left: 1; border: round #30363d; }
    #score-label { margin-bottom: 1; }
    
    #action-buttons, #modal-nav-buttons { height: auto; align-horizontal: right; margin-top: 1; }
    #modal-nav-buttons { align-horizontal: center; }
    #btn-next, #btn-answer, #btn-modal-back, #btn-modal-next, #btn-set, #btn-cancel {
        width: 20; height: 3; margin: 0 1; background: transparent; color: #c9d1d9; border: round #30363d; text-style: bold;
    }
    #btn-next:hover, #btn-answer:hover, #btn-modal-back:hover, #btn-modal-next:hover { background: #161b22; }

    /* LIGHT THEME OVERRIDES */
    Screen.light-mode { background: #ffffff; }
    Screen.light-mode #sidebar { background: #f6f8fa; border-right: solid #d0d7de; }
    Screen.light-mode #title, Screen.light-mode #progress, Screen.light-mode #score-label, Screen.light-mode #tab-hint { color: #24292f; }
    Screen.light-mode Markdown, Screen.light-mode Label, Screen.light-mode #question-display { color: #24292f; }
    Screen.light-mode #options-list ListItem { border: round #d0d7de; }
    Screen.light-mode ListView#options-list ListItem.active-opt { border: round #0969da; }
    Screen.light-mode #q-list { border-top: solid #d0d7de; }
    Screen.light-mode #q-list ListItem.active-q { background: #ddf4ff; border-left: thick #0969da; }
    Screen.light-mode .answered-item .q-label { color: #afb8c1; text-style: strike; }
    Screen.light-mode #modal-container, Screen.light-mode #scenario-modal-container { background: #ffffff; border: round #d0d7de; }
    Screen.light-mode #timer-label, Screen.light-mode #btn-next, Screen.light-mode #btn-answer, Screen.light-mode #btn-modal-back, Screen.light-mode #btn-modal-next { color: #24292f; border: round #d0d7de; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "toggle_scenario", "Toggle Scenario"),
        Binding("t", "configure_timer", "Set Timer"),
        Binding("tab", "switch_focus", "Switch Panel Focus"),
        Binding("p", "toggle_pause", "Pause Timer"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.exam_data, self.current_idx, self.score, self.scenario_text = [], 0, 0, ""
        self.user_answers, self.drafted, self.answered, self.bookmarks = {}, set(), set(), set()
        self.time_left, self.timer_paused = 190 * 60, True

    def on_mount(self):
        exams = list(Path("exams").glob("*.json"))
        if Path("exam_data.json").exists(): exams.append(Path("exam_data.json"))
        if len(exams) > 1:
            modal = ExamSelector()
            if self.screen.has_class("light-mode"): modal.add_class("light-mode")
            self.push_screen(modal, self.load_selected_exam)
        elif len(exams) == 1: self.load_selected_exam(str(exams[0]))

    def load_selected_exam(self, file_path):
        if not file_path: return
        try:
            with open(file_path, "r", encoding="utf-8") as f: self.exam_data = json.load(f)[:70]
            sp = Path("data/target_scenario/active_scenario.md")
            self.scenario_text = sp.read_text(encoding="utf-8").strip() if sp.exists() else "No scenario found."
            if self.exam_data: self.populate_sidebar(); self.update_question()
            self.timer_interval = self.set_interval(1, self.tick_timer)
            self.update_timer_display()
        except Exception as e: self.notify(f"Error: {e}", severity="error")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            with Vertical(id="sidebar"):
                yield Label("PRINCE Practitioner mock exam", id="title")
                with Horizontal(id="timer-bar"):
                    yield Label("Time: 190:00", id="timer-label")
                    yield Label("▶", id="pause-btn"); yield Label("◑", id="theme-btn")
                yield Label("Progress: 0/70", id="progress"); yield Label("Score: 0/70", id="score-label")
                yield Label("Tab: Focus | p: Pause", id="tab-hint"); yield ListView(id="q-list")
            with Vertical(id="content-area"):
                with ScrollableContainer(id="question-scroll"):
                    yield Markdown("Loading...", id="question-display"); yield ListView(id="options-list")
                    with Horizontal(id="action-buttons"):
                        yield Button("Next", id="btn-next"); yield Button("Answer", id="btn-answer")
        yield Footer()

    def tick_timer(self):
        if not self.timer_paused and self.time_left > 0: self.time_left -= 1; self.update_timer_display()

    def update_timer_display(self):
        mins, secs = divmod(self.time_left, 60)
        try: self.query_one("#timer-label").update(f"Time: {mins:02d}:{secs:02d}")
        except: pass
            
    def update_progress_display(self):
        td = len(self.drafted.union(self.answered))
        try: self.query_one("#progress").update(f"Progress: {td}/{len(self.exam_data)}")
        except: pass
            
    def mark_current_as_done(self):
        try:
            ti = self.query_one("#q-list").children[self.current_idx]
            ti.query_one(".q-label", Label).update(f"Question {self.current_idx + 1} [✓]"); ti.add_class("answered-item")
        except: pass

    def action_toggle_pause(self):
        self.timer_paused = not self.timer_paused
        try:
            pb = self.query_one("#pause-btn")
            pb.update("▶" if self.timer_paused else "⏸"); pb.set_class(self.timer_paused, "paused")
        except: pass

    def action_configure_timer(self) -> None:
        modal = TimerModal()
        if self.screen.has_class("light-mode"): modal.add_class("light-mode")
        def st(m):
            if m is not None: self.time_left = m * 60; self.update_timer_display()
        self.push_screen(modal, st)

    def on_click(self, event: Click) -> None:
        if event.control and event.control.id == "pause-btn": self.action_toggle_pause(); event.stop()
        elif event.control and event.control.id == "theme-btn": self.screen.toggle_class("light-mode"); event.stop()
        elif event.control and event.control.has_class("bookmark-icon"):
            qi = int(event.control.id.split("-")[1])
            if qi in self.bookmarks: self.bookmarks.remove(qi); event.control.update("○"); event.control.remove_class("bookmarked")
            else: self.bookmarks.add(qi); event.control.update("●"); event.control.add_class("bookmarked")
            event.stop()

    def populate_sidebar(self):
        ql = self.query_one("#q-list"); ql.clear()
        for i in range(len(self.exam_data)):
            done = i in self.answered or i in self.drafted
            bm = Label("●" if i in self.bookmarks else "○", id=f"bm-{i}", classes="bookmark-icon")
            if i in self.bookmarks: bm.add_class("bookmarked")
            item = ListItem(Horizontal(bm, Label(f"Question {i+1}{' [✓]' if done else ''}", classes="q-label")), name=str(i))
            if i == self.current_idx: item.add_class("active-q")
            if done: item.add_class("answered-item")
            ql.append(item)

    def format_question_text(self, t: str) -> str:
        t = t.replace("**", "")
        t = re.sub(r"(Statement|Item|Action) \d+:\s*[._\-\s]+(?=\n|$)", "", t)
        return re.sub(r"(?<!^)\s*((Statement|Item|Action) \d+:)", r"\n\n\1", t).strip()

    def update_question(self):
        if not self.exam_data: return
        if self.current_idx >= len(self.exam_data):
            self.query_one("#question-display").update(f"COMPLETE\nScore: {self.score}/{len(self.exam_data)}")
            self.query_one("#options-list").clear(); self.query_one("#action-buttons").display = False
            if not self.timer_paused: self.action_toggle_pause()
            return
        self.query_one("#action-buttons").display = True
        q = self.exam_data[self.current_idx]
        self.query_one("#question-display").update(f"**Q{self.current_idx + 1}:** {self.format_question_text(q['question'])}")
        lv, opts = self.query_one("#options-list"), q.get('options', {})
        lv.clear(); sc = self.user_answers.get(self.current_idx); si = None
        for i, k in enumerate(sorted(opts.keys())):
            item = ListItem(Label(f"{k}) {opts[k]}"), name=k)
            if k == sc: item.add_class("active-opt"); si = i
            lv.append(item)
        if si is not None: lv.index = si
        self.update_progress_display(); ql = self.query_one("#q-list"); ql.index = self.current_idx
        for i, item in enumerate(ql.children): item.set_class(i == self.current_idx, "active-q")

    def on_list_view_selected(self, event: ListView.Selected):
        if event.list_view.id == "q-list":
            if self.user_answers.get(self.current_idx) and self.current_idx not in self.answered:
                self.drafted.add(self.current_idx); self.mark_current_as_done(); self.update_progress_display()
            self.current_idx = int(event.item.name); self.update_question(); self.query_one("#options-list").focus()
        elif event.list_view.id == "options-list":
            if self.current_idx in self.answered:
                for item in event.list_view.children:
                    item.set_class(item.name == self.user_answers.get(self.current_idx), "active-opt")
                return
            for item in event.list_view.children: item.remove_class("active-opt")
            if event.item: event.item.add_class("active-opt"); self.user_answers[self.current_idx] = event.item.name

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-next":
            if self.user_answers.get(self.current_idx) and self.current_idx not in self.answered:
                self.drafted.add(self.current_idx); self.mark_current_as_done(); self.update_progress_display()
            self.current_idx += 1; self.update_question(); self.query_one("#options-list").focus()
        elif event.button.id == "btn-answer": self.submit_answer()

    def submit_answer(self):
        choice = self.user_answers.get(self.current_idx)
        if not choice: self.notify("Select answer.", severity="warning"); return
        q = self.exam_data[self.current_idx]; ca = q.get('answer', ''); ic = choice == ca
        if self.current_idx not in self.answered:
            if ic: self.score += 1
            self.answered.add(self.current_idx); self.query_one("#score-label").update(f"Score: {self.score}/{len(self.exam_data)}")
            self.mark_current_as_done(); self.update_progress_display()
        tr = not self.timer_paused
        if tr: self.action_toggle_pause()
        def am(res):
            if tr: self.action_toggle_pause()
            if res == "btn-modal-next": self.current_idx += 1
            self.update_question(); self.query_one("#options-list").focus()
        rr = q.get('rationale', '')
        if isinstance(rr, dict):
            fr = f"**Option {ca} is correct:**\n{rr.get('correct','')}\n\n**Others:**\n"
            wd = rr.get('wrong',{})
            for k in sorted(wd.keys()):
                if k != ca and wd[k].strip(): fr += f"- **{k}:** {wd[k]}\n"
            fr += f"\n**Manual:** {rr.get('manual_reference','')}"
        else: fr = str(rr)
        modal = RationaleModal(fr, ic, ca)
        if self.screen.has_class("light-mode"): modal.add_class("light-mode")
        self.push_screen(modal, am)

    def action_switch_focus(self):
        q, o = self.query_one("#q-list"), self.query_one("#options-list")
        if q.has_focus: o.focus()
        else: q.focus()

    def action_cursor_down(self):
        for w in ["#options-list", "#q-list"]:
            if self.query_one(w).has_focus: self.query_one(w).action_cursor_down()

    def action_cursor_up(self):
        for w in ["#options-list", "#q-list"]:
            if self.query_one(w).has_focus: self.query_one(w).action_cursor_up()

    def action_toggle_scenario(self):
        if self.scenario_text:
            modal = ScenarioModal(self.scenario_text)
            if self.screen.has_class("light-mode"): modal.add_class("light-mode")
            self.push_screen(modal)

if __name__ == "__main__": ExamApp().run()
