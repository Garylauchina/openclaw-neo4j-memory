#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os
from pathlib import Path
from openai import OpenAI

COMPRESS_PROMPT = """你要把输入压缩成适合 LLM 后续生长的高密度表示，不是普通摘要。
要求：
1. 保留核心机制、关系递进、证据边界。
2. 不要空泛上升为宏大结论。
3. 输出 JSON：
{
  \"crystal\": {
    \"summary\": \"...\",
    \"key_points\": [\"...\"],
    \"relation_paths\": [\"A -> B -> C\"],
    \"constraints\": [\"...\"]
  }
}
只返回 JSON。"""

GROW_PROMPT = """你要基于给定 crystal 进行生长，生成局部解释/规律候选。
要求：
1. 必须尽量保持与原始材料可参照。
2. 不要把弱相关直接写成强因果。
3. 不要空泛上升为宏大结论。
4. 输出 JSON：
{
  \"growth\": {
    \"summary\": \"...\",
    \"mechanisms\": [\"...\"],
    \"possible_drifts\": [\"...\"]
  }
}
只返回 JSON。"""

ANCHORED_GROW_PROMPT = """你要基于给定 crystal 进行生长，但必须持续服从锚点约束。
锚点约束优先级高于自由发挥：
1. source anchor: 新内容必须与原始语料主题保持可参照。
2. relation path anchor: 必须尽量保留原始关系递进路径，不得自行替换为更一般化系统设计语言。
3. core topic anchor: 必须反复围绕原始核心主题，不得漂移到未在原始语料中讨论的工程机制。
4. 不要把弱相关直接写成强因果。
5. 不要空泛上升为宏大结论。
输出 JSON：
{
  \"growth\": {
    \"summary\": \"...\",
    \"mechanisms\": [\"...\"],
    \"anchor_check\": [\"...\"],
    \"possible_drifts\": [\"...\"]
  }
}
只返回 JSON。"""


def call_json(client, model, system_prompt, user_content):
    resp = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    text = resp.choices[0].message.content or '{}'
    return text


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('input_path')
    p.add_argument('--rounds', type=int, default=4)
    p.add_argument('--model', default=os.environ.get('RAW_REFLECTION_MODEL', 'gemma4:e4b'))
    p.add_argument('--anchored', action='store_true')
    p.add_argument('--output', default='tmp/growth-drift-output.json')
    args = p.parse_args()

    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', 'ollama'), base_url=os.environ.get('OPENAI_BASE_URL', 'http://localhost:11434/v1'))
    original = Path(args.input_path).read_text(encoding='utf-8')
    current = original
    history = []

    for i in range(1, args.rounds + 1):
        crystal_text = call_json(client, args.model, COMPRESS_PROMPT, current)
        growth_prompt = ANCHORED_GROW_PROMPT if args.anchored else GROW_PROMPT
        growth_text = call_json(client, args.model, growth_prompt, crystal_text)
        history.append({
            'round': i,
            'input': current,
            'crystal': crystal_text,
            'growth': growth_text,
        })
        current = growth_text

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'original': original, 'anchored': args.anchored, 'rounds': history}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(out))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
