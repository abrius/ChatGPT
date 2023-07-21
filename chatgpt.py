import gi
import time
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk

import openai

openai.api_key = "your_api_key"


class ChatWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="ChatGPT")
        self.set_default_size(300, 600)  # Set the default size of the window
        self.set_icon_from_file("gpt.png")
        self.set_border_width(10)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        grid_engine_model = Gtk.Grid()
        vbox.pack_start(grid_engine_model, False, True, 0)



        label_model = Gtk.Label.new("Model: ")
        grid_engine_model.attach(label_model, 0, 0, 1, 1)

        self.combo_model = Gtk.ComboBoxText.new()
        self.combo_model.append_text("gpt-3.5-turbo-16k")
        self.combo_model.append_text("gpt-3.5-turbo")
        self.combo_model.append_text("gpt-3.5-turbo-0613")
        self.combo_model.append_text("gpt-3.5-turbo-0301")
        self.combo_model.set_active(0)
        grid_engine_model.attach(self.combo_model, 3, 0, 1, 1)

        label_temperature = Gtk.Label.new(" Temperature: ")
        grid_engine_model.attach(label_temperature, 4, 0, 1, 1)

        self.combo_temperature = Gtk.ComboBoxText.new()
        #for value in [str(i / 10) for i in range(0, 11)]:
        self.combo_temperature.append_text("0")
        self.combo_temperature.append_text("0.1")
        self.combo_temperature.append_text("0.2")
        self.combo_temperature.append_text("0.3")
        self.combo_temperature.append_text("0.4")
        self.combo_temperature.append_text("0.5")
        self.combo_temperature.append_text("0.6")
        self.combo_temperature.append_text("0.7")
        self.combo_temperature.append_text("0.8")
        self.combo_temperature.append_text("0.9")
        self.combo_temperature.append_text("1")
        self.combo_temperature.set_active(0)  # Default selection: 0
        grid_engine_model.attach(self.combo_temperature, 5, 0, 1, 1)

        label_max_tokens = Gtk.Label.new(" Max Tokens: ")
        grid_engine_model.attach(label_max_tokens, 6, 0, 1, 1)

        self.entry_max_tokens = Gtk.Entry.new()
        self.entry_max_tokens.set_width_chars(6)  # Set the width of the entry widget
        self.entry_max_tokens.set_text("16000")  # Default value: 1000
        grid_engine_model.attach(self.entry_max_tokens, 7, 0, 1, 1)

        hbox_buttons = Gtk.Box(spacing=5)
        vbox.pack_end(hbox_buttons, False, True, 0)

        self.clear_button = Gtk.Button.new_with_label("Clear")
        hbox_buttons.pack_start(self.clear_button, False, False, 0)
        self.clear_button.connect("clicked", self.clear_conversation)

        self.send_button = Gtk.Button.new_with_label("Send")
        hbox_buttons.pack_start(self.send_button, False, False, 0)
        self.send_button.connect("clicked", self.send_message)

        self.resend_button = Gtk.Button.new_with_label("Resend")
        hbox_buttons.pack_start(self.resend_button, False, False, 0)
        self.resend_button.connect("clicked", self.resend_message)

        self.token_label = Gtk.Label.new("Total Tokens: 0 | Used Tokens: 0")
        hbox_buttons.pack_start(self.token_label, False, False, 0)

        self.save_log_switch = Gtk.Switch.new()
        self.save_log_switch.set_active(False)
        self.save_log_switch.set_valign(Gtk.Align.CENTER)  # Set vertical alignment to center
        hbox_buttons.pack_end(self.save_log_switch, False, False, 0)
        
        # Set the height of the save_log_switch widget
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"* { min-height: 5px; }")  # Adjust the height as needed
        context = self.save_log_switch.get_style_context()
        context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        save_log_label = Gtk.Label.new("  Log")
        hbox_buttons.pack_end(save_log_label, False, False, 0)

        scrolled_window = Gtk.ScrolledWindow.new()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        vbox.pack_start(scrolled_window, True, True, 0)

        self.textview = Gtk.TextView.new()
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textbuffer = self.textview.get_buffer()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        scrolled_window.add(self.textview)

        self.entry = Gtk.TextView.new()
        self.entry.set_wrap_mode(Gtk.WrapMode.WORD)
        self.entry.set_size_request(-1, 90)  # Set the width and height of the textview widget
        vbox.pack_start(self.entry, False, False, 0)

        self.entry.connect("key-press-event", self.on_key_press_event)

        self.show_all()

        self.load_conversation()  # Load conversation from log file

    def add_message(self, role, content):
        end_iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end_iter, "{}: {}\n\n".format(role, content))
        mark = self.textbuffer.create_mark(None, end_iter, True)
        self.textview.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

    def clear_conversation(self, button):
        self.textbuffer.set_text("")
        self.delete_log_file()

    def delete_log_file(self):
        log_file_path = "logs/gpt.log"
        if os.path.exists(log_file_path):
            os.remove(log_file_path)

    def send_message(self, button=None):
        api_key = openai.api_key
        max_tokens = self.entry_max_tokens.get_text().strip()
        model = self.combo_model.get_active_text()
        temperature = float(self.combo_temperature.get_active_text())

        if api_key and max_tokens and model:
            openai.api_key = api_key

            user_message = self.entry.get_buffer().get_text(
                self.entry.get_buffer().get_start_iter(),
                self.entry.get_buffer().get_end_iter(),
                True
            ).strip()

            self.add_message("User", user_message)
            self.entry.get_buffer().set_text("")

            # Delay for a few seconds before sending the request to ChatGPT
            GLib.timeout_add_seconds(1, self.retrieve_response, model, user_message, int(max_tokens), temperature)

    def retrieve_response(self, model, user_message, max_tokens, temperature):
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": user_message}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            n=1,
            stop=None,
        )
        message = response.choices[0]['message']
        self.add_message(message['role'].replace('assistant', 'ChatGPT'), message['content'])
        self.update_token_counts(response['usage']['total_tokens'], response['usage']['prompt_tokens'])

        adj = self.textview.get_buffer().get_end_iter()
        self.textview.scroll_to_iter(adj, 0.0, True, 0.0, 1.0)

        # Save conversation to log file
        if self.save_log_switch.get_active():
            self.save_conversation()

        return False

    def resend_message(self, button):
        text = self.textbuffer.get_text(
            self.textbuffer.get_start_iter(),
            self.textbuffer.get_end_iter(),
            True
        ).strip()

        # Split the conversation by newlines
        conversation = text.split('\n')

        # Find the last user message in the conversation
        last_user_message = None
        for line in reversed(conversation):
            if line.startswith("User:"):
                last_user_message = line.replace("User:", "").strip()
                break

        if last_user_message:
            self.entry.get_buffer().set_text(last_user_message)  # Set the text entry widget with the last user message

    def toggle_save_log(self, switch, state):
        if state:
            self.save_conversation()
        else:
            self.delete_log_file()

    def on_key_press_event(self, widget, event):
        keyval = event.keyval
        state = event.state

        if keyval == Gdk.KEY_Return and not state & Gdk.ModifierType.SHIFT_MASK:
            self.send_message()
            return True
        return False

    def update_token_counts(self, total_tokens, prompt_tokens):
        self.token_label.set_text(f"Total Tokens: {total_tokens} | Used Tokens: {prompt_tokens}")

    def save_conversation(self):
        conversation = self.textbuffer.get_text(
            self.textbuffer.get_start_iter(),
            self.textbuffer.get_end_iter(),
            True
        )

        with open("logs/gpt.log", "w") as file:
            file.write(conversation)

    def load_conversation(self):
        try:
            with open("logs/gpt.log", "r") as file:
                conversation = file.read()
                self.textbuffer.set_text(conversation)
                mark = self.textbuffer.create_mark("end", self.textbuffer.get_end_iter(), False)
                self.textview.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
        except FileNotFoundError:
            pass


win = ChatWindow()
win.connect("destroy", Gtk.main_quit)
Gtk.main()
