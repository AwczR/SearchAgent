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
	•	app/agents/agent3_write.py
	•	compose_answer(llm, ws:Workspace) -> str

Pipeline
	•	app/pipelines/main_loop.py
	•	init_workspace(query:str) -> Workspace
	•	apply_user_feedback(llm, ws:Workspace, answers:list[str]) -> Workspace
	•	gather_more(llm, ws:Workspace, retriever, rerank_model:str, k:int=8) -> Workspace
	•	finalize_answer(llm, ws:Workspace) -> str