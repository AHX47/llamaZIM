
# 🚀 Llama-ZIM Integrated System (Low-Hardware Edition)

<div align="center">
  <a href="#english">English</a> | <a href="#arabic">العربية</a>
</div>

---

<a name="english"></a>
## 📖 English Version

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![CPU Only](https://img.shields.io/badge/hardware-CPU%20only-green.svg)]()
[![RAM 2-8GB](https://img.shields.io/badge/RAM-2GB--8GB-orange.svg)]()

> **Fully offline Arabic AI assistant** with RAG (Retrieval-Augmented Generation) on ZIM archives. Optimized for low-resource devices (2–8GB RAM, CPU only). Comes with **25+ built‑in skills** (PDF, DOCX, XLSX, PPTX, web art, coding, design, etc.).



### ✨ Key Features
- **llama.cpp engine** – Runs on CPU, no GPU required.
- **Arabic RAG system** – Search Wikipedia / dictionaries from ZIM files (e.g., `wiktionary_ar_mini.zim`).
- **Vector database** – Uses Chroma DB for fast similarity search.
- **25+ skills** – Ready‑to‑use: PDF, DOCX, XLSX, PPTX, canvas design, algorithmic art, web testing, MCP builder, Slack GIF creator, theme factory, and more (see `skills/` folder).
- **Smart memory** – Maintains conversation context.
- **Offline-first** – Complete privacy, no internet needed.





### 📋 Requirements
- **OS:** Linux, Windows, macOS
- **RAM:** 2GB (small models) – 8GB (larger models)
- **CPU:** Any modern processor (AVX2 recommended)
- **Storage:** ~5GB for models + ZIM file size
- **Software:** Python 3.8+, pip, git

### 🛠️ Installation & Usage

#### 1. Clone the repository
```bash
git clone https://github.com/AHX47/llamaZIM.git
cd LlamaZIM
```

#### 2. Install dependencies
```bash
pip install -r requirements.txt
```

#### 3. Place a GGUF model
Download a GGUF model (e.g., `SmolLM2-135M-Q4_K_M.gguf`) and put it inside:
```bash
models/SmolLM2-135M-Instruct-GGUF/
```
Your current structure already contains that folder – ensure the `.gguf` file is directly inside it.

#### 4. Place ZIM archives
Put your ZIM files (e.g., `wiktionary_ar_mini.zim`) inside:
```bash
zim_archives/
```

#### 5. Index the ZIM files (first time only)
```bash
python3 main.py --index
```
This will create/update the vector database inside `vector_db/` (Chroma).

#### 6. Run the system
```bash
python3 main.py
```

You can also test individual components with:
```bash
python3 test_system.py
```

### 🧠 Recommended Models (GGUF format)
| Model | Size | RAM | Use case |
|-------|------|-----|-----------|
| **SmolLM2-135M** | 135M | 2GB | Very weak devices, fast |
| **Gemma-3-270M** | 270M | 3–4GB | Balanced |
| **DeepSeek-Coder-1.3B** | 1.3B | 6–8GB | Programming & logic |

### 📁 Project Structure (as on your disk)
```
llamaZIM/
├── config/
│   └── config.yaml
├── models/
│   └── SmolLM2-135M-Instruct-GGUF/   # put .gguf here
├── zim_archives/
│   └── wiktionary_ar_mini.zim
├── vector_db/
│   └── chroma.sqlite3                # created after --index
├── skills/                           # 25+ ready-to-use skills
│   ├── pdf/
│   ├── docx/
│   ├── xlsx/
│   ├── pptx/
│   ├── canvas-design/
│   ├── algorithmic-art/
│   ├── webapp-testing/
│   ├── mcp-builder/
│   ├── slack-gif-creator/
│   ├── theme-factory/
│   └── ... (more)
├── src/
│   ├── core/          # model_manager.py, skill_manager.py
│   ├── rag/           # zim_manager.py (handles ZIM + Chroma)
│   ├── agents/        # agent_manager.py
│   └── cli/           # (future CLI interface)
├── main.py
├── test_system.py
├── requirements.txt
└── README.md
```

### 🔍 How RAG works with ZIM
- The system reads ZIM files (e.g., Arabic Wiktionary) and indexes them into ChromaDB (`vector_db/`).
- When you ask a question, it retrieves relevant passages from the ZIM archive and feeds them to the LLM as context.
- This enables **offline, private** question‑answering over Arabic Wikipedia / dictionaries.

### 🧩 Skill Management
All skills are located in the `skills/` folder. The system automatically discovers them. You can enable/disable skills via `config/config.yaml` or through the skill manager.

Example `config.yaml` (partial):
```yaml
model:
  path: "models/SmolLM2-135M-Instruct-GGUF/smollm2-135m-q4_k_m.gguf"
  context_size: 2048
skills:
  enabled:
    - pdf
    - docx
    - xlsx
    - canvas-design
  disabled:
    - webapp-testing   # requires optional dependencies
rag:
  
# RAG Settings
embedding_model_name: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" # A good multilingual model
vector_db_path: "/home/ubuntu/llama_zim_system/vector_db"
chunk_size: 512
chunk_overlap: 50

# Agent Settings
agent_framework: "LangGraph" # Options: CrewAI, LangGraph, Smolagents

# Skills Settings
enabled_skills:
  - "pdf-reading"
  - "docx"
  - "pptx"
  - "xlsx"
  # Add custom ZIM skills here later
                                         
  zim_path: "zim_archives/"
  vector_db_path: "vector_db/"
```

### 🔧 Troubleshooting
| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| No results from RAG | Run `python3 main.py --index` to build vector DB |
| Model not found | Check the path in `config.yaml` – point to the actual `.gguf` file |
| High RAM usage | Use a smaller model or reduce `context_size` in config |

### 🛠️ Development
- To add a new skill: create a folder under `skills/` with a `SKILL.md` description and any Python scripts. The skill manager will pick it up.
- To modify RAG: edit `src/rag/zim_manager.py`.

### 📄 License
MIT – free to use, modify, and distribute.

### 🙏 Acknowledgements
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Chroma DB](https://www.trychroma.com/)
- [KiwiX ZIM archives](https://www.kiwix.org/)
- Anthropic’s skills library (many skills under `skills/` are adapted from there)

---

<a name="arabic"></a>
## 📖 النسخة العربية

# نظام Llama-ZIM المتكامل (للأجهزة الضعيفة) 🚀

> مساعد ذكاء اصطناعي عربي يعمل دون اتصال، مع نظام RAG على أرشيفات ZIM. يعمل على المعالج فقط (2-8 جيجابايت رام). يتضمن أكثر من 25 مهارة مدمجة (PDF, DOCX, XLSX, PPTX, تصميم، برمجة، وغيرها).

### ✨ المميزات
- **محرك llama.cpp** – يعمل على المعالج فقط.
- **RAG عربي** – استعلام أرشيفات ZIM (مثل ويكيبيديا، القواميس).
- **قاعدة بيانات متجهات Chroma** – بحث سريع.
- **25+ مهارة** – جاهزة للاستخدام (انظر مجلد `skills/`).
- **ذاكرة المحادثة** – سياق ذكي.
- **بدون إنترنت** – خصوصية تامة.

### 📋 المتطلبات
- نظام تشغيل: Linux, Windows, macOS
- رام: 2-8 جيجابايت
- مساحة: 5 جيجابايت + حجم ملفات ZIM
- Python 3.8+، pip، git

### 🛠️ التشغيل
```bash
git clone https://github.com/AHX47/llamaZIM.git
cd LlamaZIM
pip install -r requirements.txt
# ضع نموذج GGUF في مجلد models/ وملف ZIM في zim_archives/
python3 main.py --index   # مرة واحدة للفهرسة
python3 main.py
```

### 📁 هيكل المشروع (كما هو على جهازك)
- `models/` – نماذج GGUF
- `zim_archives/` – ملفات ZIM (مثل wiktionary_ar_mini.zim)
- `vector_db/` – فهرس Chroma (ينشأ تلقائياً)
- `skills/` – المهارات (PDF، DOCX، إلخ)
- `src/` – الكود المصدري (core, rag, agents)
- `main.py` – نقطة الدخول

### 🧩 إدارة المهارات
المهارات موجودة في مجلد `skills/`. يمكنك تفعيلها أو تعطيلها من `config/config.yaml`.

### 🔧 حل المشكلات
- **RAG لا يعمل** → شغل `python3 main.py --index` مرة أخرى.
- **النموذج غير موجود** → تأكد من المسار في `config.yaml`.
- **استهلاك رام عالي** → استخدم نموذجاً أصغر.

### 📄 الرخصة
MIT – حرية الاستخدام والتعديل.

---
✨ **تم تطوير هذا النظام ليكون مصنع معرفة شخصي يعمل دون اتصال على أي جهاز.** ✨
```

---

