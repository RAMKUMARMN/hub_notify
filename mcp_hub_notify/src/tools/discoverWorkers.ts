import fs from "fs";
import path from "path";
import { HUB_NOTIFY_PATH } from "../config.js";

export async function discoverWorkersHandler() {
  const workersDir = path.join(
    HUB_NOTIFY_PATH,
    "app",
    "workers"
  );

  const workers = fs
    .readdirSync(workersDir)
    .filter(
      file =>
        file.endsWith(".py") &&
        file !== "__init__.py"
    );

  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(workers, null, 2),
      },
    ],
  };
}