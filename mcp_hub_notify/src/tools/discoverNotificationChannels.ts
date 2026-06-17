import fs from "fs";
import path from "path";
import { HUB_NOTIFY_PATH } from "../config.js";

export async function discoverNotificationChannelsHandler() {
  const channelsDir = path.join(
    HUB_NOTIFY_PATH,
    "app",
    "channels"
  );

  const channels = fs
    .readdirSync(channelsDir)
    .filter(
      file =>
        file.endsWith(".py") &&
        file !== "__init__.py"
    );

  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(channels, null, 2),
      },
    ],
  };
}