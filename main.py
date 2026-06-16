import os
import yaml
import argparse
from src.core.model_manager import ModelManager
from src.rag.zim_manager import ZimManager
from src.core.skill_manager import SkillManager
from src.agents.agent_manager import SimpleAgent

def main():
    parser = argparse.ArgumentParser(description="Llama-ZIM Integrated System")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")
    parser.add_argument("--index", action="store_true", help="Index ZIM files before starting")
    args = parser.parse_args()

    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize managers
    model_mgr = ModelManager(args.config)
    zim_mgr = ZimManager(config)
    skill_mgr = SkillManager(config)

    # Discover and install skills from claudeskills (if available)
    claudeskills_path = "/home/ubuntu/claudeskills"
    if os.path.exists(claudeskills_path):
        skill_mgr.discover_skills(claudeskills_path)
        for skill in config.get('enabled_skills', []):
            skill_mgr.install_skill(skill)

    # Index ZIM if requested
    if args.index:
        for zim_file in os.listdir(config['zim_archives_dir']):
            if zim_file.endswith(".zim"):
                zim_mgr.index_zim_file(zim_file)

    # Load model (ensure model exists first)
    model_name = config['llm_model_name']
    model_path = os.path.join(config['models_dir'], model_name)
    if os.path.exists(model_path):
        model_mgr.load_model(model_name)
    else:
        print(f"Warning: Model {model_name} not found at {model_path}. Please download it first.")

    # Start Agent
    agent = SimpleAgent(model_mgr, zim_mgr, skill_mgr)

    print("\n" + "="*50)
    print("نظام Llama-ZIM المتكامل جاهز للعمل!")
    print("اكتب 'خروج' للإنهاء.")
    print("="*50 + "\n")

    while True:
        user_input = input("أنت: ")
        if user_input.lower() in ['خروج', 'exit', 'quit']:
            break
        
        if not model_mgr.llm:
            print("خطأ: لم يتم تحميل أي نموذج. يرجى التأكد من وجود ملف النموذج.")
            continue

        agent.process_query(user_input)

if __name__ == "__main__":
    main()
