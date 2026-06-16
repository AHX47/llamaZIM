class SimpleAgent:
    def __init__(self, model_manager, zim_manager, skill_manager):
        self.model_manager = model_manager
        self.zim_manager = zim_manager
        self.skill_manager = skill_manager
        self.memory = []

    def process_query(self, query):
        # 1. Search ZIM for context
        context_docs = self.zim_manager.search(query)
        context_text = "\n".join(context_docs) if context_docs else "لا يوجد سياق متاح من الأرشيف."

        # 2. Prepare system prompt with context and enabled skills
        skills_info = ""
        for skill in self.skill_manager.list_enabled_skills():
            content = self.skill_manager.get_skill_content(skill)
            if content:
                skills_info += f"\n--- مهارة: {skill} ---\n{content}\n"

        system_prompt = f"""أنت مساعد ذكي يعمل محلياً. استخدم السياق التالي للإجابة على سؤال المستخدم.
السياق المستخرج من أرشيفات ZIM:
{context_text}

المهارات المتاحة لديك:
{skills_info}

أجب باللغة العربية بشكل مفصل ودقيق.
"""
        
        # 3. Add user query to memory
        self.memory.append({"role": "user", "content": query})
        
        # 4. Prepare messages for model
        messages = [{"role": "system", "content": system_prompt}] + self.memory[-5:] # Keep last 5 turns
        
        # 5. Generate response
        response_gen = self.model_manager.chat_completion(messages, stream=True)
        
        full_response = ""
        print("\nالمساعد: ", end="", flush=True)
        for chunk in response_gen:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0].get('delta', {})
                if 'content' in delta:
                    content = delta['content']
                    print(content, end="", flush=True)
                    full_response += content
        print("\n")
        
        self.memory.append({"role": "assistant", "content": full_response})
        return full_response
