def __init__(self, root):
    self.root = root
    self.root.title("Llama-ZIM Assistant")
    self.root.geometry("1280x800")
    self.root.minsize(900, 600)
    self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # RTL mode flag
    self.rtl_mode = tk.BooleanVar(value=True)

    # Configuration path
    script_dir = Path(__file__).parent.absolute()
    self.config_path = script_dir / "config" / "config.yaml"
    if not self.config_path.exists():
        self.config_path = script_dir / "config.yaml"

    # Load config (calls the method)
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
