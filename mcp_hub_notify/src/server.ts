import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { discoverNotifyArchitectureHandler } from "./tools/discoverNotifyArchitecture.js";
import { discoverNotificationChannelsHandler } from "./tools/discoverNotificationChannels.js";
import { discoverQueuesHandler } from "./tools/discoverQueues.js";
import { discoverWorkersHandler } from "./tools/discoverWorkers.js";
import { discoverApiRoutesHandler } from "./tools/discoverApiRoutes.js";
import { discoverEnvironmentConfigHandler } from "./tools/discoverEnvironmentConfig.js";
import { findFeatureHandler } from "./tools/findFeature.js";

const server = new McpServer({
  name: "hub-notify-mcp",
  version: "1.0.0",
});

server.tool(
  "discover_notify_architecture",
  "Discover notification service architecture",
  {},
  discoverNotifyArchitectureHandler
);

server.tool(
  "discover_notification_channels",
  "Discover notification channels",
  {},
  discoverNotificationChannelsHandler
);

server.tool(
  "discover_queues",
  "Discover queue infrastructure",
  {},
  discoverQueuesHandler
);

server.tool(
  "discover_workers",
  "Discover background workers",
  {},
  discoverWorkersHandler
);

server.tool(
  "discover_api_routes",
  "Discover notification API routes",
  {},
  discoverApiRoutesHandler
);

server.tool(
  "discover_environment_config",
  "Discover notification service configuration",
  {},
  discoverEnvironmentConfigHandler
);

server.tool(
  "find_feature",
  "Find notification-related files",
  {
    feature: z.string(),
  },
  findFeatureHandler
);

async function main() {
  const transport = new StdioServerTransport();

  await server.connect(transport);

  console.error("Hub Notify MCP Server Running...");
}

main().catch(console.error);