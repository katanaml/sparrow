import { NextRequest } from "next/server";
import { summarize_result } from "@/app/actions/inference";

// Same heartbeat-streaming pattern as /api/inference — keeps the connection
// active over long summarization calls so no proxy/tunnel in the path
// treats it as idle and kills it.
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { data, sparrowKey, modelName } = body as {
    data: unknown;
    sparrowKey: string;
    modelName: string;
  };

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      let closed = false;

      const heartbeat = setInterval(() => {
        if (closed) return;
        try {
          controller.enqueue(encoder.encode(JSON.stringify({ status: "processing" }) + "\n"));
        } catch {
          // controller already closed, ignore
        }
      }, 10_000);

      try {
        const result = await summarize_result(data, sparrowKey, modelName);
        controller.enqueue(encoder.encode(JSON.stringify({ status: "done", result }) + "\n"));
      } catch (err) {
        controller.enqueue(encoder.encode(JSON.stringify({ status: "error", message: String(err) }) + "\n"));
      } finally {
        closed = true;
        clearInterval(heartbeat);
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "application/x-ndjson",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  });
}