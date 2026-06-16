import os
import yaml
from src.core.model_manager import ModelManager
from src.rag.zim_manager import ZimManager
from src.core.skill_manager import SkillManager
from src.agents.agent_manager import SimpleAgent

def test_system():
    config_path = "config/config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    print("--- Testing System Initialization ---")
    model_mgr = ModelManager(config_path)
    zim_mgr = ZimManager(config)
    skill_mgr = SkillManager(config)

    # 1. Index a small part of ZIM
    print("\n--- Testing ZIM Indexing ---")
    zim_mgr.index_zim_file("wiktionary_ar_mini.zim")

    # 2. Load Model
    print("\n--- Testing Model Loading ---")
    model_mgr.load_model(config['llm_model_name'])

    # 3. Test Agent
    print("\n--- Testing Agent Response ---")
    agent = SimpleAgent(model_mgr, zim_mgr, skill_mgr)
    query = "ما هو معنى كلمة 'كتاب'؟"
    print(f"User: {query}")
    agent.process_query(query)

if __name__ == "__main__":
    test_system()
