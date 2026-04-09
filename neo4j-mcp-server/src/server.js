"use strict";

/**
 * OpenClaw Neo4j MCP Server
 * MCP Server for OpenClaw's Neo4j Memory System
 * Implements MCP 2.0 specification
 */

const express = require('express');
const { Server: MCPServer } = require('@modelcontextprotocol/sdk/server');
const neo4j = require('neo4j-driver');
const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');
const winston = require('winston');
require('dotenv').config();

// Create Express app
const app = express();
const mcpServer = new MCPServer();

// Logger configuration
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: '../logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: '../logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

// Rate limiting
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW || '15') * 60 * 1000, // 15 minutes
  max: parseInt(process.env.RATE_LIMIT_MAX || '100'), // limit each IP to 100 requests per windowMs
  message: { error: 'Too many requests, please try again later.' },
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
});

// Middlewares
app.use(express.json({ limit: '10mb' }));
app.use(limiter);
app.use('/mcp', (req, res, next) => {
  logger.info(`${req.method} ${req.path}`, {
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });
  next();
});

// CORS - Development only
if (process.env.NODE_ENV !== 'production') {
  const cors = require('cors');
  const corsOptions = {
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    optionsSuccessStatus: 200
  };
  app.use(cors(corsOptions));
}

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    server: process.env.MCP_SERVER_NAME,
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// Authentication middleware
function authenticateToken(req, res, next) {
  // First, check for MCP Authorization header
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  
  // Second, check for MCP access token
  const accessToken = req.headers['x-mcp-access-token'] || req.query.access_token;
  
  if (!token && !accessToken) {
    logger.warn('Authentication failed: no token provided', { path: req.path });
    return res.status(401).json({ 
      error: 'Access token required',
      code: 'UNAUTHORIZED' 
    });
  }

  // Verify MCP access token
  if (accessToken === process.env.ACCESS_TOKEN) {
    req.user = { id: 'system', role: 'system' };
    logger.info('System access granted via access token', { path: req.path });
    return next();
  }
  
  // Verify JWT token
  if (token) {
    jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
      if (err) {
        logger.warn('Authentication failed: invalid JWT token', { error: err.message });
        return res.status(403).json({ 
          error: 'Invalid token',
          code: 'FORBIDDEN' 
        });
      }
      req.user = user;
      logger.info('User authenticated via JWT', { userId: user.id, role: user.role });
      next();
    });
  } else {
    logger.warn('Authentication failed: invalid access token', { path: req.path });
    return res.status(403).json({ 
      error: 'Invalid access token',
      code: 'FORBIDDEN' 
    });
  }
}

// Error handling middleware
app.use((err, req, res, next) => {
  logger.error('Unhandled error', { error: err.stack, path: req.path });
  res.status(500).json({
    error: 'Internal server error',
    code: 'INTERNAL_ERROR'
  });
});

// Database connection
let driver;
let session;

async function connectToNeo4j() {
  try {
    driver = neo4j.driver(
      process.env.NEO4J_URI,
      neo4j.auth.basic(
        process.env.NEO4J_USERNAME,
        process.env.NEO4J_PASSWORD
      )
    );
    
    // Test the connection
    session = driver.session();
    await session.run('RETURN 1');
    await session.close();
    
    logger.info('Connected to Neo4j database successfully');
    
    // Set up periodic connection health check
    setInterval(async () => {
      try {
        session = driver.session();
        await session.run('RETURN 1');
        await session.close();
        logger.debug('Neo4j connection health check passed');
      } catch (error) {
        logger.error('Neo4j connection health check failed', { error: error.message });
        // Connection will be re-established on next request
      }
    }, 30000); // Check every 30 seconds
    
  } catch (error) {
    logger.error('Failed to connect to Neo4j', { error: error.message });
    throw error;
  }
}

// MCP Server Implementation

// Initialize MCP server
async function initializeMCPServer() {
  // Server capabilities
  mcpServer.setCapabilities({
    version: '2.0',
    capabilities: {
      resources: {
        list: true,
        read: true,
        write: false // Write capabilities disabled for now
      },
      prompts: {
        list: true,
        call: true
      },
      tools: {
        list: true,
        call: true
      }
    }
  });

  // Capabilities endpoint
  app.get('/mcp', (req, res) => {
    logger.info('Capabilities requested', { ip: req.ip });
    res.json(mcpServer.getCapabilities());
  });

  // Resources endpoints
  app.get('/mcp/resources', authenticateToken, async (req, res) => {
    try {
      session = driver.session();
      
      // Query for all node labels
      const result = await session.run(`
        CALL db.labels() YIELD label 
        WHERE label <> 'User' AND label <> 'Event' AND label <> 'Decision' 
        RETURN label ORDER BY label
      `);
      
      const resources = [{
        type: 'directory',
        name: 'system',
        description: 'System information and statistics'
      }, {
        type: 'directory',
        name: 'user',
        description: 'User profile and preferences'
      }, {
        type: 'directory',
        name: 'memories',
        description: 'Curated long-term memories'
      }, {
        type: 'directory',
        name: 'entities',
        description: 'All entities in memory graph'
      }];
      
      // Add resources for each label
      result.records.forEach(record => {
        const label = record.get('label');
        resources.push({
          type: 'directory',
          name: label.toLowerCase(),
          description: `Nodes with label ${label}`
        });
      });
      
      await session.close();
      logger.info('Resources list returned', { count: resources.length });
      res.json(resources);
    } catch (error) {
      logger.error('Error listing resources', { error: error.message });
      res.status(500).json({ 
        error: error.message, 
        code: 'INTERNAL_ERROR' 
      });
    }
  });

  app.get('/mcp/resources/:path', authenticateToken, async (req, res) => {
    try {
      const { path } = req.params;
      session = driver.session();
      
      // System information
      if (path === 'system') {
        const result = await session.run(`
          MATCH (n) 
          RETURN count(n) as nodeCount 
        `);
        
        const nodeCount = result.records[0]?.get('nodeCount') || 0;
        
        await session.close();
        
        logger.info('System resource accessed', { nodeCount });
        res.json({
          contentType: 'application/json',
          name: 'system',
          content: {
            server: process.env.MCP_SERVER_NAME,
            version: '1.0.0',
            nodeCount: nodeCount,
            timestamp: new Date().toISOString()
          }
        });
        
      // User information  
      } else if (path === 'user') {
        const result = await session.run(`
          MATCH (u:User) 
          RETURN u LIMIT 1
        `);
        
        if (result.records.length === 0) {
          await session.close();
          logger.info('No user data found');
          res.json({
            contentType: 'application/json',
            name: 'user',
            content: {}
          });
          return;
        }
        
        const userData = result.records[0].get('u').properties;
        await session.close();
        
        logger.info('User resource accessed', { userId: userData.id });
        res.json({
          contentType: 'application/json',
          name: 'user',
          content: userData
        });
        
      // Memory graph statistics  
      } else if (path === 'memories') {
        const result = await session.run(`
          MATCH (m:Memory) 
          WHERE m.createdAt > timestamp() - (30 * 24 * 60 * 60 * 1000) // Last 30 days
          RETURN 
            count(m) as recentCount,
            sum(m.importance) as totalImportance,
            avg(m.importance) as avgImportance
        `);
        
        const stats = result.records[0];
        const recentCount = stats?.get('recentCount') || 0;
        const totalImportance = stats?.get('totalImportance') || 0;
        const avgImportance = stats?.get('avgImportance') || 0;
        
        await session.close();
        
        logger.info('Memories resource accessed', { recentCount });
        res.json({
          contentType: 'application/json',
          name: 'memories',
          content: {
            recentCount: recentCount,
            totalImportance: totalImportance,
            avgImportance: avgImportance,
            period: 'last 30 days'
          }
        });
        
      // Entity type  
      } else if (path.startsWith('entities/')) {
        const label = path.split('/')[1].charAt(0).toUpperCase() + path.split('/')[1].slice(1);
        const result = await session.run(`
          MATCH (n:${label}) 
          WHERE n.createdAt > timestamp() - (7 * 24 * 60 * 60 * 1000) // Last 7 days
          RETURN n 
          ORDER BY n.createdAt DESC 
          LIMIT 10
        `);
        
        const entities = result.records.map(record => {
          const node = record.get('n');
          return {
            id: node.identity?.toNumber(),
            labels: node.labels,
            properties: node.properties,
            createdAt: node.properties.createdAt ? new Date(parseInt(node.properties.createdAt)).toISOString() : null
          };
        });
        
        await session.close();
        
        logger.info('Entities resource accessed', { label, count: entities.length });
        res.json({
          contentType: 'application/json',
          name: path,
          content: entities
        });
        
      } else {
        await session.close();
        logger.warn('Resource not found', { path });
        res.status(404).json({ 
          error: 'Resource not found', 
          code: 'NOT_FOUND' 
        });
      }
    } catch (error) {
      if (session) {
        await session.close();
      }
      logger.error('Error reading resource', { error: error.message, path: req.params.path });
      res.status(500).json({ 
        error: error.message, 
        code: 'INTERNAL_ERROR' 
      });
    }
  });

  // Tools endpoints
  app.get('/mcp/tools', authenticateToken, (req, res) => {
    const tools = [
      {
        name: 'memory_search',
        description: 'Search memory graph for relevant content using full-text search',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Search query text',
              minLength: 1
            },
            limit: {
              type: 'integer',
              description: 'Maximum number of results to return',
              minimum: 1,
              maximum: 100,
              default: 10
            },
            use_fulltext: {
              type: 'boolean',
              description: 'Use Neo4j full-text search index',
              default: true
            }
          },
          required: ['query']
        }
      },
      {
        name: 'get_user_context',
        description: 'Get a comprehensive summary of current user context',
        inputSchema: {
          type: 'object',
          properties: {
            include_memories: {
              type: 'boolean',
              description: 'Include recent memories in context',
              default: true
            },
            include_stats: {
              type: 'boolean',
              description: 'Include system statistics',
              default: true
            }
          }
        }
      },
      {
        name: 'list_recent_events',
        description: 'List recent events in the memory graph',
        inputSchema: {
          type: 'object',
          properties: {
            hours: {
              type: 'integer',
              description: 'Number of hours to look back',
              minimum: 1,
              maximum: 168, // 1 week
              default: 24
            },
            limit: {
              type: 'integer',
              description: 'Maximum number of events to return',
              minimum: 1,
              maximum: 100,
              default: 10
            }
          }
        }
      }
    ];
    
    logger.info('Tools list returned', { count: tools.length });
    res.json(tools);
  });

  app.post('/mcp/tools/:tool/call', authenticateToken, async (req, res) => {
    try {
      const { tool } = req.params;
      const { arguments: args } = req.body.params;
      
      // Validate input based on tool
      if (tool === 'memory_search' && (!args.query || args.query.trim().length === 0)) {
        return res.status(400).json({ 
          error: 'Query parameter is required and cannot be empty', 
          code: 'INVALID_ARGUMENT' 
        });
      }
      
      if (tool === 'memory_search') {
        session = driver.session();
        
        // Use full-text search if available and requested
        let result;
        if (args.use_fulltext !== false) {
          try {
            result = await session.run(`
              CALL db.index.fulltext.queryNodes("entityContent", $query)
              YIELD node, score
              WITH node, score, labels(node) as nodeLabels
              LIMIT $limit
              RETURN node, score, nodeLabels
            `, { 
              query: args.query, 
              limit: args.limit || 10 
            });
          } catch (error) {
            // If full-text index doesn't exist, fall back to regular search
            logger.warn('Full-text search failed, falling back to regular search', { error: error.message });
            result = await session.run(`
              MATCH (n)
              WHERE ANY(key IN keys(n) WHERE toString(n[key]) CONTAINS $query)
              RETURN n, 0.0 as score, labels(n) as nodeLabels
              LIMIT $limit
            `, { 
              query: args.query, 
              limit: args.limit || 10 
            });
          }
        } else {
          // Regular search
          result = await session.run(`
            MATCH (n)
            WHERE ANY(key IN keys(n) WHERE toString(n[key]) CONTAINS $query)
            RETURN n, 0.0 as score, labels(n) as nodeLabels
            LIMIT $limit
          `, { 
            query: args.query, 
            limit: args.limit || 10 
          });
        }
        
        const searchResults = result.records.map(record => {
          const node = record.get('n');
          return {
            id: node.identity?.toNumber(),
            labels: record.get('nodeLabels'),
            properties: node.properties,
            score: record.get('score'),
            createdAt: node.properties.createdAt ? new Date(parseInt(node.properties.createdAt)).toISOString() : null
          };
        });
        
        await session.close();
        
        logger.info('Memory search completed', { 
          query: args.query, 
          results: searchResults.length 
        });
        
        res.json({
          result: {
            content: formatSearchResults(args.query, searchResults)
          }
        });
        
      } else if (tool === 'get_user_context') {
        session = driver.session();
        
        // Get user information
        const userResult = await session.run(`
          MATCH (u:User) RETURN u LIMIT 1
        `);
        
        // Get recent memories if requested
        let recentMemories = [];
        if (args.include_memories !== false) {
          const memoriesResult = await session.run(`
            MATCH (m:Memory)
            WHERE m.createdAt > timestamp() - (24 * 60 * 60 * 1000)
            RETURN m ORDER BY m.createdAt DESC LIMIT 5
          `);
          
          recentMemories = memoriesResult.records.map(r => r.get('m').properties);
        }
        
        // Get statistics if requested
        let stats = {};
        if (args.include_stats !== false) {
          const statsResult = await session.run(`
            MATCH (n) RETURN count(n) as nodeCount
          `);
          stats = {
            nodeCount: statsResult.records[0]?.get('nodeCount') || 0
          };
        }
        
        await session.close();
        
        const user = userResult.records.length > 0 ? userResult.records[0].get('u').properties : {};
        
        logger.info('User context retrieved', { userId: user.id });
        
        res.json({
          result: {
            content: formatUserContext(user, recentMemories, stats)
          }
        });
        
      } else if (tool === 'list_recent_events') {
        session = driver.session();
        
        const hours = Math.min(Math.max(args.hours || 24, 1), 168);
        const limit = Math.min(Math.max(args.limit || 10, 1), 100);
        
        const result = await session.run(`
          MATCH (e:Event)
          WHERE e.timestamp > timestamp() - ($hours * 60 * 60 * 1000)
          RETURN e ORDER BY e.timestamp DESC LIMIT $limit
        `, { hours, limit });
        
        const events = result.records.map(r => r.get('e').properties);
        
        await session.close();
        
        logger.info('Recent events listed', { hours, count: events.length });
        
        res.json({
          result: {
            content: formatRecentEvents(events)
          }
        });
        
      } else {
        logger.warn('Tool not found', { tool });
        res.status(404).json({ 
          error: 'Tool not found', 
          code: 'NOT_FOUND' 
        });
      }
    } catch (error) {
      if (session) {
        await session.close();
      }
      logger.error('Error calling tool', { error: error.message, tool: req.params.tool });
      res.status(500).json({ 
        error: error.message, 
        code: 'INTERNAL_ERROR' 
      });
    }
  });

  // Helper functions for formatting results
  function formatSearchResults(query, results) {
    if (results.length === 0) {
      return `## 记忆搜索结果\n\n**查询**: ${query}\n**结果**: 未找到相关记忆。`;
    }
    
    return `## 记忆搜索结果\n\n**查询**: ${query}\n**结果数量**: ${results.length}\n\n${results.map((r, i) => 
      `${i+1}. **${r.labels.join('/')}**: ${Object.entries(r.properties)
        .filter(([k, v]) => k !== 'id' && k !== 'createdAt')
        .map(([k, v]) => `${k}=${v}`)
        .join(', ')}`)
      .join('\n')}\n\n---\n来源: Neo4j MCP Server`;
  }
  
  function formatUserContext(user, recentMemories, stats) {
    return `## 用户上下文摘要\n\n### 基本信息\n- **姓名**: ${user.name || '未知'}\n- **时区**: ${user.timezone || '未知'}\n- **语言**: ${user.language || '未知'}\n\n### 最近记忆 (24小时)\n${recentMemories.length > 0 ? 
      recentMemories.map((m, i) => `  ${i+1}. ${m.content || m.topic} (${new Date(parseInt(m.timestamp)).toLocaleString()})`).join('\n') : 
      '无近期记忆'}\n\n### 系统统计\n- **记忆节点数量**: ${stats.nodeCount || 0}\n- **最后活动**: ${new Date().toLocaleString()}\n\n---\n来源: Neo4j MCP Server`;
  }
  
  function formatRecentEvents(events) {
    if (events.length === 0) {
      return `## 近期事件\n\n过去${args.hours || 24}小时内没有找到事件。\n\n---\n来源: Neo4j MCP Server`;
    }
    
    return `## 近期事件\n\n过去${args.hours || 24}小时内找到${events.length}个事件:\n\n${events.map((e, i) => 
      `${i+1}. **${e.type}**: ${e.description || e.topic} (${new Date(parseInt(e.timestamp)).toLocaleString()})`)
      .join('\n')}\n\n---\n来源: Neo4j MCP Server`;
  }
}

// Prompts endpoints can be added here when needed

// Start server
async function startServer() {
  try {
    // Connect to Neo4j
    await connectToNeo4j();
    
    // Initialize MCP server
    await initializeMCPServer();
    
    // Start Express server
    const port = process.env.MCP_PORT || 8080;
    app.listen(port, () => {
      logger.info(`Neo4j MCP Server running on port ${port}`);
      logger.info(`Capabilities endpoint: http://localhost:${port}/mcp`);
      logger.info(`Health check: http://localhost:${port}/health`);
    });
    
    // Handle graceful shutdown
    process.on('SIGTERM', async () => {
      logger.info('SIGTERM received, shutting down gracefully');
      if (driver) {
        await driver.close();
      }
      process.exit(0);
    });
    
    process.on('SIGINT', async () => {
      logger.info('SIGINT received, shutting down gracefully');
      if (driver) {
        await driver.close();
      }
      process.exit(0);
    });
    
  } catch (error) {
    logger.error('Failed to start server', { error: error.stack });
    process.exit(1);
  }
}

// Start the server
startServer();

// Export for testing
module.exports = { app, initializeMCPServer, startServer };