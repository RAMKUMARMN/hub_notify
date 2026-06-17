import * as fs from "fs";
import path from "path";
import { HUB_NOTIFY_PATH } from "../config.js";

export async function findFeatureHandler({
  feature,
}: {
  feature: string;
}) {
  const root = path.join(HUB_NOTIFY_PATH, "app");

  const matches: string[] = [];

  function scan(
    dir: string,
    depth: number = 0
  ) {
    if (depth > 5) return;

    try {
      const entries = fs.readdirSync(dir, {
        withFileTypes: true,
      });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (
          entry.isDirectory() &&
          !entry.name.startsWith(".")
        ) {
          if (
            entry.name
              .toLowerCase()
              .includes(feature.toLowerCase())
          ) {
            matches.push(
              path.relative(
                HUB_NOTIFY_PATH,
                fullPath
              )
            );
          }

          scan(fullPath, depth + 1);
        }

        if (entry.isFile()) {
          if (
            entry.name
              .toLowerCase()
              .includes(feature.toLowerCase())
          ) {
            matches.push(
              path.relative(
                HUB_NOTIFY_PATH,
                fullPath
              )
            );
          }
        }
      }
    } catch {
      // Ignore unreadable directories
    }
  }

  scan(root);

  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(
          {
            feature,
            found: matches.length > 0,
            locations: matches,
          },
          null,
          2
        ),
      },
    ],
  };
}