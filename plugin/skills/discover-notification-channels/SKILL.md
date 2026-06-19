---
name: discover-notification-channels
description: Analyze broadcast mechanisms (Email, Push, SMS, WhatsApp).
---

# Discover Notification Channels

Map the third-party integrations used to send messages.

## Focus Areas
- Channel implementations (app/channels/)
- Payload formatting and provider wrappers.

## Workflow
1. Route the hub folder agent to plugin/skills for this specific skill folder.
2. Invoke the native "discoverNotificationChannels" tool.
3. Return the multi-channel broadcast matrix.
