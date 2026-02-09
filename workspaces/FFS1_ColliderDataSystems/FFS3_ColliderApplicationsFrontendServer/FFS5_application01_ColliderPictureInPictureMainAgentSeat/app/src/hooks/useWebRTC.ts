import { useEffect, useRef, useState } from 'react';
import SimplePeer from 'simple-peer';

export interface UseWebRTCOptions {
  roomId: string;
  userId: string;
  initiator?: boolean;
}

export function useWebRTC({ roomId, userId, initiator = false }: UseWebRTCOptions) {
  const [peer, setPeer] = useState<SimplePeer.Instance | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Get user media
    navigator.mediaDevices
      .getUserMedia({ video: true, audio: true })
      .then((mediaStream) => {
        setStream(mediaStream);

        // Connect to WebRTC signaling server
        const ws = new WebSocket('ws://localhost:8000/api/v1/ws/rtc/');
        wsRef.current = ws;

        ws.onopen = () => {
          // Join room
          ws.send(JSON.stringify({ type: 'join', roomId, userId }));
        };

        ws.onmessage = async (event) => {
          const data = JSON.parse(event.data);

          if (data.type === 'joined') {
            // Create peer connection
            const peerInstance = new SimplePeer({
              initiator,
              trickle: false,
              stream: mediaStream,
            });

            peerInstance.on('signal', (signal) => {
              // Send offer/answer to other peer via signaling server
              ws.send(
                JSON.stringify({
                  type: initiator ? 'offer' : 'answer',
                  sdp: signal,
                  targetUserId: data.targetUserId || 'other-user',
                })
              );
            });

            peerInstance.on('stream', (remoteStream) => {
              // Handle remote stream
              console.log('Received remote stream', remoteStream);
            });

            peerInstance.on('connect', () => {
              setConnected(true);
            });

            peerInstance.on('error', (err) => {
              setError(`Peer connection error: ${err.message}`);
            });

            setPeer(peerInstance);
          } else if (data.type === 'offer') {
            // Received offer from another peer
            if (peer) {
              peer.signal(data.sdp);
            }
          } else if (data.type === 'answer') {
            // Received answer from another peer
            if (peer) {
              peer.signal(data.sdp);
            }
          } else if (data.type === 'ice') {
            // Handle ICE candidate
            if (peer) {
              peer.signal(data.candidate);
            }
          }
        };

        ws.onerror = () => {
          setError('WebSocket connection error');
        };

        ws.onclose = () => {
          setConnected(false);
        };
      })
      .catch((err) => {
        setError(`Media access error: ${err.message}`);
      });

    return () => {
      if (peer) {
        peer.destroy();
      }
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [roomId, userId, initiator]);

  return { peer, stream, error, connected };
}
