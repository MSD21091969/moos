import { useRef, useEffect } from 'react';
import { useWebRTC } from '../hooks/useWebRTC';

export interface PiPWindowProps {
  roomId: string;
  userId: string;
}

export function PiPWindow({ roomId, userId }: PiPWindowProps) {
  const { stream, error, connected } = useWebRTC({ roomId, userId, initiator: true });
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      <div className="bg-gray-800 px-3 py-2 flex items-center justify-between">
        <h1 className="text-sm font-medium">Collider PiP</h1>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-gray-400">{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-4">
        {error ? (
          <div className="text-center">
            <p className="text-red-400 mb-2">Error</p>
            <p className="text-sm text-gray-400">{error}</p>
          </div>
        ) : stream ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-contain rounded"
          />
        ) : (
          <div className="text-center">
            <p className="text-gray-400">Connecting...</p>
          </div>
        )}
      </div>

      <div className="bg-gray-800 px-3 py-2 text-center text-xs text-gray-500">
        Room: {roomId} • User: {userId}
      </div>
    </div>
  );
}
