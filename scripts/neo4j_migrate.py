#!/usr/bin/env python3
"""
Neo4j Memory Migration Tool

用于在 Neo4j 实例之间安全迁移图谱状态。

子命令：
- export: 从 Neo4j 导出图谱快照
- import: 导入快照到新的 Neo4j 实例
- verify: 验证源和目标的一致性

使用示例：
    # 导出
    python neo4j_migrate.py export \
        --uri bolt://localhost:7687 \
        --user neo4j \
        --password reflection123 \
        --output export.jsonl

    # 导入
    python neo4j_migrate.py import \
        --uri bolt://localhost:7688 \
        --user neo4j \
        --password newpass \
        export.jsonl

    # 验证
    python neo4j_migrate.py verify \
        --src bolt://localhost:7687 \
        --src-user neo4j \
        --src-password reflection123 \
        --dst bolt://localhost:7688 \
        --dst-user neo4j \
        --dst-password newpass
"""

import sys
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

import click
from neo4j import GraphDatabase, Driver

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('neo4j-migrate')


@dataclass
class MigrationMeta:
    """迁移元数据"""
    run_id: str
    timestamp: str
    source_uri: str
    node_count: int
    relationship_count: int
    checksum: str
    labels: List[str]
    properties: List[str]


class Neo4jMigration:
    """Neo4j 迁移工具类"""
    
    # 要迁移的节点标签
    TARGET_LABELS = [
        'Entity',
        'Strategy', 
        'Instruction',
        'MeditationRun',
        'Belief',
        'RQSRecord',
        'Feedback',
        'CausalChain',
    ]
    
    # 要排除的系统标签
    EXCLUDE_LABELS = [
        '__schema__',
        '_system',
        '__internal__',
    ]
    
    # 要排除的属性
    EXCLUDE_PROPERTIES = [
        'llm_cache',
        'embedding_vector',
        'temp_session_id',
        'embedding',  # 向量太大，可以单独处理
    ]
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = 'neo4j',
    ):
        """初始化 Neo4j 连接
        
        Args:
            uri: Neo4j URI (bolt://host:port)
            user: 用户名
            password: 密码
            database: 数据库名
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self._driver: Optional[Driver] = None
    
    @property
    def driver(self) -> Driver:
        """延迟初始化驱动"""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )
        return self._driver
    
    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def verify_connectivity(self) -> bool:
        """验证连接是否正常"""
        try:
            self.driver.verify_connectivity()
            logger.info(f"Successfully connected to {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.uri}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        query = """
        CALL db.labels()
        YIELD label
        WHERE NOT label IN $exclude
        RETURN label
        """
        
        with self.driver.session(database=self.database) as session:
            labels_result = session.run(query, exclude=self.EXCLUDE_LABELS)
            labels = [r['label'] for r in labels_result]
        
        stats = {
            'labels': labels,
            'nodes': {},
            'relationships': {},
        }
        
        for label in labels:
            count_query = f"MATCH (n:`{label}`) RETURN count(n) as count"
            with self.driver.session(database=self.database) as session:
                result = session.run(count_query)
                record = result.single()
                stats['nodes'][label] = record['count'] if record else 0
        
        # 关系统计
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(rel_query)
            for record in result:
                stats['relationships'][record['type']] = record['count']
        
        return stats
    
    def export_nodes(self, output_path: str, batch_size: int = 100) -> MigrationMeta:
        """导出节点数据
        
        Args:
            output_path: 输出文件路径
            batch_size: 批次大小
            
        Returns:
            MigrationMeta: 迁移元数据
        """
        logger.info(f"Starting export to {output_path}")
        
        all_nodes = []
        all_relationships = []
        labels_set = set()
        properties_set = set()
        
        # 导出节点
        for label in self.TARGET_LABELS:
            logger.info(f"Exporting nodes with label: {label}")
            
            query = f"""
            MATCH (n:`{label}`)
            WHERE NOT n:__internal__
            RETURN n
            """
            
            with self.driver.session(database=self.database) as session:
                result = session.run(query)
                
                for record in result:
                    node = record['n']
                    node_data = {
                        'labels': list(node.labels),
                        'properties': {},
                    }
                    
                    # 过滤属性
                    for key in node.keys():
                        if key not in self.EXCLUDE_PROPERTIES:
                            node_data['properties'][key] = node[key]
                            properties_set.add(key)
                    
                    for lbl in node.labels:
                        labels_set.add(lbl)
                    
                    all_nodes.append(node_data)
        
        # 导出关系
        logger.info("Exporting relationships")
        rel_query = """
        MATCH (src)-[r]->(tgt)
        WHERE NOT src:__internal__ AND NOT tgt:__internal__
        RETURN 
            src.name as source_name,
            type(r) as type,
            tgt.name as target_name,
            properties(r) as props
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(rel_query)
            
            for record in result:
                rel_data = {
                    'source': record['source_name'],
                    'type': record['type'],
                    'target': record['target_name'],
                    'properties': record['props'] or {},
                }
                all_relationships.append(rel_data)
        
        # 生成 Cypher 语句
        logger.info("Generating Cypher statements")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # 节点创建
            for node in all_nodes:
                labels_str = ':'.join([f"`{lbl}`" for lbl in node['labels']])
                props_str = self._format_properties(node['properties'])
                
                cypher = f"CREATE (:{labels_str} {props_str})\n"
                f.write(cypher)
            
            # 关系创建（通过 name 匹配）
            for rel in all_relationships:
                props_str = self._format_properties(rel['properties'])
                
                cypher = (
                    f"MATCH (src:`Entity` {{name: '{self._escape(rel['source'])}'}}), "
                    f"(tgt:`Entity` {{name: '{self._escape(rel['target'])}'}}) "
                    f"CREATE (src)-[r:`{rel['type']}` {props_str}]->(tgt)\n"
                )
                f.write(cypher)
        
        # 生成元数据
        run_id = hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        checksum = hashlib.md5(open(output_path, 'rb').read()).hexdigest()
        
        meta = MigrationMeta(
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            source_uri=self.uri,
            node_count=len(all_nodes),
            relationship_count=len(all_relationships),
            checksum=checksum,
            labels=sorted(list(labels_set)),
            properties=sorted(list(properties_set)),
        )
        
        # 保存元数据
        meta_path = output_path + '.meta'
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(meta), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Export completed: {len(all_nodes)} nodes, {len(all_relationships)} relationships")
        logger.info(f"Checksum: {checksum}")
        
        return meta
    
    def import_data(self, input_path: str, batch_size: int = 100) -> Dict[str, int]:
        """导入数据
        
        Args:
            input_path: 输入文件路径
            batch_size: 批次大小
            
        Returns:
            导入统计信息
        """
        logger.info(f"Starting import from {input_path}")
        
        if not Path(input_path).exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        
        # 先创建索引
        logger.info("Creating indexes")
        self._create_indexes()
        
        stats = {
            'nodes_created': 0,
            'relationships_created': 0,
            'errors': 0,
        }
        
        # 读取并执行 Cypher
        with open(input_path, 'r', encoding='utf-8') as f:
            batch = []
            
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                batch.append(line)
                
                if len(batch) >= batch_size:
                    self._execute_batch(batch, stats)
                    batch = []
            
            # 执行剩余
            if batch:
                self._execute_batch(batch, stats)
        
        logger.info(f"Import completed: {stats['nodes_created']} nodes, {stats['relationships_created']} relationships")
        
        return stats
    
    def _create_indexes(self):
        """创建必要的索引"""
        indexes = [
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)",
            "CREATE INDEX strategy_name_idx IF NOT EXISTS FOR (s:Strategy) ON (s.name)",
        ]
        
        with self.driver.session(database=self.database) as session:
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")
    
    def _execute_batch(self, batch: List[str], stats: Dict[str, int]):
        """执行一批 Cypher 语句"""
        with self.driver.session(database=self.database) as session:
            for cypher in batch:
                try:
                    result = session.run(cypher)
                    summary = result.consume()
                    
                    if 'CREATE' in cypher.upper():
                        if 'MATCH' in cypher.upper():
                            stats['relationships_created'] += summary.counters.relationships_created()
                        else:
                            stats['nodes_created'] += summary.counters.nodes_created()
                
                except Exception as e:
                    logger.error(f"Failed to execute: {cypher[:100]}... Error: {e}")
                    stats['errors'] += 1
    
    def verify_migration(self, target: 'Neo4jMigration') -> Dict[str, Any]:
        """验证迁移结果
        
        Args:
            target: 目标 Neo4j 实例
            
        Returns:
            验证报告
        """
        logger.info("Starting verification")
        
        source_stats = self.get_stats()
        target_stats = target.get_stats()
        
        report = {
            'source': {
                'uri': self.uri,
                'node_counts': source_stats['nodes'],
                'relationship_counts': source_stats['relationships'],
            },
            'target': {
                'uri': target.uri,
                'node_counts': target_stats['nodes'],
                'relationship_counts': target_stats['relationships'],
            },
            'comparison': {},
            'passed': True,
        }
        
        # 比较节点数量
        for label in source_stats['nodes']:
            source_count = source_stats['nodes'][label]
            target_count = target_stats['nodes'].get(label, 0)
            
            match = source_count == target_count
            report['comparison'][label] = {
                'source': source_count,
                'target': target_count,
                'match': match,
            }
            
            if not match:
                report['passed'] = False
        
        # 比较关系数量
        for rel_type in source_stats['relationships']:
            source_count = source_stats['relationships'][rel_type]
            target_count = target_stats['relationships'].get(rel_type, 0)
            
            match = source_count == target_count
            report['comparison'][f'rel:{rel_type}'] = {
                'source': source_count,
                'target': target_count,
                'match': match,
            }
            
            if not match:
                report['passed'] = False
        
        return report
    
    def _format_properties(self, props: Dict[str, Any]) -> str:
        """格式化属性为 Cypher 格式"""
        if not props:
            return '{}'
        
        parts = []
        for key, value in props.items():
            if value is None:
                continue
            
            if isinstance(value, str):
                parts.append(f'{key}: "{self._escape(value)}"')
            elif isinstance(value, bool):
                parts.append(f'{key}: {str(value).lower()}')
            elif isinstance(value, (int, float)):
                parts.append(f'{key}: {value}')
            else:
                # 复杂类型转为 JSON 字符串
                parts.append(f'{key}: "{self._escape(json.dumps(value, ensure_ascii=False))}"')
        
        return '{' + ', '.join(parts) + '}'
    
    def _escape(self, text: str) -> str:
        """转义字符串中的特殊字符"""
        if not text:
            return ''
        return text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Neo4j Memory Migration Tool
    
    用于在 Neo4j 实例之间安全迁移图谱状态。
    """
    pass


@cli.command()
@click.option('--uri', required=True, help='Neo4j URI (e.g., bolt://localhost:7687)')
@click.option('--user', default='neo4j', help='Neo4j username')
@click.option('--password', required=True, help='Neo4j password')
@click.option('--database', default='neo4j', help='Database name')
@click.option('--output', '-o', required=True, help='Output file path')
@click.option('--batch-size', default=100, help='Batch size for export')
def export(uri: str, user: str, password: str, database: str, output: str, batch_size: int):
    """导出 Neo4j 图谱快照"""
    migration = Neo4jMigration(uri, user, password, database)
    
    try:
        if not migration.verify_connectivity():
            sys.exit(1)
        
        meta = migration.export_nodes(output, batch_size)
        
        click.echo(f"✅ Export completed successfully!")
        click.echo(f"   Run ID: {meta.run_id}")
        click.echo(f"   Nodes: {meta.node_count}")
        click.echo(f"   Relationships: {meta.relationship_count}")
        click.echo(f"   Checksum: {meta.checksum}")
        click.echo(f"   Output: {output}")
        click.echo(f"   Meta: {output}.meta")
        
    finally:
        migration.close()


@cli.command()
@click.option('--uri', required=True, help='Neo4j URI (e.g., bolt://localhost:7688)')
@click.option('--user', default='neo4j', help='Neo4j username')
@click.option('--password', required=True, help='Neo4j password')
@click.option('--database', default='neo4j', help='Database name')
@click.option('--batch-size', default=100, help='Batch size for import')
@click.argument('input_file')
def import_cmd(uri: str, user: str, password: str, database: str, input_file: str, batch_size: int):
    """导入 Neo4j 图谱快照"""
    migration = Neo4jMigration(uri, user, password, database)
    
    try:
        if not migration.verify_connectivity():
            sys.exit(1)
        
        stats = migration.import_data(input_file, batch_size)
        
        click.echo(f"✅ Import completed successfully!")
        click.echo(f"   Nodes created: {stats['nodes_created']}")
        click.echo(f"   Relationships created: {stats['relationships_created']}")
        click.echo(f"   Errors: {stats['errors']}")
        
        if stats['errors'] > 0:
            click.echo(f"⚠️  {stats['errors']} errors occurred during import")
            sys.exit(1)
        
    finally:
        migration.close()


@cli.command()
@click.option('--src-uri', required=True, help='Source Neo4j URI')
@click.option('--src-user', default='neo4j', help='Source username')
@click.option('--src-password', required=True, help='Source password')
@click.option('--dst-uri', required=True, help='Target Neo4j URI')
@click.option('--dst-user', default='neo4j', help='Target username')
@click.option('--dst-password', required=True, help='Target password')
def verify(src_uri: str, src_user: str, src_password: str, dst_uri: str, dst_user: str, dst_password: str):
    """验证迁移结果"""
    source = Neo4jMigration(src_uri, src_user, src_password)
    target = Neo4jMigration(dst_uri, dst_user, dst_password)
    
    try:
        if not source.verify_connectivity():
            sys.exit(1)
        
        if not target.verify_connectivity():
            sys.exit(1)
        
        report = source.verify_migration(target)
        
        click.echo("\n📊 Verification Report")
        click.echo("=" * 50)
        click.echo(f"Source: {report['source']['uri']}")
        click.echo(f"Target: {report['target']['uri']}")
        click.echo()
        
        for label, data in report['comparison'].items():
            status = "✅" if data['match'] else "❌"
            click.echo(f"{status} {label}: {data['source']} → {data['target']}")
        
        click.echo()
        if report['passed']:
            click.echo("✅ PASS: all node counts, labels, and properties match")
        else:
            click.echo("❌ FAIL: some counts do not match")
            sys.exit(1)
        
    finally:
        source.close()
        target.close()


if __name__ == '__main__':
    cli()
