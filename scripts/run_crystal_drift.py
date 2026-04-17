#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os
from pathlib import Path
from openai import OpenAI

FREE_GROW_PROMPT = """基于给定知识晶体进行自由展开。
要求：
1. 允许表达展开，但尽量保留核心逻辑主轴。
2. 可以做合理归纳，但不要明显脱离输入主题。
3. 输出 JSON：
{
  \"growth\": {
    \"summary\": \"...\",
    \"mechanisms\": [\"...\"],
    \"possible_drifts\": [\"...\"]
  }
}
只返回 JSON。"""

LOCK_HEAVY_GROW_PROMPT = """基于给定知识晶体进行受约束展开。
要求：
1. 必须尽量服从 constraints / forbidden_drifts / thesis_freeze / abstraction_ceiling / problem_space / core_question / in_scope / out_of_scope / non_goal_expansions。
2. 不得明显换题，不得明显升级为协议、框架、数学模型、操作手册。
3. 输出 JSON：
{
  \"growth\": {
    \"summary\": \"...\",
    \"mechanisms\": [\"...\"],
    \"logic_anchor_check\": [\"...\"],
    \"problem_space_check\": [\"...\"],
    \"possible_drifts\": [\"...\"]
  }
}
只返回 JSON。"""

GUIDED_GROW_PROMPT = """基于给定知识晶体进行引导式展开。
要求：
1. 必须服从 preferred_emergence_order / activation_conditions / delayed_abstractions / preferred_candidate_style。
2. 优先沿晶体指定的表达程序展开，不要过早激活高层抽象。
3. 输出 JSON：
{
  \"growth\": {
    \"summary\": \"...\",
    \"mechanisms\": [\"...\"],
    \"guided_expression_check\": [\"...\"],
    \"possible_drifts\": [\"...\"]
  }
}
只返回 JSON。"""

CRYSTAL_PROMPT = """把输入压缩成第一版最小知识晶体，不是普通摘要。
必须输出 JSON：
{
  \"crystal\": {
    \"core_thesis\": \"...\",
    \"nodes\": [{\"name\": \"...\", \"weight\": 0.0}],
    \"relation_paths\": [\"A -> B -> C\"],
    \"constraints\": [\"...\"],
    \"allowed_expansions\": [\"...\"],
    \"forbidden_drifts\": [\"...\"],
    \"thesis_freeze\": [\"...\"],
    \"abstraction_ceiling\": [\"...\"],
    \"problem_space\": \"...\",
    \"core_question\": [\"...\"],
    \"in_scope\": [\"...\"],
    \"out_of_scope\": [\"...\"],
    \"non_goal_expansions\": [\"...\"],
    \"preferred_reasoning_shape\": [\"...\"],
    \"forbidden_formulations\": [\"...\"],
    \"expression_shape_lock\": [\"...\"],
    \"allowed_abstraction_level\": \"...\",
    \"cognitive_level_lock\": [\"...\"],
    \"do_not_mathematize\": [\"...\"],
    \"preserve_open_hypothesis_space\": [\"...\"],
    \"do_not_finalize_as_procedure\": [\"...\"],
    \"exploration_openness_lock\": [\"...\"],
    \"preferred_emergence_order\": [\"...\"],
    \"activation_conditions\": [\"...\"],
    \"delayed_abstractions\": [\"...\"],
    \"preferred_candidate_style\": [\"...\"],
    \"must_reuse_source_fragments\": [\"...\"],
    \"source_trace_points\": [\"...\"],
    \"local_evidence_reanchors\": [\"...\"]
  }
}
要求：
1. 重点保留逻辑主轴，不追求逐字保真。
2. relation_paths 必须体现原始关系递进。
3. forbidden_drifts 必须明确指出哪些偏移不允许发生。
4. thesis_freeze 必须明确哪些核心命题不能被重写成另一类问题。
5. abstraction_ceiling 必须明确禁止哪些抽象抬升。
6. problem_space / in_scope / out_of_scope / non_goal_expansions 必须显式锁定原问题空间。
7. preferred_reasoning_shape / forbidden_formulations / expression_shape_lock 必须显式限制表达形态，避免自动漂向 metric / protocol / framework / governance 语言。
8. allowed_abstraction_level / cognitive_level_lock / do_not_mathematize 必须显式限制认知工作层级，禁止无根据上升到 formal proof、symbolic system、数学化建模。
9. preserve_open_hypothesis_space / do_not_finalize_as_procedure / exploration_openness_lock 必须显式保护探索开放性，禁止把开放问题过早收束成操作手册、固定规程、闭合规则集。
10. preferred_emergence_order / activation_conditions / delayed_abstractions / preferred_candidate_style 必须提供“引导 + 约束”式表达程序，明确哪些表达程序优先激活、哪些抽象必须延后。
11. must_reuse_source_fragments / source_trace_points / local_evidence_reanchors 必须显式要求表达持续贴近原始材料，避免漂浮到高层概念壳。
只返回 JSON。"""

CRYSTAL_GROW_PROMPT = """基于给定知识晶体进行生长。
要求：
1. 允许表达展开，但逻辑主轴不能偏。
2. 必须服从 relation_paths / constraints / forbidden_drifts / thesis_freeze / abstraction_ceiling / problem_space / core_question / in_scope / out_of_scope / non_goal_expansions / preferred_reasoning_shape / forbidden_formulations / expression_shape_lock / allowed_abstraction_level / cognitive_level_lock / do_not_mathematize / preserve_open_hypothesis_space / do_not_finalize_as_procedure / exploration_openness_lock / preferred_emergence_order / activation_conditions / delayed_abstractions / preferred_candidate_style / must_reuse_source_fragments / source_trace_points / local_evidence_reanchors。
3. 新增长内容只能附着在已有 relation_paths 上，不得另起新的支配路径。
4. 不得把原问题空间替换成另一个更泛化或更制度化的问题空间。
5. 不得把内容自动改写成评分系统、分层协议、状态机、治理框架、通用方法论、抽象评估体系，除非原始材料已明确包含这些内容。
6. 不得自动改写成数学模型、符号系统、形式证明、定理化表达、变量化约束，除非原始材料已明确包含这些内容。
7. 不得把开放问题过早收束成操作手册、固定规程、步骤清单、刚性规则集、闭合执行方案；允许保留局部歧义、候选机制和未定结论。
8. 必须优先沿着 preferred_emergence_order 指定的表达程序生长，在 activation_conditions 不满足前，不得提前激活 delayed_abstractions。
9. 每一轮表达都必须回指 source_trace_points 或 must_reuse_source_fragments 所定义的原始材料锚点，不能只停留在高层概念壳中自转。
10. 保持在局部机制 / 证据邻近 / 关系递进层级，不要上升到抽象理论设计层，也不要下降到执行手册层。
11. 输出 JSON：
{
  \"growth\": {
    \"summary\": \"...\",
    \"mechanisms\": [\"...\"],
    \"logic_anchor_check\": [\"...\"],
    \"path_attachment_check\": [\"...\"],
    \"problem_space_check\": [\"...\"],
    \"expression_shape_check\": [\"...\"],
    \"cognitive_level_check\": [\"...\"],
    \"exploration_openness_check\": [\"...\"],
    \"guided_expression_check\": [\"...\"],
    \"source_near_check\": [\"...\"],
    \"possible_drifts\": [\"...\"]
  }
}
只返回 JSON。"""


GUIDED_SOURCE_NEAR_GROW_PROMPT = CRYSTAL_GROW_PROMPT


def call_json(client, model, system_prompt, user_content):
    resp = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return resp.choices[0].message.content or '{}'


FRAGMENT_ANCHORED_GROW_PROMPT = """基于给定知识晶体进行 source-near fragment anchored 展开。
要求：
1. 必须持续回指 must_reuse_source_fragments 与 source_trace_points 中的原始短语和片段。
2. 每轮展开都要尽量复用源短语，避免只做高层概念重写。
3. 输出 JSON：
{
  \"growth\": {
    \"summary\": \"...\",
    \"mechanisms\": [\"...\"],
    \"source_fragment_check\": [\"...\"],
    \"possible_drifts\": [\"...\"]
  }
}
只返回 JSON。"""

RELATION_PATH_ANCHORED_GROW_PROMPT = """基于给定知识晶体进行 relation-path anchored 展开。
要求：
1. 必须优先沿 relation_paths 展开，保持原始关系递进顺序和依附关系。
2. 不得只复述原片段，必须把重点放在关系路径如何推进、哪里被切断、哪里被保留。
3. 输出 JSON：
{
  \"growth\": {
    \"summary\": \"...\",
    \"mechanisms\": [\"...\"],
    \"relation_path_check\": [\"...\"],
    \"possible_drifts\": [\"...\"]
  }
}
只返回 JSON。"""

COMBINED_ANCHORED_GROW_PROMPT = """基于给定知识晶体进行 combined anchored 展开。
要求：
1. 必须以 relation_paths 为主线，优先保持原始关系递进顺序和依附关系。
2. 同时必须复用 must_reuse_source_fragments / source_trace_points 中的关键原始短语，作为 lexical guard。
3. 不得只复述原片段，也不得只在高层概念层面重写，必须同时满足 path fidelity 和 fragment fidelity。
4. 输出 JSON：
{
  \"growth\": {
    \"summary\": \"...\",
    \"mechanisms\": [\"...\"],
    \"relation_path_check\": [\"...\"],
    \"source_fragment_check\": [\"...\"],
    \"combined_anchor_check\": [\"...\"],
    \"possible_drifts\": [\"...\"]
  }
}
只返回 JSON。"""

REASONING_FRAME_GROW_PROMPT = """基于给定知识晶体进行 reasoning-frame induced 展开。
要求：
1. 你的任务不是复述输入，也不是自由发挥，而是沿着一个健康的推理路径进行重建。
2. 必须先从 source-near facts / local evidence 出发，再沿 relation_paths 推进，不得先跳到高层框架、协议、治理、评分系统。
3. 必须明确区分 correlation / mechanism / causation，不得把弱相关直接升级成强因果或一般规律。
4. 必须维持 problem_space，不得把当前问题改写成另一个更抽象、更制度化或更程序化的问题。
5. 允许表达重写，但不允许替换核心 relation spine，不允许越过关键中间桥直接跳结论。
6. 允许保留开放性，不要过早收束成步骤手册、闭合规则集、治理框架或评估协议。
7. 输出 JSON：
{
  \"growth\": {
    \"summary\": \"...\",
    \"reasoning_steps\": [\"...\"],
    \"reasoning_frame_check\": [\"...\"],
    \"relation_path_check\": [\"...\"],
    \"problem_space_check\": [\"...\"],
    \"knowledge_state_check\": [\"...\"],
    \"possible_drifts\": [\"...\"]
  }
}
只返回 JSON。"""

REASONING_FRAME_COMBINED_GROW_PROMPT = """基于给定知识晶体进行 reasoning-frame + combined-anchor 展开。
要求：
1. 必须先从 source-near facts / local evidence 出发，再沿 relation_paths 推进，不得先跳到高层框架、协议、治理、评分系统。
2. 必须以 relation_paths 为主线，同时复用 must_reuse_source_fragments / source_trace_points 中的关键原始短语，作为 lexical guard。
3. 必须明确区分 correlation / mechanism / causation，不得把弱相关直接升级成强因果或一般规律。
4. 必须维持 problem_space，不得把当前问题改写成另一个更抽象、更制度化或更程序化的问题。
5. 不得替换核心 relation spine，不得另起新的支配路径，不得越过关键中间桥直接跳结论。
6. 允许保留开放性，不要过早收束成步骤手册、闭合规则集、治理框架或评估协议。
7. 输出 JSON：
{
  \"growth\": {
    \"summary\": \"...\",
    \"reasoning_steps\": [\"...\"],
    \"reasoning_frame_check\": [\"...\"],
    \"relation_path_check\": [\"...\"],
    \"source_fragment_check\": [\"...\"],
    \"problem_space_check\": [\"...\"],
    \"knowledge_state_check\": [\"...\"],
    \"combined_anchor_check\": [\"...\"],
    \"possible_drifts\": [\"...\"]
  }
}
只返回 JSON。"""


def get_grow_prompt(mode: str) -> str:
    mapping = {
        'free': FREE_GROW_PROMPT,
        'lock-heavy': LOCK_HEAVY_GROW_PROMPT,
        'guided': GUIDED_GROW_PROMPT,
        'guided-source-near': GUIDED_SOURCE_NEAR_GROW_PROMPT,
        'fragment-anchor': FRAGMENT_ANCHORED_GROW_PROMPT,
        'relation-path-anchor': RELATION_PATH_ANCHORED_GROW_PROMPT,
        'combined-anchor': COMBINED_ANCHORED_GROW_PROMPT,
        'reasoning-frame': REASONING_FRAME_GROW_PROMPT,
        'reasoning-frame-combined': REASONING_FRAME_COMBINED_GROW_PROMPT,
    }
    if mode not in mapping:
        raise ValueError(f'unsupported unfold mode: {mode}')
    return mapping[mode]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('input_path')
    p.add_argument('--rounds', type=int, default=4)
    p.add_argument('--model', default=os.environ.get('RAW_REFLECTION_MODEL', 'gemma4:e4b'))
    p.add_argument('--unfold-mode', default='guided-source-near', choices=['free', 'lock-heavy', 'guided', 'guided-source-near', 'fragment-anchor', 'relation-path-anchor', 'combined-anchor', 'reasoning-frame', 'reasoning-frame-combined'])
    p.add_argument('--output', default='tmp/crystal-drift-output.json')
    args = p.parse_args()

    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', 'ollama'), base_url=os.environ.get('OPENAI_BASE_URL', 'http://localhost:11434/v1'))
    original = Path(args.input_path).read_text(encoding='utf-8')
    current = original
    history = []

    grow_prompt = get_grow_prompt(args.unfold_mode)

    for i in range(1, args.rounds + 1):
        crystal = call_json(client, args.model, CRYSTAL_PROMPT, current)
        growth = call_json(client, args.model, grow_prompt, crystal)
        history.append({"round": i, "input": current, "crystal": crystal, "growth": growth})
        current = growth

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "metadata": {
            "model": args.model,
            "base_url": os.environ.get('OPENAI_BASE_URL', 'http://localhost:11434/v1'),
            "unfold_mode": args.unfold_mode,
            "rounds": args.rounds,
            "input_path": args.input_path,
        },
        "original": original,
        "rounds": history,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(out))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
