export async function discoverEnvironmentConfigHandler() {
  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(
          {
            configFile: "app/config.py",
            entryPoint: "app/main.py"
          },
          null,
          2
        ),
      },
    ],
  };
}