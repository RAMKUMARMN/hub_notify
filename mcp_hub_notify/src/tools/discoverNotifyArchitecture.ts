export async function discoverNotifyArchitectureHandler() {
  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(
          {
            framework: "FastAPI",
            structure: [
              "app/channels",
              "app/queue",
              "app/routers",
              "app/workers"
            ]
          },
          null,
          2
        ),
      },
    ],
  };
}