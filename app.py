import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Label, ListItem, ListView, Markdown, Button
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.events import Click

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
        # Dynamic Header
        header_text = "CORRECT" if self.is_correct else f"INCORRECT - The correct answer is {self.correct_ans}"
        
        # Dynamic String Replacement to fix cognitive dissonance
        cleaned_rationale = self.rationale.replace("**Why this is correct:**", f"**Why Option {self.correct_ans} is correct:**")
        cleaned_rationale = cleaned_rationale.replace("Why this is correct:", f"**Why Option {self.correct_ans} is correct:**")

        yield Vertical(
            Label(header_text, id="status-label", classes="correct" if self.is_correct else "incorrect"),
            ScrollableContainer(Markdown(cleaned_rationale, id="rationale-text"), id="rationale-scroll"),
            Button("OK", id="btn-ok", variant="success"),
            id="modal-container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ok":
            self.dismiss()

    def action_dismiss(self) -> None:
        self.dismiss()

    def action_scroll_down(self) -> None:
        self.query_one("#rationale-scroll").scroll_relative(y=3, animate=False)

    def action_scroll_up(self) -> None:
        self.query_one("#rationale-scroll").scroll_relative(y=-3, animate=False)

class ExamApp(App):
    theme = "textual-light"  # Natively enforces white background, black letters
    
    CSS = """
    ScenarioModal, RationaleModal {
        align: center middle;
    }
    #main-layout {
        height: 100%;
    }
    #sidebar {
        width: 30;
        background: #f4f4f4;
        border-right: solid #cccccc;
        padding: 1;
        height: 100%;
    }
    #content-area {
        padding: 2;
        height: 100%;
    }
    #question-display {
        margin-bottom: 2;
        color: #000000;
    }
    ListView {
        background: transparent;
        border: none;
    }
    ListView:focus {
        border: none;
    }
    #options-list {
        height: auto;
        margin-top: 1;
        margin-bottom: 1;
    }
    #q-list {
        margin-top: 1;
        height: 1fr;
        border-top: solid #cccccc;
        padding-top: 1;
    }
    ListItem {
        padding: 1;
        background: #ffffff;
        color: #000000;
    }
    ListItem:hover {
        background: #e0e0e0;
    }
    ListItem:focus {
        background: #d0d0d0;
    }
    ListItem.--highlight {
        background: #cccccc;
        color: #000000;
        text-style: bold;
    }
    .answered-item Label {
        color: #888888;
    }
    #modal-container {
        width: 70%;
        height: auto;
        background: #ffffff;
        border: solid #000000;
        padding: 2;
        color: #000000;
    }
    #rationale-scroll {
        max-height: 50vh;
        scrollbar-background: #eeeeee;
        scrollbar-color: #aaaaaa;
        margin-bottom: 1;
    }
    #scenario-modal-container {
        width: 80%;
        height: 80%;
        background: #ffffff;
        border: solid #000000;
        padding: 2;
        color: #000000;
    }
    #scenario-scroll {
        height: 1fr;
        scrollbar-background: #eeeeee;
        scrollbar-color: #aaaaaa;
    }
    #scenario-title {
        text-align: center;
        width: 100%;
        text-style: bold;
        color: #000000;
        margin-bottom: 1;
    }
    #scenario-close-hint {
        color: #666666;
        text-align: center;
        margin-top: 1;
    }
    #status-label {
        text-align: center;
        width: 100%;
        text-style: bold;
        margin-bottom: 1;
    }
    .correct { color: #008800; }
    .incorrect { color: #dd0000; }
    #close-hint {
        display: none; /* Replaced by OK button */
    }
    #tab-hint {
        color: #666666;
        margin-top: 1;
    }
    #timer-label {
        text-align: center;
        text-style: bold;
        background: #e0e0e0;
        color: #000000;
        padding: 1;
        margin-top: 1;
        border: solid #cccccc;
    }
    #timer-label:hover {
        background: #cccccc;
    }
    #submit-btn {
        width: 100%;
        margin-top: 1;
    }
    #btn-ok {
        width: 100%;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "toggle_scenario", "Toggle Scenario"),
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
        self.time_left = 190 * 60
        self.timer_paused = False

    def on_mount(self):
        try:
            data_file = Path("exam_data.json")
            if data_file.exists():
                with open(data_file, "r", encoding="utf-8") as f:
                    self.exam_data = json.load(f)[:70]
            
            # Simplified for Unified Narrative Grounding
            scenario_path = Path("data/target_scenario/Louistown_scenario.md")
            if scenario_path.exists():
                self.scenario_text = scenario_path.read_text(encoding="utf-8").strip()
            
            if self.exam_data:
                self.populate_sidebar()
                self.update_question()
                self.query_one("#options-list").focus() 
            else:
                self.notify("Error: exam_data.json is empty.", severity="error")
                
            self.timer_interval = self.set_interval(1, self.tick_timer)
            self.update_timer_display()
            
        except Exception as e:
            self.notify(f"Error loading exam: {e}", severity="error")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            with Vertical(id="sidebar"):
                yield Label("PRINCE2 PROCTOR", id="title")
                yield Label("Time: 190:00", id="timer-label")
                yield Label("Progress: 0/70", id="progress")
                yield Label("Score: 0", id="score-label")
                yield Label("Tab: Switch Panel\np: Pause Timer", id="tab-hint")
                yield ListView(id="q-list")
            with Vertical(id="content-area"):
                yield Markdown("Loading...", id="question-display")
                yield ListView(id="options-list")
                yield Button("Next", id="submit-btn", variant="primary")
        yield Footer()

    def tick_timer(self):
        if not self.timer_paused and self.time_left > 0:
            self.time_left -= 1
            self.update_timer_display()
            if self.time_left == 0:
                self.timer_paused = True
                self.notify("Time is up!", severity="warning")

    def update_timer_display(self):
        mins, secs = divmod(self.time_left, 60)
        status = " (PAUSED)" if self.timer_paused else ""
        try:
            self.query_one("#timer-label").update(f"Time: {mins:02d}:{secs:02d}{status}")
        except:
            pass

    def action_toggle_pause(self):
        self.timer_paused = not self.timer_paused
        self.update_timer_display()

    def on_click(self, event: Click) -> None:
        if event.control and event.control.id == "timer-label":
            self.action_toggle_pause()

    def populate_sidebar(self):
        q_list = self.query_one("#q-list")
        q_list.clear()
        for i in range(len(self.exam_data)):
            mark = " [✓]" if i in self.answered else ""
            item = ListItem(Label(f"Question {i+1}{mark}"), name=str(i))
            if i in self.answered:
                item.add_class("answered-item")
            q_list.append(item)

    def update_question(self):
        if not self.exam_data:
            return
            
        if self.current_idx >= len(self.exam_data):
            self.query_one("#question-display").update(f"EXAM COMPLETE\nFinal Score: {self.score}/{len(self.exam_data)}")
            self.query_one("#options-list").clear()
            self.query_one("#submit-btn").display = False
            self.timer_paused = True
            self.update_timer_display()
            return

        self.query_one("#submit-btn").display = True
        q = self.exam_data[self.current_idx]
        self.query_one("#question-display").update(f"**Q{self.current_idx + 1}:** {q['question']}")
        
        list_view = self.query_one("#options-list")
        list_view.clear()
        
        options = q.get('options', {})
        for key in sorted(options.keys()):
            val = options[key]
            list_view.append(ListItem(Label(f"{key}) {val}"), name=key))
        
        self.query_one("#progress").update(f"Progress: {self.current_idx + 1}/{len(self.exam_data)}")
        
        q_list = self.query_one("#q-list")
        q_list.index = self.current_idx

    def on_list_view_selected(self, event: ListView.Selected):
        list_id = event.list_view.id
        
        if list_id == "q-list":
            self.current_idx = int(event.item.name)
            self.update_question()
            self.query_one("#options-list").focus()
            
        elif list_id == "options-list":
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit-btn":
            self.submit_answer()

    def submit_answer(self):
        if self.current_idx in self.answered:
            self.notify("Already answered. Skipping...", severity="warning")
            self.current_idx += 1
            self.update_question()
            return

        opt_list = self.query_one("#options-list")
        if opt_list.index is None:
            self.notify("Please select an answer first.", severity="warning")
            return

        selected_item = opt_list.highlighted_child
        if not selected_item: return
        choice = selected_item.name
        
        q = self.exam_data[self.current_idx]
        correct_ans = q.get('answer', '')
        is_correct = choice == correct_ans
        
        if is_correct:
            self.score += 1
            self.query_one("#score-label").update(f"Score: {self.score}")

        self.answered.add(self.current_idx)
        
        try:
            q_list = self.query_one("#q-list")
            target_item = q_list.children[self.current_idx]
            target_item.query_one(Label).update(f"Question {self.current_idx + 1} [✓]")
            target_item.add_class("answered-item")
        except Exception:
            pass

        def after_modal(_=None):
            self.current_idx += 1
            self.update_question()
            self.query_one("#options-list").focus()

        self.push_screen(RationaleModal(q.get('rationale', 'No rationale provided.'), is_correct, correct_ans), callback=after_modal)

    def action_switch_focus(self):
        q_list = self.query_one("#q-list")
        opt_list = self.query_one("#options-list")
        if q_list.has_focus:
            opt_list.focus()
        else:
            q_list.focus()

    def action_cursor_down(self):
        if self.query_one("#options-list").has_focus:
            self.query_one("#options-list").action_cursor_down()
        elif self.query_one("#q-list").has_focus:
            self.query_one("#q-list").action_cursor_down()

    def action_cursor_up(self):
        if self.query_one("#options-list").has_focus:
            self.query_one("#options-list").action_cursor_up()
        elif self.query_one("#q-list").has_focus:
            self.query_one("#q-list").action_cursor_up()

    def action_toggle_scenario(self):
        if self.scenario_text:
            self.push_screen(ScenarioModal(self.scenario_text))
        else:
            self.notify("Scenario text not loaded.", severity="warning")

if __name__ == "__main__":
    ExamApp().run()
