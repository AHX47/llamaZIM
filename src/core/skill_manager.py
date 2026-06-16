import os
import shutil

class SkillManager:
    def __init__(self, config):
        self.config = config
        self.skills_dir = config['skills_dir']
        self.enabled_skills = config.get('enabled_skills', [])
        self.available_skills = {}

    def discover_skills(self, source_dir):
        """Discover skills from a source directory (like the extracted Claudeskills)"""
        if not os.path.exists(source_dir):
            return
        
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.skill') or file == 'SKILL.md':
                    skill_name = os.path.basename(root)
                    if skill_name not in self.available_skills:
                        self.available_skills[skill_name] = root

    def install_skill(self, skill_name):
        if skill_name in self.available_skills:
            dest_path = os.path.join(self.skills_dir, skill_name)
            if not os.path.exists(dest_path):
                shutil.copytree(self.available_skills[skill_name], dest_path)
                print(f"Skill '{skill_name}' installed.")
            else:
                print(f"Skill '{skill_name}' already installed.")
        else:
            print(f"Skill '{skill_name}' not found in available skills.")

    def get_skill_content(self, skill_name):
        skill_path = os.path.join(self.skills_dir, skill_name, "SKILL.md")
        if os.path.exists(skill_path):
            with open(skill_path, 'r') as f:
                return f.read()
        return None

    def list_enabled_skills(self):
        return self.enabled_skills
