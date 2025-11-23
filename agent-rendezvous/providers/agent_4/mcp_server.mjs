import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "poster-template-heuristic",
  version: "1.0.0"
});

server.tool("apply_heuristic", 
  { text: z.string() },
  async ({ text }) => {
    return { content: [{ type: "text", text: `Heuristic applied to: ${text.substring(0, 20)}` }] };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
