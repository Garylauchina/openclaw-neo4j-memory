"""
OpenClaw 配置自动发现模块

从 openclaw.json 自动提取 LLM 配置，消除 .env 冗余。
优先级：环境变量（.env）> openclaw.json > 默认值
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("openclaw_config_loader")


def find_openclaw_config() -> Optional[Path]:
    """按优先级查找 openclaw.json"""
    search_paths = [
        # 1. 显式指定路径（Docker Volume 挂载场景）
        os.environ.get("OPENCLAW_CONFIG_PATH"),
        # 2. 用户家目录（OpenClaw 默认位置）
        os.path.expanduser("~/.openclaw/openclaw.json"),
        # 3. 工作区根目录（memory_api_server.py 的父目录的父目录）
        str(Path(__file__).parent.parent / "openclaw.json"),
        # 4. 容器内挂载路径
        "/app/.openclaw/openclaw.json",
    ]

    seen: set = set()
    for path_str in search_paths:
        if not path_str:
            continue
        config_path = Path(path_str).resolve()
        if config_path in seen:
            continue
        seen.add(config_path)
        if config_path.exists() and config_path.is_file():
            return config_path

    return None


def parse_openclaw_config(config: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """从 openclaw.json 提取 LLM 连接信息

    返回 {base_url, api_key, model} 或 None
    """
    models = config.get("models", {})
    providers = models.get("providers", {})
    defaults = models.get("defaults", {})
    default_model = defaults.get("model", "")

    if not default_model:
        logger.debug("No default model found in openclaw.json")
        return None

    # 解析 provider 名称（如 "qwen/qwen3.6-plus" → "qwen"）
    if "/" in default_model:
        provider_name = default_model.split("/")[0]
        # 处理多层路径如 "openrouter/qwen/qwen-plus" → "openrouter"
        model_name = "/".join(default_model.split("/")[1:])
    else:
        provider_name = default_model
        model_name = default_model

    if provider_name not in providers:
        # 尝试第一个可用的 provider
        if providers:
            provider_name = list(providers.keys())[0]
            provider = providers[provider_name]
            # 尝试推断模型名
            models_list = provider.get("models", [])
            if models_list and isinstance(models_list, list) and len(models_list) > 0:
                first_model = models_list[0]
                if isinstance(first_model, dict):
                    model_name = first_model.get("id", first_model.get("name", default_model))
                else:
                    model_name = str(first_model)
            else:
                model_name = default_model
        else:
            logger.debug("No matching provider '%s' in openclaw.json", provider_name)
            return None

    provider = providers[provider_name]
    base_url = provider.get("baseUrl", provider.get("base_url", ""))
    api_key = provider.get("apiKey", provider.get("api_key", ""))

    return {
        "base_url": base_url,
        "api_key": api_key,
        "model": model_name,
        "provider": provider_name,
    }


def inject_openclaw_llm_config() -> str:
    """发现 openclaw.json 并注入环境变量

    仅对未设置的环境变量生效（os.environ.setdefault），
    确保 .env 文件中的显式配置优先级更高。

    返回: "openclaw.json" | "env" | "defaults"
    """
    config_path = find_openclaw_config()
    if not config_path:
        logger.info("No openclaw.json found, using .env/defaults for LLM config")
        return "defaults"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Failed to parse %s: %s", config_path, e)
        return "defaults"

    llm = parse_openclaw_config(config)
    if not llm:
        logger.info("Could not extract LLM config from %s", config_path)
        return "defaults"

    # 校验 base_url
    if not llm["base_url"]:
        logger.warning(
            "No baseUrl found for provider %s, skipping openclaw.json", llm["provider"]
        )
        return "defaults"

    # 注入环境变量（仅当未显式设置时），追踪是否真正注入了值
    injected = False
    for env_var, value in [
        ("OPENAI_BASE_URL", llm["base_url"]),
        ("OPENAI_API_KEY", llm["api_key"]),
        ("LLM_MODEL", llm["model"]),
    ]:
        if env_var not in os.environ:
            os.environ[env_var] = value
            injected = True

    if injected:
        logger.info(
            "LLM config loaded from %s: base_url=%s, model=%s",
            config_path,
            llm["base_url"],
            llm["model"],
        )
        return "openclaw.json"

    logger.info("LLM config already set via .env, skipping openclaw.json")
    return "env"
