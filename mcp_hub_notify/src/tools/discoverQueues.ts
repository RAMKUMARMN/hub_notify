import fs from "fs";
import path from "path";
import { HUB_NOTIFY_PATH } from "../config.js";

export async function discoverQueuesHandler() {
  const queueDir = path.join(
    HUB_NOTIFY_PATH,
    "app",
    "queue"
  );

  const queueFiles = fs
    .readdirSync(queueDir)
    .filter(
      file =>
        file.endsWith(".py") &&
        file !== "__init__.py"
    );

  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(queueFiles, null, 2),
      },
    ],
  };
}