from app.pipelines.main_loop import start_intake, continue_after_answers

if __name__ == "__main__":
    query = ""

    # 阶段1：澄清问题
    ws, qs = start_intake(query)
    print("澄清问题：", qs)

    # 等待更多信息
    answers = input()

    # 阶段2：带回答继续
    ws, answer = continue_after_answers(ws, answers)
    print("\n=== 最终回答 ===\n", answer)