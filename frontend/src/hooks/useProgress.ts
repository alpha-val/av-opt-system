import { useEffect, useState, useRef, useCallback } from "react";

export interface ProgressEvent {
  job_id: string;
  stage: string;
  status: string;
  progress: number;
  seq: number;
  meta?: {
    scenario_id?: string;
    project_id?: string;
    document_id?: string;
    document_index?: number;
    total_documents?: number;
    current_file?: string;
    file_index?: number;
    total_files?: number;
    current_stage?: string;
    error?: string;
    errors?: Array<{
      document_id?: string;
      filename?: string;
      doc_id?: string;
      error?: string;
      warning?: string;
    }>;
    [key: string]: any;
  };
  timestamp: string;
}

interface UseProgressReturn {
  connected: boolean;
  progress: number;
  stage: string;
  status: string;
  error: string | null;
  meta: ProgressEvent["meta"] | null;
  reconnectAttempts: number;
}

export function useProgress(jobId: string | null): UseProgressReturn {
  const [connected, setConnected] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [meta, setMeta] = useState<ProgressEvent["meta"] | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentJobIdRef = useRef<string | null>(null);
  const maxReconnectAttempts = 5;
  const baseReconnectDelay = 1000; // 1 second

  const getWebSocketUrl = useCallback((jobId: string): string => {
    const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";
    const wsProtocol = apiBaseUrl.startsWith("https") ? "wss" : "ws";
    const wsBaseUrl = apiBaseUrl.replace(/^https?:\/\//, `${wsProtocol}://`);
    
    const token = localStorage.getItem("access_token");
    const authParam = token ? `&token=${encodeURIComponent(token)}` : "";
    
    return `${wsBaseUrl}/api/v1/ws/progress/${jobId}?verbosity=low${authParam}`;
  }, []);

  const connect = useCallback(
    (jobId: string) => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      // console.log("! ! ! ! ! \n\n Connecting WebSocket for job:", jobId);
      try {
        const wsUrl = getWebSocketUrl(jobId);
        // console.log(`Connecting WebSocket for job ${jobId} at ${new Date().toISOString()}:`, wsUrl);
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          // console.log(`WebSocket connected for job ${jobId} at ${new Date().toISOString()}`);
          setConnected(true);
          setError(null);
          setReconnectAttempts(0);
          // console.log(`WebSocket ready to receive progress events for job ${jobId}`);
        };

        ws.onmessage = (event) => {
          try {
            const data: ProgressEvent = JSON.parse(event.data);
            // console.log(
            //   `Progress event received for job ${jobId}:`,
            //   `stage=${data.stage}, status=${data.status}, progress=${data.progress}%`,
            //   `seq=${data.seq}`,
            //   data
            // );

            setProgress(data.progress);
            setStage(data.stage);
            setStatus(data.status);
            setMeta(data.meta || null);

            if (data.status !== "failed") {
              setError(null);
            } else if (data.meta?.error) {
              setError(data.meta.error);
            }
          } catch (err) {
            // console.error("Failed to parse progress event:", err, event.data);
            setError("Failed to parse progress update");
          }
        };

        ws.onerror = (event) => {
          // console.error("WebSocket error:", event);
          setError("WebSocket connection error");
        };

        ws.onclose = (event) => {
          // console.log(`WebSocket closed for job ${jobId}:`, event.code, event.reason);
          setConnected(false);
          wsRef.current = null;

          if (event.code !== 1000 && jobId) {
            setReconnectAttempts((prevAttempts) => {
              if (prevAttempts < maxReconnectAttempts) {
                const delay = baseReconnectDelay * Math.pow(2, prevAttempts);
                // console.log(
                //   `Attempting to reconnect in ${delay}ms (attempt ${prevAttempts + 1}/${maxReconnectAttempts})`
                // );

                reconnectTimeoutRef.current = setTimeout(() => {
                  connect(jobId);
                }, delay);
                
                return prevAttempts + 1;
              } else {
                setError("Failed to reconnect after multiple attempts");
                return prevAttempts;
              }
            });
          }
        };

        wsRef.current = ws;
      } catch (err) {
        // console.error("Failed to create WebSocket connection:", err);
        setError("Failed to establish WebSocket connection");
        setConnected(false);
      }
    },
    [getWebSocketUrl, maxReconnectAttempts, baseReconnectDelay]
  );

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, "User disconnected");
      wsRef.current = null;
    }

    setConnected(false);
    setReconnectAttempts(0);
  }, []);

  // Effect to manage connection lifecycle based on jobId changes
  useEffect(() => {
    const prevJobId = currentJobIdRef.current;
    
    if (jobId !== prevJobId) {
      // console.log(`[useEffect] JobId changed from ${prevJobId} to ${jobId}`);
      currentJobIdRef.current = jobId;
      
      if (jobId) {
        // console.log(`[useEffect] Connecting to job ${jobId}`);
        connect(jobId);
      } else {
        // console.log(`[useEffect] Disconnecting (no jobId)`);
        disconnect();
        setProgress(0);
        setStage("");
        setStatus("");
        setError(null);
        setMeta(null);
      }
    } else {
      // console.log(`[useEffect] JobId unchanged (${jobId}), skipping reconnect`);
    }

    return () => {
      // Cleanup on re-renders (no-op, handled by disconnect below)
    };
  }, [jobId, connect, disconnect]);

  // Separate effect for final cleanup on component unmount
  useEffect(() => {
    return () => {
      disconnect();
      currentJobIdRef.current = null;
    };
  }, [disconnect]);

  return {
    connected,
    progress,
    stage,
    status,
    error,
    meta,
    reconnectAttempts,
  };
}

