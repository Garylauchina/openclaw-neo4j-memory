#!/usr/bin/env python3
"""
从 lg-imac 的 Neo4j 迁移记忆数据到本地 Neo4j
策略：SSH 隧道 + 逐批读取 + elementId 映射
"""

import subprocess
import sys
import time
import logging
import os
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("migrate")

# ========== 配置（全部通过环境变量，无硬编码凭证） ==========
# SSH
SSH_USER = os.environ.get("MIGRATE_SSH_USER", "")
SSH_HOST = os.environ.get("MIGRATE_SSH_HOST", "")
TUNNEL_PORT = int(os.environ.get("MIGRATE_TUNNEL_PORT", "17687"))

# 远程 Neo4j
REMOTE_NEO4J_USER = os.environ.get("MIGRATE_NEO4J_USER", "neo4j")
REMOTE_NEO4J_PASSWORD = os.environ.get("MIGRATE_NEO4J_PASSWORD", "")

# 本地 Neo4j
LOCAL_NEO4J_URI = os.environ.get("MIGRATE_LOCAL_NEO4J_URI", "bolt://127.0.0.1:7687")
LOCAL_NEO4J_USER = os.environ.get("MIGRATE_LOCAL_NEO4J_USER", "neo4j")
LOCAL_NEO4J_PASSWORD = os.environ.get("MIGRATE_LOCAL_NEO4J_PASSWORD", "")

NODE_BATCH = int(os.environ.get("MIGRATE_NODE_BATCH", "500"))
REL_BATCH = int(os.environ.get("MIGRATE_REL_BATCH", "2000"))


def validate_config():
    """验证必需的环境变量是否已设置"""
    missing = []
    if not SSH_USER:
        missing.append("MIGRATE_SSH_USER")
    if not SSH_HOST:
        missing.append("MIGRATE_SSH_HOST")
    if not REMOTE_NEO4J_PASSWORD:
        missing.append("MIGRATE_NEO4J_PASSWORD")
    if not LOCAL_NEO4J_PASSWORD:
        missing.append("MIGRATE_LOCAL_NEO4J_PASSWORD")
    if missing:
        log.error("缺少必需的环境变量: %s", ", ".join(missing))
        log.info("示例: MIGRATE_SSH_USER=user MIGRATE_SSH_HOST=remote-host \\\n"
                 "         MIGRATE_NEO4J_PASSWORD=xxx MIGRATE_LOCAL_NEO4J_PASSWORD=yyy \\\n"
                 "         python3 scripts/migrate_from_remote.py")
        sys.exit(1)


SSH_CMD = ["ssh", "-f", "-N", "-o", "ServerAliveInterval=30",
           "-L", f"{TUNNEL_PORT}:127.0.0.1:7687", f"{SSH_USER}@{SSH_HOST}"]
REMOTE_AUTH = (REMOTE_NEO4J_USER, REMOTE_NEO4J_PASSWORD)
LOCAL_AUTH = (LOCAL_NEO4J_USER, LOCAL_NEO4J_PASSWORD)
REMOTE_URI = f"bolt://127.0.0.1:{TUNNEL_PORT}"


def start_tunnel():
    subprocess.run(["pkill", "-f", "17687:127.0.0.1:7687"], capture_output=True)
    time.sleep(1)
    log.info("建立 SSH 隧道...")
    p = subprocess.Popen(SSH_CMD)
    time.sleep(3)
    r = subprocess.run(["lsof", "-i", ":17687"], capture_output=True, text=True)
    if r.returncode != 0:
        log.error("隧道失败: %s", r.stderr.strip())
        return None
    log.info("隧道 OK")
    return p


def stop_tunnel():
    subprocess.run(["pkill", "-f", "17687:127.0.0.1:7687"], capture_output=True)


def main():
    validate_config()
    tunnel = start_tunnel()
    if not tunnel:
        sys.exit(1)

    try:
        remote = GraphDatabase.driver(REMOTE_URI, auth=REMOTE_AUTH)
        remote.verify_connectivity()
        local = GraphDatabase.driver(LOCAL_NEO4J_URI, auth=LOCAL_AUTH)
        local.verify_connectivity()
        log.info("双端连接成功")

        # 获取远程总量
        with remote.session() as s:
            total_nodes = s.run("MATCH (n) RETURN count(n) as c").single()["c"]
            total_rels = s.run("MATCH ()-[r]->() RETURN count(r) as c").single()["c"]
        log.info("远程: %d 节点, %d 关系", total_nodes, total_rels)

        # 清空本地
        with local.session() as s:
            old = s.run("MATCH (n) RETURN count(n) as c").single()["c"]
            if old > 0:
                log.info("清空本地 %d 个节点", old)
                s.run("MATCH (n) DETACH DELETE n")

        # ===== 阶段1：迁移节点 =====
        log.info("=== 阶段1：迁移节点 ===")
        id_map = {}  # remote eid -> local eid
        offset = 0

        while offset < total_nodes:
            with remote.session() as rs:
                rows = list(rs.run(
                    "MATCH (n) RETURN elementId(n) as eid, labels(n) as lbls, properties(n) as props "
                    "ORDER BY eid SKIP $sk LIMIT $lm",
                    sk=offset, lm=NODE_BATCH))

            if not rows:
                break

            with local.session() as ls:
                for rec in rows:
                    lbls = rec["lbls"]
                    props = rec["props"]
                    label_clause = ":".join(f"`{l}`" for l in lbls if l) or "Entity"
                    params = {}
                    set_parts = []
                    for k, v in props.items():
                        sk = k.replace(" ", "_").replace("-", "_")
                        params[f"v_{sk}"] = v
                        set_parts.append(f"n.`{sk}` = $v_{sk}")
                    set_clause = f"SET {', '.join(set_parts)}" if set_parts else ""
                    cypher = f"CREATE (n:{label_clause})"
                    if set_clause:
                        cypher += f" {set_clause}"
                    cypher += " RETURN elementId(n) as eid"
                    r = ls.run(cypher, **params)
                    row = r.single()
                    if row:
                        id_map[rec["eid"]] = row["eid"]

            offset += NODE_BATCH
            log.info("  节点 %d/%d (%.0f%%)", min(offset, total_nodes), total_nodes,
                     min(offset, total_nodes) / max(total_nodes, 1) * 100)

        log.info("节点完成: %d 个, 映射 %d 条", len(id_map), len(id_map))

        # ===== 阶段2：迁移关系 =====
        log.info("=== 阶段2：迁移关系 ===")
        rel_offset = 0
        rel_ok = 0
        rel_skip = 0

        while rel_offset < total_rels:
            with remote.session() as rs:
                rows = list(rs.run(
                    "MATCH (a)-[r]->(b) RETURN "
                    "elementId(a) as src, elementId(b) as tgt, "
                    "type(r) as rt, properties(r) as props "
                    "ORDER BY elementId(r) SKIP $sk LIMIT $lm",
                    sk=rel_offset, lm=REL_BATCH))

            if not rows:
                break

            with local.session() as ls:
                tx = ls.begin_transaction()
                try:
                    for rec in rows:
                        src_eid = id_map.get(rec["src"])
                        tgt_eid = id_map.get(rec["tgt"])
                        if not src_eid or not tgt_eid:
                            rel_skip += 1
                            continue

                        props = rec["props"]
                        rt = rec["rt"]
                        params = {"src": src_eid, "tgt": tgt_eid}
                        set_parts = []
                        for k, v in props.items():
                            sk = k.replace(" ", "_").replace("-", "_")
                            params[f"rp_{sk}"] = v
                            set_parts.append(f"r.`{sk}` = $rp_{sk}")
                        set_clause = f"SET {', '.join(set_parts)}" if set_parts else ""
                        cypher = (f"MATCH (a), (b) WHERE elementId(a)=$src AND elementId(b)=$tgt "
                                  f"CREATE (a)-[r:`{rt}`]->(b) {set_clause}".strip())
                        tx.run(cypher, **params)
                        rel_ok += 1

                        if rel_ok % 1000 == 0:
                            tx.commit()
                            tx = ls.begin_transaction()
                    tx.commit()
                except Exception as e:
                    tx.rollback()
                    log.error("关系批次错误: %s", e)

            rel_offset += REL_BATCH
            log.info("  关系 %d/%d 成功=%d 跳过=%d",
                     min(rel_offset, total_rels), total_rels, rel_ok, rel_skip)

        # ===== 验证 =====
        log.info("=== 验证 ===")
        with local.session() as s:
            ln = s.run("MATCH (n) RETURN count(n) as c").single()["c"]
            lr = s.run("MATCH ()-[r]->() RETURN count(r) as c").single()["c"]
        log.info("本地: %d 节点, %d 关系", ln, lr)
        log.info("远程: %d 节点, %d 关系", total_nodes, total_rels)
        if ln == total_nodes:
            log.info("✅ 节点一致")
        else:
            log.info("⚠️  节点差 %d", total_nodes - ln)
        if lr == total_rels:
            log.info("✅ 关系一致")
        else:
            log.info("⚠️  关系差 %d", total_rels - lr)

        remote.close()
        local.close()
        log.info("🎉 完成!")

    except Exception as e:
        log.error("失败: %s", e, exc_info=True)
    finally:
        stop_tunnel()


if __name__ == "__main__":
    main()
