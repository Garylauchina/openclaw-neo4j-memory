#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os
from pathlib import Path
from openai import OpenAI

SYSTEM_PROMPT = """你在做局部规律候选归纳，不是在发明全局真理。
给定一组原始语料切片和最小图提示，请只基于这些局部材料提出 1-3 条局部规律候选。
要求：
1. 明确区分相关性、机制性、因果候选，不要把弱相关直接写成强因果。
2. 结论必须保留 local identity，尽量点名 slice 中出现的关键实体/工具/主题。
3. 不要上升为整个系统、整个领域或宏大范式。
4. 如果证据不足，就降低 confidence，不要强行归纳。
输出 JSON：
{
  \"candidates\": [
    {
      \"type\": \"correlation|mechanism|causal_candidate\",
      \"summary\": \"...\",
      \"evidence_slices\": [\"slice-1\"],
      \"key_entities\": [\"...\"],
      \"confidence\": 0.0
    }
  ]
}
只返回 JSON。"""

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('input_json')
    p.add_argument('--model', default=os.environ.get('RAW_REFLECTION_MODEL', 'gemma4:e4b'))
    p.add_argument('--output', default='tmp/raw-reflection-output.json')
    args = p.parse_args()

    payload = Path(args.input_json).read_text(encoding='utf-8')
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', 'ollama'), base_url=os.environ.get('OPENAI_BASE_URL', 'http://localhost:11434/v1'))
    resp = client.chat.completions.create(
        model=args.model,
        temperature=0.1,
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': payload},
        ],
    )
    text = resp.choices[0].message.content or '{}'
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding='utf-8')
    print(str(out))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
