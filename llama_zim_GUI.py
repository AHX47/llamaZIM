#!/usr/bin/env python3
# gui.py - Llama-ZIM Assistant with Arabic RTL Support (compatible with older Tk)

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog
import yaml
from pathlib import Path
import re

# Import your existing modules
from src.core.model_manager import ModelManager
from src.rag.zim_manager import ZimManager
from src.core.skill_manager import SkillManager
from src.agents.agent_manager import SimpleAgent

class LlamaZIMGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Llama-ZIM Assistant")
        self.root.geometry("1280x800")
        self.root.minsize(900, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # RTL mode flag (right‑alignment only, no direction tag)
        self.rtl_mode = tk.BooleanVar(value=True)

        # Configuration file path
        script_dir = Path(__file__).parent.absolute()
        self.config_path = script_dir / "config" / "config.yaml"
        if not self.config_path.exists():
            self.config_path = script_dir / "config.yaml"

        self.load_config()

        # Managers
        self.model_manager = None
        self.zim_manager = None
        self.skill_manager = None
        self.agent = None

        # UI state
        self.current_thinking_widget = None
        self.current_response_widget = None
        self.current_bubble_frame = None
        self.thinking_visible = True

        # Build UI
        self.create_menu()
        self.create_main_layout()
        self.status("Ready. Load a model to start.")
        self.refresh_model_list()
        self.refresh_zim_list()
        self.refresh_skills_list()

    # ---------- Configuration ----------
    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            script_dir = Path(__file__).parent.absolute()
            for key in ['models_dir', 'zim_archives_dir', 'skills_dir', 'vector_db_path']:
                if key in self.config:
                    p = Path(self.config[key])
                    if not p.is_absolute():
                        self.config[key] = str(script_dir / p)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")
            self.root.quit()

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self.config, f)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    # ---------- RTL Helpers (safe for older Tk) ----------
    def is_arabic(self, text):
        arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
        return bool(arabic_pattern.search(text))

    def apply_rtl_to_widget(self, widget, text=""):
        """Apply right alignment if Arabic or RTL mode is on."""
        if self.rtl_mode.get() or (text and self.is_arabic(text)):
            try:
                widget.configure(justify='right')
            except:
                pass
        else:
            try:
                widget.configure(justify='left')
            except:
                pass

    def set_input_direction(self, event=None):
        text = self.user_input.get("1.0", "end-1c")
        if self.rtl_mode.get() or self.is_arabic(text):
            self.user_input.configure(justify='right')
            self.user_input.mark_set("insert", "end")
        else:
            self.user_input.configure(justify='left')

    def toggle_rtl_mode(self):
        mode = "RTL" if self.rtl_mode.get() else "LTR"
        self.status(f"Switched to {mode} mode.")
        self.set_input_direction()

    # ---------- Menu ----------
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Model", command=self.load_model_dialog)
        file_menu.add_command(label="Index ZIM File", command=self.index_zim_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        skills_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Skills", menu=skills_menu)
        skills_menu.add_command(label="Manage Skills (Enable/Disable)", command=self.manage_skills_dialog)
        skills_menu.add_command(label="Create New Skill", command=self.create_skill_dialog)
        skills_menu.add_separator()
        skills_menu.add_command(label="Create Sample Skills", command=self.create_sample_skills)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="RTL Mode (Arabic)", variable=self.rtl_mode, command=self.toggle_rtl_mode)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    # ---------- Layout ----------
    def create_main_layout(self):
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=3)

        right_frame = ttk.Frame(main_pane, width=280)
        main_pane.add(right_frame, weight=1)

        # Chat area
        chat_container = ttk.Frame(left_frame)
        chat_container.pack(fill=tk.BOTH, expand=True)

        self.chat_canvas = tk.Canvas(chat_container, highlightthickness=0, bg="#f5f5f5")
        v_scrollbar = ttk.Scrollbar(chat_container, orient="vertical", command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=v_scrollbar.set)
        self.chat_canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")

        self.scrollable_frame = ttk.Frame(self.chat_canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=self.chat_canvas.winfo_width())

        def on_canvas_configure(event):
            self.chat_canvas.itemconfig(1, width=event.width)
        self.chat_canvas.bind("<Configure>", on_canvas_configure)

        # Input area
        input_frame = ttk.Frame(left_frame)
        input_frame.pack(fill=tk.X, pady=(8,0))

        self.user_input = tk.Text(input_frame, height=4, font=("Segoe UI", 11), wrap=tk.WORD, relief="flat", borderwidth=1)
        self.user_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,8))
        self.user_input.bind("<Return>", self.send_message_event)
        self.user_input.bind("<FocusIn>", self.set_input_direction)
        self.user_input.bind("<KeyRelease>", lambda e: self.set_input_direction())

        send_btn = ttk.Button(input_frame, text="Send", command=self.send_message, width=10)
        send_btn.pack(side=tk.RIGHT)

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Right panel: Model
        model_frame = ttk.LabelFrame(right_frame, text="Model", padding=5)
        model_frame.pack(fill=tk.X, pady=(0,8))

        self.model_listbox = tk.Listbox(model_frame, height=6, exportselection=False)
        self.model_listbox.pack(fill=tk.X, pady=2)
        ttk.Button(model_frame, text="Load Selected", command=self.load_selected_model).pack(pady=2)

        self.model_label = ttk.Label(model_frame, text="No model loaded", foreground="gray")
        self.model_label.pack(anchor=tk.W, pady=2)

        # Skills panel
        skills_frame = ttk.LabelFrame(right_frame, text="Skills", padding=5)
        skills_frame.pack(fill=tk.BOTH, expand=True, pady=(0,8))

        self.skills_listbox = tk.Listbox(skills_frame, selectmode=tk.MULTIPLE, height=8, exportselection=False)
        self.skills_listbox.pack(fill=tk.BOTH, expand=True, pady=2)

        btn_frame = ttk.Frame(skills_frame)
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Enable Selected", command=self.enable_selected_skills).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Disable Selected", command=self.disable_selected_skills).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="New Skill", command=self.create_skill_dialog).pack(side=tk.RIGHT, padx=2)

        # ZIM archives
        zim_frame = ttk.LabelFrame(right_frame, text="ZIM Archives", padding=5)
        zim_frame.pack(fill=tk.X)

        self.zim_listbox = tk.Listbox(zim_frame, height=4, exportselection=False)
        self.zim_listbox.pack(fill=tk.X, pady=2)
        ttk.Button(zim_frame, text="Refresh", command=self.refresh_zim_list).pack(pady=2)

    # ---------- Status ----------
    def status(self, msg):
        self.status_var.set(msg)
        self.root.update_idletasks()

    # ---------- Model Management ----------
    def refresh_model_list(self):
        models_dir = self.config.get('models_dir', './models')
        self.model_listbox.delete(0, tk.END)
        if not os.path.exists(models_dir):
            self.model_listbox.insert(tk.END, "Directory not found")
            return
        for f in os.listdir(models_dir):
            
                self.model_listbox.insert(tk.END, f)
        if self.model_listbox.size() == 0:
            self.model_listbox.insert(tk.END, "No .gguf models found")

    def load_selected_model(self):
        selection = self.model_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a model from the list")
            return
        model_name = self.model_listbox.get(selection[0])
        self.load_model(model_name)

    def load_model_dialog(self):
        self.refresh_model_list()
        messagebox.showinfo("Info", "Select a model from the right panel and click 'Load Selected'")

    def load_model(self, model_name):
        self.status(f"Loading model {model_name}...")
        try:
            # Ensure model path is absolute
            models_dir = self.config.get('models_dir', './models')
            model_path = os.path.join(models_dir, model_name)
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")

            self.config['llm_model_name'] = model_name
            self.model_manager = ModelManager(str(self.config_path))
            # Override the model name inside the manager
            self.model_manager.config['llm_model_name'] = model_name
            self.model_manager.load_model(model_name)

            self.zim_manager = ZimManager(self.config)
            self.skill_manager = SkillManager(self.config)

            claudeskills_path = "/home/ubuntu/claudeskills"
            if os.path.exists(claudeskills_path):
                self.skill_manager.discover_skills(claudeskills_path)

            self.agent = SimpleAgent(self.model_manager, self.zim_manager, self.skill_manager)

            self.model_label.config(text=f"Loaded: {model_name}", foreground="green")
            self.refresh_skills_list()
            self.status(f"Model '{model_name}' loaded successfully.")
            self.append_system_message(f"Model '{model_name}' loaded. You can now chat.")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))
            self.status("Failed to load model.")
            self.model_manager = None
            self.agent = None

    # ---------- Skills Management ----------
    def refresh_skills_list(self):
        self.skills_listbox.delete(0, tk.END)
        enabled = self.config.get('enabled_skills', [])
        skills_dir = self.config.get('skills_dir', './skills')
        available = []
        if os.path.exists(skills_dir):
            available = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]
        all_skills = set(available + enabled)
        self.skill_display_map = {}
        for skill in sorted(all_skills):
            if skill in enabled:
                self.skills_listbox.insert(tk.END, f"✓ {skill}")
                self.skill_display_map[f"✓ {skill}"] = skill
            else:
                self.skills_listbox.insert(tk.END, f"  {skill}")
                self.skill_display_map[f"  {skill}"] = skill

    def enable_selected_skills(self):
        selected = self.skills_listbox.curselection()
        enabled = self.config.get('enabled_skills', [])
        changed = False
        for idx in selected:
            display = self.skills_listbox.get(idx)
            skill_name = self.skill_display_map.get(display)
            if skill_name and skill_name not in enabled:
                enabled.append(skill_name)
                changed = True
        if changed:
            self.config['enabled_skills'] = enabled
            self.save_config()
            self.refresh_skills_list()
            self.status("Skills enabled.")
        else:
            self.status("No new skills enabled.")

    def disable_selected_skills(self):
        selected = self.skills_listbox.curselection()
        enabled = self.config.get('enabled_skills', [])
        changed = False
        for idx in selected:
            display = self.skills_listbox.get(idx)
            skill_name = self.skill_display_map.get(display)
            if skill_name and skill_name in enabled:
                enabled.remove(skill_name)
                changed = True
        if changed:
            self.config['enabled_skills'] = enabled
            self.save_config()
            self.refresh_skills_list()
            self.status("Skills disabled.")
        else:
            self.status("No skills disabled.")

    def create_skill_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Skill")
        dialog.geometry("600x550")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Skill Name (folder name):", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(dialog, text="Skill Description (will be written to SKILL.md):", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        desc_text = scrolledtext.ScrolledText(dialog, height=15, wrap=tk.WORD)
        desc_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        desc_text.bind("<KeyRelease>", lambda e: self.apply_rtl_to_widget(desc_text, desc_text.get("1.0", "end-1c")))

        example = """# مهارة: [اسم المهارة]

## الوصف
[شرح مبسط للمهارة]

## طريقة الاستخدام
- الخطوة 1
- الخطوة 2

## مثال
[مثال توضيحي]

## ملاحظات
[أي ملاحظات إضافية]
"""
        desc_text.insert(tk.END, example)
        self.apply_rtl_to_widget(desc_text, example)

        def save_skill():
            skill_name = name_entry.get().strip()
            if not skill_name:
                messagebox.showwarning("Warning", "Skill name is required")
                return
            content = desc_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Warning", "Skill description cannot be empty")
                return

            skills_dir = self.config.get('skills_dir', './skills')
            skill_path = Path(skills_dir) / skill_name
            try:
                skill_path.mkdir(parents=True, exist_ok=True)
                md_file = skill_path / "SKILL.md"
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Skill '{skill_name}' created at {md_file}")
                dialog.destroy()
                self.refresh_skills_list()
                enabled = self.config.get('enabled_skills', [])
                if skill_name not in enabled:
                    enabled.append(skill_name)
                    self.config['enabled_skills'] = enabled
                    self.save_config()
                    self.refresh_skills_list()
                    self.status(f"Skill '{skill_name}' created and enabled.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create skill: {e}")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Create Skill", command=save_skill).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def create_sample_skills(self):
        skills_dir = self.config.get('skills_dir', './skills')
        sample_skills = {
            "create_zim_archive": """# مهارة: إنشاء أرشيف ZIM جديد

## الوصف
هذه المهارة تسمح لك بإنشاء ملف ZIM جديد من مجموعة من النصوص أو المقالات.

## طريقة الاستخدام
1. اطلب من المساعد إنشاء أرشيف ZIM باسم محدد.
2. قدم قائمة بالمقالات (عنوان ومحتوى).
3. سيتم إنشاء الملف في مجلد zim_archives.

## مثال
"أنشئ أرشيف ZIM باسم `my_articles.zim` يحتوي على مقالتين: الأولى عن الذكاء الاصطناعي والثانية عن التعلم العميق"

## ملاحظات
يتطلب تثبيت مكتبة libzim.
""",
            "extract_pdf_text": """# مهارة: استخراج النص من PDF

## الوصف
استخراج النص من ملفات PDF وعرضه أو حفظه.

## طريقة الاستخدام
1. قدم مسار ملف PDF.
2. سيتم استخراج النص وإظهار معاينة.

## مثال
"استخرج النص من /home/user/document.pdf"

## المتطلبات
مكتبة pdfplumber أو PyPDF2.
""",
            "search_zim": """# مهارة: البحث في أرشيفات ZIM

## الوصف
البحث الدلالي داخل أرشيفات ZIM المفهرسة.

## طريقة الاستخدام
1. اكتب سؤالاً أو كلمة مفتاحية.
2. سيتم عرض النتائج من أرشيفات ZIM.

## مثال
"ابحث في ZIM عن تاريخ المغرب"

## ملاحظات
يجب أن تكون الأرشفة قد فهرست مسبقاً.
"""
        }
        created = []
        for skill_name, content in sample_skills.items():
            skill_path = Path(skills_dir) / skill_name
            if not skill_path.exists():
                skill_path.mkdir(parents=True, exist_ok=True)
                md_file = skill_path / "SKILL.md"
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                created.append(skill_name)
        if created:
            messagebox.showinfo("Sample Skills", f"Created skills:\n" + "\n".join(created))
            self.refresh_skills_list()
        else:
            messagebox.showinfo("Sample Skills", "Sample skills already exist.")

    def manage_skills_dialog(self):
        self.refresh_skills_list()
        messagebox.showinfo("Skills", "Use the Skills panel on the right to enable/disable.\nClick 'New Skill' to create a skill.")

    # ---------- ZIM Management ----------
    def refresh_zim_list(self):
        self.zim_listbox.delete(0, tk.END)
        zim_dir = self.config.get('zim_archives_dir', './zim_archives')
        if os.path.exists(zim_dir):
            for f in os.listdir(zim_dir):
                if f.endswith('.zim'):
                    self.zim_listbox.insert(tk.END, f)
        else:
            self.zim_listbox.insert(tk.END, "Directory not found")

    def index_zim_dialog(self):
        if not self.zim_manager:
            messagebox.showwarning("Warning", "ZimManager not initialized. Load a model first.")
            return
        zim_dir = self.config.get('zim_archives_dir', './zim_archives')
        if not os.path.exists(zim_dir):
            messagebox.showerror("Error", f"ZIM directory not found: {zim_dir}")
            return
        zim_files = [f for f in os.listdir(zim_dir) if f.endswith('.zim')]
        if not zim_files:
            messagebox.showwarning("Warning", "No ZIM files found.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Index ZIM File")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="Select ZIM file to index:").pack(pady=5)
        lb = tk.Listbox(dialog, height=10)
        lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        for zf in zim_files:
            lb.insert(tk.END, zf)
        def on_index():
            sel = lb.curselection()
            if sel:
                zim_file = lb.get(sel[0])
                dialog.destroy()
                threading.Thread(target=self.index_zim, args=(zim_file,), daemon=True).start()
        ttk.Button(dialog, text="Index", command=on_index).pack(pady=5)

    def index_zim(self, zim_filename):
        self.status(f"Indexing {zim_filename}...")
        try:
            self.zim_manager.index_zim_file(zim_filename)
            self.status(f"Indexing completed for {zim_filename}")
            self.append_system_message(f"ZIM file '{zim_filename}' indexed successfully.")
        except Exception as e:
            self.status(f"Indexing failed: {e}")
            messagebox.showerror("Index Error", str(e))

    # ---------- Chat ----------
    def send_message_event(self, event):
        if not event.state & 0x1:
            self.send_message()
            return "break"
        return None

    def send_message(self):
        if not self.agent:
            messagebox.showwarning("Warning", "No model loaded. Please load a model first.")
            return
        user_msg = self.user_input.get("1.0", tk.END).strip()
        if not user_msg:
            return
        self.user_input.delete("1.0", tk.END)
        self.append_user_message(user_msg)
        self.status("Generating...")
        thread = threading.Thread(target=self.generate_response, args=(user_msg,), daemon=True)
        thread.start()

    def generate_response(self, user_msg):
        try:
            context_docs = []
            if self.zim_manager:
                try:
                    context_docs = self.zim_manager.search(user_msg)
                except:
                    pass
            context_text = "\n".join(context_docs) if context_docs else "لا يوجد سياق متاح من الأرشيف."
            if len(context_text) > 1500:
                context_text = context_text[:1500] + "..."

            enabled_skills = self.skill_manager.list_enabled_skills() if self.skill_manager else []
            if enabled_skills:
                skills_info = "المهارات المتاحة: " + ", ".join(enabled_skills)
            else:
                skills_info = "لا توجد مهارات إضافية."

            system_prompt = f"""أنت مساعد ذكي يعمل محلياً. استخدم السياق التالي للإجابة على سؤال المستخدم.
السياق المستخرج من أرشيفات ZIM:
{context_text}

المهارات المتاحة لديك:
{skills_info}

أجب باللغة العربية بشكل مفصل ودقيق.
"""
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]

            self.root.after(0, self.create_assistant_bubble)

            response_gen = self.model_manager.chat_completion(messages, stream=True)

            thinking_buffer = ""
            response_buffer = ""
            in_think = False

            for chunk in response_gen:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        content = delta['content']
                        while content:
                            if not in_think and "<think>" in content:
                                parts = content.split("<think>", 1)
                                if parts[0]:
                                    response_buffer += parts[0]
                                    self.root.after(0, self.update_response, response_buffer)
                                content = parts[1]
                                in_think = True
                            elif in_think and "</think>" in content:
                                parts = content.split("</think>", 1)
                                if parts[0]:
                                    thinking_buffer += parts[0]
                                    self.root.after(0, self.update_thinking, thinking_buffer)
                                content = parts[1]
                                in_think = False
                            else:
                                if in_think:
                                    thinking_buffer += content
                                    self.root.after(0, self.update_thinking, thinking_buffer)
                                else:
                                    response_buffer += content
                                    self.root.after(0, self.update_response, response_buffer)
                                break

            self.root.after(0, self.finish_response)
            self.status("Ready")
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Generation Error", str(e)))
            self.status(f"Error: {e}")

    def create_assistant_bubble(self):
        frame = ttk.Frame(self.scrollable_frame, relief="flat")
        frame.pack(fill=tk.X, pady=6, padx=8)
        self.current_bubble_frame = frame

        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X)
        self.think_toggle_btn = ttk.Button(header_frame, text="▼ Thinking", width=12,
                                           command=self.toggle_thinking)
        self.think_toggle_btn.pack(side=tk.LEFT, padx=5, pady=2)

        self.thinking_text = scrolledtext.ScrolledText(frame, height=5, wrap=tk.WORD,
                                                       font=("Segoe UI", 9), bg="#f0f0f0")
        self.thinking_text.pack(fill=tk.X, padx=5, pady=2)
        self.thinking_text.config(state=tk.DISABLED)

        self.response_text = scrolledtext.ScrolledText(frame, height=8, wrap=tk.WORD,
                                                       font=("Segoe UI", 11), bg="#ffffff")
        self.response_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        self.response_text.config(state=tk.DISABLED)

        self.current_thinking_widget = self.thinking_text
        self.current_response_widget = self.response_text
        self.thinking_visible = True
        self.chat_canvas.yview_moveto(1)

    def toggle_thinking(self):
        if self.thinking_visible:
            self.thinking_text.pack_forget()
            self.thinking_visible = False
            self.think_toggle_btn.config(text="▶ Thinking")
        else:
            self.thinking_text.pack(fill=tk.X, padx=5, pady=2)
            self.thinking_visible = True
            self.think_toggle_btn.config(text="▼ Thinking")

    def update_thinking(self, text):
        if self.current_thinking_widget:
            self.current_thinking_widget.config(state=tk.NORMAL)
            self.current_thinking_widget.delete(1.0, tk.END)
            self.current_thinking_widget.insert(tk.END, text)
            self.apply_rtl_to_widget(self.current_thinking_widget, text)
            self.current_thinking_widget.config(state=tk.DISABLED)

    def update_response(self, text):
        if self.current_response_widget:
            self.current_response_widget.config(state=tk.NORMAL)
            self.current_response_widget.delete(1.0, tk.END)
            self.current_response_widget.insert(tk.END, text)
            self.apply_rtl_to_widget(self.current_response_widget, text)
            self.current_response_widget.config(state=tk.DISABLED)

    def finish_response(self):
        self.current_thinking_widget = None
        self.current_response_widget = None
        self.current_bubble_frame = None

    def append_user_message(self, msg):
        frame = ttk.Frame(self.scrollable_frame, relief="flat")
        frame.pack(fill=tk.X, pady=6, padx=8)
        user_label = ttk.Label(frame, text="You:", font=("Segoe UI", 10, "bold"), foreground="#1565C0")
        user_label.pack(anchor=tk.W, padx=5, pady=2)
        msg_text = tk.Text(frame, height=3, wrap=tk.WORD, font=("Segoe UI", 10), bg="#E3F2FD", relief="flat")
        msg_text.insert(tk.END, msg)
        msg_text.config(state=tk.DISABLED)
        msg_text.pack(fill=tk.X, padx=5, pady=2)
        self.apply_rtl_to_widget(msg_text, msg)
        self.chat_canvas.yview_moveto(1)

    def append_system_message(self, msg):
        frame = ttk.Frame(self.scrollable_frame, relief="flat")
        frame.pack(fill=tk.X, pady=6, padx=8)
        sys_label = ttk.Label(frame, text="System:", font=("Segoe UI", 10, "bold"), foreground="#616161")
        sys_label.pack(anchor=tk.W, padx=5, pady=2)
        msg_text = tk.Text(frame, height=2, wrap=tk.WORD, font=("Segoe UI", 9), bg="#EEEEEE", relief="flat")
        msg_text.insert(tk.END, msg)
        msg_text.config(state=tk.DISABLED)
        msg_text.pack(fill=tk.X, padx=5, pady=2)
        self.apply_rtl_to_widget(msg_text, msg)
        self.chat_canvas.yview_moveto(1)

    def show_about(self):
        messagebox.showinfo("About", "Llama-ZIM Assistant v2.1\n\n"
                                     "Features:\n"
                                     "- Split thinking/response display\n"
                                     "- Full Arabic RTL support\n"
                                     "- Skill creation (SKILL.md editor)\n"
                                     "- Enable/disable skills\n"
                                     "- ZIM indexing and search\n"
                                     "- Streaming responses\n\n"
                                     "Built with tkinter, llama-cpp-python, chromadb")

    def on_closing(self):
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = LlamaZIMGUI(root)
    root.mainloop()
