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
        
        # Find all JSON files in the exams directory
        exams = list(Path("exams").glob("*.json"))
        # Also include the root work-in-progress file if it exists
        if Path("exam_data.json").exists():
            exams.append(Path("exam_data.json"))
            
        if not exams:
            exam_list.append(ListItem(Label("No exams found. Please run generator.py"), name=""))
            return
            
        # Sort so newest exams are at the top
        for path in sorted(exams, reverse=True):
            exam_list.append(ListItem(Label(f"📄 {path.name}"), name=str(path)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.name:
            self.dismiss(event.item.name)

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
        if event.button.id == "btn-set":
            self.submit()
        else:
            self.dismiss()

    def on_input_submitted(self) -> None:
        self.submit()

    def submit(self) -> None:
        value = self.query_one("#timer-input").value
        if value.isdigit():
            self.dismiss(int(value))
        else:
            self.dismiss()


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

    def action_dismiss(self) -> None:
        self.dismiss()
        
    def action_scroll_down(self) -> None:
        self.query_one("#scenario-scroll").scroll_relative(y=3, animate=False)

    def action_scroll_up(self) -> None:
        self.query_one("#scenario-scroll").scroll_relative(y=-3, animate=False)


class RationaleModal(ModalScreen):
    """Zero-border rationale feedback."""
    
    BINDINGS = [
        Binding("enter", "dismiss", "Continue"),
        Binding("escape", "dismiss", "Continue"),
        Binding("space", "dismiss", "Continue"),
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
        if self.is_correct:
            header_text = "[#3fb950]CORRECT[/#3fb950]"
        else:
            header_text = f"[#f85149]INCORRECT[/#f85149] - The correct answer is {self.correct_ans}"
        
        # Keep this for backward compatibility with V0.1 flat strings
        cleaned_rationale = self.rationale.replace("**Why this is correct:**", f"**Why Option {self.correct_ans} is correct:**")
        cleaned_rationale = cleaned_rationale.replace("Why this is correct:", f"**Why Option {self.correct_ans} is correct:**")

        yield Vertical(
            Label(header_text, id="status-label"),
            ScrollableContainer(
                Markdown(cleaned_rationale, id="rationale-text"),
                id="rationale-scroll"
            ),
            Button("OK", id="btn-ok"),
            id="modal-container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ok":
            event.stop() 
            self.dismiss()

    def action_dismiss(self) -> None:
        self.dismiss()

    def action_scroll_down(self) -> None:
        self.query_one("#rationale-scroll").scroll_relative(y=3, animate=False)

    def action_scroll_up(self) -> None:
        self.query_one("#rationale-scroll").scroll_relative(y=-3, animate=False)


class ExamApp(App):
    theme = "textual-dark"
    
    CSS = """
    /* --- DARK THEME (DEFAULT) --- */
    Screen {
        background: #0d1117; 
        scrollbar-color: #30363d;
        scrollbar-background: transparent;
    }
    ScenarioModal, RationaleModal, TimerModal, ExamSelector {
        align: center middle;
    }
    #main-layout {
        height: 100%;
    }
    #sidebar {
        width: 35;
        background: #0d1117;
        border-right: solid #30363d;
        padding: 1;
        height: 100%;
        overflow: hidden;
    }
    #content-area {
        padding: 2;
        height: 100%;
    }
    #question-scroll {
        height: 1fr;
        padding-right: 1;
        scrollbar-color: #30363d;
        scrollbar-background: transparent;
    }
    #question-display {
        margin-bottom: 1; 
        color: #c9d1d9;
    }
    ListView {
        background: transparent;
        border: none;
    }
    
    /* OPTIONS LIST */
    #options-list {
        height: auto;
        margin-top: 1;
        margin-bottom: 1;
    }
    #options-list ListItem {
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
        background: transparent;
        border: round #30363d;
    }
    #options-list Label {
        height: auto;
        width: 100%;
        color: #c9d1d9;
    }
    #options-list ListItem:hover {
        background: #161b22;
    }
    
    ListView#options-list ListItem.active-opt,
    ListView#options-list ListItem.--highlight {
        background: transparent;
        border: round #58a6ff;
    }
    
    ListView#options-list ListItem.active-opt Label,
    ListView#options-list ListItem.--highlight Label {
        color: #58a6ff !important;
        text-style: bold;
    }
    
    /* SIDEBAR LIST */
    #q-list {
        margin-top: 1;
        height: 1fr;
        border-top: solid #30363d;
        padding-top: 1;
        overflow-x: hidden;
    }
    #q-list ListItem {
        padding: 1;
        background: transparent;
        height: auto;
        width: 100%;
        overflow: hidden;
    }
    #q-list Horizontal {
        height: 1;
        width: 100%;
        overflow: hidden;
    }
    #q-list ListItem:hover {
        background: #161b22;
    }
    #q-list ListItem.active-q {
        background: #21262d;
        border-left: thick #58a6ff;
    }
    #q-list ListItem.active-q .q-label {
        color: #c9d1d9;
        text-style: bold;
    }
    
    .bookmark-icon {
        width: 3;
        color: #8b949e;
        text-style: bold;
        text-align: center;
        height: 1;
    }
    .q-label {
        width: 1fr;
        height: 1;
        color: #8b949e;
        overflow: hidden;
    }
    
    /* Answered and Bookmark overrides */
    .answered-item .q-label, .answered-item .bookmark-icon {
        color: #484f58;
    }
    .bookmark-icon.bookmarked {
        color: #f85149 !important;
    }
    
    /* MODALS */
    #modal-container {
        width: 70%;
        height: auto;
        background: #161b22;
        border: round #30363d;
        padding: 2;
    }
    #timer-modal-container, #selector-container {
        width: 70%;
        height: auto;
        background: #161b22;
        border: round #30363d;
        padding: 2;
        align-horizontal: center;
    }
    #selector-container {
        width: 50%;
        max-height: 80%;
    }
    #rationale-scroll {
        max-height: 50vh;
        margin-bottom: 1;
        scrollbar-color: #30363d;
        scrollbar-background: transparent;
    }
    #scenario-modal-container {
        width: 80%;
        height: 80%;
        background: #161b22;
        border: round #30363d;
        padding: 2;
    }
    #scenario-scroll {
        height: 1fr;
        scrollbar-color: #30363d;
        scrollbar-background: transparent;
    }
    #scenario-title, #timer-modal-title, #selector-title {
        text-align: center;
        width: 100%;
        text-style: bold;
        margin-bottom: 1;
        color: #c9d1d9;
    }
    
    /* EXAM SELECTOR LIST */
    #exam-choice-list {
        height: 1fr;
        margin-bottom: 1;
        scrollbar-color: #30363d;
        scrollbar-background: transparent;
    }
    #exam-choice-list ListItem {
        padding: 1;
        background: transparent;
        border: round #30363d;
        margin-bottom: 1;
    }
    #exam-choice-list ListItem:hover {
        background: #21262d;
    }
    
    /* TIMER & BUTTON BAR */
    #timer-bar {
        height: auto;
        align-horizontal: left;
        margin-top: 1;
    }
    #timer-label {
        text-align: center;
        text-style: bold;
        background: transparent;
        color: #c9d1d9;
        padding: 0 1;
        border: round #30363d;
    }
    #timer-label:hover {
        background: #161b22;
    }
    #pause-btn, #theme-btn {
        width: 5;
        content-align: center middle;
        text-align: center;
        background: transparent;
        color: #8b949e; 
        padding: 0 1;
        margin-left: 1;
        border: round #30363d;
    }
    #pause-btn:hover, #theme-btn:hover {
        background: #161b22;
    }
    #pause-btn.paused {
        color: #c9d1d9; 
        background: transparent;
    }

    #score-label {
        margin-bottom: 1;
    }

    #timer-input {
        margin: 1 0;
        border: round #30363d;
    }
    
    /* BUTTONS */
    #submit-btn, #btn-ok, #btn-set, #btn-cancel {
        width: 30;
        height: 3;
        margin: 0 0; 
        content-align: center middle;
        background: transparent; 
        color: #c9d1d9;
        border: round #30363d;
        text-style: bold;
    }
    #submit-btn:hover, #btn-ok:hover, #btn-set:hover, #btn-cancel:hover {
        background: #161b22;
    }
    #timer-modal-buttons {
        height: auto;
        align-horizontal: center;
    }
    #btn-set { margin-right: 1; }

    /* --- LIGHT THEME OVERRIDES --- */
    Screen.light-mode { 
        background: #ffffff; 
        scrollbar-color: #24292f;      
        scrollbar-background: #eaeef2; 
    }
    Screen.light-mode #sidebar { background: #f6f8fa; border-right: solid #d0d7de; }
    
    Screen.light-mode #title,
    Screen.light-mode #progress,
    Screen.light-mode #score-label,
    Screen.light-mode #tab-hint {
        color: #24292f;
    }
    
    Screen.light-mode Markdown, 
    Screen.light-mode Label,
    Screen.light-mode #question-display { 
        color: #24292f; 
    }
    
    Screen.light-mode #options-list ListItem { border: round #d0d7de; }
    Screen.light-mode #options-list Label { color: #24292f; }
    Screen.light-mode #options-list ListItem:hover { background: #eaeef2; }
    
    Screen.light-mode ListView#options-list ListItem.--highlight { border: round #0969da; }
    Screen.light-mode ListView#options-list ListItem.active-opt { border: round #0969da; }
    Screen.light-mode ListView#options-list ListItem.active-opt Label,
    Screen.light-mode ListView#options-list ListItem.--highlight Label { color: #0969da !important; }
    
    Screen.light-mode #q-list, Screen.light-mode #question-scroll, 
    Screen.light-mode #rationale-scroll, Screen.light-mode #scenario-scroll { 
        border-top: solid #d0d7de; 
        scrollbar-color: #24292f; 
        scrollbar-background: #eaeef2;
    }
    Screen.light-mode #q-list ListItem:hover { background: #eaeef2; }
    Screen.light-mode #q-list ListItem.active-q { background: #ddf4ff; border-left: thick #0969da; }
    Screen.light-mode #q-list ListItem.active-q .q-label { color: #24292f; }
    
    Screen.light-mode .bookmark-icon { color: #57606a; }
    Screen.light-mode .q-label { color: #57606a; }
    Screen.light-mode .answered-item .q-label, Screen.light-mode .answered-item .bookmark-icon { color: #afb8c1; }
    Screen.light-mode .bookmark-icon.bookmarked { color: #cf222e !important; }
    
    Screen.light-mode #modal-container, 
    Screen.light-mode #scenario-modal-container,
    Screen.light-mode #timer-modal-container,
    Screen.light-mode #selector-container { 
        background: #ffffff; 
        border: round #d0d7de; 
    }
    Screen.light-mode #scenario-title, Screen.light-mode #timer-modal-title, Screen.light-mode #selector-title { color: #24292f; }
    
    Screen.light-mode #exam-choice-list ListItem { border: round #d0d7de; }
    Screen.light-mode #exam-choice-list ListItem:hover { background: #eaeef2; }
    
    Screen.light-mode #timer-label { color: #24292f; border: round #d0d7de; }
    Screen.light-mode #timer-label:hover { background: #eaeef2; }
    
    Screen.light-mode #timer-input { 
        background: #ffffff; 
        color: #24292f; 
        border: round #d0d7de; 
    }
    Screen.light-mode #timer-input:focus { border: round #0969da; }
    
    Screen.light-mode #pause-btn, Screen.light-mode #theme-btn { color: #57606a; border: round #d0d7de; }
    Screen.light-mode #pause-btn:hover, Screen.light-mode #theme-btn:hover { background: #eaeef2; }
    Screen.light-mode #pause-btn.paused { color: #24292f; background: transparent; }
    
    Screen.light-mode #submit-btn, Screen.light-mode #btn-ok, Screen.light-mode #btn-set, Screen.light-mode #btn-cancel { 
        background: transparent; 
        color: #24292f; 
        border: round #d0d7de;
    }
    Screen.light-mode #submit-btn:hover, Screen.light-mode #btn-ok:hover, 
    Screen.light-mode #btn-set:hover, Screen.light-mode #btn-cancel:hover { 
        background: #eaeef2; 
    }
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
        self.exam_data = []
        self.current_idx = 0
        self.score = 0
        self.scenario_text = ""
        self.answered = set()
        self.bookmarks = set()
        self.time_left = 190 * 60
        self.timer_paused = True # Start paused

    def on_mount(self):
        # Scan for existing exams
        exams = list(Path("exams").glob("*.json"))
        if Path("exam_data.json").exists(): 
            exams.append(Path("exam_data.json"))

        # Decide whether to show selector or load directly
        if len(exams) > 1:
            modal = ExamSelector()
            if self.screen.has_class("light-mode"):
                modal.add_class("light-mode")
            self.push_screen(modal, self.load_selected_exam)
        elif len(exams) == 1:
            self.load_selected_exam(str(exams[0]))
        else:
            self.notify("No exams found. Please run generator.py first.", severity="error")

    def load_selected_exam(self, file_path):
        if not file_path:
            # User canceled selection, or no file passed
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.exam_data = json.load(f)[:70]
            
            scenario_path = Path("data/target_scenario/Louistown_scenario.md")
            if scenario_path.exists():
                self.scenario_text = scenario_path.read_text(encoding="utf-8").strip()
            
            if self.exam_data:
                self.populate_sidebar()
                self.update_question()
                self.query_one("#options-list").focus() 
                self.notify(f"Loaded: {Path(file_path).name}")
            else:
                self.notify("Error: Selected exam file is empty.", severity="error")
                
            self.timer_interval = self.set_interval(1, self.tick_timer)
            self.update_timer_display()
            
        except Exception as e:
            self.notify(f"Error loading exam: {e}", severity="error")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            with Vertical(id="sidebar"):
                yield Label("PRINCE Practitioner mock exam", id="title")
                with Horizontal(id="timer-bar"):
                    yield Label("Time: 190:00", id="timer-label")
                    yield Label("▶", id="pause-btn") 
                    yield Label("◑", id="theme-btn")
                yield Label("Progress: 0/70", id="progress")
                yield Label("Score: 0/70", id="score-label")
                yield Label("Tab: Switch Panel\np: Pause Timer", id="tab-hint")
                yield ListView(id="q-list")
            with Vertical(id="content-area"):
                with ScrollableContainer(id="question-scroll"):
                    yield Markdown("Loading...", id="question-display")
                    yield ListView(id="options-list")
                    yield Button("Next", id="submit-btn")
        yield Footer()

    def tick_timer(self):
        if not self.timer_paused and self.time_left > 0:
            self.time_left -= 1
            self.update_timer_display()

    def update_timer_display(self):
        mins, secs = divmod(self.time_left, 60)
        try:
            self.query_one("#timer-label").update(f"Time: {mins:02d}:{secs:02d}")
        except:
            pass

    def action_toggle_pause(self):
        self.timer_paused = not self.timer_paused
        try:
            pause_btn = self.query_one("#pause-btn")
            if self.timer_paused:
                pause_btn.update("▶")
                pause_btn.add_class("paused")
            else:
                pause_btn.update("⏸")
                pause_btn.remove_class("paused")
        except Exception:
            pass
        self.update_timer_display()

    def action_configure_timer(self) -> None:
        modal = TimerModal()
        if self.screen.has_class("light-mode"):
            modal.add_class("light-mode")
        
        def set_time(minutes):
            if minutes is not None:
                self.time_left = minutes * 60
                self.update_timer_display()
        
        self.push_screen(modal, set_time)

    def on_click(self, event: Click) -> None:
        if event.control and event.control.id == "pause-btn":
            self.action_toggle_pause()
            event.stop()
        elif event.control and event.control.id == "timer-label":
            self.action_configure_timer()
            event.stop()
        elif event.control and event.control.id == "theme-btn":
            self.screen.toggle_class("light-mode")
            event.stop()
        elif event.control and event.control.has_class("bookmark-icon"):
            try:
                q_idx = int(event.control.id.split("-")[1])
                if q_idx in self.bookmarks:
                    self.bookmarks.remove(q_idx)
                    event.control.update("○")
                    event.control.remove_class("bookmarked")
                else:
                    self.bookmarks.add(q_idx)
                    event.control.update("●")
                    event.control.add_class("bookmarked")
                event.stop()
            except Exception:
                pass

    def populate_sidebar(self):
        q_list = self.query_one("#q-list")
        q_list.clear()
        for i in range(len(self.exam_data)):
            mark = " [✓]" if i in self.answered else ""
            b_icon = "●" if i in self.bookmarks else "○"
            
            bm_label = Label(b_icon, id=f"bm-{i}", classes="bookmark-icon")
            if i in self.bookmarks:
                bm_label.add_class("bookmarked")
                
            q_label = Label(f"Question {i+1}{mark}", classes="q-label")
            layout = Horizontal(bm_label, q_label)
            
            item = ListItem(layout, name=str(i))
            if i == self.current_idx:
                item.add_class("active-q")
            if i in self.answered:
                item.add_class("answered-item")
            q_list.append(item)

    def format_question_text(self, text: str) -> str:
        """Systematically cleans visual noise, removes orphan markers, and fixes paragraph spacing."""
        # 1. Remove markdown bold markers (**)
        text = text.replace("**", "")
        # 2. Remove orphan placeholders
        text = re.sub(r"(Statement|Item|Action) \d+:\s*[._\-\s]+(?=\n|$)", "", text)
        # 3. Fix paragraph spacing for actual content
        text = re.sub(r"(?<!^)\s*((Statement|Item|Action) \d+:)", r"\n\n\1", text)
        # 4. Clean up whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def update_question(self):
        if not self.exam_data: return
        
        if self.current_idx >= len(self.exam_data):
            self.query_one("#question-display").update(f"EXAM COMPLETE\nFinal Score: {self.score}/{len(self.exam_data)}")
            self.query_one("#options-list").clear()
            self.query_one("#submit-btn").display = False
            self.timer_paused = True
            return

        self.query_one("#submit-btn").display = True
        q = self.exam_data[self.current_idx]
        formatted_q = self.format_question_text(q['question'])
        self.query_one("#question-display").update(f"**Q{self.current_idx + 1}:** {formatted_q}")
        
        list_view = self.query_one("#options-list")
        list_view.clear()
        options = q.get('options', {})
        for key in sorted(options.keys()):
            list_view.append(ListItem(Label(f"{key}) {options[key]}"), name=key))
        
        self.query_one("#progress").update(f"Progress: {len(self.answered)}/{len(self.exam_data)}")
        
        q_list = self.query_one("#q-list")
        q_list.index = self.current_idx
        for i, item in enumerate(q_list.children):
            if i == self.current_idx:
                item.add_class("active-q")
            else:
                item.remove_class("active-q")

    def on_list_view_selected(self, event: ListView.Selected):
        if event.list_view.id == "q-list":
            self.current_idx = int(event.item.name)
            self.update_question()
            self.query_one("#options-list").focus()
        elif event.list_view.id == "options-list":
            for item in event.list_view.children:
                item.remove_class("active-opt")
            if event.item:
                event.item.add_class("active-opt")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit-btn":
            self.submit_answer()
        elif event.button.id == "btn-ok":
            self.dismiss()

    def submit_answer(self):
        if self.current_idx in self.answered:
            self.current_idx += 1
            self.update_question()
            return
            
        opt_list = self.query_one("#options-list")
        choice = None
        for item in opt_list.children:
            if item.has_class("active-opt"):
                choice = item.name
                break
                
        if not choice and opt_list.highlighted_child is not None:
            choice = opt_list.highlighted_child.name
            
        if not choice: 
            self.notify("Please select an answer first.", severity="warning")
            return
            
        q = self.exam_data[self.current_idx]
        correct_ans = q.get('answer', '')
        is_correct = choice == correct_ans
        
        if is_correct: self.score += 1
        
        self.answered.add(self.current_idx)
        self.query_one("#score-label").update(f"Score: {self.score}/{len(self.exam_data)}")
        self.query_one("#progress").update(f"Progress: {len(self.answered)}/{len(self.exam_data)}")
        
        try:
            target_item = self.query_one("#q-list").children[self.current_idx]
            target_item.query_one(".q-label", Label).update(f"Question {self.current_idx + 1} [✓]")
            target_item.add_class("answered-item")
        except: pass

        def after_modal(_=None):
            self.current_idx += 1
            self.update_question()
            self.query_one("#options-list").focus()

        # V0.2: Dynamically parse the nested rationale schema
        raw_rationale = q.get('rationale', '')
        if isinstance(raw_rationale, dict):
            correct_text = raw_rationale.get('correct', '')
            wrong_dict = raw_rationale.get('wrong', {})
            manual_ref = raw_rationale.get('manual_reference', '')
            
            formatted_rationale = f"**Why Option {correct_ans} is correct:**\n{correct_text}\n\n**Why the other options are wrong:**\n"
            for opt_key in sorted(wrong_dict.keys()):
                if opt_key != correct_ans and wrong_dict.get(opt_key, '').strip():
                    formatted_rationale += f"- **Option {opt_key}:** {wrong_dict[opt_key]}\n"
            
            if manual_ref:
                formatted_rationale += f"\n**Manual reference:** {manual_ref}"
        else:
            # Fallback for V0.1 flat strings
            formatted_rationale = str(raw_rationale)

        modal = RationaleModal(formatted_rationale, is_correct, correct_ans)
        if self.screen.has_class("light-mode"):
            modal.add_class("light-mode")
            
        self.push_screen(modal, callback=after_modal)

    def action_switch_focus(self):
        q = self.query_one("#q-list")
        o = self.query_one("#options-list")
        if q.has_focus: o.focus()
        else: q.focus()

    def action_cursor_down(self):
        if self.query_one("#options-list").has_focus: self.query_one("#options-list").action_cursor_down()
        elif self.query_one("#q-list").has_focus: self.query_one("#q-list").action_cursor_down()

    def action_cursor_up(self):
        if self.query_one("#options-list").has_focus: self.query_one("#options-list").action_cursor_up()
        elif self.query_one("#q-list").has_focus: self.query_one("#q-list").action_cursor_up()

    def action_toggle_scenario(self):
        if self.scenario_text:
            modal = ScenarioModal(self.scenario_text)
            if self.screen.has_class("light-mode"):
                modal.add_class("light-mode")
            self.push_screen(modal)

if __name__ == "__main__":
    ExamApp().run()
