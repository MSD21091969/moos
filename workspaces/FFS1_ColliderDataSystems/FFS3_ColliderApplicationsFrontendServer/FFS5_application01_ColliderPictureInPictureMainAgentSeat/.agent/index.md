# FFS5 Collider Picture-in-Picture Communications - Agent Context

> Chrome Document Picture-in-Picture window for user-to-user communications via WebRTC

## Location

`D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\FFS5_application01_ColliderPictureInPictureMainAgentSeat\.agent\`

## Hierarchy

```
FFS0_Factory (Root)
  └── FFS1_ColliderDataSystems (IDE Context)
        └── FFS3_ColliderFrontend (Frontend Server)
              └── FFS5_PiP (This Application)
```

## Purpose

### User-Facing Purpose
The Picture-in-Picture (PiP) window provides always-on-top user-to-user communication:
- Video/audio calls between users via WebRTC
- Screen sharing capabilities
- Chat/messaging overlay
- Collaborative features (co-browsing, shared cursors)
- Stays visible while users browse other tabs/windows

### Technical Role
Leverages Chrome's Document Picture-in-Picture API to create a persistent communication window that:
- Establishes peer-to-peer WebRTC connections
- Manages video/audio streams
- Handles signaling via backend WebSocket server
- Provides rich communication UI in a floating window

### Key Responsibilities
- Establish and manage WebRTC peer connections
- Handle video/audio streaming (getUserMedia, RTCPeerConnection)
- Manage signaling (offer/answer/ICE candidates) via WebSocket
- Provide PiP window UI for video, controls, chat
- Handle connection state (connecting, connected, disconnected, reconnecting)
- Manage permissions (camera, microphone, screen share)

## Key Components

### Pages/Routes
- PiP window operates via Chrome's Document Picture-in-Picture API (not a web route)
- Opened via Chrome Extension action or from Sidepanel (FFS4)

### Main Components
- **VideoChatWindow** - Main PiP window container
- **LocalVideoStream** - User's own video/audio feed
- **RemoteVideoStream** - Peer's video/audio feed
- **ChatOverlay** - Text messages during call
- **ControlBar** - Mute, video on/off, screen share, end call
- **ConnectionStatus** - Connection quality indicator
- **ScreenShareViewer** - Screen sharing display

### State Management
- **Zustand store** for PiP UI state
- **WebRTC state** managed in custom hooks
- Key stores:
  - `usePipStore` - PiP window state, minimized, position
  - `useWebRTCStore` - Connection state, streams, peers
  - `useChatStore` - Chat messages, typing indicators

### Integration Points

**Backend APIs:**
- `WebSocket ws://backend/signaling` - WebRTC signaling channel
- `POST /api/calls/initiate` - Start a call
- `POST /api/calls/end` - End a call
- `GET /api/users/:id/online` - Check if user is online

**Chrome Extension:**
- Messages sent:
  - `PIP_WINDOW_OPENED` - Notify extension PiP opened
  - `CALL_STARTED` - Call initiated
  - `CALL_ENDED` - Call ended
  - `SCREEN_SHARE_STARTED` - Screen sharing started
- Messages received:
  - `INCOMING_CALL` - Incoming call notification
  - `PEER_JOINED` - Another user joined
  - `PEER_LEFT` - User left the call

**WebRTC Signaling:**
- Offer/Answer exchange via WebSocket
- ICE candidate exchange
- STUN/TURN server configuration

**Other FFS Apps:**
- FFS4 (Sidepanel): Initiates calls from user list
- FFS8 (my-tiny-data-collider): Call history logs

## Development

### Running Locally

The PiP window is part of the Chrome Extension (FFS2):

```bash
cd FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderMultiAgentsChromeExtension
pnpm dev
# Load unpacked extension in Chrome
# Initiate call from sidepanel to open PiP
```

### Key Dependencies

- `@plasmohq/messaging` - Chrome extension messaging
- WebRTC APIs (native browser APIs)
- WebSocket for signaling
- React - UI framework
- Zustand - State management

### Environment Variables

```bash
PLASMO_PUBLIC_SIGNALING_WS=ws://localhost:8000/ws/signaling
PLASMO_PUBLIC_STUN_SERVER=stun:stun.l.google.com:19302
PLASMO_PUBLIC_TURN_SERVER=turn:yourserver.com:3478
```

## Domain Context

- **Domain**: pip-main-seat
- **App Type**: picture-in-picture
- **Features**:
  - video_audio_calls - WebRTC video/audio
  - screen_sharing - Share screens
  - peer_chat - Text chat during calls
  - connection_quality - Monitor connection

**Note:** Despite the folder name "MainAgentSeat", this is for **user-to-user communications**. The AI Pilot/Agent Seat is integrated into FFS4 Sidepanel.

## Implementation Note

The actual implementation code lives in FFS2 Chrome Extension:
```
FFS2_ColliderBackends_MultiAgentChromeExtension/
└── ColliderMultiAgentsChromeExtension/
    └── src/
        ├── pipWindow.tsx              # PiP window entry point
        └── components/
            └── pip/
                ├── VideoChatWindow.tsx
                ├── LocalVideoStream.tsx
                ├── RemoteVideoStream.tsx
                ├── ControlBar.tsx
                └── ChatOverlay.tsx
```

## Related Documentation

- FFS3 Frontend: `../knowledge/codebase.md`
- FFS4 Sidepanel: `../FFS4_application00_ColliderSidepanelAppnodeBrowser/.agent/`
- Chrome Extension: `../../../FFS2_ColliderBackends_MultiAgentChromeExtension/.agent/`
- Backend Signaling: `../../../FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderGraphToolServer/.agent/` (WebSocket server)
