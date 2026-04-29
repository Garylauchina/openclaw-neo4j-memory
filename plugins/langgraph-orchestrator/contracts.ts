import { Type, type Static } from "@sinclair/typebox";

export const BeforeAgentStartRequestSchema = Type.Object({
  graph_id: Type.String(),
  session_id: Type.Union([Type.String(), Type.Null()]),
  channel: Type.Union([Type.String(), Type.Null()]),
  user_id: Type.Union([Type.String(), Type.Null()]),
  query: Type.String(),
  messages: Type.Optional(Type.Array(Type.Any())),
  metadata: Type.Optional(Type.Record(Type.String(), Type.Any())),
});

export const BeforeAgentStartResponseSchema = Type.Object({
  prepend_context: Type.Optional(Type.String()),
  planning_hints: Type.Optional(Type.Array(Type.String())),
  retrieval_metadata: Type.Optional(Type.Record(Type.String(), Type.Any())),
});

export const AgentEndRequestSchema = Type.Object({
  graph_id: Type.String(),
  session_id: Type.Union([Type.String(), Type.Null()]),
  channel: Type.Union([Type.String(), Type.Null()]),
  user_id: Type.Union([Type.String(), Type.Null()]),
  success: Type.Boolean(),
  conversation: Type.String(),
  messages: Type.Optional(Type.Array(Type.Any())),
  tool_outcomes: Type.Optional(Type.Any()),
  metadata: Type.Optional(Type.Record(Type.String(), Type.Any())),
});

export const AgentEndResponseSchema = Type.Object({
  event_written: Type.Optional(Type.Boolean()),
  summary_written: Type.Optional(Type.Boolean()),
  reflection_scheduled: Type.Optional(Type.Boolean()),
});

export const BeforeCompactionRequestSchema = Type.Object({
  graph_id: Type.String(),
  session_id: Type.Union([Type.String(), Type.Null()]),
  channel: Type.Union([Type.String(), Type.Null()]),
  user_id: Type.Union([Type.String(), Type.Null()]),
  conversation: Type.String(),
  message_count: Type.Optional(Type.Union([Type.Number(), Type.Null()])),
  compacting_count: Type.Optional(Type.Union([Type.Number(), Type.Null()])),
  token_count: Type.Optional(Type.Union([Type.Number(), Type.Null()])),
  metadata: Type.Optional(Type.Record(Type.String(), Type.Any())),
});

export const BeforeCompactionResponseSchema = Type.Object({
  checkpoint_written: Type.Optional(Type.Boolean()),
  archive_written: Type.Optional(Type.Boolean()),
});

export const HealthResponseSchema = Type.Object({
  status: Type.String(),
  details: Type.Optional(Type.Record(Type.String(), Type.Any())),
});

export type BeforeAgentStartRequest = Static<typeof BeforeAgentStartRequestSchema>;
export type BeforeAgentStartResponse = Static<typeof BeforeAgentStartResponseSchema>;
export type AgentEndRequest = Static<typeof AgentEndRequestSchema>;
export type AgentEndResponse = Static<typeof AgentEndResponseSchema>;
export type BeforeCompactionRequest = Static<typeof BeforeCompactionRequestSchema>;
export type BeforeCompactionResponse = Static<typeof BeforeCompactionResponseSchema>;
export type HealthResponse = Static<typeof HealthResponseSchema>;
