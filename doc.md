.模块边界与接口

数据与持久化
	•	app/schema.py
	•	Doc: {id,title,url,content,score,source,meta}
	•	SubGoal: {id,query,status}
	•	Workspace: {id,question,goal,docs:list[Doc],sub_goals:list[SubGoal],created_at,updated_at}
	•	Decision: {need_more: bool, sub_goals: list[SubGoal]}
	•	app/workspace.py
	•	load_ws(ws_id:str) -> Workspace
	•	save_ws(ws:Workspace) -> None
	•	add_docs(ws:Workspace, docs:list[Doc]) -> Workspace
	•	set_goal(ws:Workspace, goal:str) -> Workspace
	•	add_subgoals(ws:Workspace, subs:list[SubGoal]) -> Workspace

基础设施
	•	app/config.py
	•	Settings: 读取 .env
	•	get_settings() -> Settings 单例
	•	app/llm/chat_sf.py
	•	get_chat(model:str) -> ChatOpenAI 通过 OpenAI 兼容协议直连 SiliconFlow
	•	get_embed(model:str) -> OpenAIEmbeddings 同上
	•	app/retrievers/web_tavily.py
	•	WebRetriever.search(query:str,k:int=8) -> list[Doc]
	•	app/retrievers/rerank_sf.py
	•	rerank(query:str, docs:list[Doc], model:str) -> list[Doc] 按得分降序返回

Agents
	•	app/agents/agent0_intake.py
	•	gen_clarifying_questions(llm, query:str, k:int=3) -> list[str]
	•	rewrite_goal(llm, query:str, user_answers:list[str]) -> str
	•	app/agents/agent1_plan.py
	•	decide_and_plan(llm, ws:Workspace) -> Decision
	•	app/agents/agent2_filter.py
	•	select_docs(llm, query:str, subquery:str, docs:list[Doc], top_k:int=6) -> list[Doc]
	•	**app/agents/agent2b_clean.py**
	•	**clean_text(llm, content:str) -> str**
	•	**clean_docs(llm, docs:list[Doc]) -> list[Doc]** （覆盖 Doc.content，meta.cleaned=true）
	•	app/agents/agent3_write.py
	•	compose_answer(llm, ws:Workspace) -> str
    	•	app/agents/agent3_write.py
	•	compose_answer(llm, ws:Workspace) -> str
	    - 行为：基于 ws.docs 生成答案，**正文不含链接**；结尾自动追加“参考来源”列表，**逐条标注 URL**（从 ws.docs 去重后生成）

Pipeline
	•	app/pipelines/main_loop.py
	•	start_intake(query:str) -> (Workspace, list[str])
	•	continue_after_answers(ws:Workspace, answers:str) -> (Workspace, str)
	•	流程：改写目标 → 规划 →（可选）检索 → 筛选 → **清洗** → 写作