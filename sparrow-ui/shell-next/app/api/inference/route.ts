import { NextRequest } from "next/server";
import { run_inference } from "@/app/actions/inference";

// Streams heartbeat chunks to the browser every 10s while the backend
// inference call is in flight, so no proxy/tunnel in the path (e.g. ngrok)
// sees a fully idle connection and kills it. The final chunk carries the
// real InferenceResult. run_inference itself still runs entirely server-side,
// unchanged from before — only the transport to the browser changed.
export async function POST(req: NextRequest) {
  const formData = await req.formData();
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
        const result = await run_inference(formData);
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